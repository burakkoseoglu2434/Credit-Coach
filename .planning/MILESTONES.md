# Project Milestones: Credit Coach

**Current active milestone:** v2.3 Threshold & Outcome Optimization

## v2.3 Threshold & Outcome Optimization (Active)

**Goal:** Improve approval and conditional yield from the shipped `v2.2` trust baseline by tuning bounded thresholds and making existing offer/readiness signals produce real funnel movement.

**Why this milestone exists now:**
- `v2.2` closed the remaining winner-integrity and consumer-consistency trust repairs, so the next bottleneck is business lift rather than trust repair
- pilot-facing demos are now credible, but the decision funnel still needs stronger `APPROVED + CONDITIONAL` movement to support customer conversations
- offer maturity and readiness are currently measured well but remain too descriptive rather than outcome-producing
- the system should first optimize results using existing signals before expanding action semantics or feature space

**Planned phases:** 49-52

**Workstreams:**
- Phase 49: Threshold Policy Evaluation & Provenance
- Phase 50: Offer & Readiness Outcome Rules
- Phase 51: Funnel Movement Guardrails & Evidence
- Phase 52: Preferred Policy Baseline & Demo Proof

**Acceptance checks:**
- at least one bounded policy profile improves `APPROVED + CONDITIONAL` yield versus the shipped `v2.2` baseline on the standard cohorts
- `offer_needed_balanced` shows explicit outcome movement attributable to offer/readiness rules rather than descriptive-only diagnostics
- yield proof can separate threshold-driven movement from offer/readiness-driven movement
- all shipped `v2.2` trust counters remain clean while candidate and promoted policies are evaluated
- one preferred policy profile and one fallback profile are ready for pilot demos and first customer conversations

**Not in this milestone:**
- expanding action semantics or opening new recommendation feature space
- redesign of Phases `40`, `40.5`, `41`, `42`, `42.5`, `43`, `45`, `46`, `47`, or `48`
- new borrower-facing channels, live institution integrations, or compliance automation

**Current status:** Milestone defined; requirements and roadmap are ready, phase execution has not started yet.

## v2.2 Winner Integrity & Consumer Consistency (Shipped: 2026-04-02)

**Goal:** Fix selected-winner integrity and consumer-surface consistency before any threshold widening or approval-rate optimization.

**Why this milestone exists now:**
- targeted failure analysis showed that selected invalid recommendation leakage is dominated by a planner filtering fallback bug in `choose_best_plan(...)`
- all leaked selected invalid winners observed in large-sample reruns were `dice` winners
- recommendation validity annotation appears to be working, so the remaining gap is winner enforcement and surface coherence
- operator packet inconsistencies remain: invalid selected actions can still appear in short view, some external `CONDITIONAL` cases still point at selected `REJECTED` rows, and approved packets can still show fallback blockers

**Planned phases:** 45-48

**Workstreams:**
- Phase 45: Winner Integrity Hard Stop
- Phase 46: Dice Lane Validity Enforcement
- Phase 47: Selected Surface Consistency
- Phase 48: Operator Packet Coherence

**Acceptance checks:**
- `0` selected invalid winners across large-sample reruns
- `0` external `CONDITIONAL` outputs pointing at selected `REJECTED` rows
- `0` approved packets with fallback blockers when no active drivers exist
- `0` operator short views rendering invalid selected actions as the chosen recommendation

**Not in this milestone:**
- threshold widening
- approval-rate optimization
- redesign of Phases `40`, `40.5`, `41`, `42`, `42.5`, or `43`
- new borrower-facing channels, live institution integrations, or compliance automation

**Delivered:** A trust-repair milestone that made winner selection fail closed, enforced DICE contender quality before planner contention, aligned selected consumer truth across raw and derived surfaces, and removed tracked operator packet contradictions without widening thresholds or reopening shipped decision semantics.

**Phases completed:** 45-48 (12 plans total)

