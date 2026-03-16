# Phase 16: Outcome Feedback & Learning Loop - Context

**Gathered:** 2026-03-16
**Status:** Ready for replanning

<domain>
## Phase Boundary

Complete the learning loop by extending decision logging, normalizing delayed real-world outcomes, and adding confidence-aware off-policy evaluation on top of the existing outcome-feedback path. This phase builds on the Phase 11 outcome-feedback and release-evidence contracts and the Phase 15 offer-policy semantics. It does not weaken inherited fairness, reliability, telemetry, or acceptance governance, and it does not yet introduce autonomous online learning or automatic production policy promotion.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-15
- Phase 8 through Phase 11 governance remains authoritative:
  - fairness, reliability, telemetry, and release evidence contracts are inherited guardrails
  - learning-loop evidence cannot override those gates
- Machine-readable artifacts remain the canonical source of truth
- Markdown review remains derived and explanation-first rather than dashboard-like
- Phase 11 outcome-feedback comparison language remains authoritative:
  - primary comparative framing is `treatment vs control`
  - if the control arm is missing:
    - `comparison_status = baseline_missing`
    - confidence must downgrade
    - outputs fall back to descriptive-only summaries rather than strong comparative claims
- Phase 11 canonical proxy set remains authoritative:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- Phase 15 offer-policy semantics remain authoritative:
  - `policy_arm` may represent richer offer-policy profiles
  - `plan_execution_probability` remains distinct from `offer_acceptance_probability`
  - offer-policy evidence is already supporting, non-blocking
- Phase 16 is additive to those contracts; it completes the learning loop without defining a second release path

### Decision Logging Contract
- The canonical logged decision unit should stay compact and learning-grade rather than embedding a full raw plan snapshot
- The decision log is a compact learning ledger, not the canonical plan artifact
- Minimum canonical identity and policy fields are:
  - `decision_id`
  - `selected_plan_id`
  - `candidate_set_id`
  - `policy_arm`
  - `policy_arm_profile`
  - `selection_propensity`
  - `propensity_source`
  - `reason_codes`
- Minimum recommendation-context fields are:
  - `selected_plan_status`
  - `selected_offer_type` when present
  - `plan_execution_probability`
  - `offer_acceptance_probability` when present
  - `combined_plan_realization_probability` when present
  - `recommended_plan_flag`
- Strongly preferred companion context fields are:
  - `selected_plan_policy_label`
  - `trajectory_status`
- `selection_propensity` is a required canonical field for every logged decision
- If true randomized propensity is not available, the system must still log an explicit fallback propensity plus `propensity_source`
- The full raw plan snapshot must not be duplicated into the decision log
- Full plan truth remains in:
  - persisted plan records
  - canonical run artifacts
- The decision log should instead reference those sources through stable identifiers

### Outcome Completeness Semantics
- Completeness should be graded rather than binary
- Canonical completeness levels are:
  - `descriptive_only`
  - `partial_learning_ready`
  - `learning_ready`
- `learning_ready` requires at minimum:
  - a complete decision log
  - sufficient delayed reward-proxy outcome coverage
  - present policy metadata including:
    - `selection_propensity`
    - `policy_arm`
- Richer signals such as action completion or offer acceptance should improve learning richness but are not required for every record to count as `learning_ready`
- Missing richer signals must not automatically discard the record
- Canonical coverage dimensions that should be explicit are:
  - `has_action_completion`
  - `has_offer_acceptance`
  - `has_payment_behavior`
  - `has_recovery_outcome`
- Completeness should therefore be visible by dimension rather than hidden behind one aggregate failure reason
- The canonical primary learning window is:
  - `90d`
- `30d` and `60d` remain supporting early signals, but default `learning_ready` semantics should be anchored on the 90-day reward window

### Off-Policy Reward Contract
- Phase 16 off-policy evaluation should be proxy-vector-first rather than collapsing everything into one hidden reward
- Canonical reward axes are:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- Internal composite rewards may be used inside estimators or ranking helpers, but machine-readable artifacts and review must stay metric-by-metric
- Primary baseline for IPS / Doubly Robust reporting is:
  - `control`
- If control is missing:
  - `comparison_status = baseline_missing`
  - `ope_confidence = tentative`
  - outputs should be descriptive-only rather than strong comparative claims
- OPE confidence must downgrade when evidence quality is weak, including cases such as:
  - missing or weak propensities
  - low reward coverage
  - severe arm imbalance
  - low effective sample size
- OPE remains:
  - mandatory supporting evidence
  - non-blocking
  - not a release-gate override

### Learning Review Surface
- Phase 16 should add a new derived markdown section:
  - `Learning Loop Summary`
