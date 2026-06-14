from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_recourse import _dice_plan_record
from credit_coach.coaching.planner import annotate_plan_planner_quality
from credit_coach.recourse.action_space import (
    get_action_template,
    get_institution_rule_contract,
    list_institution_rule_contracts,
)
from credit_coach.recourse.institution_quality import annotate_rule_candidate_quality
from credit_coach.recourse.institution_rules import generate_institution_rule_action_sets


class _DummyModel:
    def predict_proba(self, x):
        frame = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        revol_util = pd.to_numeric(frame.get("revol_util", pd.Series([55.0] * len(frame))), errors="coerce").fillna(55.0)
        pd_values = revol_util.div(100.0).clip(lower=0.05, upper=0.95)
        return pd.DataFrame({"good": 1.0 - pd_values, "bad": pd_values}).to_numpy()


def test_phase57_institution_rule_contracts_cover_first_wave_actions() -> None:
    contracts = list_institution_rule_contracts()

    assert [contract.action_key for contract in contracts] == [
        "credit_limit_adjustment",
        "debt_consolidation",
        "installment_plan",
        "settlement_discount",
    ]
    for contract in contracts:
        template = get_action_template(contract.action_key)
        assert contract.primary_anchor_feature == template.primary_target_feature_name
        assert contract.owner == template.action_owner


def test_generate_institution_rule_action_sets_emits_deterministic_first_wave_candidates() -> None:
    row = pd.Series(
        {
            "annual_inc": 48_000.0,
            "verification_status": 2.0,
            "revol_bal": 8_200.0,
            "revol_util": 71.0,
            "total_rev_hi_lim": 9_000.0,
            "dti": 29.0,
            "acc_now_delinq": 1.0,
            "delinq_amnt": 2_400.0,
            "collections_12_mths_ex_med": 2.0,
            "tot_coll_amt": 0.0,
        }
    )

    action_sets = generate_institution_rule_action_sets(
        row,
        feature_cols=list(row.index),
        max_candidates=4,
    )

    assert [action_set[0]["action_key"] for action_set in action_sets] == [
        "installment_plan",
        "credit_limit_adjustment",
        "debt_consolidation",
    ]


def test_rule_plan_record_serializes_credit_limit_adjustment_as_truthful_shell() -> None:
    row = pd.Series(
        {
            "annual_inc": 55_000.0,
            "verification_status": 2.0,
            "revol_bal": 4_800.0,
            "revol_util": 72.0,
            "total_rev_hi_lim": 6_000.0,
        }
    )

    plan = _dice_plan_record(
        idx=1,
        customer_id="cust-rule",
        run_id="run-rule",
        row=row,
        feature_cols=list(row.index),
        actions=[generate_institution_rule_action_sets(row, feature_cols=list(row.index), max_candidates=2)[0][0]],
        model=_DummyModel(),
        calibrator=None,
        tau=0.35,
        graph=None,
        source_tag="rule",
    )
    plan = annotate_rule_candidate_quality(plan)
    action = plan.actions[0]

    assert plan.plan_source == "rule"
    assert action.action_key == "credit_limit_adjustment"
    assert action.offer_required_flag is True
    assert action.offer_feasibility == "provisional"
    assert action.offer_contract is not None
    assert action.offer_contract.institutional_approval_state == "pending"
    assert annotate_plan_planner_quality(plan).contender_bucket == "APPROVAL_SHELL_ONLY"
    assert plan.rule_contender_eligible is False


def test_rule_plan_record_keeps_installment_offer_actionable_when_terms_are_complete() -> None:
    row = pd.Series(
        {
            "annual_inc": 62_000.0,
            "verification_status": 2.0,
            "delinq_amnt": 2_100.0,
            "acc_now_delinq": 1.0,
            "collections_12_mths_ex_med": 2.0,
            "revol_util": 42.0,
        }
    )
    installment_contract = get_institution_rule_contract("installment_plan")

    plan = _dice_plan_record(
        idx=1,
        customer_id="cust-installment",
        run_id="run-installment",
        row=row,
        feature_cols=list(row.index),
        actions=[
            {
                "action_key": installment_contract.action_key,
                "feature_name": installment_contract.primary_anchor_feature,
                "current_value": float(row["delinq_amnt"]),
                "target_value": 1_200.0,
            }
        ],
        model=_DummyModel(),
        calibrator=None,
        tau=0.35,
        graph=None,
        source_tag="rule",
    )
    plan = annotate_rule_candidate_quality(plan)
    action = plan.actions[0]

    assert action.offer_required_flag is True
    assert action.offer_feasibility == "active_rankable"
    assert plan.rule_annotation_complete is True
    assert plan.rule_semantic_quality_status == "valid"
    assert annotate_plan_planner_quality(plan).contender_bucket == "ACTIONABLE"
    assert plan.rule_contender_eligible is True
