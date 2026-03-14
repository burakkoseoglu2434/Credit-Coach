# Phase 10: Candidate Quality and Trajectory Tuning - Context

**Gathered:** 2026-03-15
**Status:** Ready for replanning

<domain>
## Phase Boundary

Improve the quality and explainability of existing candidate generation once fairness and KPI measurement contracts are stable. This phase clarifies which candidate-quality metrics are canonical seeded evidence, how denied high-risk tuning should be interpreted, how generator and policy impact should be described, and what the derived review surface should emphasize. It does not add new end-user capabilities and it does not change the Phase 8 or Phase 9 release gate contract.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-9
- Phase 8 and Phase 9 release and acceptance semantics remain authoritative:
  - release decisions are still driven by reliability, lift, and fairness precedence
  - candidate-quality and high-risk tuning evidence must not override those gates
- Phase 10 must preserve the artifact principle established earlier:
  - machine-readable artifacts are the canonical source of truth
  - markdown review text is always a derived companion

### Candidate Quality Contract
- Canonical seeded candidate-quality metrics are:
  - `candidate_pool_diversity_index`
  - `candidate_source_entropy`
  - `best_source_internal_rate`
  - `best_source_dice_rate`
  - `best_source_rule_rate`
  - `best_source_fallback_rate`
- Canonical population for candidate-quality summaries:
  - `denied`
- Secondary companion population:
  - `high_risk_denied`
- If explicit population fields are written, preferred values are:
  - `candidate_quality_population = denied`
  - `candidate_quality_secondary_population = high_risk_denied`
- Canonical source taxonomy is fixed to:
  - `internal`
  - `dice`
  - `rule`
  - `fallback`
- The following remain companion metadata or breakdown dimensions rather than canonical source labels:
  - `policy_profile`
  - `dice_backend`
  - `fallback_reason`
- Candidate-quality metrics are mandatory seeded evidence in Phase 10, but they are not release-blocking gates
- Strong companion artifacts for this phase include:
  - `denied_candidate_source_breakdown.csv`
  - `dice_backend_distribution.csv`
  - `dice_fallback_distribution.csv`

### High-Risk Tuning Policy
- The primary success metric for denied high-risk tuning is:
  - `denied_high_risk_lift`
- Supporting metrics for high-risk tuning interpretation are:
  - `high_risk_reachability_rate`
  - `trajectory_partial_progress_rate`
- Existing trajectory gate-rate metrics remain part of the broader KPI layer and should not replace the primary high-risk tuning metric
- High-risk tuning should be considered diagnostic-only when any of the following are true:
  - seeded direction is unstable
  - `high_risk_profile_applied_rate` is below the activation threshold
  - supporting metrics deteriorate even if the primary metric improves
  - Phase 8 or Phase 9 release gates fail
- The activation threshold for non-anecdotal high-risk tuning evidence is:
  - `high_risk_profile_applied_rate >= 0.05`
- If activation is below that threshold, any apparent improvement should be labeled anecdotal and diagnostic-only
- High-risk tuning is never a gate override
- High-risk tuning may serve as promotion evidence or a tie-breaker only after the locked release gates already pass

### Impact Attribution Contract
- Phase 10 attribution language must be comparative, not causal
- Allowed framing:
  - a source, policy, or tuning change was observed alongside KPI movement in repeated seeded comparison
- Disallowed framing:
  - a change is described as having conclusively caused the KPI movement
- Primary attribution baseline:
  - `control variant`
- Secondary attribution baselines may be used as companions only:
  - previous accepted config
  - previous run baseline
- Helped or harmed judgments must be metric-by-metric rather than collapsed into one synthetic score
- Primary interpretation axes are:
  - `denied_to_approved_lift`
  - `denied_high_risk_lift`
  - `equalized_odds_gap_delta`
  - `denied_reliability_violation_rate`
- Supporting interpretation axes are:
  - `high_risk_reachability_rate`
  - `trajectory_partial_progress_rate`
  - `candidate_source_entropy`
- Allowed metric-level impact labels are:
  - `helped`
  - `harmed`
  - `mixed`
  - `no_material_change`
- Strong comparative attribution is only allowed when:
  - repeated seeded evidence exists
  - the direction of the aggregate delta matches the majority seed direction
  - the evidence is not degraded
- Preferred confidence labels are:
  - `strong`
  - `tentative`
- When strong-attribution conditions are not met, the output should remain tentative or explicitly diagnostic-only

### Review Surface
- The primary goal of the Phase 10 review surface is:
  - decision explanation, not dashboarding
