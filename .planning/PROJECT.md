# Credit Coach

## What This Is

Credit Coach is a credit-risk and recourse platform for financial institutions. It moves beyond binary approve or deny decisions by combining PD prediction, explanation, phased recourse planning, institution-side offer logic, and evidence-driven governance in one decision surface.

The platform now has a shipped `v1.2` recommendation-quality core and a partially productized website surface. The next milestone should not rebuild typed actions, offers, or learning-loop basics from scratch. Instead, it should validate the engine across the full portfolio, translate technical outputs into institution-ready product language, and explicitly re-harden behavior-aware ranking and phased trajectories wherever portfolio proof or product-surface credibility exposes gaps.

## Core Value

Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can actually understand and trust.

## Current State

`v1.2 Recommendation Quality Hardening` shipped on `2026-03-16` and passed milestone audit. Credit Coach now supports:
- typed behavioral, structural, and institutional actions
- behavior-aware execution probability and expected-utility ranking
- phased trajectories with checkpoint and replan metadata
- institution-side offer optimization under inherited governance gates
- compact learning-ledger logging, normalized delayed outcomes, and confidence-aware offline policy evaluation

The repo also contains an early `credit-coach-website/` full-stack product surface, but it is still only partially tied back to full-portfolio proof, curated demo-data contracts, analyst workflow validation, and pilot readiness.

## Next Milestone Goals

The next active milestone is `v1.3 Portfolio Intelligence & Productization`.

Its goals are to:
- prove how the engine behaves across the full customer portfolio, not just in curated demos
- translate recommendation outputs into analyst-friendly and buyer-friendly decision narratives
- re-harden execution and trajectory truth only where product and proof credibility show clear gaps
- stabilize artifact-to-website demo and proof sync so product surfaces stay consistent with engine truth
- turn the website into a business-first enterprise product surface for buyers, proof review, and investor storytelling
- validate analyst workflows and reach a credible pilot-readiness baseline

## Requirements

### Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1
- ✓ Recommendation quality is now typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-loop-capable - v1.2

### Active

- [ ] **PORT-01**: Full-portfolio evaluation reports coverage, feasibility, execution-weighted impact, offer reach, checkpoint health, and governance-safe rates across the whole evaluation population
- [ ] **PORT-02**: Recommendation outputs can be translated into a controlled narrative layer with executive summaries, business-first action stories, and optional technical reveal without losing traceability
- [ ] **PORT-03**: Behavior-aware recourse is re-validated as an explicit execution-aware ranking layer with measurable action or plan execution probabilities, expected utility ordering, and evidence outputs
- [ ] **PORT-04**: Sequential trajectory planning is re-validated as a checkpoint-governed roadmap layer with stable phases, readable statuses, and controlled replan semantics
- [ ] **WEB-01**: The website can consume curated demo and proof snapshots from engine artifacts through a stable, typed sync contract
- [ ] **WEB-02**: Demo Center and buyer-facing product surfaces present single-customer, portfolio, offer, and learning views in business-first bilingual language
- [ ] **WEB-03**: Proof and investor surfaces clearly explain measurement, release controls, learning evidence, category story, and monetization logic
- [ ] **OPS-01**: Analyst workflow and UAT validate that recommendations are understandable, useful, and trustworthy in representative institution tasks
- [ ] **OPS-02**: Pilot-readiness baseline covers lead capture, deployment, auth or ops basics, and institution-specific curated demo flows

### Out of Scope

- Full borrower-facing product surfaces or consumer self-serve apps
- Fully online autonomous learning or policy auto-promotion
- Legal or compliance opinion automation
- Mandatory deep external institution integrations in every workflow before pilot proof is stable

## Context

- The repository already contains a substantial brownfield implementation under `credit-coach/`.
- The imported `v1.0` baseline established model, recourse, fairness, telemetry, and audit foundations.
- `v1.1 Fairness Stability & KPI Hardening` remains the audited governance baseline.
- `v1.2 Recommendation Quality Hardening` shipped typed actions, execution-aware ranking, phased trajectories, offer optimization, and learning-loop evidence.
- `credit-coach-website/` now exists as a brownfield website codebase and should be treated as a first-class product surface in the next milestone, not as a throwaway demo.
- The next milestone should continue from Phase 17 and focus on proof, translation, productization, and only targeted hardening of inherited `v1.2` behavior-aware and trajectory contracts where portfolio or product-readiness evidence justifies reopening them.
- Phase 20 should now stay intentionally small: deterministic trajectory contract hardening first, then refreshed proof in the next phase.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; product surfaces cannot soften them
- **Artifact Truth**: The Python engine remains the source of truth; website data should be curated, typed, and synchronized from artifacts rather than recomputed in the frontend stack
- **Business-First Surface**: Default UI must speak in analyst and enterprise-buyer language; raw technical traces belong in controlled secondary views
- **Portfolio Proof**: Demo stories must eventually be justified by full-population coverage and segment evidence, not only curated single-case examples
- **Brownfield**: Existing CLI runners, artifacts, website stack, and review surfaces should be evolved rather than replaced
- **Milestone Continuity**: Phase numbering continues from the completed `v1.2` range, so the next roadmap starts at Phase 17

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Preserve `v1.2` as the completed recommendation-quality baseline | Typed actions, behavior-aware ranking, trajectories, offers, and learning evidence are already shipped and should be inherited, not reopened | ✓ Good |
| Open `v1.3 Portfolio Intelligence & Productization` as the next milestone | The main gap is no longer core recommendation mechanics; it is full-cohort proof, narrative translation, and product surface credibility | ✓ Good |
| Re-add behavior-aware and trajectory phases inside `v1.3` as explicit hardening passes | Full-portfolio proof and product translation work can expose credibility gaps even in already shipped mechanics, so these layers may need a focused revisit without discarding the `v1.2` baseline | ✓ Good |
| Keep Phase 20 as a mini hardening phase and push the next proof answer to Phase 21 | Trajectory correctness and portfolio proof answer different questions, so separating them reduces scope drift and keeps validation honest | ✓ Good |
| Make full-portfolio evaluation the first new phase | Demo and proof claims should be grounded in cohort-wide evidence before more product storytelling is layered on top | ✓ Good |
| Treat `credit-coach-website/` as milestone scope | The website is now central to buyer demos, investor communication, and pilot readiness | ✓ Good |
| Keep the Python engine as source-of-truth and sync curated website snapshots from artifacts | This avoids duplicating model logic in the website stack and keeps product surfaces auditable | ✓ Good |
| Continue phase numbering from 17 | Milestone continuity matters more than restarting numbering around website work | ✓ Good |

---
*Last updated: 2026-03-17 after opening milestone v1.3 Portfolio Intelligence & Productization*
