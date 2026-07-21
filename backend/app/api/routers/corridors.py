"""Corridor definitions, live risk scores (+ evidence), vessels, prices."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import risk_scoring
from app.db import get_db
from app.models import Vessel
from app.services import corpus, prices

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


@router.get("/vessels")
def vessels(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Vessel)).scalars().all()
    return [
        {
            "mmsi": v.mmsi,
            "name": v.name,
            "lat": v.lat,
            "lon": v.lon,
            "corridor": v.corridor,
            "synthetic": v.synthetic,
        }
        for v in rows
    ]


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
