# Phase 50: Offer & Readiness Outcome Rules - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn existing offer-state and readiness-state signals from mostly descriptive review context into bounded, auditable, analysis-only outcome rules that can create real funnel movement on top of the shipped `v2.2` trust baseline. This phase does **not** reopen Phase `49` threshold-only tuning, does not expand feature space or action semantics, and does not redesign any trust layer from Phases `40` through `48`.

Phase 50 owns:

- evaluating whether existing offer/readiness signals can safely move customers through `REJECTED -> CONDITIONAL -> APPROVED`
- defining a tiny, deterministic catalog of outcome-rule profiles
- making outcome-rule effects replayable in artifacts and comparison tables
- making candidate operator/explanation surfaces able to say when an offer/readiness rule changed the evaluated decision outcome

Guardrails:

- `decision_policy_version` and live selected truth remain the shipped baseline
- outcome-rule candidates stay analysis-only in this phase
- trust invariants from `v2.2` stay fixed and must remain clean
- direct feature-space growth and recourse/action expansion are deferred

</domain>

<decisions>
## Implementation Decisions

### Current offer/readiness signals: descriptive vs decision-bearing

#### Already decision-bearing today

- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already uses:
  - `expected_readiness`
  - `approval_ready_4w`
  - `offer_maturity`
  - `combined_plan_realization_probability` indirectly through `realization_anchor`
- These signals currently act mostly as **eligibility and blocking inputs**:
  - readiness and `approval_ready_4w` participate in the approve gate and time-gated conditional classification
  - `offer_maturity` can block approval and trigger offer-gated conditional classification

#### Still descriptive-only or not yet direct outcome levers

- `approval_ready_12w`
- `approval_ready_24w`
- `rankable_offer_count`
- `approval_pending_action_count`
- `offer_acceptance_probability`
- `approval_dependent_plan_probability`
- `offer_needed_flag`
- operator “likely to upgrade soon” queues
- operator offer/readiness hotspots and segment breakdowns

These already exist in artifacts and planning logic, but they do **not** yet create their own explicit, auditable decision movement rules.

### Candidate bounded outcome-rule profiles

Phase 50 should evaluate a tiny, deterministic rule ladder on top of the shipped baseline. The candidate set should stay small and replayable:

- `analysis_offer_support_v2_3b`
- `analysis_readiness_support_v2_3b`
- `analysis_offer_readiness_combo_v2_3b`

#### `analysis_offer_support_v2_3b`

- Intended movement:
  - `REJECTED -> CONDITIONAL`
- Eligibility:
  - baseline decision is `REJECTED`
  - `selection_outcome = selected_valid_winner`
  - valid selected plan exists and trust gates pass (`raw_contract_pass`, `parity_pass`, `plan_contract_pass`)
  - `recommendation_validity_status != invalid`
  - `offer_maturity in {provisional, active_rankable}`
  - `rankable_offer_count >= 1`
  - `approval_dependent_plan_probability >= 0.50`
  - `expected_pd_improvement >= 0.01`
  - `decision_confidence >= 0.40`
- Projected effect:
  - candidate decision becomes `CONDITIONAL`
  - candidate subtype/source becomes `OFFER_GATED`

#### `analysis_readiness_support_v2_3b`

- Intended movement:
  - `REJECTED -> CONDITIONAL`
  - bounded `CONDITIONAL -> APPROVED` only when the readiness state is already near-term and all shipped approval-quality conditions are present
- Eligibility for `REJECTED -> CONDITIONAL`:
  - baseline decision is `REJECTED`
  - trust gates pass and selected winner is valid
  - `expected_readiness in {week_4, week_12}` or `approval_ready_12w = 1`
  - `realization_anchor >= 0.20`
  - `expected_pd_improvement >= 0.01`
  - `decision_confidence >= 0.40`
- Eligibility for `CONDITIONAL -> APPROVED`:
  - baseline decision is `CONDITIONAL`
  - `conditional_type = TIME_GATED`
  - `expected_readiness = week_4`
  - `approval_ready_4w = 1`
  - `offer_maturity not in {inactive, provisional}`
  - shipped approval-quality floors are met (`realization_anchor >= 0.50`, `expected_pd_improvement >= 0.02`, `decision_confidence >= 0.60`)
- Projected effect source:
  - `readiness_rule`

#### `analysis_offer_readiness_combo_v2_3b`

- Intended movement:
  - conservative one-step movement only
  - no default direct `REJECTED -> APPROVED`
- Eligibility:
  - trust-clean, valid selected winner
  - `offer_maturity = active_rankable`
  - `approval_ready_4w = 1`
  - `combined_plan_realization_probability >= 0.50`
  - `expected_pd_improvement >= 0.02`
  - `decision_confidence >= 0.60`
- Projected effect:
  - `CONDITIONAL -> APPROVED` when approval-quality state is already present but offer/readiness combination is the only remaining bounded story
  - otherwise no movement

### Promotion posture and movement limits

- Phase 50 remains **analysis-only**; no live policy promotion yet.
- Default movement posture is **one-step only**:
  - `REJECTED -> CONDITIONAL`
  - `CONDITIONAL -> APPROVED`
- Direct `REJECTED -> APPROVED` is intentionally excluded from the initial rule catalog because it is too aggressive for the first offer/readiness outcome phase.
- Threshold floors from Phase `49` do not reopen here as free tuning knobs. Any numeric guard used in these rules must stay attached to an explicit offer/readiness condition, not become a generic relaxation lane again.

