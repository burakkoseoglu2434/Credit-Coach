# Phase 57: Heuristic / Institution Action Lane - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 57 introduces a deterministic Heuristic / Institution Action Lane that can generate institution-assisted and hybrid recourse actions which are not safely DICE-generatable, while still flowing through the same `PlanAction` contract and the same trust-preserving downstream surfaces.

This phase owns:
- a new deterministic non-DICE candidate lane for institution and hybrid actions
- first-wave institution / hybrid action generation for:
  - `credit_limit_adjustment`
  - `debt_consolidation`
  - `settlement_discount`
  - `installment_plan`
  - institution-triggered offer variants
  - hybrid actions that require both customer participation and institution approval
- explicit offer / institution contract semantics for heuristic candidates
- deterministic feasibility / generation rules for those actions
- integration of heuristic-lane candidates into the existing contender pool
- validity, semantic quality, and contender-eligibility rules for the new lane
- regression proof that winner integrity, selected-surface consistency, operator packet coherence, and DICE quality enforcement remain intact

This phase does not own:
- planner redesign
- decision-threshold changes
- validity-taxonomy redesign
- trust-rule relaxation
- probabilistic or fuzzy institution promises
- DICE contract expansion beyond what Phase 56 already locked
- changes to canonical action taxonomy
- changes to feature-to-action mapping semantics

Guardrail:
- Phase 57 must expand reachable solution space by adding deterministic institution/hybrid candidates, not by relaxing the v2.2 trust baseline or widening planner semantics.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 57

- Phase 57 adds a dedicated heuristic candidate generator for institution-owned and hybrid actions that sit outside the safe DICE runtime contract.
- The new lane must serialize into the existing `PlanAction` schema, including:
  - canonical `action_key`
  - legacy `action_class`
  - legacy `action_family`
  - `primary_numeric_target` when required
  - `offer_contract` when institution-side terms or approval semantics are present
- The lane must produce deterministic, auditable candidate plans, not open-ended policy speculation.
- The lane may coexist with DICE and internal plans in the same candidate pool, but it must not change how the planner ranks or chooses among eligible contenders.

### 2. Problem Statement

- Phase 56 made the DICE lane safer and more semantically complete, but it is intentionally limited to customer-controllable or near-customer actions.
- High-impact movement paths that can break the `structural_cohort_limited` ceiling remain unavailable or under-represented when they require:
  - institution approval
  - institution-generated terms
  - structured hardship relief
  - hybrid customer-plus-institution execution
- The system already contains offer contracts, approval states, institution-condition messaging, and institutional action semantics, but it does not yet have a dedicated lane that deterministically generates those candidates as planner contenders.
- Phase 57 closes that gap while keeping all trust rules intact.

### 3. First-Wave Action Types To Introduce

#### `credit_limit_adjustment`

- canonical action key: `credit_limit_adjustment`
- action owner: `institution`
- offer / approval requirement:
  - `offer_required_flag = true`
  - institution approval required
- role in Phase 57:
  - institution-assisted utilization-capacity relief path
  - deterministic candidate for customers whose utilization pressure cannot be credibly relieved by customer-only movement

#### `debt_consolidation`

- canonical action key: `debt_consolidation`
- action owner: `hybrid`
- offer / approval requirement:
  - `offer_required_flag = true`
  - institution approval typically required when the recommendation assumes new structured terms, refinancing intake, or consolidation shell support
- role in Phase 57:
  - structured multi-balance relief path
  - first-wave hybrid route for profiles with fragmented revolving pressure

#### `settlement_discount`

- canonical action key: `settlement_discount`
- action owner: `institution`
- offer / approval requirement:
  - `offer_required_flag = true`
  - institution approval required
  - customer acceptance required
- role in Phase 57:
  - controlled delinquency / collections relief path
  - should only surface when the system can state the institution-side dependency explicitly

#### `installment_plan`

- canonical action key: `installment_plan`
- action owner: `institution`
- offer / approval requirement:
  - `offer_required_flag = true`
  - institution approval required
  - customer acceptance required
- role in Phase 57:
  - institution-triggered delinquency resolution path
  - should be prioritized ahead of settlement when structured repayment remains viable

#### Institution-triggered offer actions

- these are not new taxonomy keys; they are first-wave generation patterns for existing institution-side actions whose serialized truth depends on `offer_contract`
- initial covered set:
  - `credit_limit_adjustment`
  - `settlement_discount`
  - `installment_plan`
- lock:
  - Phase 57 should not invent generic opaque "institution offer" actions without a canonical action key

#### Hybrid actions

- initial first-wave hybrid coverage:
  - `debt_consolidation`
  - optionally hybrid serialization of refinance-like restructuring only if the action key remains canonical and planner semantics do not change
