"""Declarative, typed SQLAlchemy 2.0 models.

The ``evidence`` / ``result`` / ``payload`` columns are JSON so every risk score
and scenario run carries its full transparent trail (which events moved it,
weights used, formula strings) so every decision is fully auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Event(Base):
    """A raw signal (news headline / maritime incident) plus its LLM structure."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32))            # gdelt | injected | ofac
    headline: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Structured extraction (filled by SignalExtractionAgent).
    event_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    corridor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severity: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0..1
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0..1
    entities: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RiskScore(Base):
    """A point-in-time corridor risk score with its full evidence trail."""

    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    corridor: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float)               # 0..100
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # evidence: {baseline, contributions:[{event_id, headline, type, weight,
    #            severity, age_hours, decay, contribution}], weighted_sum, formula}
    evidence: Mapped[dict] = mapped_column(JSON)


class Scenario(Base):
    """A named disruption scenario definition (loaded from config/scenarios.yaml)."""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSON)                # multipliers + shock params

    runs: Mapped[list[ScenarioRun]] = relationship(back_populates="scenario")


class ScenarioRun(Base):
    """A single execution of a scenario against a captured state snapshot."""

    __tablename__ = "scenario_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"))
    triggered_by: Mapped[str] = mapped_column(String(32))    # manual | auto:hormuz
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # result: full ScenarioResult dict (shortfalls, spr_runway, cost delta,
    #         retail pass-through) with formula strings attached.
    result: Mapped[dict] = mapped_column(JSON)

    scenario: Mapped[Scenario] = relationship(back_populates="runs")
    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="run")


class Recommendation(Base):
    """A ranked, executable procurement rerouting recommendation card."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scenario_runs.id"))
    rank: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # payload: {crude, source, route, volume_kbd, eta_days, cost_delta_usd_bbl,
    #           compatible_refineries:[...], rationale, caveats:[...]}
    payload: Mapped[dict] = mapped_column(JSON)

    run: Mapped[ScenarioRun] = relationship(back_populates="recommendations")


class Vessel(Base):
    """A tanker position sample (AIS or synthetic replay)."""

    __tablename__ = "vessels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mmsi: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(64))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    corridor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    synthetic: Mapped[bool] = mapped_column(default=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Price(Base):
    """A daily price sample (Brent BZ=F or a freight proxy)."""

    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)   # BRENT
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16), default="USD/bbl")
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
