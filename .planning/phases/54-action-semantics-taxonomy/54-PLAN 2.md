---
wave: 1
depends_on: []
files_modified:
  - "src/credit_coach/recourse/action_space.py"
  - "src/credit_coach/recourse/action_constraints.py"
autonomous: true
requirements_addressed: ["SEM-01", "SEM-02", "SEM-03"]
---

# Phase 54: Action Semantics Taxonomy Implementation Plan

## Objective
Implement canonical action types, rigid definitions, taxonomy categories, and ownership semantics into `action_space.py` without breaking existing recourse evaluation or validity bounds.

## Requirements Covered
- **SEM-01**: Define canonical action categories: utilization, burden reduction, delinquency cleanup, verification, restructuring, application flexing, institution relief
- **SEM-02**: Add action_owner field (customer, institution, hybrid)
- **SEM-03**: Verify all existing actions map into the taxonomy with zero unclassified leftovers

## Tasks

```xml
<task id="update_action_space_types">
  <read_first>
    - src/credit_coach/recourse/action_space.py
  </read_first>
  <action>
    1. In `src/credit_coach/recourse/action_space.py`, modify `ActionClass` to `ActionOwner = Literal["customer", "institution", "hybrid"]`.
    2. Modify `ActionFamily` to `ActionCategory = Literal["utilization_capacity", "burden_reduction", "delinquency_cleanup", "credit_structure", "income_trust", "application_parameters", "institution_relief"]`.
    3. Update `ActionTemplate` fields:
       - Remove `action_class` and `action_family`.
       - Add `action_type: str = ""`
       - Add `action_owner: ActionOwner`
       - Add `action_category: ActionCategory`
       - Rename `feature_names` to `primary_features_impacted`
       - Add `dice_eligible: bool = False`
       - Add `heuristic_only: bool = False`
       - Add `requires_numeric_target: bool = False`
    4. Make the exact same field replacements to `ActionSpec` dataclass (replace `action_class`, `action_family`, `feature_names`; add the new 6 fields with `| None = None` correctly defaulted for specs).
  </action>
  <acceptance_criteria>
    - `grep "ActionOwner = Literal" src/credit_coach/recourse/action_space.py` returns true.
    - `grep "action_category: ActionCategory" src/credit_coach/recourse/action_space.py` returns true.
    - `grep "primary_features_impacted: tuple" src/credit_coach/recourse/action_space.py` returns true.
  </acceptance_criteria>
</task>

<task id="update_action_catalog">
  <read_first>
    - src/credit_coach/recourse/action_space.py
  </read_first>
  <action>
    Refactor `ACTION_CATALOG` in `action_space.py` to use the new fields. Ensure semantic mapping:
    - `adjust_requested_loan_amount`: type="adjustment", owner="customer", category="application_parameters", primary_features_impacted=("loan_amnt",)
    - `refinance`: type="restructure", owner="hybrid", category="credit_structure", primary_features_impacted=("int_rate", "installment")
    - `increase_regular_income`: type="documentation", owner="customer", category="income_trust", primary_features_impacted=("annual_inc",)
    - `verify_income_documentation`: type="documentation", owner="customer", category="income_trust", primary_features_impacted=("verification_status",)
    - `reduce_spending`: type="behavioral", owner="customer", category="utilization_capacity", primary_features_impacted=("dti",)
    - `debt_consolidation`: type="restructure", owner="hybrid", category="credit_structure", primary_features_impacted=("revol_bal", "tot_cur_bal", "total_bal_ex_mort")
    - `limit_credit_usage`: type="behavioral", owner="customer", category="utilization_capacity", primary_features_impacted=("revol_util",)
    - `improve_payment_consistency`: type="behavioral", owner="customer", category="delinquency_cleanup", primary_features_impacted=("fico_range_low", "fico_range_high", ...)
    - `credit_limit_adjustment`: type="institutional", owner="institution", category="institution_relief", primary_features_impacted=("total_rev_hi_lim", ...)
    - `settlement_discount`: type="institutional", owner="institution", category="burden_reduction", primary_features_impacted=("tot_coll_amt",)
    - `installment_plan`: type="institutional", owner="institution", category="burden_reduction", primary_features_impacted=("acc_now_delinq", ...)

    Adjust `get_action_metadata`, `_spec()`, and `_validate_action_mapping` to correctly use `action_category` and `action_owner` instead of `action_family` and `action_class`. Note that `ACTION_FAMILY_NUMERIC_DEFAULTS` needs to be renamed and rekeyed to match `ActionCategory` (e.g. `loan_sizing` -> `application_parameters`, `debt_restructuring` -> `credit_structure`, etc.).
  </action>
  <acceptance_criteria>
    - `grep "action_owner=\"hybrid\"" src/credit_coach/recourse/action_space.py` returns true.
    - `pytest tests/test_action_space.py` or similar verification validates without KeyError or TypeError on initialization.
  </acceptance_criteria>
</task>

<task id="update_action_constraints">
  <read_first>
    - src/credit_coach/recourse/action_constraints.py
  </read_first>
  <action>
    In `src/credit_coach/recourse/action_constraints.py`, update usage of deprecated properties. Specifically, replace `action_class` with `action_owner` in dictionary traces (e.g., `_append_trace` dict appending `"action_owner": str(getattr(action, "action_owner", "") ...)`).

    Ensure that we do not break any constraint priority grouping unless it explicitly required `action_family`. Currently constraints don't deeply check `action_family` explicitly except for debugging telemetry.
  </action>
  <acceptance_criteria>
    - `grep "action_class" src/credit_coach/recourse/action_constraints.py` returns empty or handles backwards compat.
    - `grep "action_owner" src/credit_coach/recourse/action_constraints.py` returns true.
  </acceptance_criteria>
</task>
```

## Must Haves
- The new `ActionOwner` and `ActionCategory` literals uniquely and comprehensively replace `ActionClass` and `ActionFamily`.
- No feature is left behind in `ACTION_CATALOG`. All 11 existing actions must receive valid mappings.
- Output shapes for downstream constraints and `diagnostic_flags` adhere closely to previous milestones, meaning fields must just be properly propagated to tracelogs.
