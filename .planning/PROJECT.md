# Credit Coach

## What This Is

Credit Coach is a credit-risk, recourse, and decision-intelligence platform for financial institutions. It now turns model-native recourse outputs into customer-specific, numeric, feasible, execution-aware, institution-aware, and path-aware action plans, then carries those plans through product-safe narratives, typed buyer and analyst surfaces, portfolio proof, calibration review, pilot-facing package delivery, deterministic grouped-path artifacts, and winner-safe consumer surfaces.

## Core Value

Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## Current State

`v2.4 Recourse Capability Expansion & Action Semantics` shipped on `2026-04-05` and passed milestone audit. Credit Coach now supports:
- canonical action semantics with explicit `action_owner` and `action_category`
- deterministic feature → action mapping with explicit non-actionable reasoning and coverage accounting
- safely expanded DICE and institution/hybrid generation lanes under the locked `v2.2` trust baseline
- deterministic multi-path grouping and deterministic selected/path rendering across customer and operator artifacts
- cohort-level evidence for movement potential, path diversity, institution/hybrid rates, and selected-path distribution

The system now proves that it can expand the recourse surface without regressing winner integrity, contender quality, selected-surface consistency, or operator packet coherence.

The remaining open question is movement concentration. The latest cohort evaluation showed rich and trustworthy path generation, but only a small minority of denied customers exhibited meaningful movement while the vast majority remained structurally limited. That shifts the bottleneck from "more actions" to "better customer targeting and honest recourse mode selection."

## Current Milestone: v2.5 Recoverable Customer Targeting & Movement Optimization

**Goal:** Identify which denied customers are realistically recoverable, focus full recourse generation on them, and avoid pretending to help structurally limited customers with low-yield aggressive recommendations.

**Target features:**
- Phase 61 — Recoverability Signal Definition
- Phase 62 — Recoverable Customer Classifier
- Phase 63 — Recourse Gating By Recoverability
- Phase 64 — Movement-Focused Path Ranking
- Phase 65 — Targeted Cohort Evaluation
- Phase 66 — Demo & Narrative Alignment

**Milestone direction:**
- derive deterministic recoverability signals from existing scores and shipped path evidence only
- classify customers into recoverable versus structural-limited segments with explicit reason codes
- route recoverable customers into full multi-path recourse and non-recoverable customers into limited, honest guidance
- concentrate movement where it is realistic instead of maximizing recommendation volume
- prove whether targeted movement concentration improves relative to the global denied baseline without breaking trust

<details>
<summary>Archived Milestone Context: v2.4 Recourse Capability Expansion & Action Semantics</summary>

**Goal:** Expand the recourse solution space with richer action semantics, safer lane diversity, deterministic multi-path organization, and honest cohort-level evidence while preserving the `v2.2` trust baseline.

**Target features:**
- Phase 54 — Action Semantics Taxonomy
- Phase 55 — Feature → Action Mapping
- Phase 56 — DICE Action Space Expansion
- Phase 57 — Heuristic / Institution Action Lane
- Phase 58 — Multi-Path Recourse Generation
- Phase 59 — Action Semantics Rendering
- Phase 60 — Validation & Cohort Evaluation

</details>

<details>
<summary>Archived Milestone Context: v2.3 Threshold & Outcome Optimization</summary>

**Goal:** Improve approval and conditional yield from the shipped `v2.2` trust baseline by tuning bounded thresholds and making existing offer/readiness signals produce real funnel movement.

**Target features:**
- threshold policy evaluation and promotion using only existing signals and existing trust-clean winner outputs
- outcome-producing offer and readiness rules that can move customers from `REJECTED -> CONDITIONAL -> APPROVED`
- funnel movement proof that decomposes gains into threshold-driven versus offer/readiness-driven lift
- one preferred policy profile and one fallback profile for pilot demos and first customer conversations

</details>

<details>
<summary>Archived Milestone Context: v2.1 Decision Ownership & Pilot-Ready Trust</summary>

