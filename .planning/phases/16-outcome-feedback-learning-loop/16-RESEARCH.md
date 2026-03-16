# Phase 16: Outcome Feedback & Learning Loop - Research

**Researched:** 2026-03-16
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can log full recommendation context, ingest delayed real-world outcomes, and compute off-policy learning signals without breaking the governance and evidence contracts built in Phases 8-15?

## Planning Basis

Phase 16 does **not** yet have a `16-CONTEXT.md`. For this planning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/v1.2-RECOMMENDATION-QUALITY-HARDENING.md`
- `.planning/phases/11-release-evidence-and-outcome-feedback/11-CONTEXT.md`
- `.planning/phases/15-policy-optimization-layer/15-CONTEXT.md`
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
- `credit-coach/src/credit_coach/storage/repository.py`
- `credit-coach/src/credit_coach/storage/models.py`
- `credit-coach/src/credit_coach/data/schema.py`
- local legacy research notes under `.planning/research/legacy/`

This is enough because the milestone goal and the already-shipped brownfield seams are clear: Phase 16 is about completing the learning loop on top of the existing action, behavior, trajectory, offer, telemetry, and release-evidence contracts.

## Executive Summary

The repository already has the first half of an outcome-feedback system:

- `DecisionOutcomeRecord` and `DecisionOutcomeORM` exist
- repository code can upsert delayed 30/60/90-day default and margin outcomes
- `run_outcome_feedback.py` can ingest CSV rows and emit machine-readable proxy summaries
- Phase 11 already wired outcome-feedback summaries into release review as supporting evidence
- Phase 15 enriched `policy_arm` semantics with offer-policy profile metadata

But the current seam is still descriptive, not learning-ready.

Today the repo is missing four capabilities that Phase 16 must close:

1. **Full decision logging context**
   - recommendation, selected plan, offer terms, execution likelihood, candidate-set identity, and propensity-style policy metadata are not persisted with decision outcomes
2. **Richer outcome ingestion**
   - the system can ingest defaults and realized margin, but not action completion, offer acceptance, payment behavior, or recovery outcomes as one normalized learning dataset
3. **Coverage/completeness semantics**
   - there is no canonical summary for whether the logged decisions have enough complete outcome context to support learning
4. **Off-policy evaluation**
   - IPS / Doubly Robust style estimation does not exist, so treatment-vs-control outcome summaries remain descriptive rather than reusable for safer policy evaluation

The correct sequencing is:

- first extend the logging contract
- then normalize and score outcome ingestion coverage
- then layer off-policy evaluation on top of the logged propensities and observed rewards

That sequence fits the repo’s brownfield constraints and the lack of a migration framework.

## Brownfield Constraints That Matter

### 1. Persistence evolves without a formal migration framework

`.planning/codebase/CONCERNS.md` already flags schema and persistence drift as a risk. Because the repo currently relies on ORM models plus `create_all`, Phase 16 should prefer **additive companion tables or additive JSON payload fields** over destructive persistence changes.

That means the phase should avoid risky “rewrite the whole outcome table” moves. Instead it should:

- extend the existing decision outcome seam carefully
- prefer additive logging payloads and companion records
- keep repository tests and audit tests in sync

### 2. Outcome feedback already exists and should be extended, not replaced

`run_outcome_feedback.py` plus `repository.py` already own:

- policy-arm summaries
- proxy deltas
- machine-readable JSON output

Phase 16 should keep that CLI as the main orchestration seam and broaden what it ingests and emits.

### 3. Policy-arm semantics are now richer after Phase 15

Because `policy_arm` can now represent offer-policy profiles, Phase 16 must preserve:

- treatment-vs-control reporting language
- explicit arm profiles in artifacts
- enough logged policy context to support offline policy evaluation

### 4. Review and release evidence remain evidence-first

Outcome-learning artifacts should continue to be:

- machine-readable first
- explanation-first in review
- supporting evidence unless and until later milestones promote them

Phase 16 should therefore add learning artifacts without redefining the primary release contract.

## Existing Assets We Can Reuse

### Decision outcome storage already exists

- `credit-coach/src/credit_coach/data/schema.py`
  - `DecisionOutcomeRecord` already exists
- `credit-coach/src/credit_coach/storage/models.py`
  - `DecisionOutcomeORM` already exists
- `credit-coach/src/credit_coach/storage/repository.py`
  - `save_decision_outcome`, `summarize_decision_outcomes`, and `compute_policy_outcome_deltas` already exist

This gives Phase 16 a stable key:

- `decision_id`

and a stable storage seam to extend.

### Audit logging is already built in

Repository writes already append audit-chain events. That makes repository the right seam for richer decision logging because the logging path will automatically stay auditable if implemented there rather than via ad hoc file writes.

### Outcome CLI already owns the feedback artifact path

`run_outcome_feedback.py` already writes:

- `outcome_policy_summary.csv`
- `outcome_policy_deltas.json`
- `outcome_feedback_summary.json`

Phase 16 should extend this family instead of inventing a separate CLI.

### Suite already mirrors optional outcome artifacts

`run_phase_experiment_suite.py` already knows how to mirror optional outcome-feedback artifacts into seeded review bundles. That makes it a natural consumer of future Phase 16 learning artifacts such as completeness summaries or off-policy evaluation outputs.

## Gaps Phase 16 Must Close

### 1. Decision logs are too thin for learning

Current logged fields are mostly:

- decision identity
- policy arm
- approval flag
- delayed default labels
- realized margin

Missing fields include:

- selected plan id or recommendation id
- action plan / offer branch summary
- reason codes
- candidate-set identity
- logging propensity / selection probability
- execution and offer-acceptance probabilities
- recommendation-time context sufficient for OPE and post-hoc attribution

### 2. There is no canonical outcome-ingestion completeness contract

The repo can summarize outcomes, but it cannot yet answer:

- how many logged decisions have usable delayed outcomes
- how many have action completion data
- how many have offer acceptance data
- how many are complete enough for learning versus only descriptive reporting

Phase 16 needs a machine-readable completeness summary for this.

### 3. There is no normalized real-world learning dataset

The current outcome path effectively stops at descriptive arm summaries. There is no stable dataset or companion artifact that joins:

- logged decision context
- delayed outcomes
- action completion
- offer acceptance
- recovery results

Phase 16 needs that join if it is going to support learning loops.

### 4. Off-policy evaluation is entirely absent

There is no module today for:

- IPS
- Doubly Robust
- coverage / positivity diagnostics
- confidence signaling when propensities or reward coverage are insufficient

Phase 16 must add that capability, but keep it evidence-first and non-destructive.

## Recommended Architecture

### A. Extend the decision logging contract first

The safest path is to add a richer decision-log contract keyed by `decision_id` that carries:

- `policy_arm`
- `policy_arm_profile`
- `candidate_set_id`
- `propensity`
- `reason_codes`
- selected plan / offer summary
- execution / acceptance / combined realization probabilities
- timestamps and review metadata

Because of migration risk, this should be done additively.

### B. Introduce a normalized outcome-ingestion summary

`run_outcome_feedback.py` should evolve from “ingest CSV and compute deltas” into:

- ingest richer outcome payloads
- compute coverage/completeness
- materialize a normalized learning-ready dataset
- still emit descriptive proxy summaries for backward compatibility

### C. Add a dedicated off-policy evaluation module

The repo needs a focused module, likely under `credit-coach/src/credit_coach/evaluation/`, that can compute:

- IPS estimates
- Doubly Robust estimates
- coverage / positivity diagnostics
- per-policy-arm comparative summaries

This module should be consumed by `run_outcome_feedback.py` rather than embedded inside repository aggregation logic.

### D. Keep learning evidence non-blocking but reviewable

Phase 16 should likely introduce canonical machine-readable artifacts such as:

- `decision_logging_summary.json`
- `outcome_ingestion_summary.json`
- `off_policy_evaluation.json`

These should integrate into suite/review as supporting artifacts, not as immediate release overrides.

## Recommended Execution Order

### Plan 16-01: Decision logging expansion

Do this first because:

- richer outcome ingestion and OPE both depend on the logging contract
- it is the least ambiguous brownfield seam
- it can reuse audit-chain infrastructure immediately

### Plan 16-02: Outcome ingestion pipeline

Do this second because:

- learning coverage and normalized datasets depend on richer logging
- the CLI and repository seams already exist

### Plan 16-03: Off-policy evaluation

Do this last because:

- IPS / DR require logged policy metadata plus usable reward coverage
- it should build on the artifacts created in the first two plans

## Planning Implications

- Phase 16 should be planned as an **evidence-first learning loop**, not as autonomous online learning
- additive persistence changes are preferable to destructive schema churn
- review and seeded suite integration should continue to treat learning outputs as supporting evidence
- tests should expand in parallel with schema and repository changes because the audit and persistence seam is fragile

---
*Phase: 16-outcome-feedback-learning-loop*
*Research completed: 2026-03-16*
