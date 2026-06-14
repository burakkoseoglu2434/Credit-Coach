# Phase 61: Recoverability Signal Definition - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 61 defines the deterministic recoverability signal layer for denied customers. It owns the signal fields and bucket semantics that later phases will consume:

- `approval_gap`
- `normalized_gap`
- `risk_band`
- `recoverability_score`
- `recoverability_bucket`
- `threshold_reach_possible`
- additive reason-code vocabulary that explains the signal

This phase does not change planner behavior, decision thresholds, winner selection, or recourse routing. It prepares a classification-ready contract for Phase 62, which will own the explicit `recoverable_flag` decision.

</domain>

<decisions>
## Implementation Decisions

### Canonical gap definition
- `approval_gap` should be the canonical primary field and should remain the raw denied-distance to the current approval threshold:
  - `approval_gap = max(0.0, base_pd - tau)`
- The canonical source inputs are the same shipped fields already used in cohort selection and calibration:
  - `base_pd` from the current model prediction
  - `tau` from the shipped decision threshold config
- Phase 61 should not introduce a second competing "feature gap" concept. Feature-level distance is too implementation-specific and would weaken audit clarity.
- `normalized_gap` should be additive and secondary, not the main business field. It should normalize raw gap against the shipped `mid_upper` threshold:
  - `normalized_gap = min(1.0, approval_gap / mid_upper)`
- Business and demo language should prefer raw `approval_gap`; internal prioritization may use both.

### Recoverability buckets
- Bucket boundaries should be absolute, not percentile-based, so the same customer lands in the same bucket across reruns and cohort mixes.
- Reuse the shipped risk-band thresholds already present in recourse and calibration config:
  - `near_upper = 0.10`
  - `mid_upper = 0.25`
- Bucket mapping should stay aligned with the existing raw-gap semantics:
  - `near_threshold` when `approval_gap <= near_upper`
  - `mid_risk` when `near_upper < approval_gap <= mid_upper`
  - `structural_limited` when `approval_gap > mid_upper`
- `risk_band` should remain the low-level engine-friendly label already used elsewhere:
  - `near`
  - `mid`
  - `high`
- `recoverability_bucket` should be the business-facing milestone label:
  - `near_threshold`
  - `mid_risk`
  - `structural_limited`
- Do not use percentile bucketing in this phase. Percentiles would make the signal look better or worse depending on sample composition and would conflict with the phase goal of auditability.

### Recoverability score
- The score should be heuristic, bounded, and easy to explain. No learned or opaque scoring logic belongs here.
- The score should be strictly gap-driven:
  - `recoverability_score = 1.0 - normalized_gap`
- The score should remain:
  - a prioritization signal
  - not a classifier
  - not a substitute for later recoverable decision logic
- Path evidence and structural realism should remain visible through additive helper flags, not blended into the score formula:
  - `has_valid_path_flag`
  - `has_rankable_path_flag`
  - `structural_blocker_flag`

### Threshold reachability signal
- Phase 61 should add one deterministic helper field:
  - `threshold_reach_possible`
- This field estimates whether already-available recourse paths can realistically close the current denial gap.
- Minimum viable heuristic:
  - compute `best_possible_pd_improvement` from existing valid/rankable path outputs
  - set `threshold_reach_possible = true` when `best_possible_pd_improvement >= approval_gap`
  - otherwise set `threshold_reach_possible = false`
- Phase 61 should not simulate new plans or infer hypothetical future actions to populate this field.
- `threshold_reach_possible` is a signal for Phase 62 classification, not a decision by itself.

### Classification boundary
- Phase 61 must not finalize `is_recoverable_customer`.
- Phase 61 owns only the signal layer:
  - `approval_gap`
  - `normalized_gap`
  - `recoverability_bucket`
  - `recoverability_score`
  - `threshold_reach_possible`
  - additive helper flags
  - reason codes
- All final recoverable classification logic belongs to Phase 62.

### Structural blocker semantics
- Phase 61 should distinguish between hard and soft structural blockers instead of treating all blockers equally.
- Hard structural blockers:
  - `NO_VALID_WINNER`
  - `NO_PATH`
  - `HIGH_RISK_DISTANCE`
- Soft structural blockers:
  - `BLOCKED_BY_TIME`
  - `BLOCKED_BY_OFFER`
  - `BLOCKED_BY_LOW_IMPACT`
- Interpretation rule:
  - hard blockers should strongly affect recoverability interpretation
  - soft blockers should remain visible but should not automatically imply structural limitation
- `structural_blocker_flag` may be emitted as a simple helper flag, but downstream logic should preserve the hard-vs-soft distinction rather than flattening them into one undifferentiated state.

### Explainability and reason codes
- Reason codes should be minimal, stable, and separable by meaning:
  - threshold proximity
  - path availability
  - structural blockers
  - threshold reachability
- Recommended Phase 61 reason-code set:
  - `LOW_APPROVAL_GAP`
  - `MID_APPROVAL_GAP`
  - `HIGH_APPROVAL_GAP`
  - `HAS_VALID_PATH`
  - `NO_VALID_PATH`
  - `HAS_RANKABLE_PATH`
  - `THRESHOLD_REACHABLE`
  - `THRESHOLD_NOT_REACHABLE`
  - `BLOCKED_BY_TIME`
  - `BLOCKED_BY_OFFER`
  - `BLOCKED_BY_LOW_IMPACT`
  - `BLOCKED_BY_NO_PATH`
  - `BLOCKED_BY_NO_VALID_WINNER`
  - `HIGH_RISK_DISTANCE`
  - `HARD_STRUCTURAL_BLOCK`
  - `SOFT_STRUCTURAL_BLOCK`
  - `STRUCTURAL_LIMIT`
