# Phase 33: Action Difficulty & Execution Modeling - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Strengthen the difficulty and follow-through profile of each action so realistic completion becomes part of plan quality. This phase hardens:
- difficulty contract
- action-to-plan execution aggregation
- feasibility vs difficulty boundary
- business vs technical visibility of execution truth

This phase does **not** reopen:
- action taxonomy
- action grouping identity
- numeric target generation posture or contract
- feasibility verdict semantics
- repair vs reject posture
- offer-layer semantics
- expanded product narratives beyond execution-truth wording

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 30 remains authoritative for semantic identity:
  - top-level taxonomy stays `behavioral | structural | institutional`
  - `action_family` is canonical
  - grouped action identity is deterministic
  - `business_view` vs `technical_view` is already engine-owned
- Phase 31 remains authoritative for numeric target generation:
  - actions already carry one canonical `PrimaryNumericTarget`
  - numeric posture is minimum credible change
  - mixed-unit actions expose one primary numeric target plus secondary technical effects
  - this phase must not reopen target generation or clipping posture
- Phase 32 remains authoritative for feasibility truth:
  - canonical action-level verdicts are `valid | clipped | repaired | provisional | invalid`
  - `repair-if-safe, reject-if-semantic-break` is already locked
  - feasibility still answers whether a target can stand
  - this phase starts only after an action remains alive enough to carry execution truth

### Difficulty Contract
- Each action should carry both:
  - `difficulty_score`
  - `difficulty_label`
- The score remains canonical engine truth.
- The label remains the default product-safe expression of that truth.
- Difficulty means:
  - the difficulty of carrying through a valid target
  - not whether the target is feasible
- Locked primary difficulty drivers:
  - `burden`
  - `horizon`
  - `action_class`
  - `coordination_load`
- Institutional or approval-dependent actions stay inside the same difficulty contract.
- But approval-gated truth must also carry a distinct driver:
  - `approval_friction`
- Difficulty should therefore distinguish:
  - customer effort burden
  - outside approval friction

### Action-To-Plan Execution Aggregation
- Plan-level follow-through should stay:
  - `weakest-link aware`
  - but not pure minimum-only
- Locked aggregation posture:
  - action difficulty rolls up to group truth first
  - group truth then rolls up to plan truth
- `action_group_id` remains the canonical grouping seam.
- Grouped actions should contribute one follow-through truth to plan aggregation rather than fragmenting a single business action across multiple plan entries.
- Plan-level execution should remain split into two distinct truths:
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
- Phase 33 should not collapse these into a single combined execution number.
- Plan aggregation must include an explicit load penalty so larger multi-action plans are penalized for coordination burden even when individual actions look reasonable.

### Feasibility vs Difficulty Boundary
- Locked contract:
  - feasibility asks whether the target can stand
  - difficulty asks how hard it is to carry through
- `invalid` or semantic-break actions should not receive difficulty truth.
- Difficulty is emitted only for actions that remain alive enough to matter:
  - `valid`
  - `clipped`
  - `repaired`
  - `provisional`
- `repaired` remains a feasibility verdict first.
- But repaired actions may carry a small additional difficulty burden because softened targets can still imply follow-through friction.
- `provisional` remains inside the difficulty contract.
- But Phase 33 must keep these dimensions separate:
  - customer effort
  - approval friction
- This prevents dependency-gated actions from being mislabeled as pure user-execution burden.

### Business vs Technical Visibility Of Execution Truth
- Business-facing default action output should show:
  - `difficulty_label`
  - a short follow-through note
- Raw action-level probabilities should not appear in the default business view.
- Business-facing default plan output should show:
  - a `follow_through_readiness` style label
  - a short risk sentence
- Plan-level business wording should remain narrative rather than numeric.
- The product default should therefore say things like:
  - the plan is realistically executable
  - the plan needs disciplined follow-through
  - expected effect falls if follow-through weakens
