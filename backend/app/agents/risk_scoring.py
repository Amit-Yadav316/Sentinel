"""RiskScoringAgent — deterministic, transparent corridor risk model.

No ML. For each corridor:

    weighted_sum = Σ_event  severity × type_weight × decay(age)
    decay(age)   = 0.5 ** (age_hours / half_life_hours)
    score        = baseline + (100 − baseline) × logistic01(weighted_sum)

where ``logistic01`` normalises a logistic curve so weighted_sum=0 → 0 bump and
large weighted_sum → full bump toward 100. Every score persists its complete
evidence trail (each event's weight, severity, age, decay, contribution).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, RiskScore
from app.services import corpus


def _logistic01(weighted_sum: float, midpoint: float, scale: float) -> float:
    """Logistic squash normalised to [0,1): 0 at ws=0, →1 as ws→∞."""

    def logistic(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-(x - midpoint) / scale))

    base = logistic(0.0)
    return (logistic(weighted_sum) - base) / (1.0 - base)


def score_corridor(
    corridor_id: str,
    events: list[dict[str, Any]],
    now: datetime,
    risk_cfg: dict[str, Any],
) -> dict[str, Any]:
    """Pure scoring function.

    ``events`` items: {event_id, headline, event_type, severity, occurred_at}.
    Returns {score, baseline, weighted_sum, contributions, formula}.
    """
    baseline = float(risk_cfg["baseline_floor"].get(corridor_id, 10))
    type_weights = risk_cfg["type_weights"]
    half_life = risk_cfg["decay_half_life_hours"]
    midpoint = risk_cfg["squash_midpoint"]
    scale = risk_cfg["squash_scale"]

    contributions: list[dict[str, Any]] = []
    weighted_sum = 0.0
    for ev in events:
        if ev.get("severity") is None:
            continue
        weight = float(type_weights.get(ev.get("event_type", "other"), type_weights["other"]))
        occurred = ev["occurred_at"]
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        age_hours = max(0.0, (now - occurred).total_seconds() / 3600.0)
        decay = 0.5 ** (age_hours / half_life)
        contribution = float(ev["severity"]) * weight * decay
        weighted_sum += contribution
        contributions.append(
            {
                "event_id": ev.get("event_id"),
                "headline": ev["headline"],
                "event_type": ev.get("event_type", "other"),
                "weight": round(weight, 2),
                "severity": round(float(ev["severity"]), 2),
                "age_hours": round(age_hours, 1),
                "decay": round(decay, 3),
                "contribution": round(contribution, 3),
            }
        )

    bump = (100.0 - baseline) * _logistic01(weighted_sum, midpoint, scale)
    score = round(min(100.0, baseline + bump), 1)
    contributions.sort(key=lambda c: c["contribution"], reverse=True)
    formula = (
        f"score = baseline({baseline:.0f}) + (100−baseline) × "
        f"logistic01(Σ severity×weight×decay = {weighted_sum:.2f}) = {score:.1f}"
    )
    return {
        "score": score,
        "baseline": baseline,
        "weighted_sum": round(weighted_sum, 3),
        "contributions": contributions,
        "formula": formula,
    }


def recompute_all(db: Session, now: datetime | None = None) -> list[RiskScore]:
    """Recompute + persist a fresh risk score for every corridor from all events."""
    now = now or datetime.now(timezone.utc)
    risk_cfg = corpus.assumptions()["risk_model"]

    rows = db.execute(select(Event).where(Event.corridor.is_not(None))).scalars().all()
    by_corridor: dict[str, list[dict[str, Any]]] = {}
    for e in rows:
        by_corridor.setdefault(e.corridor, []).append(
            {
                "event_id": e.id,
                "headline": e.headline,
                "event_type": e.event_type,
                "severity": e.severity,
                "occurred_at": e.occurred_at,
            }
        )

    saved: list[RiskScore] = []
    for c in corpus.corridors():
        cid = c["id"]
        computed = score_corridor(cid, by_corridor.get(cid, []), now, risk_cfg)
        rs = RiskScore(
            corridor=cid,
            score=computed["score"],
            computed_at=now,
            evidence={
                "name": c["name"],
                "baseline": computed["baseline"],
                "weighted_sum": computed["weighted_sum"],
                "formula": computed["formula"],
                "contributions": computed["contributions"],
            },
        )
        db.add(rs)
        saved.append(rs)
    db.commit()
    return saved


def latest_scores(db: Session) -> list[RiskScore]:
    """Most recent risk score per corridor."""
    rows = db.execute(select(RiskScore).order_by(RiskScore.computed_at.desc())).scalars().all()
    latest: dict[str, RiskScore] = {}
    for r in rows:
        latest.setdefault(r.corridor, r)
    ordered_ids = [c["id"] for c in corpus.corridors()]
    return [latest[cid] for cid in ordered_ids if cid in latest]
