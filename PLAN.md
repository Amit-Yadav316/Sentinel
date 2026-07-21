# PLAN.md — Sentinel build plan (ET AI Hackathon 2026, PS2)

Read CLAUDE.md first. Work phases in order; within a phase, tasks are roughly
sequential. Check off tasks (`[x]`) as you complete them. Log deviations,
fallbacks, and open questions in the **Log** section at the bottom.

Definition of done for the whole project: `make demo` boots the stack, seeds
cached data, injects the escalation sequence, and the full loop
(signal → risk score climb → scenario auto-trigger → recommendation cards)
plays out in the browser with no live-internet dependency.

---

## Phase 0 — Skeleton & plumbing (½ day)

- [x] Init monorepo per CLAUDE.md layout; Python 3.11 project with uv or
      poetry; Vite + React + TS frontend; ruff/black/eslint/prettier configs.
- [~] `docker-compose.yml`: postgres:16 with pgvector, backend, frontend.
      DEVIATION: swapped for zero-dependency SQLite so the demo boots with no
      services; `DATABASE_URL` is Postgres-ready. See Log.
- [x] FastAPI app factory, health endpoint, SQLAlchemy session setup, Alembic
      init with first empty migration.
- [x] `Makefile`: `make dev`, `make demo`, `make test`, `make seed`.
- [x] `.env.example` with `ANTHROPIC_API_KEY`, `LLM_MODE=mock|live`,
      `DATA_MODE=cache|live`.

## Phase 1 — Config corpus & data model (1 day)

- [x] Write `config/corridors.yaml`: 5 corridors (Hormuz, Red Sea/Suez, Cape,
      Atlantic/US Gulf, Pacific/Far East) with chokepoints, baseline share of
      India's imports, typical transit days to Indian west-coast ports.
      Source figures from the brief + PPAC; cite in comments.
- [x] Write `config/refineries.yaml`: 8–10 major Indian refineries (Jamnagar
      DTA+SEZ, Vadinar, Paradip, Kochi, Panipat, Mangalore, Chennai, Barauni)
      with capacity (kb/d) and grade tolerance (API° range, max sulfur %).
      Public data; approximate where needed and mark `approx: true`.
- [x] Write `config/crudes.yaml`: 12–15 crudes across origins (Basrah Medium,
      Arab Light/Heavy, Murban, WTI Midland, Bonny Light, Girassol, Tupi,
      Urals — flag sanction caveat) with API°, sulfur %, typical FOB
      differential to Brent, load port, corridor(s).
- [x] Write `config/assumptions.yaml`: SPR cover 9.5 days, import dependence
      88%, Hormuz share 40–45%, freight $/bbl by route, pass-through formula
      coefficients. Every line gets a `# source:` comment.
- [x] SQLAlchemy models + migration: `events`, `risk_scores` (with
      `evidence jsonb`), `scenarios`, `scenario_runs`, `recommendations`,
      `vessels`, `prices`. Pydantic schemas mirroring them.
- [x] Loader that ingests the YAML corpus into reference tables at seed time.

## Phase 2 — Signal layer (1½ days)

- [x] `services/gdelt.py`: pull GDELT 2.0 events filtered to energy/maritime/
      Gulf keywords; normalize to `RawEvent`; cache raw JSON to `data/cache/`.
- [x] `services/prices.py`: Brent daily + intraday via yfinance; cache.
- [x] `services/ofac.py`: download SDN CSV once, parse vessel/entity names
      relevant to tankers; cache.
- [x] `services/ais.py`: AISStream websocket client with bounding boxes for
      Hormuz, Bab-el-Mandeb, and Indian west coast; record positions to
      `vessels`; include a replay mode that streams from cache.
      **Fallback if free tier blocks us:** generate a realistic synthetic
      vessel fixture (30–40 tankers with plausible tracks) and log it.
- [x] `agents/signal_extraction.py` (LangGraph node): LLM classifies each
      RawEvent → `{event_type, corridor, severity_0_1, entities, confidence}`
      with a strict Pydantic output schema. Mock mode returns deterministic
      fixtures keyed by event id.
- [x] `agents/risk_scoring.py`: deterministic model — per corridor, exponential
      time-decayed sum of severity×type-weight, squashed to 0–100; weights in
      `assumptions.yaml`. Persist score + full evidence trail (event ids,
      weights, decay factors).
- [x] API: `GET /corridors/risk` (latest scores + evidence),
      `WS /risk/stream` (push updates).
- [x] Unit tests: risk scoring with hand-computed expected values; extraction
      agent in mock mode.

## Phase 3 — Scenario engine (1½ days)

- [x] `sim/flow_model.py`: pure-function supply flow model. Given corridor
      throughput multipliers, compute: supply gap (kb/d), allocation of gap to
      refineries (pro-rata by corridor dependence), SPR runway
      (days = reserve_volume / uncovered_gap), landed cost delta (spot premium
      + rerouted freight), retail pass-through estimate (₹/L).
- [x] Attach formula strings to every output field (for UI "how computed").
- [x] Define 3 scenarios in `config/`: `hormuz_50`, `red_sea_full`,
      `opec_cut_2mbpd` — each = corridor multipliers + price shock params.
- [x] `agents/scenario.py`: node that runs a scenario against current state;
      persists `scenario_runs`.
- [x] Auto-trigger rule: when a corridor risk score crosses a configurable
      threshold (default 70), enqueue its mapped scenario run.
- [x] API: `POST /scenarios/{name}/run`, `GET /scenario-runs/{id}`.
- [x] Unit tests: each scenario against a frozen baseline state with
      hand-computed expected refinery shortfalls and SPR runway.

