"""Brent price service. Cache-first: reads data/cache/brent.json; live mode
pulls BZ=F via yfinance and rewrites the cache. Offline it synthesises a
deterministic ~30-day series so the demo always has a price strip.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone

import httpx

from app.config import DATA_CACHE_DIR, get_settings
from app.services import corpus

_CACHE = DATA_CACHE_DIR / "brent.json"

# Yahoo Finance chart API for Brent front-month (BZ=F). A direct httpx call is
# ~2s vs ~20s through the yfinance machinery, so we use it for the live path.
_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F"


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


def _parse_chart(payload: dict) -> dict:
    """Extract {value, series} from a Yahoo chart response."""
    res = payload["chart"]["result"][0]
    meta = res["meta"]
    stamps = res.get("timestamp", []) or []
    closes = res["indicators"]["quote"][0].get("close", []) or []
    series = [
        {"date": datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat(), "value": round(float(c), 2)}
        for t, c in zip(stamps, closes)
        if c is not None
    ]
    value = meta.get("regularMarketPrice")
    value = round(float(value), 2) if value is not None else (series[-1]["value"] if series else 0.0)
    return {"value": value, "series": series}


async def fetch_live_brent() -> dict | None:
    """Live Brent via a fast, timeout-bounded direct call. Returns
    {value, series} on success (and refreshes the cache), or None on any
    failure — so the caller can fall back to cache and the demo never hangs.
    """
    try:
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = await client.get(_YAHOO_URL, params={"interval": "1d", "range": "1mo"})
            r.raise_for_status()
            data = _parse_chart(r.json())
        if data["series"]:
            _CACHE.write_text(json.dumps(data["series"], indent=2))
        return data
    except Exception:  # noqa: BLE001 — any failure => fall back to cache
        return None