- The review should help a human answer:
  - why a generator or policy path looked better or riskier
  - whether candidate generation quality improved
  - whether denied high-risk tuning helped consistently
  - which tradeoffs appeared against fairness or reliability
- Default review structure should be:
  - `Decision`
  - `Candidate Quality Summary`
  - `High-Risk Tuning Summary`
  - `Impact Attribution Summary`
  - `Fairness & Reliability Snapshot`
  - `Supporting Artifacts`
- The `Decision` section should surface at minimum:
  - `release_decision`
  - `acceptance_status`
  - `evidence_level`
  - freeze and provenance summary
- The `Candidate Quality Summary` section should surface at minimum:
  - `candidate_pool_diversity_index`
  - `candidate_source_entropy`
  - `best_source_internal_rate`
  - `best_source_dice_rate`
  - `best_source_rule_rate`
  - `best_source_fallback_rate`
  - note that the canonical population is `denied`
  - note that `high_risk_denied` is the companion population
- The `High-Risk Tuning Summary` section should surface at minimum:
  - `high_risk_profile_applied_rate`
  - `denied_high_risk_lift`
  - `high_risk_reachability_rate`
  - `trajectory_partial_progress_rate`
  - whether the result is strong evidence or diagnostic-only
- The `Impact Attribution Summary` section should use the metric-level labels:
  - `helped`
  - `harmed`
  - `mixed`
  - `no_material_change`
  - and also show `comparative_impact_confidence = strong | tentative`
- The review must remain concise and should not turn into an exhaustive KPI dump or analytics dashboard

### Claude's Discretion
- Exact JSON nesting for candidate-quality and impact companion artifacts, as long as the locked field names and review labels remain explicit
- Exact markdown wording and ordering inside each review section, as long as the default sections and required signals remain visible
- Whether companion fields such as `diagnostic_only` are emitted directly or represented through a small structured status block

</decisions>

<specifics>
## Specific Ideas

- Candidate-quality metrics are mandatory evidence, but not release-blocking gates in Phase 10
- High-risk tuning should behave as promotion evidence or a tie-breaker only after release gates already pass
- Review text should let a human answer the Phase 10 questions in roughly one to two minutes without reading raw JSON or CSV files
- If policy logic eventually becomes a first-class generator family, the canonical source taxonomy can be revisited in a later phase rather than expanded now

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits `candidate_pool_diversity_index`, `candidate_source_entropy`, `best_source_*` rates, `high_risk_profile_applied_rate`, `denied_high_risk_lift`, and `high_risk_reachability_rate`
  - already writes companion breakdown artifacts such as `denied_candidate_source_breakdown.csv`, `dice_backend_distribution.csv`, and `dice_fallback_distribution.csv`
  - already contains `_apply_high_risk_profile(...)` and the bounded high-risk tuning hook
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already promotes seeded KPI and fairness evidence into aggregate artifacts
  - already emits `milestone_acceptance_summary.json`, `milestone_acceptance_review.md`, and `release_review_summary.md`
  - already carries high-risk and trajectory summary metrics into seeded suite outputs
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already computes challenger summary rows, control-versus-champion deltas, and seeded release payloads
  - already exposes a natural primary attribution baseline through the control variant
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already owns the canonical machine-readable and markdown review helpers that Phase 10 should extend instead of bypassing

### Established Patterns
- Canonical machine-readable evidence lives in JSON and CSV under `artifacts/runs/<run_id>/tables/`
- Derived markdown review is generated from canonical summaries, not handwritten as a separate decision path
- Seeded suite and challenger flows are the accepted place to compare repeated evidence; batch evaluation remains the source of local raw metrics

### Integration Points
- Phase 10 changes must primarily hook into:
  - `run_batch_recourse_eval.py`
  - `run_phase_experiment_suite.py`
  - `run_model_challenger_matrix.py`
  - `ops/kpi_contract.py`
- Candidate-quality raw metrics should continue to originate from batch evaluation and be promoted upward into seeded artifacts
- Impact attribution should anchor to challenger control-versus-champion comparisons and then feed concise derived review text

</code_context>

<deferred>
## Deferred Ideas

- Revisit the canonical source taxonomy if policy logic later becomes a first-class generator family
- Turning candidate-quality metrics into release-blocking gates would be a later phase, not Phase 10
- Building a richer operator dashboard is out of scope for this phase

</deferred>

---
*Phase: 10-candidate-quality-and-trajectory-tuning*
*Context gathered: 2026-03-15*
