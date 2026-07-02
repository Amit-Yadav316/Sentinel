"""Sentinel scenario flow model.

Pure functions only. ``run_scenario(scenario_cfg, state, corpus)`` maps corridor
throughput multipliers onto a transparent supply-flow chain and returns a
:class:`ScenarioResult` where **every numeric output carries the formula string
that produced it** — so the UI can render "how was this computed" with no
black boxes (a hard CLAUDE.md requirement).

Chain:
    net imports  ->  per-corridor lost volume  ->  supply gap
                 ->  per-refinery shortfall (pro-rata by corridor dependence)
                 ->  SPR runway (days)
                 ->  landed cost delta ($/bbl)
                 ->  retail pass-through (INR/litre)

All coefficients come from ``config/assumptions.yaml`` via the ``corpus`` arg;
there are no magic numbers here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class State:
    """A captured snapshot the scenario runs against."""

    brent_usd: float
    # Total physical reserve in thousand-barrels (kb). If 0, computed from
    # assumptions (cover days * net imports).
    reserve_kb: float = 0.0


@dataclass
class ScenarioResult:
    scenario_name: str
    net_imports_kbd: float
    supply_gap_kbd: float
    supply_gap_pct: float
    refinery_shortfalls: list[dict[str, Any]]
    spr_runway_days: float
    landed_cost_delta_usd_bbl: float
    brent_after_usd: float
    retail_passthrough_inr_l: float
    reserve_kb: float
    formulas: dict[str, str] = field(default_factory=dict)
    assumptions_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _interp(curve: list[dict[str, float]], x: float, xk: str, yk: str) -> float:
    """Piecewise-linear interpolation of a monotonically-increasing curve."""
    pts = sorted(curve, key=lambda p: p[xk])
    if x <= pts[0][xk]:
        return pts[0][yk]
    if x >= pts[-1][xk]:
        return pts[-1][yk]
    for a, b in zip(pts, pts[1:]):
        if a[xk] <= x <= b[xk]:
            span = b[xk] - a[xk]
            if span == 0:
                return a[yk]
            t = (x - a[xk]) / span
            return a[yk] + t * (b[yk] - a[yk])
    return pts[-1][yk]


def net_imports_kbd(macro: dict[str, Any]) -> float:
    """Net crude imports = demand - domestic production (kb/d)."""
    return macro["india_crude_demand_kbd"] - macro["domestic_production_kbd"]


def default_reserve_kb(assumptions: dict[str, Any]) -> float:
    """Total reserve (kb) = (strategic + commercial cover days) * net imports."""
    spr = assumptions["spr"]
    net = net_imports_kbd(assumptions["macro"])
    days = spr["strategic_cover_days"] + spr["commercial_cover_days"]
    return days * net


def run_scenario(
    scenario_cfg: dict[str, Any],
    state: State,
    corpus: dict[str, Any],
) -> ScenarioResult:
    """Run one named scenario against ``state``.

    ``corpus`` must supply keys: ``assumptions`` (parsed assumptions.yaml),
    ``corridors`` (list), ``refineries`` (list).
    """
    assumptions = corpus["assumptions"]
    macro = assumptions["macro"]
    corridors = corpus["corridors"]
    refineries = corpus["refineries"]

    multipliers: dict[str, float] = scenario_cfg.get("corridor_multipliers", {})
    net = net_imports_kbd(macro)

    # 1) Per-corridor lost volume and total supply gap.
    lost_by_corridor: dict[str, float] = {}
    for c in corridors:
        mult = multipliers.get(c["id"], 1.0)
        baseline_flow = net * c["baseline_share"]
        lost = baseline_flow * (1.0 - mult)
        if lost > 1e-9:
            lost_by_corridor[c["id"]] = lost
    supply_gap = sum(lost_by_corridor.values())
    gap_pct = (supply_gap / net * 100.0) if net else 0.0

    # 2) Allocate each corridor's lost volume to refineries pro-rata by
    #    (capacity * that refinery's dependence on the disrupted corridor).
    shortfall_kbd: dict[str, float] = {r["id"]: 0.0 for r in refineries}
    for corridor_id, lost in lost_by_corridor.items():
        weights = {
            r["id"]: r["capacity_kbd"] * r.get("corridor_dependence", {}).get(corridor_id, 0.0)
            for r in refineries
        }
        total_w = sum(weights.values())
        if total_w <= 0:
            continue
        for rid, w in weights.items():
            shortfall_kbd[rid] += lost * w / total_w

    ref_by_id = {r["id"]: r for r in refineries}
    refinery_shortfalls = [
        {
            "refinery_id": rid,
            "name": ref_by_id[rid]["name"],
            "capacity_kbd": ref_by_id[rid]["capacity_kbd"],
            "shortfall_kbd": round(sf, 1),
            "shortfall_pct": round(sf / ref_by_id[rid]["capacity_kbd"] * 100.0, 1),
        }
        for rid, sf in shortfall_kbd.items()
        if sf > 0.05
    ]
    refinery_shortfalls.sort(key=lambda x: x["shortfall_kbd"], reverse=True)

    # 3) SPR runway against the uncovered gap.
    reserve_kb = state.reserve_kb or default_reserve_kb(assumptions)
    spr_runway = (reserve_kb / supply_gap) if supply_gap > 1e-9 else float("inf")

    # 4) Landed cost delta = interpolated spot premium + scenario shock + reroute freight.
    prices = assumptions["prices"]
    spot_premium = _interp(prices["spot_premium_curve"], gap_pct, "gap_pct", "premium_usd")
    price_shock = float(scenario_cfg.get("price_shock_usd", 0.0))
    reroute_key = scenario_cfg.get("reroute")
    reroute_adder = 0.0
    if reroute_key:
        reroute_adder = assumptions["freight"]["reroute_adder_usd"].get(reroute_key, 0.0)
    landed_cost_delta = spot_premium + price_shock + reroute_adder
    brent_after = state.brent_usd + landed_cost_delta

    # 5) Retail pass-through (INR/litre).
    pt = assumptions["pass_through"]
    retail_delta = landed_cost_delta * pt["usd_per_bbl_to_inr_per_litre"] * pt["pass_through_efficiency"]

    formulas = {
        "supply_gap_kbd": (
            "supply_gap = Σ_corridor  net_imports × baseline_share × (1 − multiplier)  "
            f"= {supply_gap:.0f} kb/d"
        ),
        "supply_gap_pct": f"gap% = supply_gap / net_imports × 100 = {gap_pct:.1f}%",
        "refinery_shortfall": (
            "shortfall_r = Σ_corridor  lost_c × (capacity_r × dep_r,c) / Σ_r(capacity × dep)"
        ),
        "spr_runway_days": (
            f"runway = reserve_kb / supply_gap = {reserve_kb:.0f} / {supply_gap:.0f} "
            f"= {spr_runway:.1f} days"
        ),
        "landed_cost_delta_usd_bbl": (
            f"Δ$/bbl = spot_premium({spot_premium:.1f}) + shock({price_shock:.1f}) "
            f"+ reroute({reroute_adder:.1f}) = {landed_cost_delta:.1f}"
        ),
        "retail_passthrough_inr_l": (
            f"₹/L = Δ$/bbl × {pt['usd_per_bbl_to_inr_per_litre']} × "
            f"{pt['pass_through_efficiency']} = {retail_delta:.2f}"
        ),
    }
    assumptions_used = {
        "net_imports_kbd": round(net, 0),
        "strategic_cover_days": assumptions["spr"]["strategic_cover_days"],
        "commercial_cover_days": assumptions["spr"]["commercial_cover_days"],
        "spot_premium_usd": round(spot_premium, 1),
        "pass_through_efficiency": pt["pass_through_efficiency"],
    }

    return ScenarioResult(
        scenario_name=scenario_cfg.get("name", "unnamed"),
        net_imports_kbd=round(net, 0),
        supply_gap_kbd=round(supply_gap, 1),
        supply_gap_pct=round(gap_pct, 1),
        refinery_shortfalls=refinery_shortfalls,
        spr_runway_days=round(spr_runway, 1) if spr_runway != float("inf") else -1.0,
        landed_cost_delta_usd_bbl=round(landed_cost_delta, 1),
        brent_after_usd=round(brent_after, 1),
        retail_passthrough_inr_l=round(retail_delta, 2),
        reserve_kb=round(reserve_kb, 0),
        formulas=formulas,
        assumptions_used=assumptions_used,
    )
