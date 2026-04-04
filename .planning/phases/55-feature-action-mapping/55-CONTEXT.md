# Phase 55: Feature -> Action Mapping - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 55 maps the modeled feature space onto the canonical action taxonomy introduced in Phase 54. The mapping applies to the 47 modeled features listed in `credit-coach/configs/features_48.yaml`; the `target` label is excluded from Phase 55.

This phase owns:
- deterministic feature -> action interpretation
- explicit primary vs supporting feature roles for shared canonical actions
- owner classification (`customer`, `institution`, `hybrid`)
- lane assignment (`dice_eligible` vs `heuristic_only`) as mapping metadata
- explicit non-actionable classification for features that must not drive movement semantics
- coverage proof and regression-safe validation artifacts

This phase does not own:
- threshold expansion
- decision-policy redesign
- planner-semantic redesign
- validity-taxonomy changes
- DICE search/runtime expansion itself
- institution offer-lane redesign
- selected-surface or operator packet changes

Guardrail:
- Phase 55 is about deterministic interpretation, not new business logic. It must expand movement understanding without reopening the v2.2 trust baseline or the v2.3 structural bottleneck finding.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 55

- Every modeled feature must receive one deterministic classification:
  - `primary_actionable`
  - `supporting_actionable`
  - `non_actionable`
- If a feature is action-interpretable, it must resolve to exactly one canonical `action_key` in Phase 55.
- One feature may not map to multiple canonical actions in this phase.
- Many features may map to one canonical action, but one feature in that group must be designated the `primary_target_feature_name`.
- The canonical source of truth remains the recourse action mapping layer in `credit-coach/src/credit_coach/recourse/action_space.py`. Do not create a second authoritative mapping source that can drift from engine behavior.

### 2. Problem Statement

- Phase 54 established the canonical action taxonomy, but the system still lacks a complete deterministic interpretation layer from modeled features to canonical actions.
- Today, some features already resolve cleanly to semantic actions, while many others are either hard-coded as non-actionable or only implicitly related to movement.
- Without a full feature -> action interpretation layer, the system cannot cleanly separate:
  - features that truly expand movement capability
  - supporting features that belong to an existing action family
  - provenance-only or frozen features that should never masquerade as actionable movement
- Phase 55 must close this gap without relaxing winner integrity, DICE contender quality, selected-surface consistency, or operator packet coherence.

### 3. Canonical Mapping Contract

- For every feature, Phase 55 must materialize or derive the following deterministic mapping fields:
  - `mapping_status`
  - `action_key` or `null`
  - `mapping_role` (`primary`, `supporting`, `none`)
  - `action_owner` or `null`
  - `action_category` or `null`
  - `action_type` or `null`
  - `dice_eligible`
  - `heuristic_only`
  - `requires_numeric_target`
  - `requires_institutional_approval`
  - `non_actionable_reason` or `null`
- `action_type`, `action_owner`, `action_category`, `dice_eligible`, `heuristic_only`, and `requires_numeric_target` are inherited from the Phase 54 canonical templates. Phase 55 consumes and propagates them; it does not redefine them.
- `requires_institutional_approval` remains a contract flag, not a planner redesign hook.
- `non_actionable_reason` is mandatory for every `non_actionable` feature. No silent fallback is allowed.

### 4. Deterministic Feature -> Action Rules

#### One-to-one primary mappings

- `loan_amnt` -> `adjust_requested_loan_amount`
- `annual_inc` -> `increase_regular_income`
- `verification_status` -> `verify_income_documentation`
- `dti` -> `reduce_spending`
- `revol_util` -> `limit_credit_usage`
- `tot_coll_amt` -> `settlement_discount`

These are single-feature, single-action interpretations. They should remain direct and deterministic.

#### Many-features -> one canonical action mappings

- `refinance`
  - primary: `installment`
  - supporting: `int_rate`, `term`