**Key accomplishments:**
- Hard-stopped invalid selected winners with deterministic valid-only widening and explicit `no_valid_winner` behavior.
- Converged DICE onto the shared typed-action contract and added lane-specific contender-quality gates with rerun-proven selected DICE cleanliness.
- Aligned raw summary, flat metrics, operator packets, and explanation packs on one selected projection and explicit empty-state contract.
- Made operator packets decision-aware and proved zero approved blocker/action contradictions and zero tracked packet-coherence mismatches on large-sample reruns.

**Stats:**
- 4 GSD phases completed with 12 executed plans and 66 planned tasks
- Milestone audit passed with 11/11 requirements satisfied
- Nyquist compliance: 4/4 phases compliant
- 78 files changed in the shipped milestone range with 8,600 insertions and 502 deletions
- Timeline: 2026-03-24 through 2026-04-02

**Known gaps carried forward:**
- Large-sample reruns still surfaced zero natural `no_valid_winner` cases, so empty-state selected-surface and packet behavior remain proven by automated tests rather than cohort evidence.
- Collection reruns still emit pandas `FutureWarning` messages from empty/all-NA frame concatenation.
- Local `gsd-tools.cjs` milestone-op helper still requires manual fallback.

**What's next:** Define the next milestone with `$gsd-new-milestone`

## v1.0 Brownfield Baseline (Shipped: 2026-03-10)

**Delivered:** A reconstructed brownfield baseline covering deterministic model training, gate-aligned recourse generation, trajectory-aware evaluation, benchmark and challenger workflows, telemetry export, audit controls, and production smoke gates.

**Phases completed:** 1-7 (20 plans total)

**Key accomplishments:**
- Established deterministic backend selection, calibration, and reproducible artifact generation
- Shifted recourse scoring toward approval, reliability, and worst-margin gate passing
- Added high-risk and trajectory-style planning paths with richer KPI outputs
- Expanded explainability, fairness, stress, benchmark, and backtesting coverage
- Added telemetry, runbooks, release gates, auth hardening, and audit-chain persistence
- Aligned smoke, challenger, and batch workflows around a measurable KPI contract baseline

**Stats:**
- 7 historical phases reconstructed from imported planning and execution documents
- 20 plans represented in the imported roadmap
- Git range unavailable - pre-GSD history was imported from legacy docs rather than reconstructed from phase commits

**Known gaps carried forward:**
- Fairness and equalized-odds stability still break under repeated seeded KPI checks
- 4-week trajectory and short-term effectiveness need a more realistic contract and stronger action space
- Candidate diversity and source-mix evidence are still weaker than release needs
- Telemetry enforcement and outcome-feedback loops need tighter production-grade guarantees

**What's next:** v1.1 Fairness Stability & KPI Hardening

---

## v1.1 Fairness Stability & KPI Hardening (Shipped: 2026-03-15)

**Delivered:** A seed-stable release hardening layer covering fairness release semantics, unified KPI contracts, canonical candidate-quality evidence, telemetry-gated release packs, and business-proxy outcome feedback summaries.

**Phases completed:** 8-11 (12 plans total)

**Key accomplishments:**
- Standardized `GO | LIMITED_GO | NO_GO` fairness release semantics across suite, smoke, and challenger workflows
- Unified seeded KPI contracts, frozen model provenance, and milestone acceptance artifacts
- Promoted candidate diversity, high-risk tuning, and comparative impact into canonical seeded evidence
- Made telemetry fail closed for operational rollout while preserving release-decision traceability
- Added suite-owned `release_evidence_pack.json` bundles and linked outcome-feedback summaries into derived milestone review

**Stats:**
- 4 GSD phases completed with 12 executed plans
- Milestone audit passed with 12/12 requirements satisfied
- Nyquist compliance: 4/4 phases compliant