- This section should remain separate from `Outcome Feedback Summary`
- The separation is intentional:
  - `Outcome Feedback Summary` answers “what happened?”
  - `Learning Loop Summary` answers “what can we reliably learn from it?”
- `Learning Loop Summary` should default to showing:
  - `decision_log_completeness`
  - `learning_readiness_status_distribution`
  - `reward_90d_coverage`
  - `ope_confidence`
  - `preferred_policy_signal` when available
- OPE review language should use concise metric-by-metric labels such as:
  - `supports_control`
  - `supports_treatment`
  - `mixed`
  - `insufficient_evidence`
- The section should also expose:
  - `ope_confidence = strong | tentative | degraded`
- Canonical machine-readable learning artifacts should live as supporting artifacts, for example:
  - `decision_logging_summary.json`
  - `outcome_ingestion_summary.json`
  - `off_policy_evaluation.json`
- These artifacts should be referenced from `release_evidence_pack.json`
- Markdown remains derived explanation only; JSON and CSV remain the source of truth

### Claude's Discretion
- Exact JSON nesting for decision-log companion metadata as long as the locked canonical fields remain explicit and testable
- Exact formulas for heuristic fallback propensity generation as long as `selection_propensity` and `propensity_source` are always present
- Exact thresholds for “low” effective sample size, arm imbalance, or weak coverage as long as confidence degradation is deterministic and reviewable
- Exact phrasing of the `Learning Loop Summary` markdown as long as the required signals and labels remain visible

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants the decision log to behave like a compact learning ledger rather than a bloated plan archive
- Completeness should describe what data is missing, not merely collapse records into usable vs unusable
- OPE should stay comparative and cautious; strong policy claims require both baseline availability and data-quality confidence
- Review should make learning readiness obvious without collapsing into a dashboard dump

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/data/schema.py`
  - already contains `DecisionOutcomeRecord`
  - already contains Phase 13-15 plan, probability, offer, and trajectory fields that decision logging can reference instead of duplicating
- `credit-coach/src/credit_coach/storage/models.py`
  - already contains `DecisionOutcomeORM`
  - is the current persistence seam for delayed outcome storage
- `credit-coach/src/credit_coach/storage/repository.py`
  - already owns:
    - `save_decision_outcome`
    - `summarize_decision_outcomes`
    - `compute_policy_outcome_deltas`
    - `_policy_arm_profile`
  - already computes metric-by-metric treatment-vs-control proxy deltas
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already ingests CSV-delayed outcomes
  - already emits:
    - `outcome_policy_summary.csv`
    - `outcome_policy_deltas.json`
    - `outcome_feedback_summary.json`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already mirrors `outcome_feedback_summary.json`
  - already threads optional supporting artifacts into `release_evidence_pack.json`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders an explanation-first `Outcome Feedback Summary`
  - already normalizes supporting-artifact references for milestone review
- `credit-coach/src/credit_coach/recourse/generator.py`
  - already carries `reason_codes` in generation details, which is a reusable seam for compact learning-ledger fields

### Established Patterns
- Canonical evidence lives under `artifacts/runs/<run_id>/tables/`
- JSON and CSV are the source of truth; markdown is derived
- `supporting_artifacts` is the established bridge from compact summaries to deeper evidence
- Policy-arm reporting already distinguishes arm-level semantics from concise human-readable review
- Plan records already act as canonical rich plan truth, so learning logs do not need to duplicate that payload

### Integration Points
- Decision logging expansion should primarily hook into:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/storage/models.py`
  - `credit-coach/src/credit_coach/storage/repository.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- Outcome completeness and ingestion should primarily hook into:
  - `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - `credit-coach/src/credit_coach/storage/repository.py`
- OPE should likely enter through a dedicated evaluation module under:
  - `credit-coach/src/credit_coach/evaluation/`
- Review-surface integration should continue through:
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/ops/kpi_contract.py`

### Brownfield Risks
- The repo still lacks a formal migration framework, so persistence changes should stay additive and audit-safe
- No off-policy evaluation module exists yet, so Phase 16 must create one without entangling release-gate logic
- Current delayed outcome storage is still too thin for learning-grade policy evaluation until new context fields are added

</code_context>

<deferred>
## Deferred Ideas

- Full online randomized experimentation and stop-rule orchestration remain future work beyond Phase 16
- Automatic production promotion from learning-loop evidence remains out of scope
- A fuller operator dashboard for learning readiness remains future productization work rather than a Phase 16 requirement

</deferred>

---
*Phase: 16-outcome-feedback-learning-loop*
*Context gathered: 2026-03-16*
