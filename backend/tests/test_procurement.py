"""Procurement compatibility + ranking tests."""

from __future__ import annotations

from app.agents.procurement import check_compatibility, rank_candidates
from app.services import corpus


def _crude(cid: str) -> dict:
    return next(c for c in corpus.crudes() if c["id"] == cid)


def _refinery(rid: str) -> dict:
    return next(r for r in corpus.refineries() if r["id"] == rid)


def test_sweet_crude_compatible_with_light_sweet_refinery():
    ok, reason = check_compatibility(_crude("bonny_light"), _refinery("numaligarh"))
    assert ok, reason


def test_sour_crude_incompatible_with_low_sulfur_refinery():
    # Arab Heavy (2.9% S) exceeds Numaligarh's 0.5% sulfur ceiling.
    ok, reason = check_compatibility(_crude("arab_heavy"), _refinery("numaligarh"))
    assert not ok
    assert "sulfur" in reason


def test_heavy_sour_fits_deep_conversion_refinery():
    ok, _ = check_compatibility(_crude("basrah_heavy"), _refinery("jamnagar_dta"))
    assert ok


def test_rank_excludes_affected_corridor():
    scenario_cfg = {"corridor_multipliers": {"hormuz": 0.5}}
    result = {
        "supply_gap_kbd": 1000.0,
        "refinery_shortfalls": [
            {"refinery_id": "jamnagar_dta", "name": "Jamnagar DTA", "shortfall_kbd": 200.0}
        ],
    }
    cands = rank_candidates(scenario_cfg, result)
    corridors_used = {c["route"] for c in cands}
    # No Hormuz-corridor crude should appear as a replacement source.
    assert "Strait of Hormuz" not in corridors_used
    assert len(cands) > 0
    # Every candidate carries an executable shape.
    top = cands[0]
    for key in ("crude", "volume_kbd", "eta_days", "cost_delta_usd_bbl", "compatible_refineries"):
        assert key in top


def test_urals_carries_sanctions_caveat():
    scenario_cfg = {"corridor_multipliers": {"hormuz": 0.5}}
    result = {"supply_gap_kbd": 1000.0, "refinery_shortfalls": []}
    cands = rank_candidates(scenario_cfg, result)
    urals = next((c for c in cands if c["crude_id"] == "urals"), None)
    assert urals is not None
    assert any("Sanctions" in cav for cav in urals["caveats"])
