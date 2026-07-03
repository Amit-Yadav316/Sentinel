"""Scenario flow-model tests with hand-computed expected values.

Baseline (from config): net_imports = 5300 − 590 = 4710 kb/d.
hormuz_50 halves the Hormuz corridor (baseline_share 0.43):
    lost = 4710 × 0.43 × 0.5 = 1012.65 kb/d
    gap% = 0.215 × 100 = 21.5 %
    reserve = (9.5 + 55) × 4710 = 303,795 kb
    runway = 303,795 / 1012.65 = 300.0 days
    spot premium @21.5% = 22 + 0.075×(55−22) = 24.475
    landed Δ = 24.475 + 6.0 (shock) = 30.475 → 30.5 $/bbl
    retail = 30.475 × 0.52 × 0.35 = 5.55 ₹/L
"""

from __future__ import annotations

import pytest

from app.services import corpus
from app.sim import State, run_scenario


@pytest.fixture
def corpus_bundle() -> dict:
    return {
        "assumptions": corpus.assumptions(),
        "corridors": corpus.corridors(),
        "refineries": corpus.refineries(),
    }


def test_net_imports(corpus_bundle):
    from app.sim.flow_model import net_imports_kbd

    assert net_imports_kbd(corpus_bundle["assumptions"]["macro"]) == pytest.approx(4710.0)


def test_hormuz_50_supply_gap(corpus_bundle):
    cfg = corpus.scenario_by_name()["hormuz_50"]
    res = run_scenario(cfg, State(brent_usd=82.0), corpus_bundle)
    assert res.supply_gap_kbd == pytest.approx(1012.65, abs=0.1)
    assert res.supply_gap_pct == pytest.approx(21.5, abs=0.05)


def test_hormuz_50_spr_runway(corpus_bundle):
    cfg = corpus.scenario_by_name()["hormuz_50"]
    res = run_scenario(cfg, State(brent_usd=82.0), corpus_bundle)
    assert res.reserve_kb == pytest.approx(303795.0, abs=1.0)
    assert res.spr_runway_days == pytest.approx(300.0, abs=0.5)


def test_hormuz_50_cost_and_retail(corpus_bundle):
    cfg = corpus.scenario_by_name()["hormuz_50"]
    res = run_scenario(cfg, State(brent_usd=82.0), corpus_bundle)
    assert res.landed_cost_delta_usd_bbl == pytest.approx(30.5, abs=0.1)
    assert res.brent_after_usd == pytest.approx(112.5, abs=0.1)
    assert res.retail_passthrough_inr_l == pytest.approx(5.55, abs=0.05)


def test_hormuz_50_refinery_allocation(corpus_bundle):
    cfg = corpus.scenario_by_name()["hormuz_50"]
    res = run_scenario(cfg, State(brent_usd=82.0), corpus_bundle)
    shortfalls = {s["refinery_id"]: s["shortfall_kbd"] for s in res.refinery_shortfalls}

    # Numaligarh has zero Hormuz dependence -> no shortfall, filtered out.
    assert "numaligarh" not in shortfalls
    # Jamnagar DTA weight 660×0.6=396 of total 1799.25 -> 1012.65×396/1799.25.
    assert shortfalls["jamnagar_dta"] == pytest.approx(222.9, abs=0.5)
    # Allocation conserves the gap (within rounding).
    assert sum(shortfalls.values()) == pytest.approx(1012.65, abs=1.0)


def test_no_disruption_is_calm(corpus_bundle):
    res = run_scenario({"name": "calm", "corridor_multipliers": {}}, State(brent_usd=82.0), corpus_bundle)
    assert res.supply_gap_kbd == 0.0
    assert res.spr_runway_days == -1.0  # sentinel for "infinite" (no gap)
    assert res.landed_cost_delta_usd_bbl == 0.0
