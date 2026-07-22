# Sentinel — Presentation Deck (13 slides)

Speaker notes + slide content. Optimised for the ET AI Hackathon 2026 judging
weights: Innovation 25 · Business Impact 25 · Technical Excellence 20 ·
Scalability 15 · User Experience 15. The deck is maintained separately (Canva /
local export); this file is the authoritative outline.

---

**1 · Title.** Sentinel — AI-Driven Energy Supply Chain Resilience for
Import-Dependent Economies. Tagline: *"Signal to executable recommendation in
under 5 minutes."* Stat band: 88% import dependence · 40–45% via Hormuz ·
9.5-day strategic reserve · <5 min response.

**2 · The problem (brief's own numbers).** India imports **88%** of its crude;
**40–45%** transits the Strait of Hormuz; strategic reserves cover only
**~9.5 days**. The 2025 US–Iran standoff sent Brent **+8% in one session**. A
McKinsey analysis found economies without automated rerouting took **47 days
longer** to stabilise. The cascade hits in days: refinery run-cuts → landed-cost
spikes → pump-price pass-through.

**3 · The gap.** Signals (news, AIS, prices, sanctions) sit in silos; scenario
planning is spreadsheet-bound and opaque; procurement rerouting is tribal
knowledge. No single owner of the loop from *signal* to *executable decision* —
that handoff gap is the 47-day lag.

**4 · Solution — the loop.** **Watch → Simulate → Decide.** Live corridor risk
(0–100 with an evidence trail) → a risk breach **auto-runs** the mapped scenario
→ ranked, grade-checked procurement reroutes. Reactive becomes anticipatory.

**5 · Architecture.** Ingestion (GDELT news, AISStream vessels, Yahoo Brent,
OFAC sanctions) → four agents (1 LLM extraction · 2 risk scoring · 3 scenario ·
4 procurement) → SQLAlchemy storage → FastAPI REST + websocket → React
dashboard. **The LLM only extracts; risk, scenario and procurement are
deterministic, auditable math.** Every coefficient lives in `assumptions.yaml`
with a cited source.

**6 · Live demo — calm state (Corridor Risk Map).** Real coastline basemap,
live AIS vessels, a live signal feed classified by the extraction agent. Hormuz
rests at **45** (WATCH). Click a corridor → the **evidence trail**: which
headlines moved the score, with weights and time-decay. Baseline: Hormuz 45 ·
Red Sea 40 · Cape 15 · Atlantic 10 · Pacific 12.

**7 · Live demo — escalation.** Run Escalation Demo: 9 headlines drive Hormuz
**45 → 76**; at **70** the `hormuz_50` scenario **auto-fires** — no human in the
loop. Model: `score = baseline + (100−baseline) × logistic01(Σ severity ×
type-weight × decay)`, half-life 36h. Deterministic and reproducible.

**8 · Live demo — scenario math (transparency).** Supply gap **1,013 kb/d**
(21.5% of imports), SPR runway **300 days**, landed cost **+$30.5/bbl**
($82→$112.5), retail **₹5.55/L**, Jamnagar shortfall **223 kb/d**. Downstream:
**+$52 bn/yr** import bill · **−0.43 pp** GDP · **+1.22 pp** current-account ·
power-sector stress **33/100**. Every number reveals its formula; coefficients
sourced and **unit-tested** against hand-computed values.

**9 · Live demo — executable recommendation (Procurement).** Three ranked
replacement crudes (Urals, Tupi, Bonny Light), scored on cost, transit,
availability and a **deterministic API°/sulfur grade check** per shortfall
refinery — only liftable cargoes qualify. Urals flagged for sanctions risk.
One-click procurement brief. *"Signal → recommendation: 4 minutes."*

**10 · Historical backtest.** The *same* model replayed on the **June 2025
Israel–Iran / Hormuz escalation**: risk climbs from baseline (Jun 9), crosses
**CRITICAL on Jun 13** as the strikes begin, stays critical through Brent's run-up
to its **Jun 20** peak, and re-flags the **Jun 23** US strikes — overlaid on
Brent. Validates lead time on real history, not just a scripted demo.

**11 · Technical excellence.** Deterministic, auditable models (not ML);
pure-function scenario engine **unit-tested (31 tests)** against hand-computed
values; strict schemas on the LLM step (Gemini / Claude / mock); full evidence
trail persisted per score; runs fully offline from cache; zero magic numbers.

**12 · Business impact + scalability.** Lead time *is* the buffer: with 9.5 days
of cover, decision time is the scarce resource — compressed from days to <5 min
vs the 47-day manual gap, and every recommendation is grade-checked. The engine
is **commodity-agnostic** — swap `config/*.yaml` for LNG, coal, fertilizer,
edible oils. Postgres + pgvector and a multi-agent framework are drop-in for
scale.

**13 · Roadmap & ask.** Next: SPR drawdown optimiser · full supply-chain digital
twin. Then: expanded backtests · live production feeds. Recap: 88% dependence ·
9.5-day cover · 31 tests · <5 min. **The ask: a pilot with a refiner or PPAC.**
Sentinel — energy security, made fast and made transparent.
