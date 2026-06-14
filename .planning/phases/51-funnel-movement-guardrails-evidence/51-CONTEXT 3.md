# Phase 51: Funnel Movement Guardrails & Evidence - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 51 does **not** try a new policy family and does **not** reopen threshold tuning, offer/readiness rule design, feature space, or action semantics. Its job is to turn the current `no_safe_uplift` result into explicit evidence:

- why `APPROVED` and `CONDITIONAL` movement is still not happening
- which blockers are policy/guardrail blockers versus structural blockers
- whether the current system is bottlenecked by thresholds, offer/readiness, recommendation-space limits, or cohort composition
- which candidate profiles are blocked because of guardrails versus because they created no movement at all

Phase 51 owns:

- movement evidence and promotion-blocker diagnostics for the Phase `49` threshold profiles and Phase `50` outcome-rule profiles
- one canonical bottleneck-classification layer over existing artifacts
- explicit guardrail reporting that separates trust blockers from structural no-movement blockers
- portfolio outputs that distinguish threshold-driven lift from offer/readiness-driven lift, even when both are zero

Guardrails:

- no live policy promotion
- no change to `decision_policy_version`
- no redesign of Phases `40` through `50`
- no new recommendation families or feature inputs
- all `v2.2` trust counters remain fixed promotion prerequisites

</domain>

<decisions>
## Implementation Decisions

### Exact scope

Phase 51 should produce a **diagnostic evidence layer**, not a new decision layer.

It should answer:

1. did any candidate profile create movement at all?
2. if yes, was it blocked by trust/risk guardrails or merely not chosen?
3. if no, is the dominant reason:
   - threshold gate rigidity
   - offer/readiness weakness
   - recommendation-space weakness
   - structural cohort composition

The phase is successful if it produces an explicit bottleneck diagnosis and promotion-blocker proof, even if the answer remains “no promotable movement exists.”

### Canonical comparison inputs

Phase 51 should consume the existing Phase `49` and Phase `50` comparison artifacts as the only candidate movement sources:

- threshold comparison from [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
  - `analysis_mild_relax_v2_3a`
  - `analysis_relaxed_v2_3a`
  - `analysis_strict_control_v2_3a`
- outcome-rule comparison from the same owner
  - `analysis_offer_support_v2_3b`
  - `analysis_readiness_support_v2_3b`
  - `analysis_offer_readiness_combo_v2_3b`

No new candidate policy or rule profiles belong in Phase 51.

### Guardrails that must be measured explicitly

Phase 51 should group guardrails into four explicit families.

#### 1. Trust guardrails

These remain hard promotion blockers and should be surfaced directly, not inferred:

- `selected_invalid_winner_count`
- `selected_invalid_winner_rate`
- `selected_dice_valid_rate`
- `selected_decision_mismatch_count`
- `approved_with_blocker_count`
- `approved_with_action_count`
- `approved_with_upgrade_condition_count`
- `action_blocker_mismatch_count`
- `readiness_decision_mismatch_count`

If any of these regress, the candidate is trust-blocked, full stop.

#### 2. Risk / promotion guardrails

These explain whether a candidate created movement but still cannot be promoted:

- `false_positive_proxy`
- `false_positive_proxy_delta`
- `internal_needs_review_share`
- `internal_needs_review_share_delta`
- `north_star_pass`
- `direct_rejected_to_approved_count`

Phase 51 should keep direct `REJECTED -> APPROVED` movement explicitly disallowed for the Phase `50` outcome profiles.

#### 3. Movement evidence counters

These show whether a candidate actually moved the funnel:

- `approved_share`
- `conditional_share`
- `rejected_share`
- `approve_plus_conditional_share`
- `approve_plus_conditional_share_delta`
- `rejected_to_conditional_count`
- `conditional_to_approved_count`
- `direct_rejected_to_approved_count`

#### 4. Structural ceiling signals

These diagnose whether the portfolio itself contains too few movable cases:

- readiness distribution, especially:
  - `now`
  - `week_4`
  - `week_12`
  - `not_ready`
- `offer_ready_contender_share`
- `provisional_offer_share`
- `approval_shell_only_share`
- `non_empty_contender_share`
- dominant blocker mix from operator briefing
- risk-band mix and segment breakdown

### How bottleneck types should be distinguished

Phase 51 should use a deterministic, priority-ordered bottleneck classifier.

#### A. Threshold bottleneck

Classification rule:

- mark `threshold_bottleneck = guardrail_blocked` if any Phase `49` candidate profile creates positive movement or positive `approve_plus_conditional_share_delta`, but is blocked by risk/trust guardrails
- mark `threshold_bottleneck = no_movement` if all Phase `49` candidates show zero movement and zero uplift deltas

This distinction matters:

- `guardrail_blocked` means thresholds might matter later
- `no_movement` means threshold tuning is not the current binding constraint

#### B. Offer/readiness bottleneck

Classification rule:

- mark `offer_readiness_bottleneck = guardrail_blocked` if any Phase `50` profile creates bounded one-step movement but is blocked by proxy/trust guardrails
- mark `offer_readiness_bottleneck = no_movement` if all Phase `50` profiles show:
  - `rejected_to_conditional_count = 0`
  - `conditional_to_approved_count = 0`
  - `approve_plus_conditional_share_delta = 0`

This phase already observed the second case on the standard cohorts, so the classifier should preserve that diagnosis explicitly.

#### C. Recommendation-space bottleneck

This is the first “engine-side” bottleneck classifier in v2.3.

Classification rule:

- mark `recommendation_space_bottleneck = primary` when movement is absent and the evidence shows weak plan availability or weak impact, such as:
  - low `non_empty_contender_share`
  - high `approval_shell_only_share`
  - dominant blocker “No actionable step is available”
  - dominant blocker “Expected impact is still too small”
  - high empty/constraint pressure from candidate or roadmap outputs

Interpretation:

- threshold and offer/readiness rules did not fail because of strict policy only
- they failed because the current recommendation set rarely produces sufficiently strong, eligible candidates

#### D. Structural cohort bottleneck

Classification rule:

- mark `structural_cohort_bottleneck = primary` when movement is absent and the cohort composition itself leaves too few near-term movable cases, for example:
  - very high `not_ready` share
  - very low `week_4 + week_12` share
  - low offer-needed / rankable-offer presence
  - concentration of rejections in structurally weak segments from `segment_breakdown.csv`

Interpretation:

- the current sample is dominated by customers who are genuinely too far from movement under the shipped action space

### Dominant bottleneck selection contract

Phase 51 should not output four unrelated diagnostics only. It should also output one explicit dominant diagnosis per cohort:

- `threshold_guardrail_blocked`
- `offer_readiness_guardrail_blocked`
- `recommendation_space_limited`
- `structural_cohort_limited`
- `mixed_no_safe_uplift`

Selection rule:

- trust regression always overrides everything else and becomes `trust_regression_blocked`
- otherwise:
  - if threshold or offer/readiness candidates created movement but failed guardrails, choose the strongest guardrail-blocked label
  - if no candidates created movement, prefer:
    - `recommendation_space_limited` when actionable/impact scarcity dominates
    - `structural_cohort_limited` when near-term movable population scarcity dominates
  - use `mixed_no_safe_uplift` only when no single evidence family clearly dominates

### Required evidence outputs and artifacts

Phase 51 should add a compact but first-class evidence package:

- `calibration/movement_guardrail_summary.json`
- `calibration/movement_promotion_blockers.csv`
- `calibration/movement_bottleneck_breakdown.csv`
- `calibration/movement_ceiling_breakdown.csv`
- `calibration/movement_guardrail_review.md`

Additive collection outputs:

- collection manifest fields:
  - `dominant_movement_bottleneck`
  - `movement_guardrail_summary`
  - `promotion_blocker_summary`
- collection summary sections:
  - `## Funnel Guardrails`
  - `## Movement Diagnosis`

Pilot-facing additive outputs:

- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) should report the dominant bottleneck and whether movement absence is policy-blocked or structure-blocked
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) should verify that the new guardrail/evidence artifacts exist when Phase `51` outputs are present

