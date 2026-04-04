# Phase 56: DICE Action Space Expansion - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 56 expands the DICE lane so it can safely generate a broader set of candidate actions using the canonical action taxonomy from Phase 54 and the deterministic feature-to-action mapping from Phase 55.

This phase owns:
- a DICE-specific feature/action generation contract
- safe expansion of the DICE-vary feature set beyond the old implicit runtime seam
- grouped-action generation rules for canonical DICE actions
- categorical / verification-style DICE generation rules
- DICE annotation completeness and semantic-quality hardening for the newly expanded action space
- DICE contender eligibility rules for the expanded set
- regression proof that winner integrity, DICE contender quality, selected-surface consistency, and operator packet coherence still hold

This phase does not own:
- planner redesign
- decision-threshold changes
- validity-taxonomy changes
- selected-surface redesign
- operator packet redesign
- heuristic / institution lane expansion beyond what is required to serialize safe DICE candidates
- multi-path generation

Guardrail:
- Phase 56 must expand DICE candidate generation without turning the global `actionable=True` seam into a broader internal-planner contract. DICE runtime expansion should be owned by a dedicated DICE generation allowlist / contract, not by silently widening the internal action space for every lane.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 56

- Phase 56 should introduce a dedicated DICE generation contract that is narrower and safer than "all globally actionable features."
- The DICE lane must consume Phase 54 canonical action metadata and Phase 55 mapping metadata instead of inferring movement semantics from raw feature names.
- The initial expansion set is limited to features/actions that have:
  - deterministic action identity
  - bounded movement direction
  - canonical annotation completeness
  - safe contender semantics under the existing Phase 46 quality gate
- Brownfield compatibility remains mandatory:
  - legacy `action_class`
  - legacy `action_family`
  must still be emitted for DICE-generated actions.

### 2. Problem Statement

- Today the DICE lane still depends on the broad `get_actionable_features()` seam, which was never designed to be the long-term DICE runtime contract.
- Phase 55 gave the system a deterministic feature-to-action map, but DICE does not yet use that mapping to decide:
  - which features are genuinely DICE-generatable
  - which grouped actions require a primary feature
  - which supporting features can only appear in the presence of their primary action
  - how categorical or verification-style changes should serialize semantically
- Without a dedicated Phase 56 contract, DICE expansion would either:
  - widen global runtime behavior accidentally
  - keep relying on raw feature deltas with under-specified semantics
  - or let supporting / categorical features appear as orphan contenders
- Phase 56 closes that gap while preserving the locked v2.2 trust baseline.

### 3. Which Actions / Features Should Become DICE-Generatable First

The first rollout should be conservative and action-led, not feature-led.

#### First-wave canonical actions

- `adjust_requested_loan_amount`
  - primary DICE feature: `loan_amnt`
  - rationale: customer-owned, numeric, one-step, clean primary target contract

- `refinance`
  - primary DICE feature: `installment`
  - supporting DICE feature: `term`
  - retained existing DICE feature: `int_rate`
  - rationale: `installment` is the locked primary target for the canonical refinance action; `term` is useful but must not appear as a stand-alone orphan action

- `verify_income_documentation`
  - primary DICE feature: `verification_status`
  - rationale: deterministic categorical / boolean-state movement with strong semantic identity and no planner redesign

- `installment_plan`
  - primary DICE feature: `delinq_amnt`
  - supporting DICE features: `acc_now_delinq`, `collections_12_mths_ex_med`
  - rationale: this is the safest first delinquency action because the canonical action, primary target, and offer-contract semantics already exist

#### Explicitly not first-wave in Phase 56

- `credit_limit_adjustment`
- `settlement_discount`
- heuristic-only customer actions such as:
  - `reduce_spending`
  - `limit_credit_usage`
  - `improve_payment_consistency`
- mapped-but-descriptive support features such as:
  - `emp_title`
  - `home_ownership`
  - `open_acc`

Reason:
- these either require stronger institution-lane semantics, depend on persistence / behavior rather than bounded counterfactual movement, or risk reopening scope that belongs to Phase 57.

### 4. DICE-Eligible Action Selection Rules

- Runtime DICE feature selection must stop using the broad "all actionable features" heuristic as its source of truth.
- Phase 56 should introduce one canonical helper for DICE runtime eligibility, for example:
  - `get_dice_generatable_features()`
  - or `list_dice_generation_contract()`
