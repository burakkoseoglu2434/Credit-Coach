"""
recourse/action_space.py
========================
Feature bazli aksiyon uzayi tanimlari.

Phase 12 ile birlikte bu modul yalnizca "hangi feature degisir" bilgisini
degil, bu degisimin hangi gercek dunya action semantigine ait oldugunu da
tasir. Brownfield uyumluluk icin generator hala feature-level effect uzerinden
calisir; fakat her actionable spec artik bir `action_key` ve `action_class`
tasir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ActionClass = Literal["behavioral", "structural", "institutional"]


@dataclass(frozen=True)
class ActionTemplate:
    action_key: str
    action_class: ActionClass
    title: str
    description: str = ""
    feature_names: tuple[str, ...] = field(default_factory=tuple)
    requires_institutional_approval: bool = False
    approval_pending_semantic_only: bool = False
    prerequisite_tags: tuple[str, ...] = field(default_factory=tuple)
    conflict_tags: tuple[str, ...] = field(default_factory=tuple)


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
    action_key: str | None = None
    action_class: ActionClass | None = None
    action_title: str = ""
    requires_institutional_approval: bool = False
    approval_pending_semantic_only: bool = False
    prerequisite_tags: tuple[str, ...] = field(default_factory=tuple)
    conflict_tags: tuple[str, ...] = field(default_factory=tuple)


ACTION_CATALOG: dict[str, ActionTemplate] = {
    "adjust_requested_loan_amount": ActionTemplate(
        action_key="adjust_requested_loan_amount",
        action_class="structural",
        title="Adjust requested loan amount",
        description="Reduce the requested loan size to improve affordability and approval odds.",
        feature_names=("loan_amnt",),
    ),
    "refinance": ActionTemplate(
        action_key="refinance",
        action_class="structural",
        title="Refinance or restructure debt",
        description="Use refinancing to improve rate and installment affordability.",
        feature_names=("int_rate", "installment"),
        prerequisite_tags=("stable_income",),
    ),
    "increase_regular_income": ActionTemplate(
        action_key="increase_regular_income",
        action_class="behavioral",
        title="Increase regular income",
        description="Improve recurring income through additional work or stable earnings.",
        feature_names=("annual_inc",),
    ),
    "verify_income_documentation": ActionTemplate(
        action_key="verify_income_documentation",
        action_class="structural",
        title="Verify income documentation",
        description="Complete documentation or verification steps to strengthen the file.",
        feature_names=("verification_status",),
    ),
    "reduce_spending": ActionTemplate(
        action_key="reduce_spending",
        action_class="behavioral",
        title="Reduce spending pressure",
        description="Reduce ongoing spending to improve debt-to-income behavior.",
        feature_names=("dti",),
    ),
    "debt_consolidation": ActionTemplate(
        action_key="debt_consolidation",
        action_class="structural",
        title="Consolidate revolving debt",
        description="Use consolidation or structured repayment to reduce revolving balances.",
        feature_names=("revol_bal", "tot_cur_bal", "total_bal_ex_mort"),
        conflict_tags=("settlement_discount",),
    ),
    "limit_credit_usage": ActionTemplate(
        action_key="limit_credit_usage",
        action_class="behavioral",
        title="Limit credit usage",
        description="Reduce revolving utilization and slow new card usage.",
        feature_names=("revol_util",),
    ),
    "improve_payment_consistency": ActionTemplate(
        action_key="improve_payment_consistency",
        action_class="behavioral",
        title="Improve payment consistency",
        description="Build more consistent repayment behavior over time.",
        feature_names=("fico_range_low", "fico_range_high", "last_fico_range_low", "last_fico_range_high"),
    ),
    "credit_limit_adjustment": ActionTemplate(
        action_key="credit_limit_adjustment",
        action_class="institutional",
        title="Request or negotiate credit limit adjustment",
        description="Institution-mediated credit limit changes can improve utilization headroom.",
        feature_names=("total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim"),
        requires_institutional_approval=True,
    ),
    "settlement_discount": ActionTemplate(
        action_key="settlement_discount",
        action_class="institutional",
        title="Negotiate settlement discount",
        description="Use an institution-approved settlement to reduce collections pressure.",
        feature_names=("tot_coll_amt",),
        requires_institutional_approval=True,
        approval_pending_semantic_only=True,
        conflict_tags=("installment_plan",),
    ),
    "installment_plan": ActionTemplate(
        action_key="installment_plan",
        action_class="institutional",
        title="Enter an installment plan",
        description="Restructure delinquent balances into an approved installment plan.",
        feature_names=("acc_now_delinq", "delinq_amnt", "collections_12_mths_ex_med"),
        requires_institutional_approval=True,
        approval_pending_semantic_only=True,
        prerequisite_tags=("stable_income",),
        conflict_tags=("settlement_discount",),
    ),
}


def _spec(
    *,
    feature_name: str,
    actionable: bool,
    direction: Literal["decrease", "increase", "any"],
    action_key: str | None = None,
    min_val: float | None = None,
    max_val: float | None = None,
    step: float = 1.0,
    cost_weight: float = 0.5,
    time_months: int = 3,
    description: str = "",
) -> ActionSpec:
    template = ACTION_CATALOG.get(action_key) if action_key else None
    return ActionSpec(
        feature_name=feature_name,
        actionable=actionable,
        direction=direction,
        min_val=min_val,
        max_val=max_val,
        step=step,
        cost_weight=cost_weight,
        time_months=time_months,
        description=description or (template.description if template else ""),
        action_key=template.action_key if template else None,
        action_class=template.action_class if template else None,
        action_title=template.title if template else "",
        requires_institutional_approval=bool(template.requires_institutional_approval) if template else False,
        approval_pending_semantic_only=bool(template.approval_pending_semantic_only) if template else False,
        prerequisite_tags=tuple(template.prerequisite_tags) if template else (),
        conflict_tags=tuple(template.conflict_tags) if template else (),
    )


ACTION_SPACE: dict[str, ActionSpec] = {
    "loan_amnt": _spec(
        feature_name="loan_amnt",
        actionable=True,
        direction="decrease",
        action_key="adjust_requested_loan_amount",
        min_val=500.0,
        step=500.0,
        cost_weight=0.15,
        time_months=1,
    ),
    "funded_amnt": _spec(feature_name="funded_amnt", actionable=False, direction="any"),
    "term": _spec(feature_name="term", actionable=False, direction="any"),
    "int_rate": _spec(
        feature_name="int_rate",
        actionable=True,
        direction="decrease",
        action_key="refinance",
        min_val=0.0,
        step=0.5,
        cost_weight=0.20,
        time_months=3,
    ),
    "installment": _spec(
        feature_name="installment",
        actionable=True,
        direction="decrease",
        action_key="refinance",
        min_val=0.0,
        step=50.0,
        cost_weight=0.12,
        time_months=1,
    ),
    "grade": _spec(feature_name="grade", actionable=False, direction="any"),
    "sub_grade": _spec(feature_name="sub_grade", actionable=False, direction="any"),
    "purpose": _spec(feature_name="purpose", actionable=False, direction="any"),
    "application_type": _spec(feature_name="application_type", actionable=False, direction="any"),
    "emp_title": _spec(feature_name="emp_title", actionable=False, direction="any"),
    "emp_length": _spec(feature_name="emp_length", actionable=False, direction="any"),
    "home_ownership": _spec(feature_name="home_ownership", actionable=False, direction="any"),
    "addr_state": _spec(feature_name="addr_state", actionable=False, direction="any"),
    "zip_code": _spec(feature_name="zip_code", actionable=False, direction="any"),
    "earliest_cr_line": _spec(feature_name="earliest_cr_line", actionable=False, direction="any"),
    "issue_d": _spec(feature_name="issue_d", actionable=False, direction="any"),
    "initial_list_status": _spec(feature_name="initial_list_status", actionable=False, direction="any"),
    "debt_settlement_flag": _spec(feature_name="debt_settlement_flag", actionable=False, direction="any"),
    "disbursement_method": _spec(feature_name="disbursement_method", actionable=False, direction="any"),
    "annual_inc": _spec(
        feature_name="annual_inc",
        actionable=True,
        direction="increase",
        action_key="increase_regular_income",
        min_val=0.0,
        step=2000.0,
        cost_weight=0.1,
        time_months=6,
    ),
    "verification_status": _spec(
        feature_name="verification_status",
        actionable=True,
        direction="increase",
        action_key="verify_income_documentation",
        step=1.0,
        cost_weight=0.05,
        time_months=1,
    ),
    "dti": _spec(
        feature_name="dti",
        actionable=True,
        direction="decrease",
        action_key="reduce_spending",
        min_val=0.0,
        step=1.0,
        cost_weight=0.6,
        time_months=1,
    ),
    "revol_bal": _spec(
        feature_name="revol_bal",
        actionable=True,
        direction="decrease",
        action_key="debt_consolidation",
        min_val=0.0,
        step=500.0,
        cost_weight=0.7,
        time_months=1,
    ),
    "revol_util": _spec(
        feature_name="revol_util",
        actionable=True,
        direction="decrease",
        action_key="limit_credit_usage",
        min_val=0.0,
        step=2.0,
        cost_weight=0.5,
        time_months=1,
    ),
    "fico_range_low": _spec(
        feature_name="fico_range_low",
        actionable=True,
        direction="increase",
        action_key="improve_payment_consistency",
        step=5.0,
        cost_weight=0.2,
        time_months=6,
    ),
    "fico_range_high": _spec(
        feature_name="fico_range_high",
        actionable=True,
        direction="increase",
        action_key="improve_payment_consistency",
        step=5.0,
        cost_weight=0.2,
        time_months=6,
    ),
    "last_fico_range_low": _spec(
        feature_name="last_fico_range_low",
        actionable=True,
        direction="increase",
        action_key="improve_payment_consistency",
        step=5.0,
        cost_weight=0.2,
        time_months=3,
    ),
    "last_fico_range_high": _spec(
        feature_name="last_fico_range_high",
        actionable=True,
        direction="increase",
        action_key="improve_payment_consistency",
        step=5.0,
        cost_weight=0.2,
        time_months=3,
    ),
    "tot_cur_bal": _spec(
        feature_name="tot_cur_bal",
        actionable=True,
        direction="decrease",
        action_key="debt_consolidation",
        min_val=0.0,
        step=500.0,
        cost_weight=0.6,
        time_months=6,
    ),
    "total_rev_hi_lim": _spec(
        feature_name="total_rev_hi_lim",
        actionable=True,
        direction="increase",
        action_key="credit_limit_adjustment",
        min_val=0.0,
        step=1000.0,
        cost_weight=0.1,
        time_months=3,
    ),
    "total_bal_ex_mort": _spec(
        feature_name="total_bal_ex_mort",
        actionable=True,
        direction="decrease",
        action_key="debt_consolidation",
        min_val=0.0,
        step=500.0,
        cost_weight=0.6,
        time_months=6,
    ),
    "total_bc_limit": _spec(
        feature_name="total_bc_limit",
        actionable=True,
        direction="increase",
        action_key="credit_limit_adjustment",
        step=1000.0,
        cost_weight=0.1,
        time_months=3,
    ),
    "tot_hi_cred_lim": _spec(
        feature_name="tot_hi_cred_lim",
        actionable=True,
        direction="increase",
        action_key="credit_limit_adjustment",
        step=1000.0,
        cost_weight=0.1,
        time_months=3,
    ),
    "open_acc": _spec(feature_name="open_acc", actionable=False, direction="any"),
    "total_acc": _spec(feature_name="total_acc", actionable=False, direction="any"),
    "mort_acc": _spec(feature_name="mort_acc", actionable=False, direction="any"),
    "delinq_2yrs": _spec(feature_name="delinq_2yrs", actionable=False, direction="any"),
    "inq_last_6mths": _spec(feature_name="inq_last_6mths", actionable=False, direction="any"),
    "pub_rec": _spec(feature_name="pub_rec", actionable=False, direction="any"),
    "pub_rec_bankruptcies": _spec(feature_name="pub_rec_bankruptcies", actionable=False, direction="any"),
    "chargeoff_within_12_mths": _spec(feature_name="chargeoff_within_12_mths", actionable=False, direction="any"),
    "tax_liens": _spec(feature_name="tax_liens", actionable=False, direction="any"),
    "acc_open_past_24mths": _spec(feature_name="acc_open_past_24mths", actionable=False, direction="any"),
    "tot_coll_amt": _spec(
        feature_name="tot_coll_amt",
        actionable=True,
        direction="decrease",
        action_key="settlement_discount",
        min_val=0.0,
        step=100.0,
        cost_weight=0.9,
        time_months=6,
    ),
    "acc_now_delinq": _spec(
        feature_name="acc_now_delinq",
        actionable=True,
        direction="decrease",
        action_key="installment_plan",
        min_val=0.0,
        max_val=1.0,
        step=1.0,
        cost_weight=0.9,
        time_months=1,
    ),
    "delinq_amnt": _spec(
        feature_name="delinq_amnt",
        actionable=True,
        direction="decrease",
        action_key="installment_plan",
        min_val=0.0,
        step=100.0,
        cost_weight=0.9,
        time_months=1,
    ),
    "collections_12_mths_ex_med": _spec(
        feature_name="collections_12_mths_ex_med",
        actionable=True,
        direction="decrease",
        action_key="installment_plan",
        min_val=0.0,
        step=1.0,
        cost_weight=0.9,
        time_months=1,
    ),
}


def get_actionable_features() -> list[str]:
    return [name for name, spec in ACTION_SPACE.items() if spec.actionable]


def get_action_spec(feature_name: str) -> ActionSpec:
    if feature_name not in ACTION_SPACE:
        raise KeyError(
            f"'{feature_name}' ACTION_SPACE icinde tanimli degil. "
            f"features_48.yaml ile senkron mu?"
        )
    return ACTION_SPACE[feature_name]


def get_action_template(action_key: str) -> ActionTemplate:
    if action_key not in ACTION_CATALOG:
        raise KeyError(f"'{action_key}' ACTION_CATALOG icinde tanimli degil.")
    return ACTION_CATALOG[action_key]


def derive_action_group_id(action_key: str | None, action_month: int | None = None) -> str | None:
    key = str(action_key or "").strip()
    if not key:
        return None
    if action_month is None:
        return key
    return f"{key}:m{max(1, int(action_month))}"


def get_action_metadata(
    feature_name: str,
    *,
    action_month: int | None = None,
    action_group_id: str | None = None,
) -> dict[str, Any]:
    spec = get_action_spec(feature_name)
    if not spec.action_key:
        return {
            "action_key": None,
            "action_class": None,
            "action_title": "",
            "action_group_id": action_group_id,
            "composite_action": False,
            "requires_institutional_approval": False,
            "approval_pending_semantic_only": False,
            "prerequisite_tags": [],
            "conflict_tags": [],
        }
    template = get_action_template(spec.action_key)
    return {
        "action_key": template.action_key,
        "action_class": template.action_class,
        "action_title": template.title,
        "action_group_id": action_group_id or derive_action_group_id(template.action_key, action_month),
        "composite_action": len(template.feature_names) > 1,
        "requires_institutional_approval": bool(template.requires_institutional_approval),
        "approval_pending_semantic_only": bool(template.approval_pending_semantic_only),
        "prerequisite_tags": list(template.prerequisite_tags),
        "conflict_tags": list(template.conflict_tags),
    }


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
