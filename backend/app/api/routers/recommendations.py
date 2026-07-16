"""Recommendation cards + one-page brief export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import procurement
from app.db import get_db
from app.models import Recommendation, ScenarioRun

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations")
def list_recommendations(run_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    stmt = select(Recommendation)
    if run_id is not None:
        stmt = stmt.where(Recommendation.run_id == run_id)
    rows = db.execute(stmt.order_by(Recommendation.run_id.desc(), Recommendation.rank)).scalars().all()
    return [{"id": r.id, "run_id": r.run_id, "rank": r.rank, "payload": r.payload} for r in rows]


@router.get("/recommendations/{rec_id}/brief", response_class=PlainTextResponse)
def brief(rec_id: int, db: Session = Depends(get_db)) -> str:
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="recommendation not found")
    run = db.get(ScenarioRun, rec.run_id)
    all_recs = db.execute(
        select(Recommendation).where(Recommendation.run_id == run.id).order_by(Recommendation.rank)
    ).scalars().all()
    return procurement.render_brief(run, all_recs)


@router.get("/runs/{run_id}/brief", response_class=PlainTextResponse)
def run_brief(run_id: int, db: Session = Depends(get_db)) -> str:
    run = db.get(ScenarioRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    recs = db.execute(
        select(Recommendation).where(Recommendation.run_id == run_id).order_by(Recommendation.rank)
    ).scalars().all()
    return procurement.render_brief(run, recs)
