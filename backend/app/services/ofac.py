"""OFAC SDN sanctions flags. Live mode would download + parse the SDN CSV and
filter to tanker/entity names; offline it returns a small cached fixture of
flagged names used to badge recommendations (e.g. Urals sanctions caveat).
"""

from __future__ import annotations

import json

from app.config import DATA_CACHE_DIR

_CACHE = DATA_CACHE_DIR / "ofac_flags.json"

_FLAGS = {
    "flagged_origins": ["Russia"],
    "flagged_vessels": ["SUN ARROWS", "KRASNO", "NS LEADER"],
    "note": "G7 price-cap / SDN designations relevant to crude tankers (cached snapshot).",
}


def get_flags() -> dict:
    if _CACHE.exists():
        return json.loads(_CACHE.read_text())
    _CACHE.write_text(json.dumps(_FLAGS, indent=2))
    return _FLAGS
