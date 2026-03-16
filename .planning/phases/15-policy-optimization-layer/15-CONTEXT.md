# Phase 15: Policy Optimization Layer - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate institution-side offer optimization into the existing recourse engine so offer-bearing plans can be represented, ranked, and evaluated beside user-driven recourse actions. This phase builds on the Phase 12 institutional action contract, Phase 13 behavior-aware probability contract, and Phase 14 sequential trajectory contract. It does not weaken inherited fairness, reliability, telemetry, or milestone-acceptance governance, and it does not yet introduce learned off-policy optimization or full outcome-learning loops reserved for Phase 16.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-14
- Phase 8 through Phase 11 governance remains authoritative:
  - fairness, reliability, telemetry, and release evidence contracts are inherited guardrails
  - offer optimization cannot override those gates
- Machine-readable artifacts remain the canonical source of truth
- Markdown review remains derived and explanation-first rather than dashboard-like
- Phase 12 action contract remains authoritative:
  - typed actions stay `hybrid`
  - `action_key` is user-facing
  - `feature_name` remains the effect anchor
  - composite actions stay grouped under `action_group_id`
  - institutional placeholders without explicit terms remain provisional non-winner evidence
- Phase 13 probability contract remains authoritative:
  - `plan_execution_probability` remains the customer-action realization signal
  - behavior-aware evidence remains mandatory supporting, non-blocking evidence
- Phase 14 trajectory contract remains authoritative:
  - `phases[]` is the canonical trajectory layer
  - weekly loop remains the canonical simulation grain
  - short-term-first optimization and review-boundary transition logic stay intact

### Offer Action Contract
- Offer actions remain under `action_class = institutional`
- Phase 15 adds a second semantic layer on top:
  - `offer_type`
  - `offer_terms`
- Institutional action remains the broad class
- Offer becomes a scored, term-bearing subfamily of institutional actions
- Mixed plans may contain:
  - user-driven actions
  - plus at most one active institution-side offer branch
- A winner plan must not contain multiple competing active offers
- An offer may enter ordinary winner ranking only if:
  - terms are explicit
  - approval state is explicit
  - it can participate in ordinary expected-utility computation
- Term-incomplete or approval-ambiguous institutional actions remain:
  - `provisional`
  - non-winner
  - reason-coded evidence
- Minimum offer-term schema must be able to carry:
  - `offer_type`
  - `payment_delta_monthly`
  - `discount_amount` or `discount_pct`
  - `term_extension_months`
  - `interest_rate_delta`
  - `grace_period_weeks`
  - `requires_acceptance`
  - `requires_institutional_approval`
  - strongly recommended companion flag: `offer_terms_complete`

### Recovery Objective Contract
- Phase 15 primary business objective is:
  - `expected_recovery_proxy`
- The canonical recovery proxy set is:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- Phase 15 may use a weighted composite internally for optimizer ranking:
  - `approval_rate` contributes positively
  - `default_rate_90d` contributes negatively
  - `avg_margin_90d` contributes positively
- Review and evidence artifacts must still explain recovery impact metric-by-metric rather than only through one opaque score
- Ranking order stays governance-first:
  - inherited gates first (`fairness`, `reliability`, `telemetry`, `action realism`, `trajectory health`)
  - then nominal feasibility and short-term trajectory health
  - then `expected_recovery_proxy`
- Offer optimization only counts as “good” when:
  - recovery proxy composite improves
  - fairness and reliability do not regress
  - trajectory health does not worsen
- Margin gain alone is not sufficient if governance or trajectory safety worsens

### Offer Acceptance Probability Contract
- Canonical probability units are distinct:
  - `plan_execution_probability`
  - `offer_acceptance_probability`
- These must not be collapsed into one field because they model different real-world behaviors
- For offer-bearing plans:
  - `combined_plan_realization_probability = plan_execution_probability × offer_acceptance_probability`
- Review and artifacts must still show:
  - plan execution probability
  - offer acceptance probability
  - combined realization probability
  separately
- The Phase 15 initial offer-acceptance estimator may remain lightweight and replaceable
- The initial input family should be limited to:
  - `offer_type`
  - `offer_terms`
  - `action_burden`
  - `risk_band`
  - `income_band`
  - `stress_band`
  - short-term trajectory health
  - approval state
- Real acceptance history is not required until Phase 16

### Policy Arm Semantics
- `policy_arm` may now represent offer-policy profiles rather than only bare `control` / `treatment`
- Outcome feedback still defaults to `treatment vs control` language
- But machine-readable artifacts must make arm meaning explicit, for example through:
  - `offer_family`
  - `scoring_profile`
  - `term_generation_rule`
