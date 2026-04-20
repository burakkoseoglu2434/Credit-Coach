# Requirements: v2.7 Coverage Expansion & Action Surface Unlock

## Milestone Summary

This milestone expands the surfaced action space from a narrow recoverable-only slice into a broader, still-trust-safe recommendation product. The core challenge is not planner capability; it is how recoverability gating and surface rendering collapse rich internal plans into sparse, often empty user output.

## Goals

- increase actionable recommendation coverage from `~3%` to at least `10-20%`
- unlock non-zero actionable coverage for the mid-risk segment
- reduce single-action dominance in surfaced output
- expose multi-step plans where staged progression is more honest or useful than a flat single action
- preserve all trust, validity, and consistency counters at zero

## Out Of Scope

- retraining or replacing the underlying model
- redesigning approval thresholds or lender policy
- integrating new external datasets
- inventing action semantics beyond the current supported action family

## Functional Requirements

### Coverage Diagnostics

- `COV-01`: The system MUST emit a machine-readable coverage diagnostic artifact that explains why each evaluated customer entered `full`, `assisted_full`, or `limited` recommendation mode.
- `COV-02`: The diagnostic artifact MUST bucket failure reasons by customer segment, including at least `near_threshold`, `mid_risk`, and `hard_denied`.
- `COV-03`: The diagnostic artifact MUST quantify empty-state rate, actionability rate, and winner-selection availability by segment and overall cohort.

### Controlled Gate Relaxation

- `GATE-01`: The recoverability layer MUST support at least one intermediate non-empty recommendation tier for customers who do not qualify for strict full recourse but still have credible progress actions.
- `GATE-02`: Relaxed gating MUST never allow a surfaced recommendation whose selected winner violates existing validity checks or operator packet consistency.
- `GATE-03`: Each relaxed-gate recommendation MUST carry explicit provenance showing whether it is `full`, `assisted_full`, or `limited`, and why.

### Action Surface Expansion

- `SURF-01`: The product surface MUST be able to expose more than one actionable recommendation candidate when multiple valid action families exist.
- `SURF-02`: Surfaced action diversity MUST draw only from existing internal action semantics already produced by the planner or heuristics.
- `SURF-03`: The surfaced output MUST publish action-type distribution metrics so dominance by a single action family can be detected in cohort evaluation.

### Multi-Step Plan Surfacing

- `STEP-01`: The system MUST support surfaced plans with ordered steps when the selected internal strategy contains meaningful sequencing or dependency structure.
- `STEP-02`: Step-by-step narratives MUST stay aligned with the underlying selected-plan evidence and MUST not imply unattested outcomes.
- `STEP-03`: Multi-step surfacing MUST preserve deterministic ordering and reproducible artifact output for the same inputs.

### Mid-Risk Unlock

- `MID-01`: Mid-risk customers MUST be eligible for non-empty progress recommendations even when full threshold reach is unlikely in one step.
- `MID-02`: These recommendations MUST frame progress honestly as partial improvement, staged readiness, or longer-horizon movement rather than implied approval certainty.
- `MID-03`: Cohort reporting MUST separately publish actionable coverage for the mid-risk segment.

### Performance And Artifact Integrity

- `PERF-01`: Larger surfaced candidate sets MUST remain evaluation-feasible through payload reduction, caching, reuse, batching, or equivalent implementation improvements.
- `PERF-02`: Performance optimizations MUST not change recommendation semantics silently; any ranking or surfacing effect MUST remain measurable and attributable.
- `PERF-03`: Artifact generation MUST stay reproducible and comparable to the W2a baseline, including evaluation metadata and cohort summaries.

### Comparative Evaluation

- `EVAL-01`: Cohort reruns MUST compare the v2.7 logic against the W2a baseline for coverage, movement, recommendation mode, and action diversity.
- `EVAL-02`: The comparison report MUST include overall and segment-level metrics, including at least `near_threshold`, `mid_risk`, and `hard_denied`.
- `EVAL-03`: The final comparison report MUST explicitly state whether trust counters remained clean and whether milestone success criteria were met.

### Trust And Consistency Guardrails

- `TRUST-01`: `selected_invalid_winner_count` MUST remain `0`.
- `TRUST-02`: `selected_surface_drift_count` MUST remain `0`.
- `TRUST-03`: `operator_packet_contradiction_count` MUST remain `0`.
- `TRUST-04`: Recommendation expansion MUST not introduce narrative or surface claims that exceed the evidence in the selected internal plan.

## Phase Mapping

- **Phase 71: Coverage Diagnostics & Failure Analysis**
  - `COV-01`, `COV-02`, `COV-03`
- **Phase 72: Recoverability Gate Relaxation (Controlled)**
  - `GATE-01`, `GATE-02`, `GATE-03`, `TRUST-01`, `TRUST-02`, `TRUST-03`
- **Phase 73: Action Surface Expansion**
  - `SURF-01`, `SURF-02`, `SURF-03`, `TRUST-04`
- **Phase 74: Multi-Step Plan Surfacing**
  - `STEP-01`, `STEP-02`, `STEP-03`, `TRUST-04`
- **Phase 75: Mid-Risk Segment Unlock**
  - `MID-01`, `MID-02`, `MID-03`, `TRUST-04`
- **Phase 76: Performance & Artifact Optimization**
  - `PERF-01`, `PERF-02`, `PERF-03`
- **Phase 77: Cohort Rerun & Comparative Evaluation**
  - `EVAL-01`, `EVAL-02`, `EVAL-03`, `TRUST-01`, `TRUST-02`, `TRUST-03`

## Acceptance Bar

The milestone is complete only if:

- actionable coverage reaches at least `10-20%`
- mid-risk actionable coverage is measurably above zero
- no single surfaced action family exceeds `50%` of actionable outputs
- multi-step plans are surfaced where applicable
- median `movement_score` remains above `0`
- trust counters remain clean