**Goal:** Transform the system from a decision-intelligence prototype into a deterministic, pilot-ready fintech decision system.

**Target outcomes:**
- repaired artifact contracts carry null-free, parity-safe decision truth
- one deterministic decision owner governs raw, flat, product, and website decision surfaces
- mixed-cohort calibration and operator review artifacts make the decision stack reviewable at scale
- planner provenance, source-mix honesty, and pilot-baseline QA make the pilot story controlled and repeatable

</details>

<details>
<summary>Archived Milestone Context: v2.0 Personalized Action & Decision Intelligence</summary>

**Goal:** Turn model-level recourse outputs into customer-specific, numeric, feasible, and institution-aware action plans with clear product-ready narratives and portfolio-level validation.

**Target outcomes:**
- feature deltas become semantic actions before they become numeric targets
- personalized plans become numeric, feasible, execution-aware, and offer-aware
- product surfaces consume engine-owned personalized narratives without UI-side reinterpretation
- portfolio proof and calibration can say whether the new layer is useful and honest
- pilot integration starts from a controlled, typed export-to-package seam

</details>

<details>
<summary>Archived Milestone Context: v1.3 Portfolio Intelligence & Productization</summary>

**Goal:** Prove the engine across the full portfolio, translate technical outputs into institution-ready narratives, re-harden execution and trajectory truth where product credibility demanded it, and turn the website into a trustworthy buyer, analyst, and pilot asset.

**Target outcomes:**
- full-portfolio proof replaces curated-story-only confidence
- default product surfaces read in business language with technical detail on demand
- proof and investor storytelling translate evidence rather than expose raw internal artifact vocabulary
- analyst workflow is validated through milestone-local UAT
- buyer intake and pilot handoff operate on a credible, repeatable baseline

</details>

## Requirements

### Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1
- ✓ Recommendation quality is now typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-loop-capable - v1.2
- ✓ Portfolio proof, business-first product surfaces, analyst validation, and pilot-baseline demo ops are now shipped and audited - v1.3
- ✓ Personalized action intelligence is now semantic, numeric, feasible, execution-aware, institution-aware, portfolio-validated, and pilot-package-ready - v2.0
- ✓ Deterministic decision ownership, contract trust repair, cohort calibration, operator review packs, planner source-mix honesty, and repeatable pilot refresh now ship together as one audited baseline - v2.1
- ✓ Winner selection is now fail-closed, DICE contenders obey shared validity standards, selected consumer truth is aligned across raw and derived surfaces, and operator packets are coherence-safe on the tracked invariants - v2.2
- ✓ Phase 53 verified 52 to officially close milestone auditable chain for POL-01 and POL-02 gaps - v2.3
- ✓ Bounded threshold profiles were evaluated without breaking the shipped winner and consumer-truth invariants - v2.3
- ✓ Existing offer and readiness signals were evaluated for explicit decision movement - v2.3
- ✓ Standard cohorts measured `REJECTED -> CONDITIONAL -> APPROVED` movement limiters - v2.3
- ✓ One preferred policy profile and one fallback profile refreshed the pilot baseline for demos - v2.3
- ✓ v2.4 established canonical action ownership/category semantics and deterministic feature → action mapping for the current recommendation surface - v2.4
- ✓ v2.4 safely expanded the DICE lane and added institution/hybrid rule-lane generation without regressing the shipped trust baseline - v2.4
- ✓ v2.4 added deterministic multi-path grouping and deterministic action/path rendering across customer and operator artifacts - v2.4
- ✓ v2.4 added cohort-level evidence for movement potential, diversity, and selected-path mix while preserving winner integrity, contender quality, selected-surface consistency, and operator packet coherence - v2.4

### Active

