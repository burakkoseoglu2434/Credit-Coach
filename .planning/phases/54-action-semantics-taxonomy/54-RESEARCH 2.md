# Phase 54: Action Semantics Taxonomy - Research

## Objective

Research how to implement Phase 54: Action Semantics Taxonomy. The goal is to define a canonical, feature-agnostic, typed action taxonomy that expands the solution space.

## Codebase Findings

The action specifications are primarily defined in `src/credit_coach/recourse/action_space.py` and constraints in `src/credit_coach/recourse/action_constraints.py`.

### 1. Existing `ActionTemplate` and `ActionSpec`
Currently, the codebase uses `ActionTemplate` and `ActionSpec` with the following attributes that map to the new schema somewhat loosely:
- `action_key` -> Present.
- `action_class` (behavioral, structural, institutional) -> Doesn't perfectly align with the new `action_owner` (customer, institution, hybrid).
- `action_family` -> Currently 9 families (e.g. `loan_sizing`, `debt_restructuring`). Needs to be replaced with the 7 new `action_category` types.
- Missing explicit boolean flags: `dice_eligible`, `heuristic_only`, `requires_numeric_target`.

### 2. Required Schema Updates (Phase 54)
The new canonical schema requires:
- `action_key` (str)
- `action_type` (str)
- `action_category` (fixed 7 categories)
- `action_owner` (Literal: `customer`, `institution`, `hybrid`)
- `primary_features_impacted` (list of strings, formerly `feature_names`)
- `dice_eligible` (bool)
- `heuristic_only` (bool)
- `requires_numeric_target` (bool)

### 3. Impacted Files
- `src/credit_coach/recourse/action_space.py`: Types, `ActionTemplate`, `ActionSpec`, `ACTION_CATALOG` updates.
- `src/credit_coach/recourse/action_constraints.py`: Logic relying on `action_family` needs to point to `action_category` and adapt `action_owner`.
- `tests/test_action_space.py`: Unit tests validating the `ACTION_CATALOG` schemas.

## Actionable Takeaways for Planning

1. **Refactor Core Literals**: Replace `ActionFamily` with `ActionCategory` literal string containing the 7 fixed categories defined in the decisions.
2. **Refactor Ownership**: Add `ActionOwner = Literal["customer", "institution", "hybrid"]` to replace or supplement `ActionClass`.
3. **Update Data Classes**: Modify `ActionTemplate` and `ActionSpec` in `action_space.py` to strictly implement the new `action_key`, `action_type`, `action_category`, `action_owner`, `primary_features_impacted`, `dice_eligible`, `heuristic_only`, and `requires_numeric_target`.
4. **Retrofit Existing Logic**: Because of the `No Regression Rule` and strict additive changes, the taxonomy update must refactor dictionary constraints (`ACTION_CATALOG` entries) and map them appropriately into the new schema without breaking operator packet logic or validity boundaries.

## Validation Architecture

The implementation will be validated by extending the unit tests to verify the schema elements (`test_action_space.py` -> `test_taxonomy_schema`). We will ensure every action has the exact rigid boolean fields and correct category/owner typing.
