from __future__ import annotations

from typing import Any

import pandas as pd

from credit_coach.recourse.action_space import (
    PHASE_57_INSTITUTION_RULE_CONTRACTS,
    get_institution_rule_contract,
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _first_present_feature(row: pd.Series, feature_names: tuple[str, ...]) -> tuple[str | None, float]:
    for feature_name in feature_names:
        if feature_name not in row.index:
            continue
        value = _safe_float(row.get(feature_name), 0.0)
        if abs(value) > 1e-9:
            return feature_name, value
    return None, 0.0


def _clamp(value: float, *, lo: float, hi: float) -> float:
    return float(min(max(float(value), float(lo)), float(hi)))


def _installment_rule_action(row: pd.Series) -> dict[str, Any] | None:
    contract = get_institution_rule_contract("installment_plan")
    delinquency_amount = _safe_float(row.get("delinq_amnt"), 0.0)
    delinquent_accounts = _safe_float(row.get("acc_now_delinq"), 0.0)
    collections_count = _safe_float(row.get("collections_12_mths_ex_med"), 0.0)
    annual_income = _safe_float(row.get("annual_inc"), 0.0)
    verification_status = _safe_float(row.get("verification_status"), 0.0)
    if delinquency_amount < 300.0:
        return None
    if annual_income < 18_000.0 and verification_status < 1.0:
        return None
    if delinquent_accounts <= 0.0 and collections_count <= 0.0:
        return None
    target = max(0.0, delinquency_amount - max(250.0, delinquency_amount * 0.35))
    return {
        "action_key": contract.action_key,
        "feature_name": contract.primary_anchor_feature,
        "current_value": delinquency_amount,
        "target_value": float(target),
        "trigger_family": contract.trigger_family,
    }


def _settlement_rule_action(row: pd.Series, *, installment_selected: bool) -> dict[str, Any] | None:
    contract = get_institution_rule_contract("settlement_discount")
    total_collections = _safe_float(row.get("tot_coll_amt"), 0.0)
    debt_settlement_flag = _safe_float(row.get("debt_settlement_flag"), 0.0)
    annual_income = _safe_float(row.get("annual_inc"), 0.0)
    delinquency_amount = _safe_float(row.get("delinq_amnt"), 0.0)
    if total_collections < 250.0 and debt_settlement_flag < 1.0:
        return None
    if installment_selected and delinquency_amount > 0.0 and annual_income >= 18_000.0:
        return None
    target = max(0.0, total_collections - max(150.0, total_collections * 0.30))
    return {
        "action_key": contract.action_key,
        "feature_name": contract.primary_anchor_feature,
        "current_value": total_collections,
        "target_value": float(target),
        "trigger_family": contract.trigger_family,
    }


def _credit_limit_rule_action(row: pd.Series, feature_cols: list[str]) -> dict[str, Any] | None:
    contract = get_institution_rule_contract("credit_limit_adjustment")
    limit_feature, current_limit = _first_present_feature(
        row,
        tuple(feature_name for feature_name in ("total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim") if feature_name in feature_cols),
    )
    if limit_feature not in {"total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim"}:
        return None
    revolving_balance = max(0.0, _safe_float(row.get("revol_bal"), 0.0))
    utilization_pct = max(0.0, _safe_float(row.get("revol_util"), 0.0))
    if current_limit <= 0.0:
        return None
    if revolving_balance <= 0.0 and utilization_pct < 58.0:
        return None
    utilization_ratio = utilization_pct / 100.0 if utilization_pct > 0.0 else revolving_balance / max(current_limit, 1.0)
    if utilization_ratio < 0.58:
        return None
    desired_limit = max(current_limit * 1.12, revolving_balance / 0.55 if revolving_balance > 0.0 else current_limit)
    target = _clamp(desired_limit, lo=current_limit + 250.0, hi=current_limit * 1.25)
    if target <= current_limit + 100.0:
        return None
    return {
        "action_key": contract.action_key,
        "feature_name": str(limit_feature),
        "current_value": current_limit,
        "target_value": float(target),
        "trigger_family": contract.trigger_family,
    }


def _debt_consolidation_rule_action(row: pd.Series) -> dict[str, Any] | None:
    contract = get_institution_rule_contract("debt_consolidation")
    revolving_balance = _safe_float(row.get("revol_bal"), 0.0)
    total_balance = _safe_float(row.get("total_bal_ex_mort"), 0.0)
    current_balance = max(revolving_balance, total_balance, _safe_float(row.get("tot_cur_bal"), 0.0))
    debt_to_income = _safe_float(row.get("dti"), 0.0)
    if revolving_balance < 4_000.0:
        return None
    if current_balance < 7_500.0 and debt_to_income < 24.0:
        return None
    target = max(0.0, revolving_balance - max(600.0, revolving_balance * 0.22))
    return {
        "action_key": contract.action_key,
        "feature_name": contract.primary_anchor_feature,
        "current_value": revolving_balance,
        "target_value": float(target),
        "trigger_family": contract.trigger_family,
    }


def generate_institution_rule_action_sets(
    row: pd.Series,
    *,
    feature_cols: list[str],
    max_candidates: int = 4,
) -> list[list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []

    installment = _installment_rule_action(row)
    if installment is not None:
        candidates.append(installment)

    settlement = _settlement_rule_action(row, installment_selected=installment is not None)
    if settlement is not None:
        candidates.append(settlement)

    credit_limit = _credit_limit_rule_action(row, feature_cols)
    if credit_limit is not None:
        candidates.append(credit_limit)

    consolidation = _debt_consolidation_rule_action(row)
    if consolidation is not None:
        candidates.append(consolidation)

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for candidate in candidates:
        dedupe_key = (str(candidate["action_key"]), str(candidate["feature_name"]))
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(candidate)
        if len(deduped) >= max(1, int(max_candidates)):
            break

    return [[candidate] for candidate in deduped]


def institution_rule_action_keys() -> list[str]:
    return sorted(PHASE_57_INSTITUTION_RULE_CONTRACTS)