**Known gaps carried forward:**
- Action space is still too tied to feature edits and lacks richer behavioral, structural, and institutional actions
- Planner scoring still treats execution as mostly static rather than explicitly behavior-aware
- Sequential, multi-phase recommendation trajectories are not yet first-class planning objects
- Institution-side offer optimization and learned feedback loops remain only partial capabilities

**What's next:** v1.2 Recommendation Quality Hardening

---

## v1.2 Recommendation Quality Hardening (Shipped: 2026-03-16)

**Delivered:** A behavior-aware recourse stack with typed action realism, execution-aware ranking, multi-phase trajectories, institution-side offer optimization, and a confidence-aware learning loop over delayed outcomes.

**Phases completed:** 12-16 (15 plans total)

**Key accomplishments:**
- Replaced raw feature-edit recommendation semantics with typed behavioral, structural, and institutional actions plus explicit feasibility and interaction constraints
- Added execution-probability modeling and behavior-aware ranking without weakening inherited fairness, reliability, telemetry, or acceptance gates
- Promoted phased trajectories, weekly checkpoint simulation, and replan-aware evidence to first-class planning contracts
- Integrated institution-side offers with separate acceptance modeling and governance-first recovery-aware ranking
- Closed the learning loop with compact decision logging, graded outcome-ingestion readiness, and IPS/Doubly Robust off-policy evaluation

**Stats:**
- 5 GSD phases completed with 15 executed plans
- Milestone audit passed with 11/11 requirements satisfied
- Nyquist compliance: 5/5 phases compliant
- 88 files changed in the shipped milestone range with 15,125 insertions and 381 deletions

**Known gaps carried forward:**
- Operator-facing dashboards still need to summarize the artifact-rich milestone health surface
- Regulatory explanation and user-facing adverse-action narratives are still future work
- Online policy promotion remains intentionally blocked behind evidence-first learning
- External institution integrations can still be deepened beyond internal artifact contracts

**What's next:** v1.3 Portfolio Intelligence & Productization

---

## v1.3 Portfolio Intelligence & Productization (Shipped: 2026-03-20)

**Delivered:** An audited portfolio-proof and productization milestone that turned the recommendation engine into a buyer-safe, analyst-safe, and pilot-baseline product system without breaking engine-owned artifact truth.

**Phases completed:** 17-25 (28 plans total)

**Key accomplishments:**
- Established full-portfolio coverage, segment, and representativeness proof instead of relying on curated demo stories
- Moved recommendation translation into an engine-owned narrative contract with business-first defaults and technical reveal on demand
- Re-hardened behavior-aware and trajectory truth before refreshing proof and product-confidence surfaces
- Turned Demo Center, Proof, and Investor into business-first product surfaces synchronized to curated engine artifacts
- Closed analyst UAT and pilot-readiness baseline with explicit runbooks, results, intake, and handoff documentation

**Stats:**
- 9 GSD phases completed with 28 executed plans and 56 planned tasks
- Milestone audit passed with 9/9 requirements satisfied
- Nyquist compliance: 9/9 phases compliant
- 151 files changed in the shipped milestone range with 25,902 insertions and 1,320 deletions
- Timeline: 2026-03-17 through 2026-03-20

**Known gaps carried forward:**
- Pilot-grade external institution integrations remain deeper future work beyond curated artifact handoff
- Regulatory explanation and adverse-action communication packs remain future milestone scope
- Release review, proof refresh, and milestone health automation remain future work
- Local `gsd-tools.cjs` milestone-op automation still requires manual fallback

**What's next:** Define the next milestone with `$gsd-new-milestone`

---

## v2.0 Personalized Action & Decision Intelligence (Shipped: 2026-03-22)

**Delivered:** A personalized action-intelligence milestone that turned recourse outputs into deterministic semantic actions, customer-specific numeric targets, feasibility- and execution-aware plans, institution-side offer contracts, product-ready narratives, typed product surfaces, portfolio impact proof, calibration review, and pilot-facing package delivery.

**Phases completed:** 30-39 (30 plans total)

