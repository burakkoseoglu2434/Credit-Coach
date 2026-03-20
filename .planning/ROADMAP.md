# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- 🚧 **v1.3 Portfolio Intelligence & Productization** - Phases 17-25 (All phases complete; milestone audit passed 2026-03-20; ready for closeout)

<details>
<summary>✅ v1.0 Brownfield Baseline (Phases 1-7) - SHIPPED 2026-03-10</summary>

Historical archive: `.planning/milestones/v1.0-ROADMAP.md`

- Phase 1: Modeling Foundation Lock
- Phase 2: Gate-Aligned Recourse Core
- Phase 3: Trajectory and High-Risk Optimization
- Phase 4: Explainability and Decision Diagnostics
- Phase 5: Evaluation and Benchmark Matrix
- Phase 6: Production Hardening and Governance
- Phase 7: KPI Gate Stabilization

</details>

<details>
<summary>✅ v1.1 Fairness Stability & KPI Hardening (Phases 8-11) - SHIPPED 2026-03-15</summary>

Historical archive: `.planning/milestones/v1.1-ROADMAP.md`

- Phase 8: Fairness Stability Matrix
- Phase 9: KPI Contract Unification
- Phase 10: Candidate Quality and Trajectory Tuning
- Phase 11: Release Evidence and Outcome Feedback

</details>

<details>
<summary>✅ v1.2 Recommendation Quality Hardening (Phases 12-16) - SHIPPED 2026-03-16</summary>

Historical archive: `.planning/milestones/v1.2-ROADMAP.md`

- Phase 12: Action Realism & Feasibility Expansion
- Phase 13: Behavior-Aware Recourse
- Phase 14: Sequential Recourse Planning
- Phase 15: Policy Optimization Layer
- Phase 16: Outcome Feedback & Learning Loop

</details>

## Active Milestone

### v1.3 Portfolio Intelligence & Productization

**Goal**: Prove the engine across the full portfolio, translate technical outputs into institution-ready narratives, harden execution and trajectory truth where product credibility demands it, stabilize artifact-driven website surfaces, and reach analyst- and pilot-ready product credibility.
**Phases**: 17-25 currently defined
**Status**: Active, Phases 17-25 complete; milestone audit passed on 2026-03-20 and closeout is next

### Phase 17: Full Portfolio Evaluation & Coverage Audit

**Goal**: Run the engine across the full evaluation population and quantify coverage, feasibility, execution-weighted improvement, offer reach, checkpoint health, and governance-safe rates across segments.
**Depends on**: Phase 16
**Plans**: 3 complete

Plans:
- [x] 17-01: Build a full-population evaluation runner and canonical portfolio coverage tables
- [x] 17-02: Add segment-level reporting for risk, income, stress, trajectory, offer, and readiness slices
- [x] 17-03: Publish a portfolio validation review that separates curated demo stories from full-cohort proof

### Phase 18: Decision Narrative & Product Output Translation

**Goal**: Build a controlled translation layer that turns engine output into analyst-friendly and buyer-friendly product narratives, with executive summaries by default and expandable technical traceability on demand.
**Depends on**: Phase 17
**Plans**: 3 complete

Plans:
- [x] 18-01: Define the narrative contract and action template library for action summaries, why-it-matters, expected outcomes, and executive summary cards
- [x] 18-02: Add controlled technical reveal, checkpoint or offer or adverse-action narration, narrative confidence, and vocabulary consistency layers
- [x] 18-03: Validate one UI-ready output schema across representative cases so website and analyst surfaces can consume the same business-first narrative contract

### Phase 19: Behavior-Aware Recourse

**Goal**: Re-open the inherited behavior-aware ranking layer as an explicit v1.3 hardening target so recommendation quality reflects not only nominal PD improvement but also whether customers are likely to execute the plan.
**Depends on**: Phase 18
**Plans**: 3 complete

Plans:
- [x] 19-01: Harden execution-probability posture, burden-horizon penalties, and composite or dual-realization semantics
- [x] 19-02: Strengthen execution-aware ranking leverage, high-risk ordering, and provisional contender penalties
- [x] 19-03: Reframe behavior-aware artifacts and review around nominal-vs-execution-aware value and risk-band evidence

### Phase 20: Trajectory Hardening

**Goal**: Harden the inherited trajectory layer into a deterministic, checkpoint-safe, product-ready planning contract that keeps short-term health, monotonicity, and replan behavior under control.
**Depends on**: Phase 19
**Plans**: 3 complete

Plans:
- [x] 20-01: Lock deterministic phase and checkpoint contracts across all roadmap outputs
- [x] 20-02: Harden trajectory consistency, soft monotonicity, and early-health protection
- [x] 20-03: Make replan logic, trajectory status, and policy labels deterministic and execution-layer aligned

Planned scope:
- Canonical phase assignment:
  - every action has exactly one `primary_phase`
  - multi-phase or ambiguous phase assignment is disallowed
- Fixed phase set:
  - `phase_1_stabilize` (`0-4w`)
  - `phase_2_build` (`4-12w`)
  - `phase_3_optimize` (`12-24w`)