- hybrid meaning in Phase 57:
  - the customer must participate materially
  - but the movement also depends on institution cooperation, approval, or structured terms

### 4. Action-Type Contract By Category

#### `credit_limit_adjustment`

- `action_owner`: `institution`
- requires offer / approval: yes
- feasibility conditions:
  - there is material utilization pressure or capacity shortfall
  - a deterministic limit gap can be computed from current vs target capacity
  - the needed increase does not exceed the bounded feasibility cap already enforced by feasibility rules
  - no conflicting hardship action in the same candidate group
- required fields:
  - `primary_numeric_target`
  - `offer_contract`
  - `requires_institutional_approval = true`
  - `institutional_approval_state = pending` by default unless a concrete approved contract exists
  - `institution_condition`
  - `offer_feasibility`

#### `debt_consolidation`

- `action_owner`: `hybrid`
- requires offer / approval: yes in Phase 57 when the recommendation assumes institution-facilitated structure
- feasibility conditions:
  - fragmented revolving or total balance pressure is materially present
  - the profile is not already best represented by pure settlement relief
  - there is enough stability signal to avoid generating a fake restructure path for clearly non-viable files
  - the action can be expressed as one canonical action with one primary target and optional support features
- required fields:
  - `primary_numeric_target`
  - `offer_contract` when the path assumes structured institution-side terms
  - `institution_condition`
  - `offer_feasibility`
  - explicit hybrid ownership carried through serialization

#### `settlement_discount`

- `action_owner`: `institution`
- requires offer / approval: yes
- feasibility conditions:
  - collections / settlement-linked stress is explicitly present
  - the proposed discount direction is bounded and deterministic
  - installment relief is either unavailable, inferior, or conflict-tagged for the same customer state
- required fields:
  - `primary_numeric_target`
  - `offer_contract`
  - `requires_acceptance = true`
  - `requires_institutional_approval = true`
  - `institution_condition`
  - `offer_feasibility`

#### `installment_plan`

- `action_owner`: `institution`
- requires offer / approval: yes
- feasibility conditions:
  - active delinquency or recent collections pressure is present
  - the action is anchored by `delinq_amnt` or an equivalent primary delinquency metric
  - the customer has enough payment stability signal to make structured repayment directionally coherent
- required fields:
  - `primary_numeric_target`
  - `offer_contract`
  - `requires_acceptance = true`
  - `requires_institutional_approval = true`
  - `institution_condition`
  - `offer_feasibility`

### 5. Heuristic Generation Rules

Generation in Phase 57 must be action-led and deterministic, not model-free guesswork.

#### General generation contract

- the heuristic lane should evaluate the mapped feature space and customer context against explicit trigger rules
- each first-wave canonical action should have:
  - deterministic trigger criteria
  - deterministic primary-feature anchor
  - deterministic target-generation rule
  - deterministic "do not generate" exclusions
- output should be a bounded list of candidate actions / plans, not an unbounded expansion sweep

#### Trigger rules by action

`credit_limit_adjustment`
- trigger when:
  - utilization stress is materially high
  - current limit features show a deterministic capacity shortfall
  - a limit increase would reduce utilization pressure more credibly than a customer-only paydown path
- numeric target definition:
  - target should be the minimum deterministic additional capacity needed to move the relevant utilization measure into the bounded safe band
  - increase magnitude must honor existing limit-adjustment feasibility caps
- do not generate when:
  - current limit is missing or non-positive in a way that prevents deterministic targeting
  - the required increase exceeds the bounded feasibility cap
  - the same candidate pool already includes a stronger non-conflicting utilization relief path that does not require fake institutional assumptions

`debt_consolidation`
- trigger when:
  - revolving / fragmented debt pressure is high across mapped support features
  - the pressure pattern indicates structure, not just one isolated metric excursion
  - a canonical consolidation action can be anchored to one primary target feature
- numeric target definition:
  - use the primary impacted balance feature as the numeric anchor
  - supporting features may annotate context but may not create separate standalone actions
- do not generate when:
  - the pressure signal is too weak or too localized
  - a conflict action such as settlement would produce a more coherent institution path
  - there is no deterministic primary target

`settlement_discount`
- trigger when:
  - collections / settlement-linked features indicate active burden that can only move through institution relief
  - the file is already in a hardship-like state where a discount action is semantically coherent
- numeric target definition:
  - derive the target as a bounded reduction from the current collections-linked amount
  - the reduction must serialize into canonical settlement offer terms, not a freeform text promise
- do not generate when:
  - no collections-linked burden is present
  - installment-plan relief is clearly the cleaner first-wave path
  - conflict tags prohibit coexistence with the installment-plan candidate

`installment_plan`
- trigger when:
  - `delinq_amnt` or linked delinquency features are materially elevated
  - the state looks suitable for structured repayment relief rather than terminal settlement
