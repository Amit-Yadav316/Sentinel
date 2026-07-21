"""AIS vessel service — real live path + a geographically-grounded fallback.

Two modes, mirroring the rest of the app:

* **live** — a real AISStream.io websocket client (``fetch_live_ais``). Given a
  free ``AISSTREAM_API_KEY`` it subscribes to the Strait of Hormuz,
  Bab-el-Mandeb, and Indian west-coast bounding boxes, collects real tanker
  positions for a few seconds, and caches them (``synthetic=False``).
* **fallback** — a deterministic synthetic fixture, but placed inside real
  maritime zones (Persian Gulf, Gulf of Oman, Arabian Sea lanes, Bab-el-Mandeb,
  Indian west-coast anchorages) so vessels sit on water over the real basemap.
  Always flagged ``synthetic=True`` and shown with a "simulated" chip.

The parser (:func:`parse_ais_message`) is a pure function so the real-data path
is unit-tested without a network/key.
"""

from __future__ import annotations

import json
import random

from app.config import DATA_CACHE_DIR, get_settings

_CACHE = DATA_CACHE_DIR / "vessels.json"

_NAMES = [
    "Front", "Nissos", "Maran", "Delta", "New", "Sea", "Ocean", "Pacific",
    "Desh", "Swarna", "Gulf", "Cosmos", "Sonangol", "Nordic", "Olympic", "Astro",
]
_SUFFIX = ["Voyager", "Pride", "Trader", "Star", "Spirit", "Glory", "Falcon", "Horizon"]

# Real maritime zones (all over water) with a corridor tag for map colouring.
# (corridor, (lat_min, lat_max), (lon_min, lon_max), weight)
_ZONES: list[tuple[str, tuple[float, float], tuple[float, float], float]] = [
    ("hormuz", (24.0, 27.0), (53.0, 57.0), 0.28),          # Persian Gulf / Hormuz approach
    ("hormuz", (22.0, 25.0), (58.0, 61.0), 0.18),          # Gulf of Oman
    ("hormuz", (19.0, 23.0), (62.0, 67.0), 0.16),          # Arabian Sea lane to India
    ("hormuz", (20.0, 22.5), (68.0, 70.5), 0.10),          # Gujarat west-coast anchorage
    ("red_sea", (12.0, 15.0), (43.0, 45.0), 0.10),         # Bab-el-Mandeb
    ("cape", (8.0, 16.0), (60.0, 66.0), 0.08),             # Indian Ocean (Cape approach)
    ("hormuz", (10.0, 14.0), (72.0, 74.0), 0.06),          # off Mangalore / Kochi
    ("pacific_fareast", (11.0, 15.0), (80.0, 83.5), 0.04), # Bay of Bengal (east coast)
]

# AISStream bounding boxes: [[lat, lon], [lat, lon]] corner pairs.
AIS_BOUNDING_BOXES = [
    [[24.0, 50.0], [30.0, 58.0]],   # Strait of Hormuz / Persian Gulf
    [[11.0, 42.0], [16.0, 45.0]],   # Bab-el-Mandeb
    [[15.0, 66.0], [23.0, 73.0]],   # Indian west coast
]


def generate_vessels(count: int = 40, seed: int = 42) -> list[dict]:
    """Deterministic synthetic tankers placed inside real maritime zones."""
    rng = random.Random(seed)
    weights = [z[3] for z in _ZONES]
    vessels: list[dict] = []
    for i in range(count):
        corridor, (la0, la1), (lo0, lo1), _ = rng.choices(_ZONES, weights=weights, k=1)[0]
        lat = round(rng.uniform(la0, la1), 3)
        lon = round(rng.uniform(lo0, lo1), 3)
        vessels.append(
            {
                "mmsi": str(419000000 + i),
                "name": f"{rng.choice(_NAMES)} {rng.choice(_SUFFIX)}",
                "lat": lat,
                "lon": lon,
                "corridor": corridor,
                "synthetic": True,
            }
        )
    return vessels


def parse_ais_message(msg: dict) -> dict | None:
    """Pure parser for an AISStream ``PositionReport`` frame → our vessel shape.

    Returns ``None`` for non-position frames so callers can skip them.
    """
    if msg.get("MessageType") != "PositionReport":
        return None
    meta = msg.get("MetaData", {})
    lat = meta.get("latitude")
    lon = meta.get("longitude")
    if lat is None or lon is None:
        return None
    return {
        "mmsi": str(meta.get("MMSI", "")),
        "name": (meta.get("ShipName") or "Unknown").strip() or "Unknown",
        "lat": round(float(lat), 4),
        "lon": round(float(lon), 4),
        "corridor": None,
        "synthetic": False,
    }


async def fetch_live_ais(seconds: float = 12.0, max_vessels: int = 60) -> list[dict] | None:
    """Collect real tanker positions from AISStream for ``seconds``.

    Requires ``AISSTREAM_API_KEY``. Returns a list of vessels (synthetic=False)
    or ``None`` if no key / any failure — caller falls back to the fixture.
    """
    settings = get_settings()
    key = settings.aisstream_api_key
    if not key:
        return None
    try:
        import asyncio

        import websockets  # bundled with uvicorn[standard]

        subscribe = {
            "APIKey": key,
            "BoundingBoxes": AIS_BOUNDING_BOXES,
            "FilterMessageTypes": ["PositionReport"],
        }
        seen: dict[str, dict] = {}

        async def _collect() -> None:
            async with websockets.connect("wss://stream.aisstream.io/v0/stream") as ws:
                await ws.send(json.dumps(subscribe))
                async for raw in ws:
                    parsed = parse_ais_message(json.loads(raw))
                    if parsed and parsed["mmsi"]:
                        seen[parsed["mmsi"]] = parsed
                        if len(seen) >= max_vessels:
                            return

        try:
            await asyncio.wait_for(_collect(), timeout=seconds)
        except asyncio.TimeoutError:
            pass  # time-boxed collection is expected

        vessels = list(seen.values())
        if vessels:
            _CACHE.write_text(json.dumps(vessels, indent=2))
        return vessels or None
    except Exception:  # noqa: BLE001 — any failure => fall back to fixture
        return None


def get_vessels() -> list[dict]:
    """Cached vessels (live snapshot if one was collected, else the fixture)."""
    if _CACHE.exists():
        return json.loads(_CACHE.read_text())
    vessels = generate_vessels()
    _CACHE.write_text(json.dumps(vessels, indent=2))
    return vessels
