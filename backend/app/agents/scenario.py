"""ScenarioAgent — run a named scenario against current state and persist it.

Also holds the auto-trigger rule: when a corridor's latest risk score crosses
``risk_model.auto_trigger_threshold`` and that corridor maps to a scenario, a run
is enqueued automatically (this is what fires during the escalation demo).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import risk_scoring
from app.models import Price, Scenario, ScenarioRun
from app.services import corpus
from app.sim import State, run_scenario


def _current_state(db: Session) -> State:
    row = db.execute(
        select(Price).where(Price.symbol == "BRENT").order_by(Price.as_of.desc())
    ).scalars().first()
    brent = row.value if row else corpus.assumptions()["prices"]["brent_baseline_usd"]
    return State(brent_usd=brent)


def run_named_scenario(db: Session, name: str, triggered_by: str = "manual") -> ScenarioRun:
    """Run scenario ``name`` and persist a ScenarioRun with the full result dict."""
    scenario_row = db.execute(select(Scenario).where(Scenario.name == name)).scalars().first()
    if scenario_row is None:
        raise ValueError(f"unknown scenario: {name}")

    state = _current_state(db)
    result = run_scenario(
        scenario_row.config,
        state,
        {
            "assumptions": corpus.assumptions(),
            "corridors": corpus.corridors(),
            "refineries": corpus.refineries(),
        },
    )
    run = ScenarioRun(
        scenario_id=scenario_row.id,
        triggered_by=triggered_by,
        result=result.to_dict(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def maybe_auto_trigger(db: Session) -> ScenarioRun | None:
    """If any corridor breached threshold, run its mapped scenario once.

    Returns the newly created run, or ``None`` if nothing tripped / already run.
    """
    threshold = corpus.assumptions()["risk_model"]["auto_trigger_threshold"]
    trigger_map = corpus.auto_trigger_map()
    for rs in risk_scoring.latest_scores(db):
        if rs.score < threshold:
            continue
        scenario_name = trigger_map.get(rs.corridor)
        if not scenario_name:
            continue
        # De-dupe: skip if an auto run for this scenario already exists.
        existing = db.execute(
            select(ScenarioRun)
            .join(Scenario)
            .where(Scenario.name == scenario_name, ScenarioRun.triggered_by.like("auto%"))
        ).scalars().first()
        if existing:
            continue
        return run_named_scenario(db, scenario_name, triggered_by=f"auto:{rs.corridor}")
    return None
