"""Backtest validation — the risk model tracks the June 2025 escalation."""

from __future__ import annotations

from app.sim.backtest import run_backtest


def test_risk_crosses_threshold_as_strikes_begin():
    r = run_backtest()
    # Risk first hits CRITICAL (>=70) on the day the strikes begin.
    assert r["risk_cross_date"] == "2025-06-13"
    assert r["peak_risk"]["score"] >= 70


def test_single_session_spike_matches_the_brief():
    r = run_backtest()
    # The brief cites "over 8% in a single session".
    assert r["brent_spike"]["date"] == "2025-06-13"
    assert r["brent_spike"]["pct"] >= 8.0


def test_critical_before_price_peak():
    r = run_backtest()
    # Model is at CRITICAL well before Brent peaks — the warning window.
    assert r["lead_days"] is not None and r["lead_days"] >= 5


def test_risk_re_escalates_on_the_us_strikes():
    r = run_backtest()
    by_date = {x["date"]: x["score"] for x in r["risk_series"]}
    # Quiet lull mid-conflict, then re-spikes on the June 22-23 US strikes.
    assert by_date["2025-06-21"] < 50
    assert by_date["2025-06-23"] >= 70
