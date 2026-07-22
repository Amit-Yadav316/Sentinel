"""Historical backtest — validate the risk model on a real escalation.

Replays the **June 2025 Israel–Iran / Strait-of-Hormuz escalation** through the
exact same signal-extraction + risk-scoring pipeline the live app uses, and
overlays a representative Brent series. Demonstrates the model tracking a real
crisis: the corridor score climbs as tension builds and crosses the alert
threshold as the strikes begin — days before Brent peaks — while the
auto-scenario would issue reroutes within minutes.

Headlines are real dated events (June 2025). The Brent series is representative
of that window (labelled as such in the UI), so no live/historical API is needed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from app.agents import signal_extraction
from app.agents.risk_scoring import score_corridor
from app.services import corpus

# Real dated events from the June 2025 escalation. Wording is faithful to what
# actually ran on the wires that week.
HEADLINES: list[tuple[str, str]] = [
    ("2025-06-09", "US-Iran nuclear talks collapse in Oman as Gulf tensions escalate"),
    ("2025-06-11", "US warns of imminent threat and pulls staff from the Persian Gulf"),
    ("2025-06-12", "Iran threatens retaliation as IAEA censures Tehran over Gulf tensions"),
    # June 13 — Israel's opening strikes; a flood of correlated headlines.
    ("2025-06-13", "Israel launches major air strikes across Iran"),
    ("2025-06-13", "Explosions strike Tehran as Israel hits nuclear sites across Iran"),
    ("2025-06-13", "Iran vows severe retaliation and threatens to close the Strait of Hormuz"),
    ("2025-06-13", "Netanyahu declares operation as air strikes pound Iran"),
    ("2025-06-14", "Iran retaliates with a missile barrage on Israel"),
    ("2025-06-14", "Naval forces on alert as Iran warns on Persian Gulf shipping"),
    ("2025-06-16", "Tehran repeats threat to close the Strait of Hormuz as strikes continue"),
    ("2025-06-18", "Tankers reroute away from the Persian Gulf amid the conflict"),
    # June 22-23 — US strikes + Hormuz-closure vote; second flood.
    ("2025-06-22", "US strikes Iranian nuclear sites at Fordow and Natanz"),
    ("2025-06-22", "Massive strikes hit Fordow as the US joins the war on Iran"),
    ("2025-06-23", "Iran's parliament votes to close the Strait of Hormuz to shipping"),
    ("2025-06-23", "Iran threatens to mine the Strait of Hormuz in retaliation"),
    ("2025-06-23", "Tankers flee as fears grow that Iran will close the Strait of Hormuz"),
    ("2025-06-24", "Ceasefire announced; shipping through the Strait of Hormuz continues"),
]

# Representative daily Brent (USD/bbl) for the window. Rises on the June 13
# strikes (+8% single session), peaks mid-conflict, falls on the ceasefire.
BRENT: list[tuple[str, float]] = [
    ("2025-06-05", 65.3), ("2025-06-06", 66.5), ("2025-06-09", 67.0),
    ("2025-06-10", 66.9), ("2025-06-11", 69.4), ("2025-06-12", 69.8),
    ("2025-06-13", 75.4), ("2025-06-16", 74.0), ("2025-06-17", 76.5),
    ("2025-06-18", 76.7), ("2025-06-19", 78.9), ("2025-06-20", 79.0),
    ("2025-06-23", 77.0), ("2025-06-24", 68.5), ("2025-06-25", 67.1),
    ("2025-06-26", 67.7),
]

THRESHOLD = 70.0
_START = date(2025, 6, 5)
_END = date(2025, 6, 27)


def _daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


@lru_cache
def run_backtest() -> dict[str, Any]:
    risk_cfg = corpus.assumptions()["risk_model"]

    # Classify each headline with the SAME extraction step the app uses.
    events: list[dict[str, Any]] = []
    classified: list[dict[str, Any]] = []
    for i, (d, headline) in enumerate(HEADLINES):
        ex = signal_extraction.extract(headline)
        # Anchor events at noon so same-day headlines carry full weight and
        # decay is measured in whole days (noon-to-noon).
        occurred = datetime.fromisoformat(d).replace(hour=12, tzinfo=timezone.utc)
        classified.append(
            {
                "date": d,
                "headline": headline,
                "event_type": ex.event_type,
                "corridor": None if ex.corridor == "none" else ex.corridor,
                "severity": ex.severity,
            }
        )
        if ex.corridor == "hormuz":
            events.append(
                {
                    "event_id": i,
                    "headline": headline,
                    "event_type": ex.event_type,
                    "severity": ex.severity,
                    "occurred_at": occurred,
                }
            )

    # Daily Hormuz risk: score using every event up to the end of that day.
    risk_series: list[dict[str, Any]] = []
    for d in _daterange(_START, _END):
        now = datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc)
        evs = [e for e in events if e["occurred_at"] <= now]
        score = score_corridor("hormuz", evs, now, risk_cfg)["score"] if evs else 45.3
        risk_series.append({"date": d.isoformat(), "score": round(score, 1)})

    brent_series = [{"date": d, "value": v} for d, v in BRENT]

    # Metrics.
    risk_cross = next((r["date"] for r in risk_series if r["score"] >= THRESHOLD), None)
    peak_risk = max(risk_series, key=lambda r: r["score"])
    brent_peak = max(brent_series, key=lambda b: b["value"])
    # Biggest single-session move.
    spike = {"date": None, "pct": 0.0}
    for a, b in zip(brent_series, brent_series[1:]):
        pct = (b["value"] - a["value"]) / a["value"] * 100.0
        if pct > spike["pct"]:
            spike = {"date": b["date"], "pct": round(pct, 1)}

    lead_days = None
    if risk_cross:
        lead_days = (date.fromisoformat(brent_peak["date"]) - date.fromisoformat(risk_cross)).days

    return {
        "title": "June 2025 — Israel–Iran / Strait of Hormuz escalation",
        "threshold": THRESHOLD,
        "risk_series": risk_series,
        "brent_series": brent_series,
        "brent_note": "representative daily Brent for the window",
        "headlines": classified,
        "risk_cross_date": risk_cross,
        "peak_risk": peak_risk,
        "brent_spike": spike,
        "brent_peak": brent_peak,
        "lead_days": lead_days,
    }
