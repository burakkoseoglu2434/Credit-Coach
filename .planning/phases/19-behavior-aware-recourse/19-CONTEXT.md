# Phase 19: Behavior-Aware Recourse - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Re-harden the inherited behavior-aware recourse layer so execution-aware ranking stays believable under full-cohort proof and product-surface scrutiny. This phase does not invent a new planner stack, replace the shipped `v1.2` execution model, or override inherited fairness, reliability, telemetry, release, trajectory, offer, or narrative contracts. It clarifies how strongly execution truth should shape ranking, composite handling, provisional branches, and executive evidence.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 13, 17, And 18
- Phase 13 behavior-aware contracts remain authoritative:
  - canonical probability fields stay:
    - `action_execution_probability`
    - `plan_execution_probability`
  - execution scenarios stay:
    - `full_execution`
    - `mixed_execution`
    - `failed_execution`
  - expected utility remains:
    - non-gating
    - ranking or tie-break evidence after eligibility filters
  - the weekly coaching loop remains the canonical execution seam
  - canonical artifacts remain:
    - `behavior_aware_summary.json`
    - `execution_probability_breakdown.csv`
    - `partial_execution_breakdown.csv`
- Phase 17 remains authoritative for proof semantics:
  - portfolio proof, product-ready coverage, and reality-gap audit remain inherited truth
  - execution-aware claims must stay believable under full-cohort evidence
- Phase 18 remains authoritative for product translation:
  - website and analyst surfaces consume engine truth
  - this phase changes behavior-aware truth inputs, not UI-side interpretation logic

### Probability Posture
- Default execution-probability posture should be:
  - balanced
  - with a mild conservative bias
- That conservative bias should become stronger when both of these are true:
  - action burden is high
  - horizon is long
- The estimator should penalize the combined burden or horizon effect more strongly than either factor in isolation.
- When signals are weak or ambiguous, the canonical default should be:
  - write the probability lower rather than higher
- Segment or customer context may lift a low default slightly, but only in a bounded and explicit way.
- The primary protective principle is:
  - avoid false optimism
- The execution layer must not make a fragile plan look easy just to preserve nominal lift or product attractiveness.

### Ranking Leverage
- Low `plan_execution_probability` should produce:
  - strong demotion
- If nominal PD improvement and execution-aware improvement disagree:
  - execution-aware improvement is the dominant ranking signal
- In `high-risk` or denied populations, ranking should become:
  - slightly more execution-aware than the default population behavior
- The winner-selection mental model for this phase is:
  - choose the plan that can be defended in the product with confidence
- Phase 19 should prefer:
  - a plan with believable follow-through
  - over a plan with stronger theoretical uplift but weak expected follow-through

### Composite And Provisional Semantics
- Composite-action groups should aggregate using:
  - a weighted hybrid of minimum and average probability
- This means:
  - the weakest link still matters
  - but the group is not reduced to a pure hard minimum
- If a plan contains both:
  - executable actions
  - approval-dependent or provisional branches
  then the phase should carry:
  - two distinct realization layers
- Those layers should stay explicit rather than collapsing approval-dependence into ordinary execution probability.
- `provisional` or approval-pending plans may remain in the contender pool, but:
  - they should receive a strong penalty
  - they should not be treated like ordinary executable winners
- In offer-bearing but action-heavy plans:
  - action burden remains the dominant behavioral interpretation
  - an offer must not hide that a plan is still difficult to execute

### Evidence And Review Emphasis
- The primary comparison this phase should surface is:
  - nominal improvement vs execution-aware improvement
- The single most important executive risk sentence this phase should make visible is:
  - high uplift but low follow-through
- The most important default segment lens for behavior-aware proof is:
  - `risk_band`
- The default website or demo message for behavior evidence should answer:
  - how much of this plan is realistically executable
- Executive evidence should emphasize realistic completion rather than only theoretical upside.

### Claude's Discretion
- Exact formulas for:
  - the weighted min-average hybrid for composite groups
  - the strength of burden or horizon interaction penalties
  - the size of strong demotion when execution-aware and nominal views diverge
- Exact thresholds and bucket boundaries for:
  - low vs moderate vs high burden
  - short vs medium vs long horizon
  - high-risk execution-aware ranking amplification
- Exact artifact nesting and review copy, as long as:
  - the locked field names remain canonical
  - nominal-vs-execution-aware comparison stays primary
  - risk-band breakout remains first-class

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 19 to be a truth-preserving hardening pass, not a rebuild of the already shipped Phase 13 stack.
- The user explicitly prefers a behavior layer that is balanced but mildly conservative, especially for heavy or long-horizon plans.
- The user wants execution-aware ranking to be strong enough that product-facing winners are defensible, not merely theoretically impressive.
- The user wants composite and provisional plans to remain visible, but not to gain credibility by hiding burden behind offers or approval-dependent branches.
- The user wants the executive behavior-aware story to center on one clear product question:
  - how much of this plan is realistically executable?

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [execution_probability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/execution_probability.py)
  - already owns action-level and plan-level execution probability estimation
  - already handles rankable offers, approval-dependent branches, group-level aggregation, and expected PD improvement
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
  - already contains gate-aware ranking and trajectory-policy scoring
  - is the natural seam for stronger execution-aware demotion behavior
- [loop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/loop.py)
  - already acts as the canonical weekly execution seam
  - already emits execution-rate and scenario truth used downstream
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
  - already emits canonical behavior-aware summary and breakdown artifacts
  - already computes nominal vs execution-aware fields that can be promoted in Phase 19 review
- [portfolio_validation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/portfolio_validation.py)
  - already consumes execution-aware fields for product-ready and reality-gap proof
  - gives this phase a full-cohort downstream validation seam
- [kpi_contract.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/kpi_contract.py)
  - already renders behavior-aware evidence in review language
  - can absorb stronger executive emphasis without redefining the primary release contract

### Established Patterns
- Machine-readable artifacts remain the canonical source of truth; review markdown is derived.
- Gates and eligibility filters still come before ranking or tie-break logic.
- Behavior-aware evidence is mandatory supporting evidence, but not a release-defining hard gate.
- Product and website surfaces should consume engine-side truth rather than add their own execution interpretation.

### Integration Points
- Likely Phase 19 code seams:
  - `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/coaching/loop.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/ops/kpi_contract.py`
- Likely regression coverage seams:
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`
  - `credit-coach/tests/test_batch_candidate_diversity.py`
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_portfolio_validation.py`

</code_context>

<deferred>
## Deferred Ideas

- Reopening sequential phase semantics beyond execution-aware ranking remains Phase 20 work.
- Offer-acceptance modeling changes beyond their interaction with action burden remain outside this phase.
- Any website-only narrative or layout change is out of scope; this phase changes engine truth, not frontend storytelling.

</deferred>

---
*Phase: 19-behavior-aware-recourse*
*Context gathered: 2026-03-19*
