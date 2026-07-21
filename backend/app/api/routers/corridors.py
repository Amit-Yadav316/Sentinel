"""Corridor definitions, live risk scores (+ evidence), vessels, prices."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agents import risk_scoring, signal_extraction
from app.db import get_db
from app.models import Vessel
from app.services import ais, corpus, gdelt, prices

router = APIRouter(tags=["corridors"])


@router.get("/corridors")
def list_corridors() -> list[dict]:
    """Corridor definitions for the map (arcs, chokepoints, baseline share)."""
    return corpus.corridors()


@router.get("/corridors/risk")
def corridor_risk(db: Session = Depends(get_db)) -> list[dict]:
    """Latest risk score per corridor with full evidence trail."""
    out = []
    for rs in risk_scoring.latest_scores(db):
        ev = rs.evidence
        out.append(
            {
                "corridor": rs.corridor,
                "name": ev.get("name"),
                "score": rs.score,
                "baseline": ev.get("baseline"),
                "weighted_sum": ev.get("weighted_sum"),
                "formula": ev.get("formula"),
                "computed_at": rs.computed_at.isoformat(),
                "contributions": ev.get("contributions", []),
            }
        )
    return out


def _vessel_dict(v: Vessel) -> dict:
    return {
        "mmsi": v.mmsi,
        "name": v.name,
        "lat": v.lat,
        "lon": v.lon,
        "corridor": v.corridor,
        "synthetic": v.synthetic,
    }


@router.get("/vessels")
def vessels(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Vessel)).scalars().all()
    return [_vessel_dict(v) for v in rows]


@router.get("/vessels/live")
async def vessels_live(db: Session = Depends(get_db)) -> dict:
    """Attempt a real AISStream feed (needs AISSTREAM_API_KEY). On success the
    live snapshot replaces the vessel set and is returned with source=live;
    otherwise the labelled synthetic fixture is returned."""
    live = await ais.fetch_live_ais()
    if live:
        db.execute(delete(Vessel))
        for v in live:
            db.add(
                Vessel(
                    mmsi=v["mmsi"],
                    name=v["name"],
                    lat=v["lat"],
                    lon=v["lon"],
                    corridor=v.get("corridor"),
                    synthetic=False,
                )
            )
        db.commit()
        return {"source": "live", "count": len(live), "vessels": live}
    rows = db.execute(select(Vessel)).scalars().all()
    return {"source": "synthetic", "count": len(rows), "vessels": [_vessel_dict(v) for v in rows]}


@router.get("/news/live")
def news_live() -> dict:
    """Real GDELT headlines classified by the extraction agent (display-only —
    NOT fed into risk scoring, so the scripted demo is unaffected)."""
    live = gdelt.fetch_live_headlines() or gdelt.get_cached_live_headlines()
    source = "live" if live else "baseline"
    if not live:
        live = [{"headline": h, "url": None, "domain": None, "seendate": None}
                for h in gdelt.get_baseline_headlines()]
    items = []
    for a in live[:12]:
        ex = signal_extraction.extract(a["headline"])
        items.append(
            {
                "headline": a["headline"],
                "url": a.get("url"),
                "domain": a.get("domain"),
                "seendate": a.get("seendate"),
                "event_type": ex.event_type,
                "corridor": None if ex.corridor == "none" else ex.corridor,
                "severity": ex.severity,
                "confidence": ex.confidence,
            }
        )
    return {"source": source, "count": len(items), "items": items}


@router.get("/prices/brent")
def brent() -> dict:
    """Cached Brent — instant, offline-safe. Frontend loads this first."""
    series = prices.get_brent_series()
    return {
        "symbol": "BRENT",
        "unit": "USD/bbl",
        "latest": series[-1]["value"],
        "series": series,
        "source": "cache",
    }


@router.get("/prices/brent/live")
async def brent_live() -> dict:
    """Attempt a real-time Brent quote (Yahoo, timeout-bounded). Falls back to
    cache on any failure so the demo never hangs offline."""
    live = await prices.fetch_live_brent()
    if live:
        return {
            "symbol": "BRENT",
            "unit": "USD/bbl",
            "latest": live["value"],
            "series": live["series"],
            "source": "live",
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    series = prices.get_brent_series()
    return {
        "symbol": "BRENT",
        "unit": "USD/bbl",
        "latest": series[-1]["value"],
        "series": series,
        "source": "cache",
    }
