"""Risk-scoring tests with hand-computed expected values.

risk_cfg: baseline hormuz=45, blockade_threat weight=1.5, half_life=36h,
midpoint=3, scale=4.

One fresh (age 0) blockade_threat, severity 0.8:
    weighted_sum = 0.8 × 1.5 × 1.0 = 1.2
    logistic(0)   = 1/(1+e^0.75)          = 0.32082
    logistic(1.2) = 1/(1+e^0.45)          = 0.38936
    logistic01    = (0.38936−0.32082)/(1−0.32082) = 0.10092
    score = 45 + (100−45)×0.10092 = 50.55 → 50.6
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.agents.risk_scoring import score_corridor

RISK_CFG = {
    "baseline_floor": {"hormuz": 45, "cape": 15},
    "type_weights": {"blockade_threat": 1.5, "naval_incident": 1.3, "other": 0.4},
    "decay_half_life_hours": 36,
    "squash_midpoint": 3.0,
    "squash_scale": 4.0,
}
NOW = datetime(2026, 7, 22, tzinfo=timezone.utc)


def _ev(sev, etype="blockade_threat", age_h=0.0):
    return {
        "event_id": 1,
        "headline": "test",
        "event_type": etype,
        "severity": sev,
        "occurred_at": NOW - timedelta(hours=age_h),
    }


def test_no_events_returns_baseline():
    out = score_corridor("hormuz", [], NOW, RISK_CFG)
    assert out["score"] == 45.0
    assert out["weighted_sum"] == 0.0


def test_single_fresh_blockade():
    out = score_corridor("hormuz", [_ev(0.8)], NOW, RISK_CFG)
    assert out["weighted_sum"] == pytest.approx(1.2, abs=1e-6)
    assert out["score"] == pytest.approx(50.6, abs=0.1)


def test_decay_halves_at_half_life():
    out = score_corridor("hormuz", [_ev(0.8, age_h=36.0)], NOW, RISK_CFG)
    # decay = 0.5 -> weighted_sum = 1.2 × 0.5 = 0.6
    assert out["weighted_sum"] == pytest.approx(0.6, abs=1e-6)
    assert out["contributions"][0]["decay"] == pytest.approx(0.5, abs=1e-3)


def test_more_events_increase_score_monotonically():
    one = score_corridor("hormuz", [_ev(0.8)], NOW, RISK_CFG)["score"]
    three = score_corridor("hormuz", [_ev(0.8), _ev(0.8), _ev(0.9)], NOW, RISK_CFG)["score"]
    assert three > one


def test_score_capped_at_100():
    heavy = [_ev(1.0) for _ in range(50)]
    out = score_corridor("hormuz", heavy, NOW, RISK_CFG)
    assert out["score"] <= 100.0


def test_unknown_corridor_uses_low_default():
    out = score_corridor("mystery", [], NOW, RISK_CFG)
    assert out["baseline"] == 10  # default in score_corridor
