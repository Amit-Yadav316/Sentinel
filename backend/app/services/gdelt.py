"""GDELT-style news feed. Cache-first: reads data/cache/gdelt_baseline.json
(the calm-state headlines that establish Hormuz ≈ 45). Live mode would query the
GDELT 2.0 DOC API for energy/maritime/Gulf keywords; offline it returns a
curated baseline fixture written at first run.
"""

from __future__ import annotations

import json

from app.config import DATA_CACHE_DIR

_CACHE = DATA_CACHE_DIR / "gdelt_baseline.json"

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