- numeric target definition:
  - anchor to `delinq_amnt`
  - supporting features such as `acc_now_delinq` and `collections_12_mths_ex_med` may adjust terms or notes but not replace the primary target
- do not generate when:
  - there is no delinquency burden to resolve
  - prerequisite stability tags are missing
  - settlement is the only semantically coherent hardship action

### 6. Offer / Institution Contract

Phase 57 should standardize three deterministic contract fields at the action level, even if some are additive wrappers around already existing schema primitives.

#### `offer_required_flag`

- meaning:
  - this action cannot be treated as a self-contained customer-executable step
  - a real institution-side offer, approval, or terms package is required for truthful rendering
- expected derivation:
  - true whenever `offer_contract` is required for semantic completeness
  - in first wave, this is true for:
    - `credit_limit_adjustment`
    - `settlement_discount`
    - `installment_plan`
    - institution-facilitated `debt_consolidation`

#### `institution_condition`

- meaning:
  - the human-readable statement of what institution-side condition must occur for the action to be real
- expected behavior:
  - always rendered separately from `primary_recommendation`
  - must describe dependency, not promise outcome
  - examples:
    - additional credit capacity must be approved
    - a structured installment offer must be activated
    - a settlement discount must be approved and accepted

#### `offer_feasibility`

- meaning:
  - deterministic machine-readable truth about whether the institution-side action is:
    - `active_rankable`
    - `provisional`
    - `inactive`
    - or absent
- preferred implementation:
  - reuse or align with the existing offer maturity / approval vocabulary instead of inventing a separate freeform status family
- effect:
  - determines whether an institution action can enter normal contention or only appear as a diagnostic / provisional candidate shell

#### Selection / rendering / operator-packet effects

- selection:
  - institution or hybrid actions may only compete if their contract is sufficiently complete for contender eligibility
  - provisional or approval-shell-only actions may remain visible diagnostically but must not masquerade as fully active winners
- rendering:
  - `primary_recommendation` stays customer-readable and action-focused
  - `institution_condition` carries the institution dependency separately
  - offer-bearing actions must serialize through `offer_contract`
- operator packet:
  - operator packet must continue to project `selected_recommendation_text` and `selected_institution_condition` cleanly
  - no institution-side action should appear without a coherent institution condition when the action depends on approval or offer terms

### 7. Integration With Existing System

#### How heuristic actions map into `PlanAction`

- every heuristic candidate must populate the normal `PlanAction` surface rather than a sidecar structure
- required baseline:
  - `feature_name`
  - `current_value`
  - `target_value`
  - `delta`
  - `time_months`
  - `action_key`
  - `action_class`
  - `action_family`
  - `action_title`
  - `action_group_id`
  - `checkpoint_metric`
- required when applicable:
  - `primary_numeric_target`
  - `offer_contract`
  - `requires_institutional_approval`
  - `institutional_approval_state`
  - `requires_acceptance`
  - `approval_pending_semantic_only`

#### Recommendation validity

- heuristic-lane actions must pass the same recommendation validity system
- institution/hybrid actions must not fail the existing customer-vs-institution labeling checks
- numeric targets must still be directionally valid and bounded

#### DICE-style semantic quality or equivalent

- Phase 57 should introduce a lane-equivalent semantic-quality gate for heuristic institution candidates instead of overloading DICE naming if that becomes misleading
- the gate should enforce:
  - annotation completeness
  - renderability
  - institution-role correctness
  - primary-target completeness
  - offer-contract completeness where required
  - conflict / prerequisite sanity

#### Contender eligibility

- heuristic institution candidates can compete only if:
  - they are not invalid under recommendation validity
  - their semantic-quality status is not invalid
  - their action set is actionable after feasibility / constraint processing
  - any required institution / offer contract is complete enough for their allowed maturity bucket
- approval-shell-only candidates may remain visible in diagnostics, but they must not silently bypass contender gating

#### Coexistence with DICE candidates

- the candidate pool should contain:
  - internal plans
  - DICE plans
  - heuristic institution/hybrid plans
- planner semantics stay unchanged:
  - Phase 57 only expands which candidates enter the pool
  - it does not change how winners are selected

### 8. Risks And Guardrails

#### Prevent fake or unrealistic institution promises

- institution-side actions must never read like guaranteed approvals unless the contract says `approved`
- `institution_condition` must describe dependency and feasibility, not certainty
- if terms are incomplete or approval is pending, the action must serialize as provisional or otherwise non-rankable under the existing offer truth

#### Prevent heuristic spam

- generation must be bounded by explicit first-wave action types
- one customer should not receive a spray of overlapping institution actions from the same hardship family
- conflict-tag and prerequisite-tag semantics from the canonical action catalog remain active
- grouped/supporting features may enrich an action, but must not multiply it into duplicate near-identical contenders