- [ ] Deterministically derive recoverability signals (`approval_gap`, `normalized_gap`, `risk_band`, `recoverability_score`, `recoverability_bucket`) from existing shipped scores and signals only
- [ ] Deterministically classify customers into recoverable versus non-recoverable with explicit reason codes and structural-limit logic
- [ ] Gate recourse mode so recoverable customers receive full multi-path generation while non-recoverable customers receive limited, honest guidance
- [ ] Re-rank paths toward threshold movement, feasibility, and simplicity without regressing winner integrity or surface trust
- [ ] Prove whether recoverable-only targeting materially improves movement concentration versus the global denied baseline
- [ ] Align narratives and demo surfaces so recoverable customers receive actionable advice and structurally limited customers receive informational honesty

### Out of Scope

- Redesigns of Phases `40`, `40.5`, `41`, `42`, `42.5`, `43`, `45`, `46`, `47`, or `48` rather than consuming their shipped semantics as fixed baselines
- Further action-taxonomy expansion, planner-semantic redesign, or broadening the recommendation space again before movement proof is gathered
- Model retraining, threshold policy redesign, or any new black-box recoverability predictor
- New action types or external data integrations during this milestone
- Full borrower-facing self-serve or mobile experiences until a future milestone explicitly opens them
- Legal or compliance opinion automation or live institution integration expansion beyond the shipped pilot baseline
- Claiming approval or conditional uplift from recoverability targeting without explicit cohort evidence

## Context

