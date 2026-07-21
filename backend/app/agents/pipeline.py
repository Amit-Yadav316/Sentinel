"""End-to-end agent pipeline: the loop the whole product is built around.

    ingest_event(headline)  →  SignalExtraction  →  persist Event
                            →  RiskScoring.recompute_all
                            →  Scenario.maybe_auto_trigger
                            →  Procurement.generate_recommendations

Returns a compact dict the API/websocket can broadcast so the frontend can move
the risk score and pop the scenario + recommendation cards live.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.agents import procurement, risk_scoring, scenario, signal_extraction
from app.models import Event


def ingest_event(
    db: Session,
    headline: str,
    *,
    source: str = "injected",
    url: str | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    """Ingest one raw headline through the full loop. Returns an event summary
    plus any auto-triggered scenario run + recommendations."""
    occurred_at = occurred_at or datetime.now(timezone.utc)

    extraction = signal_extraction.extract(headline)
    event = Event(
        source=source,
        headline=headline,
        url=url,
        occurred_at=occurred_at,
        event_type=extraction.event_type,
        corridor=None if extraction.corridor == "none" else extraction.corridor,
        severity=extraction.severity,
        confidence=extraction.confidence,
        entities=extraction.entities,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    risk_scoring.recompute_all(db, now=occurred_at)
    auto_run = scenario.maybe_auto_trigger(db)

    payload: dict[str, Any] = {
        "type": "event",
        "event": {
            "id": event.id,
            "headline": event.headline,
            "event_type": event.event_type,
            "corridor": event.corridor,
            "severity": event.severity,
        },
        "risk": [
            {"corridor": rs.corridor, "score": rs.score, "name": rs.evidence.get("name")}
            for rs in risk_scoring.latest_scores(db)
        ],
    }

    if auto_run is not None:
        recs = procurement.generate_recommendations(db, auto_run)
        payload["scenario_run"] = {
            "id": auto_run.id,
            "triggered_by": auto_run.triggered_by,
            "result": auto_run.result,
        }
        payload["recommendations"] = [
            {"id": r.id, "rank": r.rank, "payload": r.payload} for r in recs
        ]

    return payload