- A feature may be DICE-generatable in Phase 56 only if all of the following are true:
  - it has a deterministic canonical `action_key`
  - its canonical action is intended for DICE runtime in this phase rollout
  - its movement direction is bounded and non-ambiguous
  - its target can be serialized into the existing Phase 46 annotation contract
  - it does not require planner or validity-taxonomy redesign

- Supporting-feature rule:
  - a supporting feature may be DICE-generatable only if its canonical action is also DICE-generatable
  - supporting features may not become stand-alone contender actions unless explicitly allowed
  - for grouped actions in Phase 56, support-only DICE candidates should be invalid unless the group contains the primary target feature

- Phase 56 rollout lock:
  - DICE generation is safe-set driven, not "everything marked `dice_eligible=True` in templates automatically becomes live."
  - Template flags remain canonical metadata, but runtime rollout is still conservative and phase-owned.

### 5. Numeric Target Generation Rules

- Numeric target generation must continue using the canonical Phase 54 / 55 action metadata.
- Every DICE-generated action that requires a primary target must emit one deterministic `primary_numeric_target`.
- Grouped-action rule:
  - one action group = one primary target feature
  - supporting features inherit the action group and semantics
  - supporting features may contribute to the counterfactual delta set, but they do not redefine the group’s primary target identity

- Primary numeric target rules for the first-wave rollout:
  - `loan_amnt` -> metric `requested_loan_amount`
  - `installment` -> metric `monthly_payment_amount`
  - `verification_status` -> metric `income_verification_state` with unit `boolean_state`
  - `delinq_amnt` -> metric `delinquent_balance_amount`

- `term` rule:
  - `term` is a supporting refinance feature in Phase 56
  - `term` may be changed by DICE only as part of a refinance group
  - a `term`-only DICE candidate is not contender-eligible

- Delinquency supporting-feature rule:
  - `acc_now_delinq` and `collections_12_mths_ex_med` may support an `installment_plan` group
  - they should not form a stand-alone DICE contender without `delinq_amnt`

### 6. Categorical / Verification-Style Action Rules

- Phase 56 explicitly allows categorical / verification-style DICE generation, but only when the movement is deterministic and one-directional.
- `verification_status` is the canonical first case.

Rules:
- categorical DICE actions must still serialize through the existing primary-target envelope
- `boolean_state` / ordered-state targets are valid as long as the target is deterministic and renderable
- verification-style movement must be monotonic toward a stronger documented state; no oscillating or ambiguous category flips
- categorical actions must emit:
  - canonical `action_key`
  - legacy `action_class`
  - legacy `action_family`
  - deterministic `checkpoint_metric`
  - complete recommendation validity fields

### 7. Annotation Completeness Rules

Phase 46 remains the governing minimum contract.

Every Phase 56 DICE contender must remain complete for:
- `action_key`
- `action_class`
- `action_family`
- `action_title`
- `action_group_id`
- `checkpoint_metric`
- `recommendation_validity_status`
- `recommendation_validity_codes`

Required when applicable:
- `primary_numeric_target`
- `offer_contract`

Phase 56 addition:
- supporting-feature grouped actions must still serialize to the same canonical group identity as their primary action
- new categorical / grouped candidates must not degrade annotation completeness relative to the old DICE lane

### 8. Semantic Quality Rules

Phase 46 quality gates remain locked; Phase 56 only extends what they must correctly judge.

New Phase 56 semantic invalid cases:
- supporting-feature orphan candidate for a grouped action
- grouped action missing its canonical primary target identity
- categorical / verification-style candidate with non-deterministic target transition
- DICE-generated action that maps to a canonical action outside the Phase 56 rollout set

Warning cases may still include:
- `heuristic_fallback_backend`
- generic text fallback
- narrow family collapse
- institution-only-without-customer-action, if still allowed diagnostically

Key rule:
- Phase 56 should prefer invalidation over permissive warnings when the candidate’s action identity is ambiguous.

### 9. Contender Eligibility Rules

The existing Phase 46 contender gate remains fixed, and Phase 56 adds only action-space-specific prerequisites.

A DICE candidate is contender-eligible only if:
- backend is not `skipped`
- recommendation validity is not `invalid`
- annotation is complete
- semantic quality is not `invalid`
- at least one actionable step survives feasibility / constraints
- all generated actions belong to the Phase 56 DICE rollout contract
- every grouped action includes its primary target feature when required