- The repository contains a substantial Python engine under `credit-coach/` and a full-stack product surface under `credit-coach-website/`.
- `v1.2 Recommendation Quality Hardening` remains the shipped baseline for typed actions, behavior-aware ranking, trajectories, offers, and learning evidence.
- `v1.3 Portfolio Intelligence & Productization` remains the shipped baseline for full-portfolio proof, buyer-safe product surfaces, analyst validation, and pilot-baseline operations.
- `v2.0 Personalized Action & Decision Intelligence` is now shipped and audited, adding personalized numeric planning contracts, execution and offer realism, richer narratives, stricter product-surface consumption, portfolio numeric proof, calibration review, and pilot packaging.
- `v2.1 Decision Ownership & Pilot-Ready Trust` is now shipped and audited, adding repaired artifact trust, deterministic decision ownership, collection-root funnel and calibration evidence, operator review packs, planner-quality honesty, and repeatable pilot refresh infrastructure.
- Phase `42.5 Recommendation Validity Layer` remains the numeric-recommendation baseline, and `v2.2` proved that its validity truth can now govern selection and consumer surfaces cleanly.
- Phase `45` removed invalid winner leakage by making chooser fallback fail closed.
- Phase `46` proved DICE contender cleanliness separately from general winner integrity.
- Phase `47` aligned selected overlays across raw, flat, operator, and explanation outputs.
- Phase `48` proved operator packet coherence on the tracked blocker/action/readiness invariants across three large-sample reruns.
- `v2.3 Threshold & Outcome Optimization` is now shipped and audited. It operated as a truth-finding milestone that proved bounded thresholds and outcome rules cannot yield safe uplift on standard cohorts, firmly establishing `structural_cohort_limited` as the bottleneck.
- `v2.4 Recourse Capability Expansion & Action Semantics` is now shipped and audited. It safely expanded the recourse surface but did not yet prove business lift.
- The latest denied-cohort evaluation showed roughly 90% multi-path coverage but only about 10% meaningful movement, with structural limitation still dominating the population.
- The current milestone should build forward from the shipped trust and action/path baseline by targeting recoverable customers rather than expanding semantics again.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; product surfaces cannot soften them
- **Artifact Truth**: The Python engine remains the source of truth, and website data should stay curated, typed, and synchronized from artifacts rather than recomputed in the frontend stack
- **Business-First Surface**: Default UI must speak in analyst and enterprise-buyer language; raw technical traces belong in controlled secondary views
- **Proof Before Hype**: Demo, proof, and pilot claims should stay anchored to portfolio evidence and explicit trust cues
- **Brownfield**: Existing CLI runners, artifacts, website stack, and review surfaces should be evolved rather than replaced
- **Milestone Continuity**: Phase numbering continues across milestones rather than resetting
- **Outcome Proof Before Expansion**: The next milestone should measure movement on the shipped `v2.4` surface before adding more action semantics or planner complexity
- **Trust Layers Frozen**: Decision ownership, calibration math, planner-quality measurement, recommendation validity semantics, winner hard-stop, selected-surface projection, operator packet semantics, deterministic pathing, and deterministic render semantics remain inherited baselines

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD `.planning` as the single planning home for this repo | Legacy docs were scattered across the repo and made continuity difficult | ✓ Good |
| Treat the repository as a brownfield GSD project | Existing code, reports, and artifacts prove the project is already in active development | ✓ Good |
| Preserve `v1.2` as the shipped recommendation-quality baseline | Typed actions, execution-aware ranking, trajectories, offers, and learning evidence are already in place and should be inherited | ✓ Good |
| Treat `credit-coach-website/` as milestone scope rather than side documentation | Buyer demos, proof review, and pilot readiness depend on the website surface being real product infrastructure | ✓ Good |
| Keep the Python engine as source of truth and sync curated website snapshots from artifacts | This avoids duplicating model logic in the website stack and keeps product surfaces auditable | ✓ Good |
| Open `v2.0 Personalized Action & Decision Intelligence` as a 10-phase contract stack | The next leverage point required explicit separation of semantics, targets, constraints, execution, offers, narratives, surfaces, proof, calibration, and pilot seams | ✓ Good |
| Keep portfolio proof and calibration more honest than impressive | Execution-aware payoff, realism checks, and narrowness signals are more trustworthy than nominal uplift alone | ✓ Good |
| Keep pilot integration export-first and controlled | The repo should not pretend to have live institution connectivity before the contract seam is genuinely ready | ✓ Good |
| Separate business-visible decision truth from internal review diagnostics | The pilot story needed deterministic external decisions without leaking internal exception states | ✓ Good |
| Treat calibration, operator review, planner quality, and pilot refresh as additive consumers of one decision owner | This preserved deterministic ownership while still making the system measurable, reviewable, and packageable | ✓ Good |
| Open `v2.2 Winner Integrity & Consumer Consistency` before any threshold widening | Large-sample reruns showed that invalid selected winners and contradictory consumer surfaces were the real bottleneck, not approval aggressiveness | ✓ Good |
| Open `v2.3 Threshold & Outcome Optimization` after `v2.2` shipped cleanly | Pilot demos now need measurable funnel movement and outcome lift more than more trust repair or action-space expansion | ✓ Good |
| Open new milestone around action-space or movement-lever expansion | Bounded optimization tests proved the current parameter space is exhausted without yielding lift | ✓ Good |
| Treat `v2.4` as a capability-expansion milestone rather than a business-lift claim | Audit evidence separated richer path space and evidence packaging from proven cohort movement | ✓ Good |
| Open `v2.5 Recoverable Customer Targeting & Movement Optimization` as a targeting milestone rather than another action-expansion milestone | `v2.4` proved the engine is rich and trustworthy, but the dominant bottleneck is still customer distance to threshold | ✓ Good |
| Keep recoverability deterministic and explainable | The system already has trusted scores, path evidence, and structural signals; a black-box recoverability layer would weaken operator trust without adding governed leverage | ✓ Good |

<details>
<summary>Archived Milestone Context: v2.2 Winner Integrity & Consumer Consistency</summary>

**Goal:** Fix selected-winner integrity and consumer-surface consistency before any threshold widening or approval-rate optimization.

**Target outcomes:**
- invalid recommendations cannot survive winner selection
- `dice` contenders obey the same validity and contender-quality gates as internal plans
- selected surfaces stay coherent across raw, flat, operator, and explanation artifacts
- operator packets remain internally coherent without reopening decision ownership semantics

</details>

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-05 after starting milestone v2.5 Recoverable Customer Targeting & Movement Optimization*
