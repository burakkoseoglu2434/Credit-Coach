"""
recourse/action_space.py
========================
Feature bazli aksiyon uzayi tanimlari.

Phase 12 ile birlikte bu modul yalnizca "hangi feature degisir" bilgisini
degil, bu degisimin hangi gercek dunya action semantigine ait oldugunu da
tasir. Brownfield uyumluluk icin generator hala feature-level effect uzerinden
calisir; fakat her actionable spec artik bir `action_key`, `action_owner`
ve `action_category` tasir.

Phase 54: Canonical ActionOwner / ActionCategory taxonomy replaces the
legacy ActionClass / ActionFamily literals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ActionOwner = Literal["customer", "institution", "hybrid"]
ActionCategory = Literal[
    "utilization_capacity",
    "burden_reduction",
    "delinquency_cleanup",
    "credit_structure",
    "income_trust",
    "application_parameters",
    "institution_relief",
]
NumericUnit = Literal[
    "currency",
    "percentage_points",
    "ratio",
    "score_points",
    "months",
    "boolean_state",
    "count",
]


@dataclass(frozen=True)
class ActionTemplate:
    action_key: str
    action_owner: ActionOwner
    action_category: ActionCategory
    title: str
    action_type: str = ""
    description: str = ""
    primary_features_impacted: tuple[str, ...] = field(default_factory=tuple)
    primary_target_feature_name: str | None = None
    dice_eligible: bool = False
    heuristic_only: bool = False
    requires_numeric_target: bool = False
    requires_institutional_approval: bool = False
    approval_pending_semantic_only: bool = False
    institutional_approval_state: Literal["not_required", "approved", "pending", "unknown"] = "not_required"
    offer_type: str | None = None
    requires_acceptance: bool = False
    offer_family: str | None = None
    offer_scoring_profile: str | None = None
    term_generation_rule: str | None = None
    offer_policy_arm: str | None = None
    provides_tags: tuple[str, ...] = field(default_factory=tuple)
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
    action_owner: ActionOwner | None = None
    action_category: ActionCategory | None = None
    action_title: str = ""
    primary_features_impacted: tuple[str, ...] = field(default_factory=tuple)
    primary_target_feature_name: str | None = None
    dice_eligible: bool | None = None
    heuristic_only: bool | None = None
    requires_numeric_target: bool | None = None
    requires_institutional_approval: bool = False
    approval_pending_semantic_only: bool = False
    institutional_approval_state: Literal["not_required", "approved", "pending", "unknown"] = "not_required"
    offer_type: str | None = None
    requires_acceptance: bool = False
    offer_family: str | None = None
    offer_scoring_profile: str | None = None
    term_generation_rule: str | None = None
    offer_policy_arm: str | None = None
    provides_tags: tuple[str, ...] = field(default_factory=tuple)
    prerequisite_tags: tuple[str, ...] = field(default_factory=tuple)
    conflict_tags: tuple[str, ...] = field(default_factory=tuple)


ACTION_CATALOG: dict[str, ActionTemplate] = {
    "adjust_requested_loan_amount": ActionTemplate(
        action_key="adjust_requested_loan_amount",
        action_type="adjustment",
        action_owner="customer",
        action_category="application_parameters",
        title="Adjust requested loan amount",
        description="Reduce the requested loan size to improve affordability and approval odds.",
        primary_features_impacted=("loan_amnt",),
        primary_target_feature_name="loan_amnt",
        requires_numeric_target=True,
    ),
    "refinance": ActionTemplate(
        action_key="refinance",
        action_type="restructure",
        action_owner="hybrid",
        action_category="credit_structure",
        title="Refinance or restructure debt",
        description="Use refinancing to improve rate and installment affordability.",
        primary_features_impacted=("int_rate", "installment"),
        primary_target_feature_name="installment",
        requires_numeric_target=True,
        prerequisite_tags=("stable_income",),
    ),
    "increase_regular_income": ActionTemplate(
        action_key="increase_regular_income",
        action_type="documentation",
        action_owner="customer",
        action_category="income_trust",
        title="Increase regular income",
        description="Improve recurring income through additional work or stable earnings.",
        primary_features_impacted=("annual_inc",),
        primary_target_feature_name="annual_inc",
        requires_numeric_target=True,
        provides_tags=("stable_income",),
    ),
    "verify_income_documentation": ActionTemplate(
        action_key="verify_income_documentation",
        action_type="documentation",
        action_owner="customer",
        action_category="income_trust",
        title="Verify income documentation",
        description="Complete documentation or verification steps to strengthen the file.",
        primary_features_impacted=("verification_status",),
        primary_target_feature_name="verification_status",
        provides_tags=("income_verified",),
    ),
    "reduce_spending": ActionTemplate(
        action_key="reduce_spending",
        action_type="behavioral",
        action_owner="customer",
        action_category="utilization_capacity",
        title="Reduce spending pressure",
        description="Reduce ongoing spending to improve debt-to-income behavior.",
        primary_features_impacted=("dti",),
        primary_target_feature_name="dti",
        heuristic_only=True,
    ),
    "debt_consolidation": ActionTemplate(
        action_key="debt_consolidation",
        action_type="restructure",
        action_owner="hybrid",
        action_category="credit_structure",
        title="Consolidate revolving debt",
        description="Use consolidation or structured repayment to reduce revolving balances.",
        primary_features_impacted=("revol_bal", "tot_cur_bal", "total_bal_ex_mort"),
        primary_target_feature_name="revol_bal",
        requires_numeric_target=True,
        conflict_tags=("settlement_discount",),
    ),
    "limit_credit_usage": ActionTemplate(
        action_key="limit_credit_usage",
        action_type="behavioral",
        action_owner="customer",
        action_category="utilization_capacity",
        title="Limit credit usage",
        description="Reduce revolving utilization and slow new card usage.",
        primary_features_impacted=("revol_util",),
        primary_target_feature_name="revol_util",
        heuristic_only=True,
    ),
    "improve_payment_consistency": ActionTemplate(
        action_key="improve_payment_consistency",
        action_type="behavioral",
        action_owner="customer",
        action_category="delinquency_cleanup",
        title="Improve payment consistency",
        description="Build more consistent repayment behavior over time.",
        primary_features_impacted=("fico_range_low", "fico_range_high", "last_fico_range_low", "last_fico_range_high"),
        primary_target_feature_name="last_fico_range_low",
        heuristic_only=True,
    ),
    "credit_limit_adjustment": ActionTemplate(
        action_key="credit_limit_adjustment",
        action_type="institutional",
        action_owner="institution",
        action_category="institution_relief",
        title="Request or negotiate credit limit adjustment",
        description="Institution-mediated credit limit changes can improve utilization headroom.",
        primary_features_impacted=("total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim"),
        primary_target_feature_name="total_rev_hi_lim",
        dice_eligible=True,
        requires_numeric_target=True,
        requires_institutional_approval=True,
        institutional_approval_state="pending",
        offer_type="credit_limit_adjustment",
        requires_acceptance=False,
        offer_family="limit_management",
        offer_scoring_profile="limit_adjustment_v1",
        term_generation_rule="credit_limit_adjustment_terms_v1",
        offer_policy_arm="credit_limit_adjustment_policy_v1",
    ),
    "settlement_discount": ActionTemplate(
        action_key="settlement_discount",
        action_type="institutional",
        action_owner="institution",
        action_category="burden_reduction",
        title="Negotiate settlement discount",
        description="Use an institution-approved settlement to reduce collections pressure.",
        primary_features_impacted=("tot_coll_amt",),
        primary_target_feature_name="tot_coll_amt",
        dice_eligible=True,
        requires_numeric_target=True,
        requires_institutional_approval=True,
        institutional_approval_state="approved",
        offer_type="discount_offer",
        requires_acceptance=True,
        offer_family="hardship_relief",
        offer_scoring_profile="discount_offer_v1",
        term_generation_rule="discount_offer_terms_v1",
        offer_policy_arm="discount_offer_policy_v1",
        conflict_tags=("installment_plan",),
    ),
    "installment_plan": ActionTemplate(
        action_key="installment_plan",
        action_type="institutional",
        action_owner="institution",
        action_category="burden_reduction",
        title="Enter an installment plan",
        description="Restructure delinquent balances into an approved installment plan.",
        primary_features_impacted=("acc_now_delinq", "delinq_amnt", "collections_12_mths_ex_med"),
        primary_target_feature_name="delinq_amnt",
        dice_eligible=True,
        requires_numeric_target=True,
        requires_institutional_approval=True,
        institutional_approval_state="approved",
        offer_type="installment_terms",
        requires_acceptance=True,
        offer_family="payment_relief",
        offer_scoring_profile="installment_terms_v1",
        term_generation_rule="installment_terms_v1",
        offer_policy_arm="installment_terms_policy_v1",
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
        action_owner=template.action_owner if template else None,
        action_category=template.action_category if template else None,
        action_title=template.title if template else "",
        primary_features_impacted=tuple(template.primary_features_impacted) if template else (),
        primary_target_feature_name=template.primary_target_feature_name if template else None,
        dice_eligible=bool(template.dice_eligible) if template else None,
        heuristic_only=bool(template.heuristic_only) if template else None,
        requires_numeric_target=bool(template.requires_numeric_target) if template else None,
        requires_institutional_approval=bool(template.requires_institutional_approval) if template else False,
        approval_pending_semantic_only=bool(template.approval_pending_semantic_only) if template else False,
        institutional_approval_state=template.institutional_approval_state if template else "not_required",
        offer_type=template.offer_type if template else None,
        requires_acceptance=bool(template.requires_acceptance) if template else False,
        offer_family=template.offer_family if template else None,
        offer_scoring_profile=template.offer_scoring_profile if template else None,
        term_generation_rule=template.term_generation_rule if template else None,
        offer_policy_arm=template.offer_policy_arm if template else None,
        provides_tags=tuple(template.provides_tags) if template else (),
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


@dataclass(frozen=True)
class NumericTargetRule:
    metric_key: str
    unit: NumericUnit
    primary_for_action: bool = True


ACTION_CATEGORY_NUMERIC_DEFAULTS: dict[ActionCategory, NumericTargetRule] = {
    "application_parameters": NumericTargetRule(metric_key="requested_loan_amount", unit="currency"),
    "credit_structure": NumericTargetRule(metric_key="monthly_payment_amount", unit="currency"),
    "income_trust": NumericTargetRule(metric_key="documented_income_amount", unit="currency"),
    "utilization_capacity": NumericTargetRule(metric_key="credit_utilization_pct", unit="percentage_points"),
    "delinquency_cleanup": NumericTargetRule(metric_key="credit_score_points", unit="score_points"),
    "institution_relief": NumericTargetRule(metric_key="credit_limit_amount", unit="currency"),
    "burden_reduction": NumericTargetRule(metric_key="delinquent_balance_amount", unit="currency"),
}


FEATURE_NUMERIC_OVERRIDES: dict[str, NumericTargetRule] = {
    "loan_amnt": NumericTargetRule(metric_key="requested_loan_amount", unit="currency"),
    "int_rate": NumericTargetRule(metric_key="interest_rate_pct", unit="percentage_points", primary_for_action=False),
    "installment": NumericTargetRule(metric_key="monthly_payment_amount", unit="currency", primary_for_action=True),
    "annual_inc": NumericTargetRule(metric_key="documented_income_amount", unit="currency"),
    "verification_status": NumericTargetRule(metric_key="income_verification_state", unit="boolean_state"),
    "dti": NumericTargetRule(metric_key="debt_to_income_pct", unit="percentage_points"),
    "revol_bal": NumericTargetRule(metric_key="revolving_balance_amount", unit="currency", primary_for_action=True),
    "tot_cur_bal": NumericTargetRule(metric_key="total_current_balance_amount", unit="currency", primary_for_action=False),
    "total_bal_ex_mort": NumericTargetRule(metric_key="non_mortgage_balance_amount", unit="currency", primary_for_action=False),
    "revol_util": NumericTargetRule(metric_key="credit_utilization_pct", unit="percentage_points"),
    "fico_range_low": NumericTargetRule(metric_key="credit_score_points", unit="score_points", primary_for_action=False),
    "fico_range_high": NumericTargetRule(metric_key="credit_score_points", unit="score_points", primary_for_action=False),
    "last_fico_range_low": NumericTargetRule(metric_key="credit_score_points", unit="score_points", primary_for_action=True),
    "last_fico_range_high": NumericTargetRule(metric_key="credit_score_points", unit="score_points", primary_for_action=False),
    "total_rev_hi_lim": NumericTargetRule(metric_key="credit_limit_amount", unit="currency", primary_for_action=True),
    "total_bc_limit": NumericTargetRule(metric_key="bankcard_limit_amount", unit="currency", primary_for_action=False),
    "tot_hi_cred_lim": NumericTargetRule(metric_key="total_high_credit_limit_amount", unit="currency", primary_for_action=False),
    "tot_coll_amt": NumericTargetRule(metric_key="delinquent_balance_amount", unit="currency"),
    "acc_now_delinq": NumericTargetRule(metric_key="delinquent_accounts_count", unit="count", primary_for_action=False),
    "delinq_amnt": NumericTargetRule(metric_key="delinquent_balance_amount", unit="currency", primary_for_action=True),
    "collections_12_mths_ex_med": NumericTargetRule(
        metric_key="recent_collections_count",
        unit="count",
        primary_for_action=False,
    ),
}


def get_actionable_features() -> list[str]:
    actionable = []
    for name, spec in ACTION_SPACE.items():
        if not spec.actionable:
            continue
        _validate_action_mapping(name, spec)
        actionable.append(name)
    return actionable


def get_action_spec(feature_name: str) -> ActionSpec:
    if feature_name not in ACTION_SPACE:
        raise KeyError(
            f"'{feature_name}' ACTION_SPACE icinde tanimli degil. "
            f"features_48.yaml ile senkron mu?"
        )
    spec = ACTION_SPACE[feature_name]
    _validate_action_mapping(feature_name, spec)
    return spec


def get_action_template(action_key: str) -> ActionTemplate:
    if action_key not in ACTION_CATALOG:
        raise KeyError(f"'{action_key}' ACTION_CATALOG icinde tanimli degil.")
    return ACTION_CATALOG[action_key]


def _validate_action_mapping(feature_name: str, spec: ActionSpec) -> None:
    if not spec.actionable:
        return
    if not spec.action_key:
        raise ValueError(
            f"Actionable feature '{feature_name}' icin canonical action_key eksik. "
            "Phase 30 kontrati raw-feature fallback'i kabul etmez."
        )
    if spec.action_key not in ACTION_CATALOG:
        raise KeyError(
            f"Actionable feature '{feature_name}' bilinmeyen action_key='{spec.action_key}' kullaniyor."
        )
    template = ACTION_CATALOG[spec.action_key]
    if not spec.action_owner or spec.action_owner != template.action_owner:
        raise ValueError(
            f"Actionable feature '{feature_name}' icin action_owner kontrati bozuk: "
            f"spec={spec.action_owner!r}, catalog={template.action_owner!r}"
        )
    if not spec.action_category or spec.action_category != template.action_category:
        raise ValueError(
            f"Actionable feature '{feature_name}' icin action_category kontrati bozuk: "
            f"spec={spec.action_category!r}, catalog={template.action_category!r}"
        )
    if not spec.action_title or spec.action_title != template.title:
        raise ValueError(
            f"Actionable feature '{feature_name}' icin action_title kontrati bozuk: "
            f"spec={spec.action_title!r}, catalog={template.title!r}"
        )
    if spec.primary_target_feature_name is None:
        raise ValueError(f"Actionable feature '{feature_name}' icin primary_target_feature_name eksik.")
    if spec.action_category not in ACTION_CATEGORY_NUMERIC_DEFAULTS:
        raise ValueError(
            f"Actionable feature '{feature_name}' icin numeric category default eksik: "
            f"action_category={spec.action_category!r}"
        )


def validate_action_space_contract() -> list[str]:
    errors: list[str] = []
    for name, spec in ACTION_SPACE.items():
        try:
            _validate_action_mapping(name, spec)
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
    return errors


def _phase_token_for_month(action_month: int | None) -> str:
    month = max(1, int(action_month or 1))
    if month <= 1:
        return "phase_1_stabilize"
    if month <= 3:
        return "phase_2_build"
    return "phase_3_optimize"


def derive_action_group_id(
    action_key: str | None,
    action_month: int | None = None,
    *,
    action_phase: str | None = None,
) -> str | None:
    key = str(action_key or "").strip()
    if not key:
        return None
    phase_token = str(action_phase or "").strip() or _phase_token_for_month(action_month)
    return f"{key}:{phase_token}"


def get_action_metadata(
    feature_name: str,
    *,
    action_month: int | None = None,
    action_phase: str | None = None,
    action_group_id: str | None = None,
) -> dict[str, Any]:
    spec = get_action_spec(feature_name)
    if not spec.action_key:
        return {
            "action_key": None,
            "action_owner": None,
            "action_category": None,
            "action_title": "",
            "action_description": "",
            "action_group_id": action_group_id,
            "composite_action": False,
            "requires_institutional_approval": False,
            "approval_pending_semantic_only": False,
            "institutional_approval_state": "not_required",
            "offer_type": None,
            "requires_acceptance": False,
            "offer_family": None,
            "offer_scoring_profile": None,
            "term_generation_rule": None,
            "offer_policy_arm": None,
            "provides_tags": [],
            "prerequisite_tags": [],
            "conflict_tags": [],
            "primary_numeric_target": None,
        }
    assert spec.action_key is not None
    template = get_action_template(spec.action_key)
    numeric_target = get_numeric_target_metadata(feature_name, action_month=action_month)
    return {
        "action_key": template.action_key,
        "action_owner": template.action_owner,
        "action_category": template.action_category,
        "action_title": template.title,
        "action_description": template.description,
        "action_group_id": action_group_id
        or derive_action_group_id(template.action_key, action_month, action_phase=action_phase),
        "composite_action": len(template.primary_features_impacted) > 1,
        "requires_institutional_approval": bool(template.requires_institutional_approval),
        "approval_pending_semantic_only": bool(template.approval_pending_semantic_only),
        "institutional_approval_state": str(template.institutional_approval_state),
        "offer_type": template.offer_type,
        "requires_acceptance": bool(template.requires_acceptance),
        "offer_family": template.offer_family,
        "offer_scoring_profile": template.offer_scoring_profile,
        "term_generation_rule": template.term_generation_rule,
        "offer_policy_arm": template.offer_policy_arm,
        "provides_tags": list(template.provides_tags),
        "prerequisite_tags": list(template.prerequisite_tags),
        "conflict_tags": list(template.conflict_tags),
        "primary_numeric_target": numeric_target,
    }


def get_numeric_target_metadata(
    feature_name: str,
    *,
    action_month: int | None = None,
) -> dict[str, Any]:
    spec = get_action_spec(feature_name)
    if not spec.action_key or not spec.action_category:
        return {
            "metric_key": None,
            "unit": None,
            "direction": None,
            "due_month": None,
            "primary_target_feature_name": None,
            "is_primary_target": False,
        }
    action_key: str = spec.action_key
    template = get_action_template(action_key)
    primary_target_feature_name = str(
        template.primary_target_feature_name
        or spec.primary_target_feature_name
        or (template.primary_features_impacted[0] if template.primary_features_impacted else feature_name)
    )
    category_default = ACTION_CATEGORY_NUMERIC_DEFAULTS[template.action_category]
    override = FEATURE_NUMERIC_OVERRIDES.get(feature_name)
    rule = override or category_default
    is_primary_target = bool(rule.primary_for_action and feature_name == primary_target_feature_name)
    return {
        "metric_key": str(rule.metric_key),
        "unit": str(rule.unit),
        "direction": str(spec.direction),
        "due_month": int(max(1, int(action_month or spec.time_months))),
        "primary_target_feature_name": primary_target_feature_name,
        "is_primary_target": is_primary_target,
        "rule_source": "feature_override" if override is not None else "action_category_default",
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
