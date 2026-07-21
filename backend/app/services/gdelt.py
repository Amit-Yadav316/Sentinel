"""GDELT news feed.

* ``get_baseline_headlines`` — the curated calm-state fixture that keeps corridor
  scores at their structural floors for the scripted demo.
* ``fetch_live_headlines`` — a REAL, keyless pull from the GDELT 2.0 DOC API,
  filtered to energy/maritime/Gulf keywords. Used for a *display* "live signal
  feed" (classified by the extraction agent) so the demo can show genuine news
  ingestion without disturbing the scripted escalation. Cached + offline-safe.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from app.config import DATA_CACHE_DIR

_CACHE = DATA_CACHE_DIR / "gdelt_baseline.json"
_LIVE_CACHE = DATA_CACHE_DIR / "gdelt_live.json"

_GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_QUERY = (
    '("Strait of Hormuz" OR Hormuz OR "Red Sea" OR "Bab-el-Mandeb" OR tanker '
    'OR "crude oil" OR OPEC OR "oil sanctions") sourcelang:english'
)

# Calm baseline: routine headlines, mostly non-Hormuz or low-severity, so
# corridor scores rest near their structural floors.
_BASELINE = [
    "India crude imports steady in June as refiners lift Gulf and US barrels",
    "OPEC+ keeps output policy unchanged at monthly review",
    "Brent holds near $82 as demand outlook stabilises",
    "Routine naval patrol reported in Gulf of Oman, shipping unaffected",
    "West African crude differentials soft on ample Atlantic supply",
    "Suez transits normal; Red Sea insurance premiums ease slightly",
]


def get_baseline_headlines() -> list[str]:
    if _CACHE.exists():
        return json.loads(_CACHE.read_text())
    _CACHE.write_text(json.dumps(_BASELINE, indent=2))
    return _BASELINE


def _parse_seendate(raw: str) -> str:
    """GDELT seendate like '20260720T120000Z' -> ISO 8601."""
    try:
        return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        return datetime.now(timezone.utc).isoformat()


def fetch_live_headlines(max_records: int = 15, timespan: str = "3d") -> list[dict] | None:
    """Real GDELT DOC 2.0 pull (no key). Returns [{headline,url,domain,seendate}]
    or None on failure (caller falls back to cache/baseline)."""
    try:
        r = httpx.get(
            _GDELT_URL,
            params={
                "query": _QUERY,
                "mode": "artlist",
                "format": "json",
                "maxrecords": max_records,
                "timespan": timespan,
                "sort": "datedesc",
            },
            headers={"User-Agent": "Sentinel/0.1 (hackathon demo)"},
            timeout=10,
        )
        r.raise_for_status()
        articles = r.json().get("articles", []) or []
        out = [
            {
                "headline": a["title"].strip(),
                "url": a.get("url"),
                "domain": a.get("domain"),
                "seendate": _parse_seendate(a.get("seendate", "")),
            }
            for a in articles
            if a.get("title")
        ]
        if out:
            _LIVE_CACHE.write_text(json.dumps(out, indent=2))
        return out or None
    except Exception:  # noqa: BLE001 — any failure => caller falls back
        return None


def get_cached_live_headlines() -> list[dict]:
    if _LIVE_CACHE.exists():
        return json.loads(_LIVE_CACHE.read_text())
    return []