- `debt_consolidation`
  - primary: `revol_bal`
  - supporting: `tot_cur_bal`, `total_bal_ex_mort`
- `improve_payment_consistency`
  - primary: `last_fico_range_low`
  - supporting: `fico_range_low`, `fico_range_high`, `last_fico_range_high`
- `credit_limit_adjustment`
  - primary: `total_rev_hi_lim`
  - supporting: `total_bc_limit`, `tot_hi_cred_lim`
- `installment_plan`
  - primary: `delinq_amnt`
  - supporting: `acc_now_delinq`, `collections_12_mths_ex_med`

Rules for grouped mappings:
- one primary feature owns the canonical numeric target
- supporting features inherit the same `action_key`, `action_owner`, `action_category`, and lane intent
- supporting features may not produce a different canonical action just because they correlate with another action family

#### Non-actionable features

- Features that are historical facts, geographic identity, static descriptors, latent model outputs, or operational metadata must remain `non_actionable`.
- Examples likely to remain non-actionable unless the planner proves a single stable movement interpretation:
  - `funded_amnt`
  - `grade`
  - `sub_grade`
  - `addr_state`
  - `zip_code`
  - `earliest_cr_line`
  - `issue_d`
- Non-actionable classification must be explicit and reason-coded. Suggested reason-code families:
  - `historical_fact`
  - `derived_outcome`
  - `identity_or_geography`
  - `descriptive_context_only`
  - `policy_or_metadata_only`
  - `no_safe_single_action_interpretation`

### 5. Ownership Classification Rules

- `customer`
  - the customer can execute the movement directly without institution-side approval
  - examples: requested loan adjustment, income improvement, verification completion, spending reduction, usage restraint
- `institution`
  - the movement only materializes through institution-side action, approval, or offer issuance
  - examples: credit limit adjustment, settlement discount, installment plan terms
- `hybrid`
  - both customer participation and institution acceptance are required before the movement is real
  - examples: refinance, debt consolidation

Ownership is determined by execution semantics, not by which feature currently changes in the data.

### 6. Lane Assignment Rules

- `dice_eligible`
  - the feature has a bounded movement direction and a stable target representation that can later be operationalized safely in the DICE lane
  - this is a mapping annotation in Phase 55, not a runtime expansion promise
- `heuristic_only`
  - the feature requires behavioral persistence, documentation completion, or institution/process semantics that should not be expressed as a direct DICE move in this phase
- A feature may not be both `dice_eligible` and `heuristic_only`.
- Phase 55 should bias conservative:
  - if a feature lacks one stable controllable target contract, it should not be marked `dice_eligible`
  - if assigning `dice_eligible` would implicitly widen trust or contender rules, keep it out of DICE for now

### 7. MAP-02 Interpretation

- `MAP-02` should be satisfied by ensuring deterministic feature-level propagation of:
  - `action_type`
  - `requires_numeric_target`
  - `requires_institutional_approval`
- Do not reopen core schema design just because the original requirement text says "add" these fields. Phase 54 already established most of this canonical contract at the action-template layer.
- Phase 55 is about feature-level materialization and coverage, not schema churn.

### 8. Required Outputs And Artifacts

- Engine mapping source:
  - feature-level mapping truth in `credit-coach/src/credit_coach/recourse/action_space.py`
  - optional nearby helper module only if it reduces duplication without creating a second source of truth
- Validation helpers:
  - deterministic coverage validator
  - duplicate/ambiguous mapping validator
  - non-actionable reason completeness validator
- Tests:
  - coverage against `credit-coach/configs/features_48.yaml`
  - exact one-action-per-feature enforcement
  - primary-vs-supporting grouping checks
  - owner and lane assignment checks
  - no-regression checks for current action metadata consumers
- Planning artifacts:
  - `55-PLAN.md`
  - `55-SUMMARY.md`
  - `55-VERIFICATION.md`

### 9. Acceptance Criteria