**Key accomplishments:**
- Replaced raw feature-delta recommendation identity with deterministic semantic actions, grouped business-vs-technical contracts, and canonical action families
- Added customer-specific numeric targets with feasibility, difficulty, execution realism, and institution-offer truth in one plan contract
- Shipped narrative and product-surface upgrades so the website renders engine-owned personalized plans without UI-side meaning invention
- Added portfolio-level numeric impact and calibration review that measure burden, realization, false optimism, instability, and offer dependency across segments
- Closed the milestone with a typed pilot bundle, guarded pilot package runner, and engine-to-website handoff docs for institution conversations

**Stats:**
- 10 GSD phases completed with 30 executed plans and 60 planned tasks
- Milestone audit passed with 10/10 requirements satisfied
- Nyquist compliance: 10/10 phases compliant
- 150 files changed in the shipped milestone range with 19,337 insertions and 998 deletions
- Timeline: 2026-03-20 through 2026-03-22

**Known gaps carried forward:**
- Pilot-grade external institution integrations remain future work beyond the shipped export-to-package seam
- Regulatory explanation and adverse-action communication packs remain outside the shipped scope
- Proof refresh, release review, and milestone health automation remain future work
- Local `gsd-tools.cjs` milestone-op automation still requires manual fallback

**What's next:** Define the next milestone with `$gsd-new-milestone`

---

## v2.1 Decision Ownership & Pilot-Ready Trust (Shipped: 2026-03-23)

**Delivered:** An audited deterministic-decision and pilot-trust milestone that repaired artifact contracts, established one decision owner, added cohort-aware calibration and operator review surfaces, hardened planner provenance and source-mix honesty, and closed with a repeatable pilot refresh baseline, artifact QA, institution overlays, and institution-facing explanation packs.

**Phases completed:** 40-44 (18 plans total)

**Key accomplishments:**
- Repaired raw and flat customer artifacts so decision-critical fields, parity signals, and zero-step rejection became null-free, explicit, and business-safe
- Shipped one deterministic decision owner with external `APPROVED | CONDITIONAL | REJECTED` outputs, internal review diagnostics, confidence, readiness, subtype truth, and upgrade conditions
- Added mixed-cohort funnel, readiness, and shadow calibration evidence under the same collection run root as raw and flat artifacts
- Added per-customer operator packets and collection-level briefings that support fast review without creating a second truth source
- Made planner provenance, empty-contender removal, source-mix honesty, diversity guardrails, and offer-maturity signals first-class review outputs
- Closed the milestone with repeatable pilot refresh orchestration, dedicated artifact QA, thin institution overlays, institution-facing explanation packs, and bounded proof documentation

**Stats:**
- 6 GSD phases completed with 18 executed plans and 84 planned tasks
- Milestone audit passed with 12/12 requirements satisfied
- Nyquist compliance: 6/6 phases compliant
- 97 files changed in the shipped milestone range with 14,475 insertions and 778 deletions
- Timeline: 2026-03-23 through 2026-03-23

**Known gaps carried forward:**
- Live institution integrations remain future work beyond the shipped overlay and package-based pilot baseline
- Compliance-adjacent explanation workflows remain bounded support artifacts rather than full compliance automation
- Recurring proof refresh, release review, and milestone health automation remain future scope
- Local `gsd-tools.cjs` milestone-op automation still requires manual fallback, and some validation frontmatter metadata needs cleanup

**Post-shipment carry-forward completed on 2026-03-24:**
- Phase `42.5 Recommendation Validity Layer` added canonical numeric recommendation validity, hard-invalid pre-selection filtering, warning penalties, operator manual-review badges, explanation-pack human-review propagation, and additive collection metrics.
- Code and regression validation passed cleanly for the carry-forward phase.
- Full processed-data 50-customer artifact rerun validation is still deferred locally because `credit-coach/data/processed/test.parquet` is not present in the current checkout.

**What's next:** Define the next milestone with `$gsd-new-milestone`

---