- Example future arm semantics may include:
  - conservative discount policy
  - aggressive discount policy
  - installment-first policy
  - settlement-first policy

### Offer Evidence Surface
- Phase 15 must introduce one canonical machine-readable artifact:
  - `offer_optimization_summary.json`
- Minimum canonical metric set:
  - `offer_plan_rate`
  - `rankable_offer_rate`
  - `offer_acceptance_probability_mean`
  - `combined_plan_realization_probability_mean`
  - `expected_recovery_proxy`
  - `approval_rate_proxy_delta`
  - `default_rate_90d_proxy_delta`
  - `avg_margin_90d_proxy_delta`
  - `governance_safe_offer_rate`
  - `dominant_offer_type`
- Required companion breakdown artifacts:
  - `offer_type_breakdown.csv`
  - `offer_policy_arm_breakdown.csv`
  - `offer_acceptance_breakdown.csv`
  - `offer_proxy_impact_breakdown.csv`
- Phase 15 evidence is:
  - mandatory supporting evidence
  - non-blocking
  - not a second release gate
- The review surface should add a short `Offer Optimization Summary` section that highlights:
  - offer mix
  - mean acceptance
  - combined realization
  - proxy deltas
  - governance-safe offer rate
  - dominant offer type

### Claude's Discretion
- Exact JSON nesting for `offer_terms` as long as the locked minimum fields stay explicit and testable
- Exact weighting used inside `expected_recovery_proxy` as long as the canonical proxy set and signed directions stay stable
- Exact heuristic form of the initial `offer_acceptance_probability` estimator as long as it remains explicit and replaceable
- Exact review wording for `Offer Optimization Summary` as long as the required signals remain visible and explanation-first

</decisions>

<specifics>
## Specific Ideas

- Offer optimization should make institution-side relief visible as a real planning primitive rather than an opaque side condition.
- A reviewer should be able to tell whether a plan is weak because the offer is unlikely to be accepted, because the customer actions are hard to execute, or both.
- Mixed plans should look like one coherent trajectory: customer actions plus one explicit institution-side offer branch.
- Policy-arm reporting should explain what changed in the offer strategy, not just that a treatment arm exists.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already contains institutional action templates such as `credit_limit_adjustment`, `settlement_discount`, and `installment_plan`
  - is the natural seam for promoting certain institutional actions into explicit offer-bearing actions
- `credit-coach/src/credit_coach/data/schema.py`
  - already carries typed action, probability, trajectory, and `policy_arm` fields
  - is the right seam for adding `offer_type`, `offer_terms`, and offer-specific probability fields
- `credit-coach/src/credit_coach/coaching/planner.py`
  - already applies gate-first, behavior-aware, and phase-aware ranking
  - is the right seam for adding `expected_recovery_proxy` ordering after existing safety and trajectory filters
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits candidate-quality, behavior-aware, and trajectory summaries
  - is the natural owner for `offer_optimization_summary.json` and companion breakdowns
- `credit-coach/src/credit_coach/storage/repository.py`
  - already computes the canonical business proxy deltas `approval_rate`, `default_rate_90d`, and `avg_margin_90d`
  - provides the right baseline for Phase 15 recovery-proxy semantics
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already publishes machine-readable policy-arm summaries and delta artifacts
  - should remain compatible with richer offer-policy arm meanings
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders explanation-first milestone review sections
  - is the right seam for a future `Offer Optimization Summary` review block

### Established Patterns
- Canonical machine-readable evidence lives under `artifacts/runs/<run_id>/tables/`
- Supporting evidence is aggregated through batch, suite, challenger, and milestone-review seams without redefining the primary acceptance contract
- Business impact proxies already use:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- Policy-arm comparison language is already standardized around `treatment vs control`
- Institutional actions already carry approval and conflict semantics from Phase 12, which Phase 15 should extend rather than bypass

### Integration Points
- Phase 15 changes should primarily hook into:
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - `credit-coach/src/credit_coach/storage/repository.py`
  - `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
- Regression coverage should extend through:
  - `credit-coach/tests/test_action_space.py`
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`
  - `credit-coach/tests/test_batch_candidate_diversity.py`
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_challenger_matrix_selection.py`
  - and new Phase 15 tests around offer ranking, acceptance probability, and recovery-proxy evidence

</code_context>

<deferred>
## Deferred Ideas

- Learned offer-acceptance models grounded in real historical acceptance remain Phase 16 work
- Off-policy evaluation and online learning of offer strategies remain Phase 16 work
- Full borrower-facing offer presentation UX remains outside this milestone
- Any fully autonomous production promotion of offer policies remains later-stage work

</deferred>

---
*Phase: 15-policy-optimization-layer*
*Context gathered: 2026-03-16*
