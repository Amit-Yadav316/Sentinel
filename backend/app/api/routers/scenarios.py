"""Scenario listing, manual runs, run retrieval, and the live escalation demo."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import procurement, scenario
from app.api.ws import manager
from app.db import SessionLocal, get_db
from app.models import Scenario, ScenarioRun
from app.seed.inject_escalation import ESCALATION, inject_step
from app.services import corpus

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios")
def list_scenarios() -> list[dict]:
    return [
        {"name": s["name"], "title": s["title"], "description": s["description"].strip()}
        for s in corpus.scenarios()
    ]


@router.post("/scenarios/{name}/run")
def run_scenario(name: str, db: Session = Depends(get_db)) -> dict:
    try:
        run = scenario.run_named_scenario(db, name, triggered_by="manual")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    recs = procurement.generate_recommendations(db, run)
    return {
        "run_id": run.id,
        "triggered_by": run.triggered_by,
        "result": run.result,
        "recommendations": [{"id": r.id, "rank": r.rank, "payload": r.payload} for r in recs],
    }


@router.get("/scenario-runs")
def list_runs(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(ScenarioRun).order_by(ScenarioRun.created_at.desc())).scalars().all()
    out = []
    for r in rows:
        sc = db.get(Scenario, r.scenario_id)
        out.append(
            {
                "id": r.id,
                "scenario_name": sc.name,
                "scenario_title": sc.title,
                "triggered_by": r.triggered_by,
                "created_at": r.created_at.isoformat(),
                "result": r.result,
            }
        )
    return out


@router.get("/scenario-runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    run = db.get(ScenarioRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    sc = db.get(Scenario, run.scenario_id)
    return {
        "id": run.id,
        "scenario_name": sc.name,
        "scenario_title": sc.title,
        "triggered_by": run.triggered_by,
        "created_at": run.created_at.isoformat(),
        "result": run.result,
    }


async def _run_escalation(step_delay: float) -> None:
    """Background task: inject each escalation headline, broadcast the payload."""
    def _one(headline: str) -> dict:
        db = SessionLocal()
        try:
            return inject_step(db, headline)
        finally:
            db.close()

    await manager.broadcast({"type": "demo_start", "steps": len(ESCALATION)})
    for i, headline in enumerate(ESCALATION, start=1):
        payload = await asyncio.to_thread(_one, headline)
        payload["step"] = i
        await manager.broadcast(payload)
        await asyncio.sleep(step_delay)
    await manager.broadcast({"type": "demo_end"})


@router.post("/demo/escalate")
async def escalate(step_delay: float = 5.0) -> dict:
    """Kick off the scripted Hormuz escalation; updates stream over /risk/stream."""
    asyncio.create_task(_run_escalation(step_delay))
    return {"status": "started", "steps": len(ESCALATION), "step_delay": step_delay}