- Minimum technical reveal set:
  - `difficulty_score`
  - `difficulty_label`
  - `action_execution_probability`
  - `action_group_execution_probability`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - `difficulty_drivers`
  - `approval_friction`
- Low execution truth must be described:
  - honestly
  - but not alarmistically
- Business wording should explicitly surface execution risk without using model jargon or raw internal penalty language.

### Claude's Discretion
- Exact internal thresholding for `difficulty_label` bands as long as labels remain deterministic and stable
- Exact field names for action-level and plan-level execution notes as long as business and technical visibility stay clearly separated
- Exact weighting of burden, horizon, action class, coordination load, and approval friction as long as:
  - weakest-link-aware plan aggregation is preserved
  - load penalty remains explicit
  - approval friction stays distinct from customer effort
- Exact narrative wording for follow-through notes and risk sentences as long as the tone remains:
  - business-safe
  - honest
  - non-alarmist

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 33 to stop conflating these two ideas:
  - a target is feasible
  - a target is easy to execute
- A numerically valid target may still be hard to sustain in real customer behavior, and Phase 33 should make that visible.
- The phase should preserve the already-shipped execution-aware stack while upgrading it from implicit probability heuristics into a clearer difficulty contract.
- Product output should not default to raw probability percentages.
- Instead, the product should express execution truth as:
  - difficulty labels
  - follow-through readiness
  - short risk wording
- Technical surfaces should still retain the full action, group, and plan execution probability traces for analyst and validation use.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [execution_probability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/execution_probability.py)
  - is already the primary seam for action-level and plan-level execution probability estimation
  - already models:
    - `action_class` anchors
    - burden and horizon pressure
    - customer context adjustment
    - semantic ambiguity penalties
    - group-level hybrid aggregation
    - plan-level load penalty
  - is the natural place to add a clearer `difficulty` contract without reopening feasibility logic
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries:
    - `action_execution_probability`
    - `approval_dependent_probability`
    - `action_group_execution_probability`
    - `plan_execution_probability`
    - `approval_dependent_plan_probability`
  - is the correct seam to make difficulty and execution visibility canonical
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
  - already gives execution-aware truth strong leverage in plan ranking
  - already penalizes:
    - low execution probability
    - nominal vs expected improvement gaps
    - weak early health
    - provisional and repaired plans
  - should consume the hardened Phase 33 truth without redefining feasibility
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already passes plan execution truth into technical reveal and narratives
  - is the main seam for business-safe difficulty labels and follow-through wording
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
  - already serializes action and plan execution probabilities into runtime artifacts
  - should emit the new difficulty contract without pushing UI interpretation downstream
- [portfolio_validation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/portfolio_validation.py)
  - already treats execution-aware value as a proof metric
  - should remain aligned with the hardened difficulty/execution truth rather than inventing separate semantics

### Established Patterns
- Phase 19 and Phase 20 already established that:
  - execution-aware truth should outrank nominal-only optimism
  - weak early health should remain visible
  - high uplift but low follow-through is a first-class review risk
- Phase 30 established the product-safe rule that business defaults should not leak raw technical identifiers.
- Phase 32 established the feasibility visibility rule:
  - business-facing defaults show outcome labels
  - technical layers keep trace detail
- Phase 33 should mirror that pattern for execution truth:
  - business-facing difficulty/readiness summary
  - technical execution trace underneath

### Integration Points
- Primary engine seams for Phase 33:
  - `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - `credit-coach/src/credit_coach/data/schema.py`
- Important downstream consumers to keep aligned:
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`

</code_context>

<deferred>
## Deferred Ideas

- Explicit institution offer terms and offer-layer contract belong to Phase 34
- Narrative Generation v2 belongs to Phase 35
- Product-surface rollout for the hardened difficulty contract belongs to Phase 36
- Portfolio proof for personalized numeric action impact belongs to Phase 37
- Calibration and false-optimism validation belongs to Phase 38
- Pilot integration belongs to Phase 39

</deferred>

---
*Phase: 33-action-difficulty-execution-modeling*
*Context gathered: 2026-03-21*
