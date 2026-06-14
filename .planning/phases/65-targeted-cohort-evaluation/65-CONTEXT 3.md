# Phase 65: Targeted Cohort Evaluation - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 65 evaluates whether `v2.5` targeting behavior actually concentrates useful movement and improves honesty relative to the broader denied baseline.

This phase owns:
- deterministic evaluation populations for targeted-vs-global comparison
- a small, decisive movement-concentration metric contract
- explicit honesty/control reporting for limited mode
- additive cohort artifacts and report conclusions about concentration
- baseline comparison framing that avoids overstating business uplift

This phase does not own:
- planner changes
- threshold changes
- new action types or new recourse modes
- new recoverability or movement heuristics
- narrative redesign beyond minimal reporting language
- any second downstream interpretation layer that recomputes runtime truth

Guardrail:
- Phase 65 is evaluation-only
- runtime-emitted truth stays canonical
- success means proving concentration honestly, not manufacturing uplift claims

</domain>

<decisions>
## Implementation Decisions

### Canonical evaluation populations
- The minimum primary population set should be:
  - `global_denied`: the full denied evaluation population under current `v2.5` runtime
  - `recoverable_full_mode`: customers with `recoverable_flag = 1` and `recourse_mode = "full"`
  - `non_recoverable_limited_mode`: customers with `recoverable_flag = 0` and `recourse_mode = "limited"`
- `recoverable_full_mode` vs `global_denied` is the primary thesis comparison for the milestone.
- `non_recoverable_limited_mode` should be reported as a first-class honesty/control group, not a side note.
- Existing recoverability buckets should remain an essential secondary slice:
  - `near_threshold`
  - `mid_risk`
  - `structural_limited`
- First-wave evaluation should not expand beyond these into broad custom segment taxonomies.

### Core success criteria
- Phase 65 should define success as **better concentration of meaningful movement in the recoverable/full-mode population without hiding honesty tradeoffs elsewhere**.
- Mandatory success checks:
  - `recoverable_full_mode` shows higher movement concentration than `global_denied`
  - `recoverable_full_mode` shows higher threshold-reaching selection signals than `global_denied`
  - `non_recoverable_limited_mode` shows explicitly informational posture rather than fake actionability
  - the final report clearly states whether concentration improved, did not improve, or remains inconclusive
- The primary business-facing proof point should be:
  - “Does recoverability targeting concentrate movement-relevant recommendations better than the untargeted denied baseline?”
- This phase should not claim approval uplift, conversion uplift, or causal business lift.

### Minimal movement metric contract
- The mandatory top-line metrics should be:
  - `recoverable_customer_rate`
  - `movement_rate_global`
  - `movement_rate_recoverable`
  - `strong_movement_rate_global`
  - `strong_movement_rate_recoverable`
  - `mean_movement_score`
  - `mean_threshold_reach_probability`
  - `threshold_reach_priority_rate`
  - `selected_path_movement_strength_distribution`
  - `threshold_gap_distribution`
  - `recommendation_mode_distribution`
- First-wave movement-rate interpretation:
  - `movement_rate_*` should reflect customers whose selected path movement strength is not empty/none and remains runtime-derived
  - `strong_movement_rate_*` should stay anchored to the existing selected-path movement-strength categories rather than a new downstream threshold
- These should be first-class in summary tables and JSON outputs.
- Customer-level outputs should carry the additive movement fields already emitted by Phase 64 plus the population labels needed for comparison.
- Separate reporting for `full` vs `limited` mode is required because it is part of the honesty story, not just a debugging detail.

### Honesty and limited-mode evaluation
- Limited mode should become a formal evaluation lens in Phase 65.
- The minimum honesty/control metrics should be:
  - `limited_customer_rate`
  - `informational_recommendation_rate`
  - `empty_state_rate`
  - `selected_action_count_distribution` or equivalent zero-action share
  - `recommendation_mode_distribution`
  - `recourse_mode_distribution`
- The report should explicitly show that non-recoverable customers are being routed into an honest informational posture rather than silently disappearing.
- The intended interpretation:
  - recoverable customers should concentrate actionable movement
  - non-recoverable customers should concentrate informational / empty-state behavior
- “Fake actionability” should be captured as a control concept through existing runtime truth:
  - limited-mode rows with non-empty selected-action posture should be treated as regressions, not as a new heuristic score

### Essential cohort slicing
- Essential slices for first wave:
  - by primary population (`global_denied`, `recoverable_full_mode`, `non_recoverable_limited_mode`)
  - by `recoverability_bucket`
  - by `recourse_mode`
  - by `recommendation_mode`
- Important but secondary diagnostics:
  - `selected_path_type`
  - institution/hybrid exposure
  - path-count or rankable-path-count buckets
- Near-threshold should remain the primary movement-focused slice when narrative interpretation is needed, because it is the cleanest test of concentration rather than broad structural limitation.
- Do not open many extra cross-tabs in first wave; concentration should stay easy to read.

### Artifact and report contract
- The minimum artifact set should remain the existing evaluation family:
  - `customer_level_analysis.csv`
  - `cohort_metrics.json`
  - `cohort_evaluation_report.md`
  - additive evidence tables / CSVs
