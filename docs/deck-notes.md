# Sentinel — Presentation Deck (12 slides)

Speaker notes + slide content. Optimised for the ET AI Hackathon 2026 judging
weights: Innovation 25 · Business Impact 25 · Technical Excellence 20 ·
Scalability 15 · UX 15.

---

**1 · Title.** Sentinel — AI-Driven Energy Supply Chain Resilience for
Import-Dependent Economies. Tagline: *"Signal to executable recommendation in
under 5 minutes."*

**2 · The problem (brief's own numbers).** India imports **88%** of its crude.
**40–45%** transits the Strait of Hormuz. Strategic reserves cover only
**~9.5 days**. A single chokepoint event cascades to refinery run-cuts, landed
cost spikes, and pump-price pass-through — and today the response is manual and
slow (the ~47-day stabilization gap).

**3 · The gap.** Signals (news, AIS, prices, sanctions) exist but are siloed;
scenario planning is spreadsheet-bound and opaque; procurement rerouting is
tribal knowledge. No single loop from *signal* to *executable decision*.

**4 · Solution — the loop.** Watch → Simulate → Decide. One continuous engine:
live corridor risk → auto-triggered scenario → ranked, grade-checked
procurement alternatives with cost/ETA/compatibility. (Show architecture.)

**5 · Live demo (calm state).** Corridor map: Hormuz resting at 45, vessels
streaming, Brent strip. Click a corridor → the evidence trail (which headlines,
weights, decay) behind the score. *Every number is inspectable.*

**6 · Live demo (escalation).** Hit "Run escalation demo": 9 headlines replay;
Hormuz climbs 45 → 50 → 59 → 66 → **72**. At 70 the `hormuz_50` scenario
**auto-fires** — no human in the loop yet.

**7 · Live demo (scenario math, transparency slide).** Supply gap **1,013 kb/d**
(21.5% of net imports), SPR runway **300 days vs the gap**, landed cost
**+$30.5/bbl**, retail **₹5.55/L**. Click any ⓘ → the exact formula. Refinery
shortfall allocation bar chart. *No black boxes — coefficients live in
`assumptions.yaml`, each with a source.*

**8 · Live demo (executable recommendation).** 3 ranked cards: replacement
volume, source, route, ETA, $/bbl delta, **grade-compatible refineries**
(deterministic API°/sulfur check), caveat chips (sanctions flag on Urals,
"simulated" on synthetic fields). One click → **procurement brief** (markdown).
*"Signal to recommendation: 4 minutes."*

**9 · Technical excellence.** Deterministic, auditable risk model (not ML);
pure-function scenario engine **unit-tested against hand-computed values**;
strict Pydantic schemas on every LLM step with an offline mock mode; full
evidence trail persisted per score. 22 passing tests.

**10 · Business impact (quantified).** Faster lead time = smaller gap to cover.
Illustrative: shaving even 2–3 days off reroute decisions on a 1 mb/d shortfall
protects days of SPR runway and blunts the ₹/L pass-through. Decision quality:
grade-compat filtering avoids infeasible cargoes procurement would otherwise
chase.

**11 · Scalability.** Same corridor/commodity abstraction generalizes to **LNG,
coal, fertilizer/urea, edible oils** — any import-dependent chokepoint problem.
Swap `config/*.yaml`; the engine is commodity-agnostic. Postgres+pgvector and
LangGraph are drop-in for scale.

**12 · Roadmap.** SPR drawdown optimiser · full supply-chain digital twin ·
backtest module (replay historical standoffs to show lead-time edge) · live
AIS + GDELT in production mode. Ask: pilot with a refiner / PPAC.