- Fixed checkpoint set:
  - `week 4` / `primary`
  - `week 12` / `confirmation`
  - `week 24` / `stability`
- Each checkpoint must carry:
  - `checkpoint_type`
  - `predicted_pd`
  - `pd_delta`
  - `gate_pass_estimate`
  - `status`
- Soft monotonicity hardening:
  - `4w >= 12w >= 24w` as the default expectation
  - small drift tolerated, large jumps flagged
- Deterministic trajectory flags:
  - `trajectory_jump_flag`
  - `non_monotonic_flag`
  - `checkpoint_inconsistency_flag`
- Early-health protection:
  - weak `4w` health prevents a plan from reading as strong
- Deterministic replan boundaries:
  - allowed only at `week 4`, `week 12`, `week 24`
- Stable trajectory status:
  - `on_track`
  - `needs_replan`
  - `degraded`
- Rule-based policy labels:
  - `stabilize_first`
  - `balanced_progress`
  - `long_horizon_heavy`
- Phase 19 alignment:
  - `plan_execution_probability` and approval-dependent realization stay visible in trajectory evaluation

### Phase 21: Portfolio Proof & Product Confidence

**Goal**: Re-run the hardened engine across the full portfolio, refresh proof artifacts, and answer the product-facing question of whether the system is truly working beyond curated stories.
**Depends on**: Phase 20
**Plans**: 3 complete

Plans:
- [x] 21-01: Refresh the canonical portfolio proof with product-facing verdict, confidence, and Phase 17 baseline comparison
- [x] 21-02: Carry refreshed proof through suite packaging and emit one curated engine-owned confidence snapshot
- [x] 21-03: Switch website proof surfaces to the curated proof snapshot and typed proof contract

Planned scope:
- run the full portfolio again after trajectory hardening
- regenerate proof artifacts and website-facing confidence surfaces
- measure whether hardened trajectory behavior improves real cohort credibility
- produce a clearer “is this working?” answer for proof and product surfaces

### Phase 22: Business-First Demo Center Refactor

**Goal**: Turn the Demo Center from an engine-output-heavy walkthrough into a buyer-ready product experience with executive-by-default hierarchy, business-first bilingual language, and trustworthy traceability on the curated snapshot chain.
**Depends on**: Phase 21
**Requirements**: WEB-01, WEB-02
**Gap Closure**: Repairs the partial `WEB-01` traceability gap and closes the buyer-facing bilingual demo flow for `WEB-02`
**Plans**: 4 complete

Plans:
- [x] 22-01: Repair Phase 21 summary traceability for curated proof and demo snapshot sync
- [x] 22-02: Build shared demo-surface primitives for calmer product framing and repeated CTA support
- [x] 22-03: Reframe `DemoCenterPage` into executive, section, and technical-detail hierarchy
- [x] 22-04: Rewrite roadmap cards around phase-window business language and technical-on-demand detail

Delivered scope:
- repaired Phase 21 summary frontmatter and `requirements-completed` evidence so curated demo and proof snapshot traceability now passes the summary-side audit check
- refactored the Demo Center into executive, section, and technical-detail layers with technical content collapsed by default
- rewrote single-customer, portfolio, offer, and learning surfaces in business-first bilingual language, using `first 4 weeks`, `weeks 4-12`, and `weeks 12-24` instead of month labels
- reduced KPI and visual density, added context labels plus disclaimer plus CTA bridges, and shifted the surface toward a restrained product UI

### Phase 23: Proof & Investor Narrative Hardening

**Goal**: Reframe proof and investor surfaces around measurement, governance, category wedge, and monetization logic in executive language without leaking raw internal artifact vocabulary.
**Depends on**: Phase 22
**Requirements**: WEB-03
**Gap Closure**: Closes the proof plus investor story flow
**Plans**: 3 executed

- [x] 23-01: Add a shared bilingual proof and investor vocabulary seam in `site-content.ts`
- [x] 23-02: Refactor the Proof page into an executive memo with compact trust framing
- [x] 23-03: Refactor the Investor page into a disciplined product brief

Delivered scope:
- added one shared buyer-safe vocabulary seam for benchmark labels, trust rail copy, and investor story helpers
- rebuilt the Proof page around the buyer question, buyer-confidence verdict, compact trust rail, and translated baseline comparison
- rebuilt the Investor page around market pain, product wedge, translated proof logic, and `pilot -> platform` commercial framing
- kept deeper proof inputs behind explicit technical reveals while preserving context labels and locale purity

### Phase 24: Analyst Workflow & UAT Validation

**Goal**: Produce milestone-local analyst validation evidence that the product surfaces are understandable, useful, and trustworthy in representative institution tasks.
**Depends on**: Phase 23
**Requirements**: OPS-01
**Gap Closure**: Closes the analyst workflow and UAT flow
**Plans**: 3 executed

