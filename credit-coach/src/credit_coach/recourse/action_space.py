"""
recourse/action_space.py
========================
Feature bazlı aksiyon uzayı tanımları.
(Yeni CSV'deki 47 feature'a göre uyarlanmıştır.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ActionSpec:
    feature_name: str
    actionable: bool
    direction: Literal["decrease", "increase", "any"]
    min_val: float | None = None
    max_val: float | None = None
    step: float = 1.0
    cost_weight: float = 0.5
    time_months: int = 3
    description: str = ""


ACTION_SPACE: dict[str, ActionSpec] = {

    # 1. IMMUTABLE / CATEGORICAL / METADATA
    "loan_amnt": ActionSpec(
        feature_name="loan_amnt",
        actionable=True,
        direction="decrease",
        min_val=500.0,
        step=500.0,
        cost_weight=0.15,
        time_months=1,
    ),
    "funded_amnt": ActionSpec(feature_name="funded_amnt", actionable=False, direction="any"),
    "term": ActionSpec(feature_name="term", actionable=False, direction="any"),
    "int_rate": ActionSpec(
        feature_name="int_rate",
        actionable=True,
        direction="decrease",
        min_val=0.0,
        step=0.5,
        cost_weight=0.20,
        time_months=3,
    ),
    "installment": ActionSpec(
        feature_name="installment",
        actionable=True,
        direction="decrease",
        min_val=0.0,
        step=50.0,
        cost_weight=0.12,
        time_months=1,
    ),
    "grade": ActionSpec(feature_name="grade", actionable=False, direction="any"),
    "sub_grade": ActionSpec(feature_name="sub_grade", actionable=False, direction="any"),
    "purpose": ActionSpec(feature_name="purpose", actionable=False, direction="any"),
    "application_type": ActionSpec(feature_name="application_type", actionable=False, direction="any"),
    "emp_title": ActionSpec(feature_name="emp_title", actionable=False, direction="any"),
    "emp_length": ActionSpec(feature_name="emp_length", actionable=False, direction="any"),
    "home_ownership": ActionSpec(feature_name="home_ownership", actionable=False, direction="any"),
    "addr_state": ActionSpec(feature_name="addr_state", actionable=False, direction="any"),
    "zip_code": ActionSpec(feature_name="zip_code", actionable=False, direction="any"),
    "earliest_cr_line": ActionSpec(feature_name="earliest_cr_line", actionable=False, direction="any"),
    "issue_d": ActionSpec(feature_name="issue_d", actionable=False, direction="any"),
    "initial_list_status": ActionSpec(feature_name="initial_list_status", actionable=False, direction="any"),
    "debt_settlement_flag": ActionSpec(feature_name="debt_settlement_flag", actionable=False, direction="any"),
    "disbursement_method": ActionSpec(feature_name="disbursement_method", actionable=False, direction="any"),

    # 2. ACTIONABLE
    "annual_inc": ActionSpec(
        feature_name="annual_inc", actionable=True, direction="increase", min_val=0.0, step=2000.0, cost_weight=0.1, time_months=6
    ),
    "verification_status": ActionSpec(
        feature_name="verification_status", actionable=True, direction="increase", step=1.0, cost_weight=0.05, time_months=1
    ),
    "dti": ActionSpec(
        feature_name="dti", actionable=True, direction="decrease", min_val=0.0, step=1.0, cost_weight=0.6, time_months=1
    ),
    "revol_bal": ActionSpec(
        feature_name="revol_bal", actionable=True, direction="decrease", min_val=0.0, step=500.0, cost_weight=0.7, time_months=1
    ),
    "revol_util": ActionSpec(
        feature_name="revol_util", actionable=True, direction="decrease", min_val=0.0, step=2.0, cost_weight=0.5, time_months=1
    ),
    "fico_range_low": ActionSpec(
        feature_name="fico_range_low", actionable=True, direction="increase", step=5.0, cost_weight=0.2, time_months=6
    ),
    "fico_range_high": ActionSpec(
        feature_name="fico_range_high", actionable=True, direction="increase", step=5.0, cost_weight=0.2, time_months=6
    ),
    "last_fico_range_low": ActionSpec(
        feature_name="last_fico_range_low", actionable=True, direction="increase", step=5.0, cost_weight=0.2, time_months=3
    ),
    "last_fico_range_high": ActionSpec(
        feature_name="last_fico_range_high", actionable=True, direction="increase", step=5.0, cost_weight=0.2, time_months=3
    ),
    "tot_cur_bal": ActionSpec(
        feature_name="tot_cur_bal", actionable=True, direction="decrease", min_val=0.0, step=500.0, cost_weight=0.6, time_months=6
    ),
    "total_rev_hi_lim": ActionSpec(
        feature_name="total_rev_hi_lim", actionable=True, direction="increase", min_val=0.0, step=1000.0, cost_weight=0.1, time_months=3
    ),
    "total_bal_ex_mort": ActionSpec(
        feature_name="total_bal_ex_mort", actionable=True, direction="decrease", min_val=0.0, step=500.0, cost_weight=0.6, time_months=6
    ),
    "total_bc_limit": ActionSpec(
        feature_name="total_bc_limit", actionable=True, direction="increase", step=1000.0, cost_weight=0.1, time_months=3
    ),
    "tot_hi_cred_lim": ActionSpec(
        feature_name="tot_hi_cred_lim", actionable=True, direction="increase", step=1000.0, cost_weight=0.1, time_months=3
    ),
    
    # 3. HISTORICAL / LESS ACTIONABLE OR IMMUTABLE DUE TO PAST NATURE
    "open_acc": ActionSpec(feature_name="open_acc", actionable=False, direction="any"),
    "total_acc": ActionSpec(feature_name="total_acc", actionable=False, direction="any"),
    "mort_acc": ActionSpec(feature_name="mort_acc", actionable=False, direction="any"),
    "delinq_2yrs": ActionSpec(feature_name="delinq_2yrs", actionable=False, direction="any"),
    "inq_last_6mths": ActionSpec(feature_name="inq_last_6mths", actionable=False, direction="any"),
    "pub_rec": ActionSpec(feature_name="pub_rec", actionable=False, direction="any"),
    "pub_rec_bankruptcies": ActionSpec(feature_name="pub_rec_bankruptcies", actionable=False, direction="any"),
    "chargeoff_within_12_mths": ActionSpec(feature_name="chargeoff_within_12_mths", actionable=False, direction="any"),
    "tax_liens": ActionSpec(feature_name="tax_liens", actionable=False, direction="any"),
    "acc_open_past_24mths": ActionSpec(feature_name="acc_open_past_24mths", actionable=False, direction="any"),

    # 4. DEBT RESOLUTION
    "tot_coll_amt": ActionSpec(
        feature_name="tot_coll_amt", actionable=True, direction="decrease", min_val=0.0, step=100.0, cost_weight=0.9, time_months=6
    ),
    "acc_now_delinq": ActionSpec(
        feature_name="acc_now_delinq", actionable=True, direction="decrease", min_val=0.0, max_val=1.0, step=1.0, cost_weight=0.9, time_months=1
    ),
    "delinq_amnt": ActionSpec(
        feature_name="delinq_amnt", actionable=True, direction="decrease", min_val=0.0, step=100.0, cost_weight=0.9, time_months=1
    ),
    "collections_12_mths_ex_med": ActionSpec(
        feature_name="collections_12_mths_ex_med", actionable=True, direction="decrease", min_val=0.0, step=1.0, cost_weight=0.9, time_months=1
    ),
}


def get_actionable_features() -> list[str]:
    return [name for name, spec in ACTION_SPACE.items() if spec.actionable]


def get_action_spec(feature_name: str) -> ActionSpec:
    if feature_name not in ACTION_SPACE:
        raise KeyError(
            f"'{feature_name}' ACTION_SPACE içinde tanımlı değil. "
            f"features_48.yaml ile senkron mu?"
        )
    return ACTION_SPACE[feature_name]


def validate_action_space_coverage(feature_list: list[str]) -> list[str]:
    missing = [f for f in feature_list if f not in ACTION_SPACE]
    return missing


def estimate_action_cost_usd(current_value: float, target_value: float, spec: ActionSpec) -> float:
    """
    Normalized action cost to avoid raw-value scale bias across features/groups.

    Cost model:
      relative_delta = |target-current| / max(|current|, |target|, 1)
      cost = 100 * relative_delta * (1 + cost_weight)
    """
    current = float(current_value)
    target = float(target_value)
    denom = max(abs(current), abs(target), 1.0)
    relative_delta = abs(target - current) / denom
    return float(100.0 * relative_delta * (1.0 + float(spec.cost_weight)))
