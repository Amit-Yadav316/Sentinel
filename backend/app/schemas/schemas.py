"""Pydantic v2 schemas.

``ExtractionResult`` is the strict output contract for the LLM signal-extraction
step (CLAUDE.md: every LLM step must have a strict output schema).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "military_strike",
    "naval_incident",
    "sanction",
    "blockade_threat",
    "port_closure",
    "diplomatic_escalation",
    "opec_action",
    "price_spike",
    "other",
]


class ExtractionResult(BaseModel):
    """Strict schema the signal-extraction LLM step must return."""

    event_type: EventType
    corridor: str = Field(description="corridor id, e.g. 'hormuz', or 'none'")
    severity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list)


class EventOut(BaseModel):
    id: int
    source: str
    headline: str
    url: str | None = None
    occurred_at: datetime
    event_type: str | None = None
    corridor: str | None = None
    severity: float | None = None
    confidence: float | None = None
    entities: list[str] | None = None

    model_config = {"from_attributes": True}


class RiskContribution(BaseModel):
    event_id: int | None = None
    headline: str
    event_type: str
    weight: float
    severity: float
    age_hours: float
    decay: float
    contribution: float


class CorridorRisk(BaseModel):
    corridor: str
    name: str
    score: float
    baseline: float
    weighted_sum: float
    formula: str
    computed_at: datetime
    contributions: list[RiskContribution]


class ScenarioSummary(BaseModel):
    name: str
    title: str
    description: str


class ScenarioRunOut(BaseModel):
    id: int
    scenario_name: str
    scenario_title: str
    triggered_by: str
    created_at: datetime
    result: dict

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    id: int
    run_id: int
    rank: int
    payload: dict

    model_config = {"from_attributes": True}


class VesselOut(BaseModel):
    id: int
    mmsi: str
    name: str
    lat: float
    lon: float
    corridor: str | None = None
    synthetic: bool

    model_config = {"from_attributes": True}
