# Credit Coach

## What This Is

Credit Coach is a credit-risk, recourse, and decision-intelligence platform for financial institutions. It moves beyond binary approve or deny decisions by combining PD prediction, explanation, behavior-aware and phased recommendation planning, institution-side offer logic, portfolio-proof artifacts, and buyer-safe product surfaces in one artifact-driven system.

The project now has both an audited recommendation-quality core and a shipped productization layer across demo, proof, investor, analyst, and pilot-handoff workflows. The next milestone should extend this baseline rather than casually reopen it.

## Core Value

Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can actually understand and trust.

## Current State

`v1.3 Portfolio Intelligence & Productization` shipped on `2026-03-20` and passed milestone audit. Credit Coach now supports:
- full-portfolio evaluation, segment proof, and demo representativeness diagnostics
- engine-owned narrative translation with business-first defaults and technical reveal
- conservative behavior-aware ranking and deterministic `4w / 12w / 24w` trajectory contracts
- curated Demo Center, Proof, and Investor surfaces synchronized to engine artifacts
- analyst UAT, structured buyer intake, and repeatable pilot demo handoff guidance

The active milestone is now `v2.0 Personalized Action & Decision Intelligence`. This milestone should extend the shipped baseline by turning model-level recourse outputs into customer-specific, numeric, feasible, and institution-aware action plans that are easier to trust, explain, and validate at portfolio scale.

## Next Milestone Goals

## Current Milestone: v2.0 Personalized Action & Decision Intelligence

**Goal:** Turn model-level recourse outputs into customer-specific, numeric, feasible, and institution-aware action plans with clear product-ready narratives and portfolio-level validation.

**Target features:**
- convert selected recourse outputs into numeric action contracts with explicit deltas, units, timing, and completion criteria
- connect each plan to customer-specific decision readiness, review posture, and institution-side dependencies
- keep product narratives business-first while preserving numeric and technical traceability behind the same engine-owned contract
- validate the personalized planning layer across the portfolio and compare it against the shipped `v1.3` baseline

<details>
<summary>Archived Milestone Context: v1.3 Portfolio Intelligence & Productization</summary>

**Goal:** Prove the engine across the full portfolio, translate technical outputs into institution-ready narratives, re-harden execution and trajectory truth where product credibility demands it, and turn the website into a trustworthy buyer, analyst, and pilot asset.

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

### Active

- [ ] Personalized action plans become customer-specific, numeric, feasible, and ordered
- [ ] Decision intelligence explains readiness, review posture, and institution-side dependencies per customer plan
- [ ] Product surfaces consume engine-owned personalized narratives without inventing plan meaning in the UI
- [ ] Portfolio proof validates whether personalization improves action specificity and decision usefulness versus the `v1.3` baseline

### Out of Scope

- Full borrower-facing self-serve or mobile experiences until a future milestone explicitly opens them
- Fully autonomous online policy promotion before evidence-first controls are expanded
- Legal or compliance opinion automation
- Unscoped greenfield rewrites of the engine or website stacks

## Context

- The repository contains a substantial brownfield implementation under `credit-coach/` plus a full-stack website surface under `credit-coach-website/`.
- The imported `v1.0` baseline established model, recourse, fairness, telemetry, and audit foundations.
- `v1.1 Fairness Stability & KPI Hardening` remains the audited governance baseline.
- `v1.2 Recommendation Quality Hardening` remains the shipped recommendation-quality baseline for typed actions, execution-aware ranking, trajectories, offers, and learning evidence.
- `v1.3 Portfolio Intelligence & Productization` is now shipped and audited, adding full-portfolio proof, narrative translation, buyer-safe product surfaces, analyst validation, and pilot-baseline operations.
- `v2.0 Personalized Action & Decision Intelligence` now reopens the engine at the plan-contract layer rather than at the raw model or portfolio-proof baseline.
- This milestone is intentionally focused on making outputs more customer-specific and decision-useful, not on rebuilding the core scoring stack.
- Separate research was skipped for milestone initialization because the user supplied a focused milestone goal and the repo already carries rich brownfield evidence from `v1.2` and `v1.3`.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; product surfaces cannot soften them
- **Artifact Truth**: The Python engine remains the source of truth, and website data should stay curated, typed, and synchronized from artifacts rather than recomputed in the frontend stack
- **Business-First Surface**: Default UI must speak in analyst and enterprise-buyer language; raw technical traces belong in controlled secondary views
- **Proof Before Hype**: Demo, proof, and investor claims should stay anchored to full-portfolio evidence and explicit trust cues
- **Brownfield**: Existing CLI runners, artifacts, website stack, and review surfaces should be evolved rather than replaced
- **Milestone Continuity**: The next roadmap should continue from Phase 26 rather than resetting numbering

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD `.planning` as the single planning home for this repo | Legacy docs were scattered across the repo and made continuity difficult | ✓ Good |
| Treat the repository as a brownfield GSD project | Existing code, reports, and artifacts prove the project is already in active development | ✓ Good |
| Preserve `v1.2` as the shipped recommendation-quality baseline | Typed actions, execution-aware ranking, trajectories, offers, and learning evidence are already in place and should be inherited | ✓ Good |
| Treat `credit-coach-website/` as milestone scope rather than side documentation | Buyer demos, proof review, and pilot readiness depend on the website surface being real product infrastructure | ✓ Good |
| Keep the Python engine as source of truth and sync curated website snapshots from artifacts | This avoids duplicating model logic in the website stack and keeps product surfaces auditable | ✓ Good |
| Reopen behavior-aware and trajectory work only as targeted hardening passes | Portfolio proof and product translation exposed credibility gaps that needed focused repair, not a ground-up redesign | ✓ Good |
| Require business-first defaults with explicit technical reveal | The target users are institutional decision-makers, but technical trust still has to remain accessible | ✓ Good |
| Require milestone-local analyst validation before claiming pilot readiness | Trustworthiness needed explicit UAT evidence instead of implied future review | ✓ Good |
| Archive `v1.3` before opening more work | The product now sits at a milestone boundary and should move forward under a fresh requirement contract | ✓ Good |
| Open `v2.0 Personalized Action & Decision Intelligence` as the next milestone | The next leverage point is not more generic proof or productization, but sharper customer-specific plan contracts and decision-facing intelligence | — Pending |

---
*Last updated: 2026-03-20 after opening milestone v2.0 Personalized Action & Decision Intelligence*
