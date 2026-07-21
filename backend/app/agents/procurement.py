"""ProcurementAgent — turn a scenario's supply gap into ranked, executable
rerouting recommendations.

Pipeline per candidate (crude, route) from an *unaffected* corridor:
  1. deterministic grade-compatibility check (API°/sulfur) vs each shortfall
     refinery — this is the executability core, not ML;
  2. cost delta ($/bbl) = FOB diff vs displaced grade + transit freight proxy;
  3. composite rank (compatibility, availability, cost, transit);
  4. emit top-3 Recommendation cards with volume, ETA, cost delta, compatible
     refineries, and caveats (sanctions flag, simulated-availability chip).

The "RAG" rationale is generated deterministically in mock mode (a compat-aware
template); in live mode it is a one-line Claude rationale. Vector search over the
assay corpus is stubbed to an in-process cosine ranking.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Recommendation, Scenario, ScenarioRun
from app.services import corpus


def check_compatibility(crude: dict, refinery: dict) -> tuple[bool, str]:
    """Deterministic API°/sulfur window check. Returns (ok, reason)."""
    tol = refinery["grade_tolerance"]
    api_ok = tol["api_min"] <= crude["api"] <= tol["api_max"]
    sulfur_ok = crude["sulfur_pct"] <= tol["sulfur_max_pct"]
    if api_ok and sulfur_ok:
        return True, f"API {crude['api']}° & sulfur {crude['sulfur_pct']}% within window"
    reasons = []
    if not api_ok:
        reasons.append(f"API {crude['api']}° outside {tol['api_min']}–{tol['api_max']}°")
    if not sulfur_ok:
        reasons.append(f"sulfur {crude['sulfur_pct']}% > max {tol['sulfur_max_pct']}%")
    return False, "; ".join(reasons)


def _affected_corridors(scenario_cfg: dict) -> set[str]:
    return {cid for cid, m in scenario_cfg.get("corridor_multipliers", {}).items() if m < 1.0}


def _rationale(crude: dict, compatible: list[str], cost_delta: float) -> str:
    n = len(compatible)
    tag = "sweet" if crude["sulfur_pct"] < 1.0 else "sour"
    direction = "cheaper" if cost_delta < 0 else "a premium"
    return (
        f"{crude['name']} ({crude['origin']}, {tag} {crude['api']}°/"
        f"{crude['sulfur_pct']}%S) clears grade checks at {n} shortfall refiner"
        f"{'y' if n == 1 else 'ies'} and lands at {direction} of "
        f"${abs(cost_delta):.1f}/bbl vs the displaced Gulf barrel."
    )


def rank_candidates(scenario_cfg: dict, result: dict) -> list[dict]:
    """Pure ranking. Returns candidate dicts sorted best-first."""
    pc = corpus.assumptions()["procurement"]
    crudes = corpus.crudes()
    ref_by_id = {r["id"]: r for r in corpus.refineries()}
    corridor_by_id = {c["id"]: c for c in corpus.corridors()}

    affected = _affected_corridors(scenario_cfg)
    # Displaced grade = cheapest FOB among affected-corridor crudes (the lost barrel).
    affected_crudes = [c for c in crudes if c["corridor"] in affected]
    displaced_fob = min((c["fob_diff_usd"] for c in affected_crudes), default=0.0)

    shortfall_refs = [s for s in result.get("refinery_shortfalls", []) if s["shortfall_kbd"] > 0]
    supply_gap = result.get("supply_gap_kbd", 0.0)
    w = pc["rank_weights"]

    candidates: list[dict] = []
    for crude in crudes:
        if crude["corridor"] in affected:
            continue  # can't source from the disrupted corridor
        corridor = corridor_by_id[crude["corridor"]]
        transit = corridor["transit_days"]
        freight = round(
            max(0, transit - pc["reference_transit_days"]) * pc["freight_per_transit_day_usd"], 2
        )
        cost_delta = round((crude["fob_diff_usd"] - displaced_fob) + freight, 1)
        availability = pc["availability_index"].get(crude["id"], pc["availability_index"]["default"])

        compatible = []
        for s in shortfall_refs:
            ok, _ = check_compatibility(crude, ref_by_id[s["refinery_id"]])
            if ok:
                compatible.append(s["name"])

        rank_score = (
            len(compatible) * w["compat_refineries"]
            + availability * w["availability"]
            - cost_delta * w["cost_delta"]
            - transit * w["transit_days"]
        )
        volume = round(min(supply_gap, availability * pc["max_liftable_kbd"]), 0)
        eta_days = transit + 8  # +charter fixing & loading window

        caveats = []
        if crude.get("caveat") == "sanctions":
            caveats.append("Sanctions/price-cap compliance flag (G7)")
        caveats.append("Availability index is SIMULATED")

        candidates.append(
            {
                "crude": crude["name"],
                "crude_id": crude["id"],
                "source": crude["origin"],
                "route": corridor["name"],
                "load_port": crude["load_port"],
                "volume_kbd": volume,
                "eta_days": eta_days,
                "cost_delta_usd_bbl": cost_delta,
                "availability_index": availability,
                "compatible_refineries": compatible,
                "compatible_count": len(compatible),
                "rank_score": round(rank_score, 2),
                "rationale": _rationale(crude, compatible, cost_delta),
                "caveats": caveats,
            }
        )

    candidates.sort(key=lambda c: c["rank_score"], reverse=True)
    return candidates


def generate_recommendations(db: Session, run: ScenarioRun, top_n: int = 3) -> list[Recommendation]:
    """Rank candidates for a run and persist the top-N recommendation cards."""
    scenario = db.get(Scenario, run.scenario_id)
    candidates = rank_candidates(scenario.config, run.result)

    recs: list[Recommendation] = []
    for rank, cand in enumerate(candidates[:top_n], start=1):
        rec = Recommendation(run_id=run.id, rank=rank, payload=cand)
        db.add(rec)
        recs.append(rec)
    db.commit()
    for r in recs:
        db.refresh(r)
    return recs


def render_brief(run: ScenarioRun, recs: list[Recommendation]) -> str:
    """One-page procurement brief as markdown (for GET /recommendations/{id}/brief)."""
    res = run.result
    lines = [
        f"# Procurement Brief — {res['scenario_name']}",
        "",
        f"**Supply gap:** {res['supply_gap_kbd']:.0f} kb/d "
        f"({res['supply_gap_pct']:.1f}% of net imports)  ",
        f"**SPR runway vs gap:** {res['spr_runway_days']:.1f} days  ",
        f"**Landed cost delta:** ${res['landed_cost_delta_usd_bbl']:.1f}/bbl  ",
        f"**Est. retail pass-through:** ₹{res['retail_passthrough_inr_l']:.2f}/L",
        "",
        "## Recommended reroutes",
    ]
    for rec in sorted(recs, key=lambda r: r.rank):
        p = rec.payload
        compat = ", ".join(p["compatible_refineries"]) or "—"
        lines += [
            "",
            f"### {rec.rank}. {p['crude']} — {p['source']}",
            f"- **Route:** {p['route']} (load: {p['load_port']})",
            f"- **Volume:** {p['volume_kbd']:.0f} kb/d · **ETA:** {p['eta_days']} days",
            f"- **Cost delta:** ${p['cost_delta_usd_bbl']:.1f}/bbl",
            f"- **Compatible refineries:** {compat}",
            f"- **Rationale:** {p['rationale']}",
            f"- **Caveats:** {'; '.join(p['caveats'])}",
        ]
    return "\n".join(lines)