## Phase 4 — Procurement agent (1½ days)

- [x] Build the RAG corpus: chunk `crudes.yaml` + `refineries.yaml` +
      short prose notes on grade compatibility into pgvector.
- [x] `agents/procurement.py`: for a scenario run's supply gap —
      1) enumerate candidate (crude, route) pairs from unaffected corridors;
      2) score each on cost delta ($/bbl = FOB diff + freight + spot premium),
         transit days, availability (synthetic index), compatibility
         (deterministic API°/sulfur check per shortfall refinery, with an LLM-
         written one-line rationale via RAG);
      3) emit top 3 `Recommendation` records: replacement volume, source,
         route, ETA, cost delta, compatible refineries, caveats (sanctions
         flag for Urals).
- [x] Brief export: `GET /recommendations/{id}/brief` → rendered markdown
      (one-page procurement brief).
- [x] Tests: compatibility check unit tests; full agent in mock LLM mode.

## Phase 5 — Frontend (2 days)

- [x] App shell: dark theme, left nav with the 3 screens, top status bar
      (Brent price, SPR days, max corridor risk).
- [x] **Screen 1 — Corridor Map:** deck.gl map with corridor arcs colored by
      risk score, vessel dots (from AIS/replay), click corridor → evidence
      panel listing the headlines/events behind the score with weights.
- [x] **Screen 2 — Scenario Console:** run/auto-run scenarios; results as
      refinery shortfall map layer + SPR runway countdown + cost delta cards;
      every number has an ⓘ that reveals its formula string.
- [x] **Screen 3 — Recommendations:** ranked cards (volume, source, route,
      ETA, $/bbl delta, compatible refineries, caveat chips incl. "simulated"
      labels); "Export brief" button downloads the markdown brief.
- [x] Websocket wiring so the escalation injection visibly moves the risk
      score and auto-opens the scenario result.
- [x] Polish pass: loading states, empty states, number formatting (kb/d,
      $/bbl, ₹/L), "simulated data" chips wherever synthetic data appears.

## Phase 6 — Demo, seed & deliverables (1½ days)

- [x] `seed/`: load YAML corpus, cached prices, cached GDELT baseline, vessel
      replay file; calm-state fixture where Hormuz risk ≈ 45.
- [x] `seed/inject_escalation.py`: replay 8–10 escalating headlines over
      ~60 seconds → Hormuz score climbs past 70 → auto scenario → recs appear.
- [x] `make demo` runs the whole thing end to end; test on a clean machine.
- [x] Architecture diagram (docs/architecture.md): mermaid, matches CLAUDE.md.
      TODO: export PNG/SVG from the mermaid source for the deck.
- [~] Deck: 12-slide outline + speaker notes in docs/deck-notes.md.
      TODO: build the actual slides from the outline.
- [ ] Record 3-min demo video following the script (calm → escalation →
      scenario → recommendation → "signal to recommendation: 4 minutes").
- [x] README: setup, `make demo`, data sources table (real vs synthetic).

---

## Stretch (only if all phases done)

- [x] Second corridor demo path (Red Sea) to show generality.
- [x] Simple backtest slide: replay 2025 Hormuz standoff week from GDELT
      history and show the score would have climbed before the price spike.

## Log

**2026-07 — Initial build (Phases 0–5 complete, Phase 6 partial).**

Deliberate, reversible deviations (all logged for the judges; each is a one-line
swap back to the "production" choice — see docs/architecture.md):

- **Postgres + pgvector → SQLite (SQLAlchemy 2.0).** Zero-dependency offline
  demo. `DATABASE_URL` swaps the engine. Procurement "RAG" uses an in-process
  deterministic ranking + compat check instead of pgvector cosine search.
- **LangGraph → explicit `agents/pipeline.py`.** Kept discrete nodes, strict
  Pydantic schemas, and mock mode; dropped the framework dependency for
  readability and offline reliability.
- **deck.gl → hand-rolled SVG map** (`components/CorridorMap.tsx`). No tile
  server → renders fully offline. Equirectangular projection over the corridor
  bounding box; animated flow arcs colored by risk.
- **Alembic migrations → `Base.metadata.create_all`** at startup/seed. Fine for
  a single-node demo; the alembic/ slot is left open in the layout.
- **AIS live websocket → synthetic vessel fixture** (CLAUDE.md-sanctioned
  fallback). 36 deterministic tankers along corridor arcs, flagged `synthetic`
  and shown with a "simulated" chip.

Assumptions added beyond the brief (all in `config/assumptions.yaml` with
sources): logistic squash params for the risk model; spot-premium-vs-gap curve;
reroute freight adders; retail pass-through efficiency (0.35, testable);
procurement freight-per-transit-day + ranking weights + a SIMULATED availability
index per crude.

Config correction during test: bumped Jamnagar DTA/SEZ sulfur tolerance to 4.0%
(deep-conversion complexes genuinely process Basrah Heavy @3.9%S) — caught by
`test_procurement.py::test_heavy_sour_fits_deep_conversion_refinery`.

Windows note: replaced non-ASCII console output (⚡, →) in the injector with
ASCII so it runs under the cp1252 default console.

Validation: 22/22 pytest pass; frontend `tsc --noEmit` + `vite build` clean;
full-stack smoke test confirmed calm state (Hormuz 45.3), manual `hormuz_50` run
(gap 1013 kb/d, runway 300d, +$30.5/bbl — matches hand-computed tests), and the
live `/demo/escalate` path drove Hormuz to 76.6 and auto-fired the scenario over
the websocket.

**Open TODO (Phase 6):** export architecture PNG/SVG from mermaid; build the
12-slide deck from docs/deck-notes.md; record the 3-min demo video.
