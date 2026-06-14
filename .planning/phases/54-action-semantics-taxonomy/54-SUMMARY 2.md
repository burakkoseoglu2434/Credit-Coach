---
phase: "54"
plan: "54-PLAN"
status: complete
completed: "2026-04-03"
requirements_addressed: ["SEM-01", "SEM-02", "SEM-03"]
---

# Phase 54: Action Semantics Taxonomy — Summary

## What Was Built

Implemented canonical action type taxonomy in `action_space.py` and `action_constraints.py`, replacing the legacy `ActionClass`/`ActionFamily` literals with typed `ActionOwner`/`ActionCategory` semantics.

## Key Changes

### Task 1 — Type Literals & Dataclass Fields (SEM-01, SEM-02)
- `ActionClass` → `ActionOwner = Literal["customer", "institution", "hybrid"]`
- `ActionFamily` → `ActionCategory = Literal["utilization_capacity", "burden_reduction", "delinquency_cleanup", "credit_structure", "income_trust", "application_parameters", "institution_relief"]`
- `ActionTemplate`: removed `action_class`, `action_family`, `feature_names`; added `action_type`, `action_owner`, `action_category`, `primary_features_impacted`, `dice_eligible`, `heuristic_only`, `requires_numeric_target`
- `ActionSpec`: same field replacements (with `| None` defaults)

### Task 2 — ACTION_CATALOG Remapping (SEM-01, SEM-03)
All 11 existing actions remapped to new taxonomy (zero unclassified actions):
- `adjust_requested_loan_amount` → customer / application_parameters
- `refinance` → hybrid / credit_structure
- `increase_regular_income` → customer / income_trust
- `verify_income_documentation` → customer / income_trust
- `reduce_spending` → customer / utilization_capacity
- `debt_consolidation` → hybrid / credit_structure
- `limit_credit_usage` → customer / utilization_capacity
- `improve_payment_consistency` → customer / delinquency_cleanup
- `credit_limit_adjustment` → institution / institution_relief
- `settlement_discount` → institution / burden_reduction
- `installment_plan` → institution / burden_reduction

`ACTION_FAMILY_NUMERIC_DEFAULTS` renamed to `ACTION_CATEGORY_NUMERIC_DEFAULTS`, rekeyed to new `ActionCategory` values.

All callers updated: `_spec()`, `_validate_action_mapping()`, `get_action_metadata()`, `get_numeric_target_metadata()`.

### Task 3 — Constraint Telemetry (SEM-02)
`action_constraints.py` `_append_trace()`: replaced `"action_class"` key with `"action_owner"`, reading from `getattr(action, "action_owner", "")`.

## Verification

### Acceptance Criteria
- ✅ `grep "ActionOwner = Literal"` → found
- ✅ `grep "action_category: ActionCategory"` → found
- ✅ `grep "primary_features_impacted: tuple"` → found
- ✅ `grep 'action_owner="hybrid"'` → found (refinance, debt_consolidation)
- ✅ `grep "action_class" action_constraints.py` → empty (removed)
- ✅ `grep "action_owner" action_constraints.py` → found

### Test Suite
- ✅ 34/34 tests passed in `tests/test_action_space.py`
- Updated test assertions to match new API (action_owner, action_category, primary_features_impacted, ACTION_CATEGORY_NUMERIC_DEFAULTS)

### Self-Check: PASSED

## key-files

### created
- `credit-coach/src/credit_coach/recourse/action_space.py` — refactored with new taxonomy
- `credit-coach/src/credit_coach/recourse/action_constraints.py` — updated telemetry field
- `credit-coach/tests/test_action_space.py` — updated test assertions

## Deviations
None. All plan requirements implemented exactly as specified.

## Commit
`7dec626` — feat(phase-54): implement ActionOwner/ActionCategory taxonomy