- All 47 modeled features are classified with no unmapped leftovers.
- Every `primary_actionable` and `supporting_actionable` feature resolves to exactly one canonical `action_key`.
- Every grouped action defines exactly one primary target feature.
- Every `non_actionable` feature includes an explicit `non_actionable_reason`.
- No mapping change reopens planner semantics, decision-policy semantics, validity taxonomy, or v2.2 trust invariants.
- `MAP-03` target:
  - at least 38 of the 47 modeled features should be classified as action-interpretable (`primary_actionable` or `supporting_actionable`)
  - if 38 cannot be reached without ambiguous or unsafe mappings, verification must fail rather than forcing fake movement semantics

### 10. Recommended Implementation Order

1. Freeze the feature-level mapping vocabulary and status model.
2. Inventory the 47 modeled features from `features_48.yaml` and assign each to `primary_actionable`, `supporting_actionable`, or `non_actionable`.
3. Encode direct one-to-one mappings first.
4. Encode many-features -> one-action groups with a single primary target per group.
5. Add ownership and lane annotations after the canonical grouping is stable.
6. Fill explicit `non_actionable_reason` values for every remaining feature.
7. Add validation helpers and tests before touching downstream consumers.
8. Run regression checks against current recourse/planner/serialization flows to ensure the mapping layer remains additive.

### Claude's Discretion

- Exact helper names for coverage and reason-code validation
- Whether grouped mapping metadata lives entirely in `ActionSpec` or in a tightly coupled helper inside the recourse package
- Exact naming of `mapping_status`, `mapping_role`, and `non_actionable_reason`, as long as the semantics above stay locked

</decisions>

<specifics>
## Specific Ideas

- Treat the 47 modeled features as three buckets:
  - direct movement levers
  - supporting indicators that belong to a canonical action
  - frozen/provenance/context features that must be explicitly classified as non-actionable
- Do not create fake actionability just to inflate coverage.
- Coverage is useful only if the mapping remains deterministic enough to survive winner-integrity and selected-surface consumers later.
- Phase 55 should leave Phase 56 a clean lane-assignment artifact, not an ambiguous wish list.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `credit-coach/configs/features_48.yaml`
  - canonical denominator for the modeled feature inventory
- `credit-coach/src/credit_coach/recourse/action_space.py`
  - current home of `ACTION_CATALOG`, `ACTION_SPACE`, feature-level specs, and numeric target metadata
  - should remain the main mapping seam for Phase 55
- `credit-coach/tests/test_action_space.py`
  - already checks full feature coverage and typed action metadata
  - is the natural place to extend deterministic mapping assertions

### Established Patterns

- Phase 54 already locked the canonical action taxonomy and owner/category contract.
- Engine artifacts remain the source of truth; downstream surfaces should consume mapping outputs, not reinterpret them.
- v2.2 trust layers are inherited and frozen for this phase.

### Integration Points

- `credit-coach/src/credit_coach/recourse/generator.py`
  - builds `PlanAction` objects from feature-level action metadata
  - must remain compatible without planner redesign
- `credit-coach/src/credit_coach/data/schema.py`
  - still exposes legacy `action_class` / `action_family` fields in business-facing models
  - Phase 55 should avoid reopening schema semantics unless absolutely required for deterministic mapping propagation
- `credit-coach/src/credit_coach/coaching/planner.py`
  - still checks for legacy business semantics fields
  - mapping work must remain additive and not require planner-chooser logic changes in this phase

</code_context>

<deferred>
## Deferred Ideas

- Actual DICE search/runtime expansion belongs to Phase 56.
- Institution-side offer lane broadening belongs to Phase 57.
- Multi-path generation belongs to Phase 58.
- Rendering and narrative polish belong to Phase 59.
- Any planner redesign, threshold widening, validity-taxonomy rewrite, or decision-policy change is out of scope.

</deferred>

---
*Phase: 55-feature-action-mapping*
*Context gathered: 2026-04-03*
