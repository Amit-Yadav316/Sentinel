"""Brent price service. Cache-first: reads data/cache/brent.json; live mode
pulls BZ=F via yfinance and rewrites the cache. Offline it synthesises a
deterministic ~30-day series so the demo always has a price strip.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta

from app.config import DATA_CACHE_DIR, get_settings
from app.services import corpus

_CACHE = DATA_CACHE_DIR / "brent.json"


def _synthesize() -> list[dict]:
    base = corpus.assumptions()["prices"]["brent_baseline_usd"]
    today = date(2026, 7, 22)
    series = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        # gentle deterministic wave around the baseline
        val = round(base + 3.0 * math.sin(i / 4.0) - 1.5 * math.cos(i / 7.0), 2)
        series.append({"date": d.isoformat(), "value": val})
    return series


def get_brent_series() -> list[dict]:
    settings = get_settings()
    if settings.data_mode == "live":
        try:
            import yfinance as yf  # type: ignore

            hist = yf.Ticker("BZ=F").history(period="1mo")
            series = [
                {"date": idx.date().isoformat(), "value": round(float(row["Close"]), 2)}
                for idx, row in hist.iterrows()
            ]
            if series:
                _CACHE.write_text(json.dumps(series, indent=2))
                return series
        except Exception:  # noqa: BLE001 — fall through to cache
            pass
    if _CACHE.exists():
        return json.loads(_CACHE.read_text())
    series = _synthesize()
    _CACHE.write_text(json.dumps(series, indent=2))
    return series


def latest_brent() -> float:
    return get_brent_series()[-1]["value"]
