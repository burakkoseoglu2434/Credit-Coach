# Phase 62: Recoverable Customer Classifier - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 62 turns the shipped Phase 61 recoverability signal layer into one deterministic, explainable recoverable-customer classifier.

This phase owns:
- `recoverable_flag`
- runtime classifier-form `recoverable_reason_codes`
- additive propagation of classifier truth into audit-facing artifacts

This phase does not own:
- recourse gating or `recourse_mode` (Phase 63)
- planner ranking changes (Phase 64)
- threshold policy changes
- customer/operator surface narrative changes (Phase 66)

</domain>

<decisions>
## Implementation Decisions

### Canonical classifier contract
- The minimal runtime contract should be:
  - `recoverable_flag`
  - `recoverable_reason_codes`
  - `recoverability_classifier_version`
- Do not add a second bucket or classifier-only segment label in Phase 62.
- Reuse the existing Phase 61 fields as the explanatory context around the classifier:
  - `approval_gap`
  - `recoverability_bucket`
  - `threshold_reach_possible`
  - `has_valid_path_flag`
  - `has_rankable_path_flag`
  - hard vs soft blocker fields
- `recoverability_score` must remain visible but must not become the classifier.
- `recoverable_flag` should be a strict boolean or `0/1` contract, not a probabilistic or confidence value.
- `recoverability_classifier_version` should be explicit so later tightening or loosening remains auditable without changing the meaning of historical artifacts.

### Canonical classification rule
- Phase 62 should ship a deliberately strict first-wave classifier.
- A customer is recoverable only when all of the following are true:
  - `approval_gap > 0`
  - `recoverability_bucket == "near_threshold"`
  - `has_rankable_path_flag == 1`
  - `threshold_reach_possible == true`
  - no hard blocker is present
  - no active soft blocker is present
- `has_valid_path_flag` should remain an explanatory field, but the positive gate should rely on `has_rankable_path_flag`, not merely on path existence.
- Valid-but-non-rankable paths are not enough for `recoverable_flag=true`.
- `threshold_reach_possible` is required. A customer should not be classified as recoverable if existing path evidence cannot close the denial gap.
- `recoverability_score` is not part of the decision rule.
- One-sentence classifier definition:
  - "A customer is recoverable only if they are near threshold, have at least one rankable path, that path can close the threshold gap, and no blocker makes the path non-actionable right now."

### Hard vs soft blocker semantics in the classifier
- Hard blockers must always force `recoverable_flag=false`.
- The Phase 61 hard blockers remain canonical:
  - `NO_VALID_WINNER`
  - `NO_PATH`
  - `HIGH_RISK_DISTANCE`
- Soft blockers should also force `recoverable_flag=false` in Phase 62 first wave, but with different interpretation:
  - they mean "not currently recoverable"
  - they do not mean "structurally limited" by themselves
- The Phase 61 soft blockers remain canonical:
  - `BLOCKED_BY_TIME`
  - `BLOCKED_BY_OFFER`
  - `LOW_IMPACT`
- Interpretation rule:
  - hard blocker: too structurally blocked for current recoverable classification
  - soft blocker: technically interesting, but not presently actionable enough to earn `recoverable_flag=true`
- This strict handling is intentional because false positives are worse than false negatives in this milestone.
- Phase 63 or later may route soft-blocked customers differently, but Phase 62 should not classify them as recoverable yet.

### Near-threshold vs mid-risk treatment
- Phase 62 should restrict `recoverable_flag=true` to `near_threshold` customers only.
- `mid_risk` customers should remain `recoverable_flag=false` in this first wave, even if:
  - `threshold_reach_possible == true`
  - valid or rankable paths exist
- Rationale:
  - the current evidence says movement concentration is strongest near threshold
  - the milestone guidance explicitly prefers stricter classification over optimistic inclusion
  - allowing `mid_risk` recoverability now would raise false-positive risk before gating and movement-aware ranking exist
- Mid-risk cases should remain visible in artifacts for later analysis, but they should fail classification with an explicit band/out-of-policy reason instead of being promoted early.

### Explainability and classifier reason codes
- Phase 62 should not simply reuse the entire Phase 61 signal code list unchanged.
- Runtime classifier reasons should be smaller and decision-oriented, while preserving specific blocker detail where needed.
- Recommended classifier reason-code vocabulary:
  - `WITHIN_RECOVERABLE_BAND`
  - `OUTSIDE_RECOVERABLE_BAND`
  - `HAS_VALID_PATH`
  - `NO_VALID_PATH`
  - `HAS_RANKABLE_PATH`
  - `NO_RANKABLE_PATH`
  - `THRESHOLD_REACHABLE`
  - `THRESHOLD_NOT_REACHABLE`
  - `HARD_STRUCTURAL_BLOCK`
  - `SOFT_STRUCTURAL_BLOCK`
  - `NO_ACTIVE_CLASSIFIER_BLOCKERS`
  - `RECOVERABLE`
  - `NOT_RECOVERABLE`
- Preserve detailed blocker codes additively when present:
  - `NO_VALID_WINNER`
  - `NO_PATH`
  - `HIGH_RISK_DISTANCE`
  - `BLOCKED_BY_TIME`
  - `BLOCKED_BY_OFFER`
  - `LOW_IMPACT`