- Reason-code usage should be compositional:
  - bucket / gap reason
  - path-presence reason
  - threshold-reach reason
  - blocker reason if applicable
- `STRUCTURAL_LIMIT` should be a summary code, not the only code. It should appear only when one or more blocker reasons justify the summary.
- `HARD_STRUCTURAL_BLOCK` and `SOFT_STRUCTURAL_BLOCK` should act as category codes, while the more specific blocker code carries the detailed meaning.
- Phase 61 should prefer deriving reasons from existing blocker vocabulary already used in movement diagnosis and operator outputs rather than inventing a second explanation language.

### Artifact and field contract
- Phase 61 outputs should be additive and file-safe:
  - per-customer signal fields should land in evaluation and collection artifacts
  - existing trust fields must remain unchanged
- Minimum field contract to implement in this phase:
  - `approval_gap`
  - `normalized_gap`
  - `risk_band`
  - `recoverability_score`
  - `recoverability_bucket`
  - `threshold_reach_possible`
  - `recoverable_reason_codes`
- Optional analysis-only helper fields are acceptable if they improve auditability, for example:
  - `has_valid_path_flag`
  - `has_rankable_path_flag`
  - `structural_blocker_flag`
  - `top_recoverability_blocker_code`
- Do not emit `recourse_mode` in Phase 61. That belongs to Phase 63.

### Claude's Discretion
- Exact storage location for shared recoverability helpers, as long as the logic is reusable by Phase 62, Phase 65, and artifact pipelines.
- Whether `normalized_gap` is rounded at write time or only in reports, as long as internal calculations remain deterministic.
- Whether helper flags are persisted broadly or only where downstream evaluation and classification need them.

</decisions>

<specifics>
## Specific Ideas

- Keep recoverability anchored to the same raw `base_pd - tau` distance the repo already uses for denied segmentation and the v2.4 cohort evaluator.
- Reuse the shipped absolute thresholds `0.10` and `0.25` instead of inventing a new banding scheme for v2.5.
- Keep the score simple and gap-only; use helper flags and reachability instead of composite weighting.
- Treat the score as a prioritization aid and audit lens, not as a substitute for the explicit classifier rule in Phase 62.
- Reuse existing blocker language from movement diagnosis where possible so later narratives can stay consistent with operator and cohort evidence.
- Use threshold reachability as the main bridge from signal definition in Phase 61 to explicit recoverability classification in Phase 62.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already defines `_risk_band_from_pd(...)` using raw `base_pd - tau` distance and the shipped `near_upper=0.10`, `mid_upper=0.25` config.
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already builds `pd_distance_to_tau`, `risk_band`, `pilot_bucket`, movement blocker summaries, and structural cohort signals that should inform recoverability reason codes.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already computes `approval_gap = max(0, base_pd - tau)` and classifies v2.4 cohort slices by that raw gap.
- [pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py): already exposes deterministic path metrics, including `path_count`, `rankable_path_count`, and path types that can support later recoverability classification.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already computes `best_reachable_pd`, `max_path_pd_improvement`, and gap-closure signals that can inform `threshold_reach_possible` without new simulation logic.
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): already owns readiness, impact, and execution gate semantics that later phases can reuse when distinguishing recoverable from unrealistic cases.
- [recourse.yaml](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/configs/recourse.yaml): already locks the risk-band thresholds Phase 61 should inherit.

### Established Patterns
- The repo prefers deterministic, rule-based thresholds over percentile or learned segmentation for customer-facing decision logic.
- Analysis-only evidence is often emitted before runtime promotion; Phase 61 should follow that pattern and avoid turning the signal into a live routing decision yet.
- Existing movement diagnosis already separates recommendation-space limits from structural cohort limits; recoverability should reuse that vocabulary instead of creating a new ontology.
- Existing evaluation code already distinguishes reachable-vs-not-reachable movement heuristics; Phase 61 should reuse those outputs instead of introducing hypothetical reach estimates.
- Additive fields and summaries are the standard way to evolve artifact contracts without reopening trust-critical logic.

### Integration Points
- Add shared recoverability helpers near evaluation or recourse orchestration code so Phase 62 can reuse the exact same field derivation.
- Extend current evaluation outputs and collection summaries with the new signal fields rather than building a separate reporting pipeline.
- Keep any future `recoverable_flag` implementation downstream of this phase’s signal layer so Phase 61 remains classification-ready but signal-only.

</code_context>

<deferred>
## Deferred Ideas

- Emitting live `recoverable_flag` or `recourse_mode` belongs to Phase 62 and Phase 63, not Phase 61.
- Changing planner ranking based on recoverability belongs to Phase 64.
- Replacing absolute buckets with percentile or cohort-adaptive bands would be a different design direction and is intentionally deferred.
- Any model-based recoverability predictor is out of scope for this milestone.

</deferred>

---

*Phase: 61-recoverability-signal-definition*
*Context gathered: 2026-04-05*