- Phase 65 should extend the existing cohort-evidence package rather than invent a disconnected reporting system.
- Add one explicit targeted-comparison surface, either:
  - a dedicated targeted-comparison section in `cohort_metrics.json` and `cohort_evaluation_report.md`
  - or one additive comparison table artifact generated alongside the existing evidence tables
- The canonical report artifact should be `cohort_evaluation_report.md`, with `cohort_metrics.json` as the machine-readable contract.

### Baseline comparison strategy
- Primary comparison strategy should be:
  - `recoverable_full_mode` vs `global_denied` within the current `v2.5` runtime
- This is the cleanest proof of targeting concentration because it isolates the question:
  - given the shipped `v2.5` system, does the recoverable subset carry denser movement than the untargeted denied baseline?
- Secondary comparison to `v2.4` evidence may be included only as contextual appendix, not as the main thesis test.
- If `v2.4` is referenced, only safe like-for-like metrics should be compared:
  - movement-potential or selected-path movement distributions
  - recourse-mode / recommendation-mode posture where semantically compatible
  - threshold-gap or recoverability-bucket-like cohort distance framing only when directly reproducible
- Do not mix “capability expansion versus older runtime” with “targeting concentration inside current runtime” in one headline conclusion.
- The report should separate:
  - `current_runtime_targeting_result`
  - `historical_context_vs_v2_4` if included

### Final conclusion contract
- Phase 65 must end with a deterministic report statement in one of these shapes:
  - targeting improved movement concentration
  - targeting did not materially improve concentration
  - targeting improved concentration but not enough to claim meaningful business leverage
  - evidence remains inconclusive
- That conclusion should be driven by the locked comparison tables, not analyst prose alone.
- Honesty outcomes must be reported beside movement outcomes, not after them.

### Claude's Discretion
- Exact artifact names for any added comparison CSV or JSON section, as long as the existing evaluation family remains intact.
- Exact presentation order inside the report, as long as concentration and honesty are both visible near the top.
- Whether threshold-gap distribution is encoded as explicit bucket shares, summary stats, or both, as long as it remains deterministic and readable.

</decisions>

<specifics>
## Specific Ideas

- Keep the evaluation dashboard small and decisive.
- Treat `recoverable_full_mode` as the actionability concentration group and `non_recoverable_limited_mode` as the honesty control group.
- Show concentration, not just central tendency.
- Reuse Phase 64 selected-path movement fields directly instead of inventing new scoring downstream.
- Keep `v2.4` comparison secondary so Phase 65 does not confuse capability gains with targeting gains.
- Make empty-state / informational posture an explicit success condition rather than a silent background check.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already builds `customer_level_analysis.csv`, `cohort_metrics.json`, and `cohort_evaluation_report.md`, so Phase 65 should extend this runner rather than create a second evaluation CLI.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already resolves runtime-first recoverability and recourse-gate truth from roadmap and metrics summaries, which is the correct seam for population labeling.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already carries Phase 64 selected-path movement fields into customer rows and aggregate outputs, so Phase 65 can compute targeted comparisons without new heuristics.
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py): already summarizes population metrics and writes additive evidence tables, including Phase 64 movement-ranking evidence, so it can be extended for targeted-comparison packaging.
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): remains the canonical source for `recoverable_flag`, `recourse_mode`, `recommendation_mode`, `movement_score`, `threshold_reach_probability`, `threshold_reach_priority_flag`, and `selected_path_movement_strength`.

### Established Patterns
- The repo prefers runtime-first propagation and additive evaluation layers rather than downstream reinterpretation.
- Existing cohort artifacts already distinguish movement potential, recoverability, recourse gate posture, and trust regression separately; Phase 65 should preserve that decomposition.
- Trust-sensitive downstream consumers are already covered by focused regression suites, so Phase 65 should extend evaluation reporting without reopening planner or surface semantics.
- Existing report generation already emits narrative diagnosis lines; Phase 65 can upgrade those conclusions without changing customer/operator-facing artifacts.

### Integration Points
- Add explicit population labels and targeted comparison summaries inside [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py).
- Extend [summarize_population_metrics_from_rows(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py) only where needed to support targeted-comparison tables from already-emitted fields.
- Keep Phase 60 / existing evidence artifacts as the base package, then layer targeted-comparison outputs additively instead of replacing them.
- Reuse current pytest coverage around cohort evaluation and trust-safe downstream consumers; this phase should primarily deepen cohort-evaluation tests rather than create a separate trust framework.

</code_context>

<deferred>
## Deferred Ideas

- New planner or routing behavior based on Phase 65 results
- Any new recoverability heuristic or learned concentration model
- New narrative types or customer-facing copy changes beyond the planned Phase 66 scope
- Broad custom cohort taxonomies outside recoverable/full/limited and existing recoverability buckets
- Headline business uplift claims tied to approval or offer conversion
- Any expansion of action semantics, thresholds, or institution integrations

</deferred>

---

*Phase: 65-targeted-cohort-evaluation*
*Context gathered: 2026-04-08*
