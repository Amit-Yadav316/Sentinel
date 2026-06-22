# CLAUDE.md — Sentinel: Energy Supply Chain Resilience Platform

## What this project is

Hackathon entry for **ET AI Hackathon 2026 — PS2: AI-Driven Energy Supply Chain
Resilience for Import-Dependent Economies**.

Sentinel is a crisis-to-decision engine for India's crude oil supply chain. It:

1. **Watches** geopolitical + maritime signals continuously (news, AIS vessel
   data, prices, sanctions) and maintains a live **Corridor Disruption
   Probability Score** per import corridor.
2. **Simulates** disruption scenarios (Hormuz partial closure, Red Sea
   suspension, OPEC+ cut) and computes cascading impact on refinery run rates,
   SPR runway, landed cost, and retail price pass-through.
3. **Decides** — generates ranked, executable procurement rerouting
   recommendations with refinery grade-compatibility checks.

**Core demo claim: "Signal to executable recommendation in under 5 minutes."**
Everything we build serves that end-to-end loop. Depth over breadth: three
modules built properly beat five built shallow.

## Deliverables (hard requirements)

- Working prototype (runnable locally, demoed against cached data)
- Architecture diagram
- Presentation deck
- Demo video (~3 min, scripted in PLAN.md Phase 6)

## Judging criteria to optimize for

Innovation 25% · Business Impact 25% · Technical Excellence 20% ·
Scalability 15% · UX 15%. Evaluation focus explicitly includes: disruption
signal detection lead time, **executability** of procurement alternatives,
**scenario model fidelity with explicit testable assumptions**, geospatial
evidence depth, and end-to-end signal→recommendation response time.

Implications for code:
- Every risk score must carry an **evidence trail** (which events moved it, weights used).
- Scenario math must be **transparent and parameterized** — no black boxes. All
  assumptions live in `config/assumptions.yaml` with comments and source citations.
- Recommendation cards must read like something a procurement head could act on
  (volumes, ETAs, cost deltas, compatible refineries) — not ML output.

## Architecture

```
Signal Ingestion (batch + polling)
  ├── GDELT event feed / curated RSS  → news events
  ├── AISStream.io websocket          → vessel positions (Hormuz–India corridor)
  ├── Price API (EIA / yfinance)      → Brent, freight proxies
  └── OFAC SDN CSV snapshot           → sanctions flags
        ▼
Agent Layer (LangGraph orchestration, Claude API for LLM steps)
  1. SignalExtractionAgent — LLM classifies each event: {type, corridor,
     severity 0-1, entities, confidence}; stores raw + structured.
  2. RiskScoringAgent — deterministic weighted model → corridor probability
     scores; stores full evidence trail per score update.
  3. ScenarioAgent — runs parameterized flow model for a named scenario;
     outputs refinery shortfalls, SPR runway, cost deltas.
  4. ProcurementAgent — ranks alternative (source, route) pairs on cost,
     transit time, availability, grade compatibility (RAG over crude assay +
     refinery config corpus); emits recommendation cards.
        ▼
Storage: Postgres (SQLAlchemy 2.0) + pgvector for the assay/config corpus
        ▼
API: FastAPI (REST + one websocket for live risk updates)
        ▼
Frontend: React + Vite + deck.gl/Leaflet map · Tailwind
  Screens: (1) Corridor map + risk panel, (2) Scenario console,
  (3) Recommendation cards + brief export
```

## Tech stack & conventions

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (declarative, typed),
  Pydantic v2 schemas, Alembic migrations, Postgres + pgvector.
- **Agents:** LangGraph. LLM calls via Anthropic API (`claude-sonnet-4-6`).
  Every LLM step must have: a strict output schema (Pydantic), retry with
  backoff, and a cached/mock mode (`LLM_MODE=mock`) so the app runs offline.
- **Frontend:** React 18 + Vite, TypeScript, Tailwind, deck.gl (fallback:
  Leaflet if deck.gl fights us), Zustand for state, recharts for charts.
- **Repo layout:**
  ```
  backend/
    app/
      api/            # FastAPI routers
      agents/         # LangGraph nodes: signal, risk, scenario, procurement
      models/         # SQLAlchemy models
      schemas/        # Pydantic
      services/       # ingestion clients (gdelt.py, ais.py, prices.py, ofac.py)
      sim/            # scenario flow model (pure functions, unit-tested)
      seed/           # demo data injection + fixtures
    alembic/
    tests/
  frontend/
    src/{components,screens,store,lib}
  config/
    assumptions.yaml  # ALL scenario parameters + sources
    corridors.yaml    # corridor defs, chokepoints, baseline volumes
    refineries.yaml   # Indian refineries: capacity, grade tolerance (API°, sulfur %)
    crudes.yaml       # crude assays: origin, API°, sulfur, typical FOB delta
  data/cache/         # cached API responses for offline demo
  docs/               # architecture diagram source, deck notes
  ```
- **Style:** ruff + black for Python; eslint + prettier for TS. Type hints
  everywhere. Small pure functions in `sim/` — this is the code judges may read.
- **Testing:** pytest for `sim/` (scenario math MUST have unit tests with
  hand-computed expected values) and for agents in mock mode. Don't over-test
  UI; screenshot-level sanity is enough.

## Data policy (critical)

- **Real, free sources:** GDELT 2.0 event API; yfinance for Brent (BZ=F);
  AISStream.io free tier (websocket, filter to bounding boxes: Strait of
  Hormuz, Bab-el-Mandeb, Indian west coast ports); OFAC SDN list CSV; PPAC
  public data for India's import mix and refinery capacities; public crude
  assays (BP, ExxonMobil publish these).
- **Synthetic (label clearly in UI with a "simulated" chip):** tanker charter
  availability, port congestion indices, live cargo manifests.
- **Everything is cached** into `data/cache/` by ingestion services. The demo
  runs entirely from cache + a scripted event injector
  (`backend/app/seed/inject_escalation.py`) that replays a Hormuz escalation
  headline sequence. Never demo against a live API.

## Scenario model (sim/) — ground rules

- Pure functions: `run_scenario(scenario_cfg, state) -> ScenarioResult`.
- Inputs and every coefficient come from `config/assumptions.yaml`, each with a
  `# source:` comment (PPAC, brief figures: 88% import dependence, 40–45% via
  Hormuz, ~9.5 days SPR cover).
- Outputs: per-refinery shortfall (kb/d), SPR runway (days), landed cost delta
  ($/bbl), estimated retail pass-through (₹/litre), each with the formula
  string attached so the UI can render "how was this computed".

## Non-goals (do not build)

- SPR drawdown optimiser and full digital twin — roadmap slides only.
- Auth, multi-tenancy, deployment infra. `docker-compose up` locally is enough.
- Real-time training of any ML model. Risk scoring is a transparent weighted
  model; LLMs do extraction/classification only.

## Working agreements for Claude Code

- Follow PLAN.md phase order; check off tasks as completed and note deviations
  at the bottom of PLAN.md under "Log".
- Prefer boring, readable code over clever abstractions — judges may read it.
- When a free API is flaky or gated, fall back to generating a realistic cached
  fixture immediately and note it in the Log; do not burn hours on access.
- Keep the demo path sacred: after any change, `make demo` (compose up, seed,
  inject escalation, open dashboard) must still work end to end.
- Ask before adding any new heavy dependency.
