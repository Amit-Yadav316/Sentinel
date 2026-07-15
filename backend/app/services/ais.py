"""AIS vessel service.

CLAUDE.md fallback taken: the AISStream free tier is a live websocket we can't
depend on for an offline demo, so we generate a **deterministic synthetic**
fixture of ~36 tankers with plausible positions along each corridor arc, cached
to data/cache/vessels.json and clearly flagged ``synthetic=True`` (the UI shows a
"simulated" chip). A live/replay client would stream real AIS into the same shape.
"""

from __future__ import annotations

import json
import random

from app.config import DATA_CACHE_DIR
from app.services import corpus

_CACHE = DATA_CACHE_DIR / "vessels.json"

_NAMES = [
    "Front", "Nissos", "Maran", "Delta", "New", "Sea", "Ocean", "Pacific",
    "Desh", "Swarna", "Gulf", "Cosmos", "Sonangol", "Nordic", "Olympic", "Astro",
]
_SUFFIX = ["Voyager", "Pride", "Trader", "Star", "Spirit", "Glory", "Falcon", "Horizon"]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def generate_vessels(count: int = 36, seed: int = 42) -> list[dict]:
    """Deterministic synthetic tanker positions strung along corridor arcs."""
    rng = random.Random(seed)
    corr = corpus.corridors()
    # Distribute vessels across corridors weighted by baseline share.
    weights = [c["baseline_share"] for c in corr]
    vessels: list[dict] = []
    for i in range(count):
        c = rng.choices(corr, weights=weights, k=1)[0]
        t = rng.random()
        o, d = c["origin"], c["destination"]
        lat = round(_lerp(o["lat"], d["lat"], t) + rng.uniform(-0.8, 0.8), 3)
        lon = round(_lerp(o["lon"], d["lon"], t) + rng.uniform(-0.8, 0.8), 3)
        name = f"{rng.choice(_NAMES)} {rng.choice(_SUFFIX)}"
        vessels.append(
            {
                "mmsi": str(419000000 + i),
                "name": name,
                "lat": lat,
                "lon": lon,
                "corridor": c["id"],
                "synthetic": True,
            }
        )
    return vessels


def get_vessels() -> list[dict]:
    if _CACHE.exists():
        return json.loads(_CACHE.read_text())
    vessels = generate_vessels()
    _CACHE.write_text(json.dumps(vessels, indent=2))
    return vessels
