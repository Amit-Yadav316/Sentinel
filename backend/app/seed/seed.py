"""Seed the demo into a clean calm state.

Loads the config corpus + cached fixtures into the DB, ingests the calm baseline
headlines (Hormuz rests ≈ 45, Red Sea ≈ 40), and computes the initial risk
scores. Idempotent: drops and recreates all tables each run so ``make demo``
always starts from the same calm snapshot.

Run:  python -m app.seed.seed
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents import risk_scoring, signal_extraction
from app.db import SessionLocal, engine
from app.models import Base, Event, Price, Scenario, Vessel
from app.services import ais, gdelt, prices
from app.services import corpus


def reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def load_scenarios(db) -> None:
    for s in corpus.scenarios():
        db.add(
            Scenario(
                name=s["name"],
                title=s["title"],
                description=s["description"].strip(),
                config=s,
            )
        )
    db.commit()


def load_prices(db) -> None:
    for point in prices.get_brent_series():
        db.add(
            Price(
                symbol="BRENT",
                value=point["value"],
                unit="USD/bbl",
                as_of=datetime.fromisoformat(point["date"]).replace(tzinfo=timezone.utc),
            )
        )
    db.commit()


def load_vessels(db) -> None:
    for v in ais.get_vessels():
        db.add(
            Vessel(
                mmsi=v["mmsi"],
                name=v["name"],
                lat=v["lat"],
                lon=v["lon"],
                corridor=v["corridor"],
                synthetic=v["synthetic"],
            )
        )
    db.commit()


def load_baseline_events(db) -> None:
    """Ingest calm baseline headlines dated a couple days back (low influence)."""
    now = datetime.now(timezone.utc)
    for i, headline in enumerate(gdelt.get_baseline_headlines()):
        ex = signal_extraction.extract(headline)
        db.add(
            Event(
                source="gdelt",
                headline=headline,
                occurred_at=now - timedelta(days=2, hours=i),
                event_type=ex.event_type,
                corridor=None if ex.corridor == "none" else ex.corridor,
                severity=ex.severity,
                confidence=ex.confidence,
                entities=ex.entities,
            )
        )
    db.commit()


def seed() -> None:
    reset_schema()
    db = SessionLocal()
    try:
        load_scenarios(db)
        load_prices(db)
        load_vessels(db)
        load_baseline_events(db)
        scores = risk_scoring.recompute_all(db)
        print("Seeded calm state:")
        for rs in sorted(scores, key=lambda s: s.score, reverse=True):
            print(f"  {rs.corridor:16s} risk={rs.score:5.1f}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