Additional lock:
- newly added DICE features may appear in diagnostics before they are rankable, but they may not enter planner contention unless they satisfy the full Phase 46 + Phase 56 gate set.

### 10. Required Outputs And Artifacts

- Engine/runtime files:
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/recourse/dice_baseline.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/recourse/dice_quality.py`
- Potential schema touch only if additive and required for serialization consistency:
  - `credit-coach/src/credit_coach/data/schema.py`
- Tests:
  - `credit-coach/tests/test_action_space.py`
  - `credit-coach/tests/test_dice_baseline_direction.py`
  - `credit-coach/tests/test_dice_lane_validity_enforcement.py`
  - `credit-coach/tests/test_recourse_redesign.py`
  - brownfield-facing tests that cover selected-surface and operator-packet invariants if touched transitively
- Planning artifacts:
  - `56-PLAN.md`
  - `56-SUMMARY.md`
  - `56-VERIFICATION.md`

### 11. Acceptance Criteria

- Phase 56 defines one explicit DICE runtime allowlist / contract instead of reusing the broad global actionable seam.
- First-wave DICE rollout supports:
  - `loan_amnt`
  - `installment`
  - `term` as grouped refinance support only
  - `verification_status`
  - selected delinquency features anchored by `delinq_amnt`
- Supporting-feature orphan contenders are rejected.
- `verification_status` DICE candidates serialize with complete canonical and legacy metadata.
- Newly expanded DICE candidates preserve:
  - winner integrity
  - DICE contender quality
  - selected-surface consistency
  - operator packet coherence
- No change breaks legacy `action_class` / `action_family` compatibility.
- Planner semantics, decision thresholds, and validity taxonomy remain unchanged.

### 12. Recommended Implementation Order

1. Introduce a DICE-specific runtime contract helper that is distinct from `get_actionable_features()`.
2. Lock the first-wave rollout set by canonical action and feature:
   - `loan_amnt`
   - `installment`
   - `term` (support-only)
   - `verification_status`
   - `delinq_amnt` plus selected support features
3. Update DICE generation to consume the new runtime contract instead of the global actionable seam.
4. Add grouped-action rules so supporting features cannot become orphan contenders.
5. Add categorical / verification-state target handling for `verification_status`.
6. Extend DICE semantic-quality checks for grouped-support and categorical-action cases.
7. Add regression coverage proving no trust-baseline regressions across DICE, selected surfaces, and brownfield consumers.

### Claude's Discretion

- Exact helper names for the DICE runtime allowlist / contract
- Whether grouped-action completeness is checked in `dice_baseline.py`, `run_recourse.py`, or `dice_quality.py`
- Whether `term` pairing is enforced at generation time, normalization time, or semantic-quality time, as long as stand-alone `term` contenders are impossible
- Exact sequencing of tests, provided trust-baseline regression proof remains explicit

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py): canonical action taxonomy, Phase 55 feature mapping, numeric target metadata, and legacy compatibility aliases
- [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py): current DICE vary-feature seam and heuristic fallback generation
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): passes `sorted(actionable)` into DICE today and normalizes DICE actions into canonical `PlanAction`s
- [dice_quality.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_quality.py): existing annotation-completeness, semantic-quality, and contender-eligibility gates from Phase 46
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py): shared canonical action builder and numeric-target construction seam that DICE already reuses

### Established Patterns

- DICE and internal generation may differ at candidate-generation time, but not at typed-action serialization time.
- Recommendation validity and DICE semantic quality are separate truths and must stay that way.
- Diagnostics visibility may be broader than the actual contender set.
- Brownfield consumers still expect `action_class` and `action_family`, so the canonical seam must continue emitting them.

### Integration Points

- `run_recourse.py` currently uses `get_actionable_features()` for DICE input; this is the key seam Phase 56 should replace
- `dice_baseline.py` already enforces directionality and action budgets; it can be extended with grouped and categorical rules
- `dice_quality.py` is the right place to reject support-only or semantically ambiguous DICE contenders without redesigning validity taxonomy

</code_context>

<deferred>
## Deferred Ideas

- institution-lane broadening for credit-limit, settlement, and other offer-heavy actions beyond the safe first-wave DICE set
- heuristic-only customer actions as native DICE targets
- multi-path packaging of customer / hybrid / institution options
- rendering or narrative redesign for expanded action semantics

</deferred>
