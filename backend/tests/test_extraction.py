"""Signal-extraction mock classifier tests (deterministic, offline)."""

from __future__ import annotations

from app.agents.signal_extraction import extract


def test_blockade_threat_classified():
    r = extract("Iran threatens to close the Strait of Hormuz")
    assert r.event_type == "blockade_threat"
    assert r.corridor == "hormuz"
    assert 0.0 <= r.severity <= 1.0


def test_military_strike_high_severity():
    r = extract("Missile strike hits oil terminal on the Gulf coast")
    assert r.event_type == "military_strike"
    assert r.severity >= 0.8


def test_red_sea_corridor_detected():
    r = extract("Houthi attack disrupts Red Sea shipping near Bab-el-Mandeb")
    assert r.corridor == "red_sea"


def test_calm_headline_is_low_signal():
    r = extract("Brent holds near $82 as demand outlook stabilises")
    assert r.severity < 0.5


def test_deterministic():
    a = extract("Tanker seized near the Strait of Hormuz")
    b = extract("Tanker seized near the Strait of Hormuz")
    assert a.model_dump() == b.model_dump()
