"""Scripted Hormuz escalation — the demo's beating heart.

Replays 9 escalating headlines through the full pipeline. The Hormuz risk score
climbs from ~45 past the auto-trigger threshold (70), which fires the
``hormuz_50`` scenario and generates procurement recommendations.

Run standalone (prints the climb):   python -m app.seed.inject_escalation
The API imports ``ESCALATION`` + ``inject_step`` to drive the same sequence live
over the websocket.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from app.agents import pipeline
from app.db import SessionLocal

# Ordered, escalating. Each is Hormuz-relevant; severity/type climb so the
# time-decayed weighted sum crosses the threshold within the sequence.
ESCALATION: list[str] = [
    "Iran warns it could close the Strait of Hormuz amid rising tensions with the US",
    "US Navy increases escort operations for tankers near the Strait of Hormuz",
    "Diplomatic talks over Gulf shipping stall as both sides harden positions",
    "Tanker seized near the Strait of Hormuz, crew detained by naval forces",
    "Missile strike hits an oil loading terminal on the Gulf coast",
    "Major air raid reported near Bandar Abbas as shipping goes on high alert",
    "Iran threatens to mine the Strait of Hormuz if pressure continues",
    "Tanker ablaze in the Strait of Hormuz after a direct attack overnight",
    "Regional forces declare closure of the Strait of Hormuz to commercial traffic",
]


def inject_step(db, headline: str) -> dict:
    """Ingest one escalation headline at the current time. Returns pipeline payload."""
    return pipeline.ingest_event(
        db, headline, source="injected", occurred_at=datetime.now(timezone.utc)
    )


def run(delay: float = 0.0) -> None:
    db = SessionLocal()
    try:
        print("Injecting Hormuz escalation...\n")
        for i, headline in enumerate(ESCALATION, start=1):
            payload = inject_step(db, headline)
            hormuz = next((r["score"] for r in payload["risk"] if r["corridor"] == "hormuz"), None)
            fired = "  *** SCENARIO AUTO-TRIGGERED ***" if payload.get("scenario_run") else ""
            print(f"[{i}/{len(ESCALATION)}] Hormuz risk = {hormuz:5.1f}{fired}")
            print(f"        {headline}")
            if payload.get("recommendations"):
                top = payload["recommendations"][0]["payload"]
                print(f"        -> top rec: {top['crude']} ({top['source']}), "
                      f"{top['volume_kbd']:.0f} kb/d, ${top['cost_delta_usd_bbl']:.1f}/bbl")
            if delay:
                time.sleep(delay)
        print("\nDone. Signal -> executable recommendation loop complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run(delay=0.0)