#### Keep trust baseline intact

- winner integrity remains hard-stop protected
- selected-surface consistency must continue to separate consumer-facing decision status from technical status
- operator packet coherence must continue to render institution conditions deterministically
- DICE quality enforcement must remain unchanged for DICE candidates
- heuristic institution actions must not lower the bar relative to DICE; they need an equivalent or stricter completeness rule where institution truth is involved

### 9. Required Outputs And Artifacts

- Engine / contract files likely involved:
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/recourse/offer_optimization.py`
  - `credit-coach/src/credit_coach/recourse/recommendation_validity.py`
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
- Downstream surface files to verify, even if only transitively touched:
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/ops/operator_review.py`
- Tests likely required:
  - new heuristic-lane candidate tests
  - recommendation-validity tests for institution/hybrid actions
  - selected-surface consistency regressions
  - operator-packet coherence regressions
  - winner-integrity regressions
  - DICE-lane non-regression proof
- Planning artifacts:
  - `57-RESEARCH.md`
  - `57-VALIDATION.md`
  - `57-01-PLAN.md`
  - `57-02-PLAN.md`
  - `57-03-PLAN.md`
  - `57-SUMMARY.md`
  - `57-VERIFICATION.md`

### 10. Acceptance Criteria

- new institution / hybrid candidate categories appear in the candidate pool under deterministic generation rules
- at least some structurally constrained customers receive institution or hybrid candidate paths that were previously unavailable
- every first-wave heuristic action serializes through the normal `PlanAction` contract
- every offer-bearing action carries a coherent institution-side contract
- institution/hybrid actions pass recommendation validity and lane-level semantic quality before contention
- no regression in:
  - winner integrity
  - selected-surface consistency
  - operator packet coherence
  - DICE quality enforcement
- the phase is considered incomplete if it only emits placeholders that cannot be audited or rendered coherently

### 11. Recommended Implementation Order

1. Freeze the Phase 57 lane contract.
   - Define the heuristic/institution runtime boundary and the first-wave action allowlist.

2. Lock the institution / offer action schema surface.
   - Decide whether `offer_required_flag` and `offer_feasibility` are additive schema fields or deterministic derived projections from existing offer truth.

3. Implement deterministic generators by action family.
   - Start with `credit_limit_adjustment` and `installment_plan`, then `settlement_discount`, then `debt_consolidation`.

4. Wire heuristic candidates into the shared `PlanAction` serialization path.
   - Preserve legacy `action_class` and `action_family`.

5. Add heuristic-lane semantic-quality and contender gate enforcement.
   - Keep DICE gate untouched except for coexistence plumbing.

6. Verify rendering / packet / selected-surface behavior.
   - Ensure institution conditions project cleanly without fake certainty.

7. Run trust-baseline regression proof.
   - Confirm winner integrity, selected-surface consistency, operator packet coherence, and DICE quality enforcement all still hold.

</decisions>

<code_context>
## Reusable Assets And Integration Points

- Canonical action metadata already exists in [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py):
  - `credit_limit_adjustment`, `settlement_discount`, and `installment_plan` already carry:
    - ownership
    - offer type
    - approval requirement
    - offer family
    - policy-arm metadata
  - `debt_consolidation` already exists as a canonical hybrid action

- The core serialization target already exists in [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py):
  - `PlanAction`
  - `PrimaryNumericTarget`
  - `OfferContract`
  - `RoadmapStepNarrative.institution_condition`

- Offer and approval behavior already exists in [offer_optimization.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/offer_optimization.py):
  - `offer_contract_for_action()`
  - `approval_state_for_action()`
  - `is_rankable_offer_action()`
  - `is_provisional_offer_action()`
  - `build_offer_contract()`

- Numeric and institution-label sanity already exists in [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py):
  - direction checks
  - `customer_institution_mislabel`
  - bounded warning rules for limit-style targets

- DICE semantic-quality patterns in [dice_quality.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_quality.py) should be reused conceptually for the heuristic lane:
  - missing annotation detection
  - offer-contract completeness
  - role confusion detection
  - grouped primary-target rules

- Customer/operator rendering seams already exist:
  - [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py) already builds `institution_condition`, including a dedicated credit-limit condition helper
  - [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already projects selected institution conditions into the operator packet

- Trust-baseline regression fixtures already exist:
  - [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
  - [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
  - [test_dice_lane_validity_enforcement.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_dice_lane_validity_enforcement.py)

</code_context>

<deferred>
## Deferred Beyond Phase 57

- probabilistic institution approval modeling
- policy-learning or adaptive offer-arm ranking
- planner-level source-aware weighting for institution vs customer candidate lanes
- broader institution action families beyond the first-wave set
- dynamic multi-offer negotiation trees
- any threshold or decision-policy recalibration driven by the new lane

</deferred>
