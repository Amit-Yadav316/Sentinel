# Sentinel — Energy Supply Chain Resilience Platform

**ET AI Hackathon 2026 · PS2 — AI-Driven Energy Supply Chain Resilience for
Import-Dependent Economies.**

Sentinel is a crisis-to-decision engine for India's crude oil supply chain. It
**watches** geopolitical + maritime signals and maintains a live per-corridor
disruption risk score, **simulates** named disruption scenarios with fully
transparent math, and **decides** — emitting ranked, grade-checked, executable
procurement rerouting recommendations.

> **Core claim:** signal → executable recommendation in under 5 minutes, running
> entirely offline from cached data.

![loop](docs/architecture.md)

---

## Quick start

Prereqs: [`uv`](https://docs.astral.sh/uv/), Node 18+, Python 3.11 (uv can fetch it).

### 1. Install
```bash
# backend
cd backend && uv venv --python 3.11 && uv pip install -e ".[dev]"
# frontend
cd ../frontend && npm install
```

### 2. Seed the calm demo state
```bash
cd backend && uv run python -m app.seed.seed
# -> Hormuz 45.3 · Red Sea 40.2 · Cape 15.3 · ...
```

### 3. Run it (two terminals)
```bash
# terminal A — API on :8000
cd backend && uv run uvicorn app.main:app --port 8000
# terminal B — dashboard on :5173
cd frontend && npm run dev
```
Open **http://localhost:5173** and click **"▶ Run escalation demo"** (top-right).

### One-command demo (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\demo.ps1
```

### Prove the loop with no servers
```bash
cd backend && uv run python -m app.seed.inject_escalation
# replays 9 headlines: Hormuz 45 -> 72, auto-fires hormuz_50, prints top rec
```

`make` targets (`install`, `seed`, `test`, `api`, `web`, `demo`, `lint`) mirror
all of the above on systems that have GNU make.

---

## What the demo shows

1. **Corridor Map** — corridor arcs colored by live risk, synthetic tanker
   dots, Brent strip. Click a corridor → the **evidence trail** (headlines,
   type weights, time-decay) that produced the score.
2. **Escalation** — 9 replayed headlines drive Hormuz past the auto-trigger
   threshold (70); the `hormuz_50` scenario fires automatically.
3. **Scenario Console** — supply gap, SPR runway, landed-cost delta, retail
   pass-through. **Every number has an ⓘ revealing its exact formula.**
4. **Recommendations** — 3 ranked reroute cards (volume, source, route, ETA,
   $/bbl delta, grade-compatible refineries, sanctions/simulated caveats) with a
   one-click **procurement brief** export.

---

## Testing
```bash
cd backend && uv run pytest -q     # 22 tests
```
The scenario math (`sim/flow_model.py`) and risk model (`agents/risk_scoring.py`)
are unit-tested against **hand-computed expected values** — see the docstrings
in `tests/test_flow_model.py` and `tests/test_risk_scoring.py`.

---

## Data sources

| Signal | Source | Demo mode |
|---|---|---|
| News events | GDELT 2.0 / curated headlines | **cached** baseline + scripted escalation |
| Brent price | Yahoo Finance chart API (`BZ=F`) | **live** on load (real-time quote, ~1s) with instant cache fallback |
| Sanctions | OFAC SDN list | **cached** flag snapshot |
| Vessel positions | AISStream.io (free key) | **live** real tankers in Hormuz/Bab-el-Mandeb/W-coast boxes; grounded **synthetic** fallback (40 tankers in real maritime zones) — labelled *simulated* |
| Map geography | Natural Earth 110m coastlines | **bundled** public-domain basemap (real coastlines, offline) |
| Corridors / refineries / crudes | PPAC + public crude assays (BP/ExxonMobil) | `config/*.yaml`, each value sourced |
| Charter availability / port congestion | — | **synthetic** — labelled *simulated* in the UI |

Everything the demo needs is cached under `data/cache/`. **Never demoed against a
live API.**

---

## Transparency contract

- No magic numbers in code. Every scenario/risk coefficient lives in
  `config/assumptions.yaml` with a `# source:` comment.
- Every risk score persists its full evidence trail (which events moved it,
  weights, decay factors).
- Every scenario output carries the formula string that produced it.

See **[docs/architecture.md](docs/architecture.md)** for the system diagram and
the (deliberate, reversible) deviations from the original spec, and
**[docs/deck-notes.md](docs/deck-notes.md)** for the presentation outline.

## Repo layout
```
backend/   FastAPI · SQLAlchemy · agents · sim · seed · tests
frontend/  React + Vite + TS + Tailwind (3 screens)
config/    corridors · refineries · crudes · assumptions · scenarios (YAML)
data/cache/ offline fixtures
docs/      architecture + deck notes
scripts/   Windows demo helpers
```
