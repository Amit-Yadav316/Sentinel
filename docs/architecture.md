# Sentinel — Architecture

**Crisis-to-decision engine for India's crude oil supply chain.**
Signal → risk score → scenario → executable procurement recommendation, in
under 5 minutes, entirely from cached data for the demo.

![Sentinel architecture](architecture.png)

## System diagram

```mermaid
flowchart TB
  subgraph Ingestion["Signal Ingestion (cache-first)"]
    GDELT["GDELT / curated RSS<br/>news events"]
    AIS["AISStream.io<br/>vessel positions (synthetic fixture)"]
    PRICE["Price API<br/>Brent BZ=F (yfinance)"]
    OFAC["OFAC SDN CSV<br/>sanctions flags"]
  end

  subgraph Agents["Agent Layer (mock-first, hosted LLM in live mode)"]
    A1["1 · SignalExtractionAgent<br/>LLM classify → {type, corridor, severity, entities}"]
    A2["2 · RiskScoringAgent<br/>deterministic weighted + time-decay model"]
    A3["3 · ScenarioAgent<br/>parameterized flow model"]
    A4["4 · ProcurementAgent<br/>grade-compat + cost ranking"]
  end

  subgraph Storage["Storage — SQLAlchemy 2.0 (SQLite; Postgres-ready)"]
    DB[("events · risk_scores(evidence)<br/>scenarios · scenario_runs<br/>recommendations · vessels · prices")]
  end

  Config["config/*.yaml<br/>corridors · refineries · crudes · assumptions · scenarios<br/>(single source of truth, every value sourced)"]

  subgraph API["FastAPI"]
    REST["REST: /corridors/risk, /scenarios/{name}/run,<br/>/recommendations, /runs/{id}/brief"]
    WS["WS: /risk/stream (live push)"]
  end

  subgraph FE["Frontend — React + Vite + Tailwind"]
    S1["Screen 1 · Corridor Map + evidence panel"]
    S2["Screen 2 · Scenario Console (formula-transparent)"]
    S3["Screen 3 · Recommendation cards + brief export"]
  end

  GDELT --> A1
  AIS --> DB
  PRICE --> DB
  OFAC --> A4
  A1 --> A2 --> A3 --> A4
  Config -.-> A2
  Config -.-> A3
  Config -.-> A4
  A2 --> DB
  A3 --> DB
  A4 --> DB
  DB --> REST
  A2 --> WS
  A4 --> WS
  REST --> FE
  WS --> S1
  S1 --> S2 --> S3
```

## The pipeline (one loop)

```mermaid
sequenceDiagram
  participant Inj as Escalation injector
  participant Sig as SignalExtraction
  participant Risk as RiskScoring
  participant Scn as ScenarioAgent
  participant Proc as ProcurementAgent
  participant UI as Dashboard (WS)

  Inj->>Sig: headline "Iran threatens to mine Hormuz"
  Sig->>Risk: {blockade_threat, hormuz, sev 0.8}
  Risk->>Risk: recompute corridor scores (+ evidence trail)
  Risk-->>UI: hormuz 66 → 72  (push)
  Risk->>Scn: score ≥ 70 → auto-trigger hormuz_50
  Scn->>Proc: supply gap 1013 kb/d, refinery shortfalls
  Proc->>Proc: rank (crude,route) by cost·transit·availability·grade-compat
  Proc-->>UI: 3 recommendation cards + brief  (push)
```

## Key design decisions

| Concern | Decision | Why |
|---|---|---|
| Risk model | Deterministic weighted time-decay, **not** ML | Auditable; every score carries its evidence trail |
| Scenario math | Pure functions in `sim/`, coefficients in `assumptions.yaml` | Transparent, unit-tested against hand-computed values |
| LLM role | Extraction/classification only (mock-first) | Runs offline; no black-box decisions |
| Grade compatibility | Deterministic API°/sulfur window check | Executable, explainable procurement — not a vibe |
| DB | SQLite (SQLAlchemy 2.0, Postgres-ready) | Zero-dependency offline demo |
| Map | Self-contained SVG projection | No tile server → fully offline |

## Design choices & tradeoffs

Chosen to keep the offline demo reliable within the hackathon timebox; each is a
one-line swap back to the heavier "production" choice:

- **Postgres + pgvector → SQLite + in-process cosine.** `DATABASE_URL` swaps the
  engine; procurement RAG uses a small in-memory ranking instead of pgvector.
- **LangGraph → explicit `agents/pipeline.py`.** Same discrete nodes + strict
  schemas + mock mode, less dependency surface, more readable for judges.
- **deck.gl → hand-rolled SVG map.** No external tiles; renders offline.
- **Alembic migrations → `Base.metadata.create_all` at startup/seed.** Fine for
  a single-node demo; Alembic slot is left open in the layout.
