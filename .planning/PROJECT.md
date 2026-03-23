# Credit Coach

## What This Is

Credit Coach is a credit-risk, recourse, and decision-intelligence platform for financial institutions. It now turns model-native recourse outputs into customer-specific, numeric, feasible, execution-aware, and institution-aware action plans, then carries those plans through product-safe narratives, typed buyer and analyst surfaces, portfolio proof, calibration review, and pilot-facing package delivery.

## Core Value

Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## Current State

`v2.1 Decision Ownership & Pilot-Ready Trust` shipped on `2026-03-23` and passed milestone audit. Credit Coach now supports:
- null-free, parity-safe raw and flat artifact contracts that carry decision-critical truth safely
- one deterministic decision owner with external `APPROVED | CONDITIONAL | REJECTED` outcomes and internal diagnostic review state
- cohort-aware funnel, readiness, and shadow calibration outputs under the same collection run root
- per-customer operator packets and collection-level review briefings derived from the owned decision payload
- explicit planner provenance, empty-contender removal, source-mix honesty, diversity guardrails, and offer-maturity signals
- repeatable pilot baseline refresh, dedicated artifact QA, thin institution overlays, and institution-facing explanation packs

No active milestone is currently defined. The next planning step is to open a fresh milestone with `$gsd-new-milestone`.

## Next Milestone Goals

- move from pilot package handoff toward deeper institution-specific integration contracts without reopening deterministic decision ownership
- expand compliance-adjacent explanation and governance workflows while keeping internal-only decision truth bounded
- automate proof refresh, release review, and milestone health workflows that are still operator-triggered today
- clean up milestone tooling and validation metadata debt so archive and audit flows no longer need manual fallback

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

### Active

- [ ] Institution-specific inbound and outbound integration contracts beyond export-first pilot packaging
- [ ] Compliance-adjacent explanation and governance workflows beyond bounded pilot support artifacts
- [ ] Recurring proof refresh, release review, and milestone health automation
- [ ] Milestone tooling and planning metadata cleanup so archive and audit workflows can run without manual fallback

### Out of Scope

- Full borrower-facing self-serve or mobile experiences until a future milestone explicitly opens them
- Fully autonomous online policy promotion before evidence-first controls are expanded
- Legal or compliance opinion automation
- Unscoped greenfield rewrites of the engine or website stacks

## Context

- The repository contains a substantial Python engine under `credit-coach/` and a full-stack product surface under `credit-coach-website/`.
- `v1.2 Recommendation Quality Hardening` remains the shipped baseline for typed actions, behavior-aware ranking, trajectories, offers, and learning evidence.
- `v1.3 Portfolio Intelligence & Productization` remains the shipped baseline for full-portfolio proof, buyer-safe product surfaces, analyst validation, and pilot-baseline operations.
- `v2.0 Personalized Action & Decision Intelligence` is now shipped and audited, adding personalized numeric planning contracts, execution and offer realism, richer narratives, stricter product-surface consumption, portfolio numeric proof, calibration review, and pilot packaging.
- `v2.1 Decision Ownership & Pilot-Ready Trust` is now shipped and audited, adding repaired artifact trust, deterministic decision ownership, collection-root funnel and calibration evidence, operator review packs, planner-quality honesty, and repeatable pilot refresh infrastructure.
- The next milestone should build forward from this decision-and-pilot baseline rather than casually reopening finished contract layers.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; product surfaces cannot soften them
- **Artifact Truth**: The Python engine remains the source of truth, and website data should stay curated, typed, and synchronized from artifacts rather than recomputed in the frontend stack
- **Business-First Surface**: Default UI must speak in analyst and enterprise-buyer language; raw technical traces belong in controlled secondary views
- **Proof Before Hype**: Demo, proof, and pilot claims should stay anchored to portfolio evidence and explicit trust cues
- **Brownfield**: Existing CLI runners, artifacts, website stack, and review surfaces should be evolved rather than replaced
- **Milestone Continuity**: Phase numbering continues across milestones rather than resetting

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

---
*Last updated: 2026-03-23 after completing milestone v2.1*