Operator packet semantics should **not** be redesigned in this phase.

### Acceptance posture

Phase 51 is complete when:

- all three standard cohorts have explicit movement guardrail summaries
- threshold-driven and offer/readiness-driven movement are separated cleanly
- each cohort has an explicit dominant bottleneck diagnosis
- promotion blocker reasons are readable directly from artifacts
- all shipped `v2.2` trust counters remain clean

Allowed phase outcomes:

- a candidate family is shown to be guardrail-blocked, or
- the system is shown to be bottlenecked by recommendation-space or cohort structure, or
- mixed diagnosis if evidence is truly split

Phase 51 does **not** require finding uplift. It requires proving why uplift is absent.

### Claude's Discretion

- Exact names for the new guardrail/bottleneck files
- Exact numeric evidence bands used for “dominant” recommendation-space versus structural-cohort diagnosis, as long as they remain deterministic and documented
- Whether pilot refresh and QA expose the new diagnosis in markdown, JSON summary fields, or both

</decisions>

<specifics>
## Specific Ideas

- Reuse the existing Phase `49` and Phase `50` comparison owners instead of creating a third policy-evaluation system.
- Treat “no movement” as a first-class diagnosable result, not just a failed shortlist.
- Promote the current operator briefing blocker mix into a portfolio diagnosis input, but do not turn operator packet into a new evidence owner.
- Make the dominant bottleneck easy to quote in demos:
  - “thresholds are not the blocker”
  - “offer/readiness is not the blocker”
  - “the current action space is too weak”
  - “this cohort is structurally too far from movement”

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already owns baseline metrics, false-positive proxy components, policy comparison, outcome-rule comparison, decision-shift matrices, segment breakdowns, and recommendation summaries. This is the natural owner for Phase 51 guardrail and bottleneck evidence.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already packages collection summaries, calibration review, funnel/readiness distributions, policy and outcome-rule artifacts, and trust counters. This is the correct packaging seam for Phase 51 evidence.
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): already aggregates dominant blockers, conditional hotspots, and offer hotspots at collection level. These are reusable inputs for recommendation-space and structural bottleneck diagnosis.
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py): already mirrors candidate policy and outcome-rule recommendation summaries into pilot-facing markdown and JSON.
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py): already validates additive provenance contracts and can extend to Phase 51 artifact existence checks.

### Established Patterns

- Phase `49` established `shortlisted | blocked | no_safe_uplift` as the honest recommendation contract.
- Phase `50` extended the same honesty contract to offer/readiness rules and already publishes zero-movement artifacts.
- Phase `45-48` trust counters are fixed promotion prerequisites, not tunable metrics.
- Collection summary, manifest, and calibration markdown are the canonical portfolio-proof surfaces for candidate comparison evidence.

### Integration Points

- Extend [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) with:
  - movement guardrail summary
  - bottleneck classifier
  - promotion blocker matrix
  - threshold-vs-outcome attribution summary
- Extend [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) with:
  - new guardrail and bottleneck artifacts
  - collection summary sections for movement diagnosis
  - manifest pointers to the new evidence
- Extend [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) and [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) additively so pilot-facing runs can quote the dominant bottleneck.
- Keep [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py), selected projection, and operator packet rendering semantics untouched.

</code_context>

<deferred>
## Deferred Ideas

- Expanding recommendation/action semantics belongs to a later milestone, not Phase `51`.
- New feature space or new rule families belong outside this phase.
- Preferred policy promotion and demo profile selection belong to Phase `52`.
- Eliminating pandas concat warnings remains a separate edge-case operating-envelope concern, not Phase `51`.

</deferred>

---

*Phase: 51-funnel-movement-guardrails-evidence*
*Context gathered: 2026-04-03*