- [x] 24-01: Define the analyst UAT matrix and explicit `OPS-01` closure gate
- [x] 24-02: Add the route-level analyst walkthrough packet for Demo Center and Proof
- [x] 24-03: Record milestone-local analyst results and explicit `OPS-01` recommendation

Delivered scope:
- defined five representative analyst tasks across single-customer review, portfolio interpretation, offer assessment, learning-readiness interpretation, and proof-confidence review
- mapped each task to current `/demo` and `/proof` sections, artifact slugs, locale discipline, and technical-reveal expectations
- captured milestone-local walkthrough results showing that the current product surfaces pass on understandable, useful, and trustworthy criteria
- closed `OPS-01` with explicit task scoring, no blocked tasks, and clear separation from remaining pilot-readiness work

### Phase 25: Pilot Readiness & Demo Ops Baseline

**Goal**: Establish the minimum buyer-handoff baseline across lead capture, demo operations, auth or deployment readiness, and institution-specific curated demo flows.
**Depends on**: Phase 24
**Requirements**: OPS-02
**Gap Closure**: Closes the pilot-readiness flow
**Plans**: 3 executed

- [x] 25-01: Harden structured buyer and demo intake across contact, schemas, and inbound persistence
- [x] 25-02: Publish the explicit pilot-readiness baseline and link it from website docs
- [x] 25-03: Package the curated institution-specific demo handoff flow

Delivered scope:
- extended the contact and demo-request flow with structured pilot-intake fields for institution, portfolio, track, timeline, and data readiness
- published one explicit pilot-readiness baseline covering runtime commands, environment needs, persistence rules, auth posture, and operator checklist
- added one curated demo handoff pack that maps intake context into the existing `/demo` and `/proof` surfaces while preserving trust cues and artifact traceability
- closed `OPS-02` with milestone-local buyer handoff, ops, and curated demo packaging evidence

### Gap Closure Sequence

**Status**: Complete, explicit gap-closure phases executed and audit-backed

Notes:
- Phases 19-23 are now the canonical near-term `v1.3` sequence.
- Phase 24 is now complete and closes the analyst-validation blocker.
- Phase 25 is now complete and closes the pilot-readiness blocker.
- All post-audit closure phases are now complete for `v1.3`.
- This milestone passed final milestone audit on 2026-03-20 and is now ready for closeout.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Modeling Foundation Lock | v1.0 | 3/3 | Complete | 2026-03-10 |
| 2. Gate-Aligned Recourse Core | v1.0 | 3/3 | Complete | 2026-03-10 |
| 3. Trajectory and High-Risk Optimization | v1.0 | 3/3 | Complete | 2026-03-10 |
| 4. Explainability and Decision Diagnostics | v1.0 | 2/2 | Complete | 2026-03-10 |
| 5. Evaluation and Benchmark Matrix | v1.0 | 3/3 | Complete | 2026-03-10 |
| 6. Production Hardening and Governance | v1.0 | 3/3 | Complete | 2026-03-10 |
| 7. KPI Gate Stabilization | v1.0 | 3/3 | Complete | 2026-03-10 |
| 8. Fairness Stability Matrix | v1.1 | 3/3 | Complete | 2026-03-14 |
| 9. KPI Contract Unification | v1.1 | 3/3 | Complete | 2026-03-14 |
| 10. Candidate Quality and Trajectory Tuning | v1.1 | 3/3 | Complete | 2026-03-15 |
| 11. Release Evidence and Outcome Feedback | v1.1 | 3/3 | Complete | 2026-03-15 |
| 12. Action Realism & Feasibility Expansion | v1.2 | 3/3 | Complete | 2026-03-15 |
| 13. Behavior-Aware Recourse | v1.2 | 3/3 | Complete | 2026-03-16 |
| 14. Sequential Recourse Planning | v1.2 | 3/3 | Complete | 2026-03-16 |
| 15. Policy Optimization Layer | v1.2 | 3/3 | Complete | 2026-03-16 |
| 16. Outcome Feedback & Learning Loop | v1.2 | 3/3 | Complete | 2026-03-16 |
| 17. Full Portfolio Evaluation & Coverage Audit | v1.3 | 3/3 | Complete | 2026-03-18 |
| 18. Decision Narrative & Product Output Translation | v1.3 | 3/3 | Complete | 2026-03-18 |
| 19. Behavior-Aware Recourse | v1.3 | 3/3 | Complete | 2026-03-19 |
| 20. Trajectory Hardening | v1.3 | 3/3 | Complete | 2026-03-19 |
| 21. Portfolio Proof & Product Confidence | v1.3 | 3/3 | Complete | 2026-03-19 |
| 22. Business-First Demo Center Refactor | v1.3 | 4/4 | Complete | 2026-03-20 |
| 23. Proof & Investor Narrative Hardening | v1.3 | 3/3 | Complete | 2026-03-20 |
| 24. Analyst Workflow & UAT Validation | v1.3 | 3/3 | Complete | 2026-03-20 |
| 25. Pilot Readiness & Demo Ops Baseline | v1.3 | 3/3 | Complete | 2026-03-20 |