### Rule provenance and comparison contract

- Live truth remains:
  - `decision_policy_version = v2.1_phase_40_5`
- Phase 50 adds a separate analysis-only provenance layer:
  - `outcome_rule_catalog_version = v2.3_phase_50`
  - `outcome_rule_profile_version`
  - `candidate_outcome_rule_versions_compared`
  - `baseline_decision_status`
  - `candidate_decision_status`
  - `outcome_rule_applied = 0|1`
  - `outcome_rule_source = none | offer_rule | readiness_rule | offer_readiness_rule`
  - `outcome_rule_transition = REJECTED->CONDITIONAL | CONDITIONAL->APPROVED | none`
  - `outcome_rule_reason`
  - `recommended_outcome_rule_profile_version`
  - `recommended_outcome_rule_status = shortlisted | blocked | no_safe_uplift`
  - `recommended_outcome_rule_reason`
- Candidate rule profiles remain explicitly analysis-only in all comparison artifacts.

### Surface contract

- Phase 50 may not break the selected-surface owner from Phase `47`.
- Candidate operator / explanation views should consume additive outcome-rule fields, not infer rule effects themselves.
- If a rule changed the evaluated candidate decision:
  - operator and explanation views may state that the outcome moved because of offer/readiness support
- If no rule changed the candidate outcome:
  - surfaces must not invent outcome-movement language
- Suggested additive consumer fields:
  - `selected_outcome_rule_applied`
  - `selected_outcome_rule_source`
  - `selected_outcome_rule_transition`
  - `selected_outcome_rule_note`

### Acceptance posture

- Phase 50 should be judged by explicit evidence, not optimism.
- Allowed phase outcomes:
  - one or more rule profiles are `shortlisted`, or
  - explicit `no_safe_uplift` if offer/readiness rules still cannot create safe movement
- Trust guardrails remain non-negotiable:
  - zero invalid selected winners
  - zero selected-surface drift
  - zero tracked operator packet coherence regressions
- Primary proof cohorts remain:
  - `pilot_mixed`
  - `risk_band_balanced`
  - `offer_needed_balanced`

### Claude's Discretion

- Exact rule-profile names beyond the locked semantics above, as long as the catalog stays tiny and deterministic
- Exact output filenames for catalogs, comparison tables, and recommendation summaries
- Whether rule-profile review is rendered as markdown + JSON or only JSON + collection summary references, as long as replay and audit remain deterministic

</decisions>

<specifics>
## Specific Ideas

- Phase 49 proved threshold-only relaxation is a dead end for safe uplift on the current baseline, so Phase 50 should test whether **existing offer/readiness state can explain safe movement that thresholds alone could not**.
- The key positive signals already exist in the system; they are just not yet explicit outcome-rule owners:
  - `approval_ready_12w`
  - `approval_ready_24w`
  - `approval_dependent_plan_probability`
  - `rankable_offer_count`
  - `offer_maturity`
- Keep the initial rule catalog conservative and interpretable rather than broad.
- Prefer “why this case moved” provenance over opaque scoring.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): current decision owner; already consumes `expected_readiness`, `approval_ready_4w`, `offer_maturity`, and `combined_plan_realization_probability`, but only as shipped blocking/eligibility logic.
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already owns policy comparison, readiness summaries, decision-shift matrices, segment breakdowns, and candidate recommendation summaries. This is the natural analysis-only seam for Phase 50 as well.
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already publishes the summary fields Phase 50 needs, including:
  - `approval_ready_4w`
  - `approval_ready_12w`
  - `approval_ready_24w`
  - `offer_maturity`
  - `rankable_offer_count`
  - `approval_pending_action_count`
  - `approval_dependent_plan_probability`
  - `offer_acceptance_probability`
  - `combined_plan_realization_probability`
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already writes calibration artifacts, comparison tables, collection summaries, and cohort-level proof surfaces.
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py): already consume additive selected-truth fields safely, so Phase 50 can add bounded rule-effect notes without reopening selected-projection ownership.

### Established Patterns

- Phase `49` already established the analysis-only candidate-profile and provenance contract.
- Phase `45-48` already established that trust repairs are fixed baselines, not tuning knobs.
- Collection summaries and manifests are the canonical place for candidate comparison truth, recommendation summaries, and rerun evidence.
- Operator and explanation surfaces already have drift-guard posture, so any Phase 50 note about outcome movement must be additive and sourced from one selected summary payload.

### Integration Points

- Extend [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) with analysis-only outcome-rule catalog, rule comparison, rule shift matrix, and explicit shortlist/blocked/no-safe-uplift recommendation logic.
- Extend [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) with outcome-rule artifacts and summary provenance parallel to Phase `49`.
- Keep [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) untouched unless additive provenance fields are absolutely needed; live decision semantics remain fixed.
- Reuse operator/explanation surfaces only as consumers of additive rule-effect notes, not as places to invent outcome rules.

</code_context>

<deferred>
## Deferred Ideas

- Reopening threshold-only tuning belongs to Phase `49` and is closed for now.
- Expanding recommendation families or new action semantics belongs to a later milestone, not Phase `50`.
- Broader funnel guardrails, attribution splits, and promotion blocking belong to Phase `51`.
- Preferred/fallback policy pair selection and demo-proof packaging belong to Phase `52`.

</deferred>

---

*Phase: 50-offer-readiness-outcome-rules*
*Context gathered: 2026-04-02*