- Do not keep Phase 61 gap-detail codes such as:
  - `LOW_APPROVAL_GAP`
  - `MID_APPROVAL_GAP`
  - `HIGH_APPROVAL_GAP`
  in the runtime classifier reason set. `recoverability_bucket` already carries that information more cleanly.
- Positive recoverable cases should usually read like:
  - `WITHIN_RECOVERABLE_BAND`
  - `HAS_RANKABLE_PATH`
  - `THRESHOLD_REACHABLE`
  - `NO_ACTIVE_CLASSIFIER_BLOCKERS`
  - `RECOVERABLE`
- Negative cases should include the decisive failure family plus any specific blocker:
  - example mid-risk case:
    - `OUTSIDE_RECOVERABLE_BAND`
    - `HAS_RANKABLE_PATH`
    - `THRESHOLD_REACHABLE`
    - `NOT_RECOVERABLE`
  - example soft-blocked case:
    - `WITHIN_RECOVERABLE_BAND`
    - `HAS_RANKABLE_PATH`
    - `THRESHOLD_REACHABLE`
    - `SOFT_STRUCTURAL_BLOCK`
    - `BLOCKED_BY_TIME`
    - `NOT_RECOVERABLE`

### Artifact propagation plan
- Phase 62 should propagate live classifier truth only into additive, audit-facing artifacts first.
- Minimum propagation targets:
  - runtime roadmap summary
  - synced `metrics_summary`
  - customer artifact collection metrics rows
  - cohort evaluation customer-level outputs
  - cohort evidence summary tables
- Calibration-ready work frames may also receive the additive classifier fields if helpful for later analysis, as long as this remains read-only and non-routing.
- Do not update these surfaces in Phase 62:
  - selected customer recommendation text
  - selected-surface projection wording
  - operator packet rendering
  - explanation pack wording
  - website/demo surfaces
- Reason:
  - Phase 62 should publish classifier truth without changing downstream behavior or narrative semantics before Phase 63 and Phase 66.

### Classifier versioning and rollout posture
- The classifier should ship with an explicit version constant, for example a Phase 62-specific value.
- The first rollout should be conservative by design.
- If the business wants broader inclusion later, that should happen through a future explicit rule change and new evidence, not through ambiguous classifier drift.

### Claude's Discretion
- Exact naming of the version string, as long as it is phase-scoped and deterministic.
- Whether `recoverable_flag` is stored as `bool` or `0/1`, as long as artifact contracts stay consistent.
- Whether classifier reasons are derived in a new helper or layered onto the existing recoverability module, as long as Phase 61 signal semantics remain the single upstream source.

</decisions>

<specifics>
## Specific Ideas

- Keep the classifier stricter than instinct suggests. Near-threshold only is the right first-wave policy.
- Treat rankable path evidence as the positive proof, not just path existence.
- Use `threshold_reach_possible` as the main "can this customer actually move" gate.
- Let soft blockers fail classification without calling the customer structurally limited.
- Keep operator/customer surfaces untouched until routing and narrative phases so trust-safe wording does not drift ahead of product behavior.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py): already owns the canonical Phase 61 signal math, threshold reachability, and blocker separation. Phase 62 should build the classifier directly on top of this helper rather than recomputing signals elsewhere.
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already emits the recoverability signal into roadmap summary and synced metrics summary. This is the safest runtime seam for adding `recoverable_flag`.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already propagates Phase 61 recoverability fields into collection rows. It is the natural place to expose classifier truth additively for audits.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already persists recoverability fields and threshold-reach evidence at customer and cohort level. Phase 62 can add classifier truth here without creating a second evaluation seam.
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py): already packages additive recoverability summaries; it can absorb `recoverable_flag` distributions later in a trust-safe way.
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already carries additive gap-derived recoverability fields in selection work frames, which can support internal analysis of classifier concentration.

### Established Patterns
- Trust-critical behavior changes are introduced only after additive artifact proof exists. Phase 62 should follow that pattern.
- Existing surfaces distinguish engine truth from customer/operator wording. Classifier truth should land in artifacts before it changes customer-facing language.
- The codebase already uses fail-closed logic for trust-sensitive selection. The recoverable classifier should mirror that conservative posture.
- Auditability is improved by explicit version strings and additive JSON/list fields rather than hidden interpretation.

### Integration Points
- Add one classifier helper near the existing recoverability helper so all downstream artifact writers consume the same final rule.
- Runtime propagation should happen through the already-shipped roadmap summary and metrics summary sync path.
- Downstream audit propagation should stop at collection and evaluation artifacts in Phase 62.
- Do not wire the classifier into selected-surface or operator packet wording until the later routing and narrative phases.

</code_context>

<deferred>
## Deferred Ideas

- Allowing some `mid_risk` customers to qualify is deferred until later evidence shows the strict near-threshold-only rule is too narrow.
- Using recoverability classification to change recourse mode is deferred to Phase 63.
- Using classifier truth to alter path ranking is deferred to Phase 64.
- Customer-facing or operator-facing recoverability narratives are deferred to Phase 66.

</deferred>

---

*Phase: 62-recoverable-customer-classifier*
*Context gathered: 2026-04-06*
