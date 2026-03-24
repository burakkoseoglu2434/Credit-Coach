from __future__ import annotations

from credit_coach.coaching.planner import choose_best_plan
from credit_coach.data.schema import PlanAction, PlanRecord, PrimaryNumericTarget
from credit_coach.recourse.recommendation_validity import (
    annotate_action_recommendation_validity,
    annotate_plan_recommendation_validity,
    filter_invalid_numeric_plans,
)


def _action(
    *,
    feature_name: str,
    current_value: float,
    target_value: float,
    metric_key: str,
    direction: str,
    action_key: str = "action",
    action_class: str = "behavioral",
    requires_institutional_approval: bool = False,
) -> PlanAction:
    return PlanAction(
        feature_name=feature_name,
        current_value=current_value,
        target_value=target_value,
        delta=target_value - current_value,
        time_months=1,
        action_key=action_key,
        action_class=action_class,
        requires_institutional_approval=requires_institutional_approval,
        primary_numeric_target=PrimaryNumericTarget(
            metric_key=metric_key,
            unit="currency" if "amount" in metric_key or "limit" in metric_key else "percentage_points",
            current_value=current_value,
            target_value=target_value,
            delta_value=target_value - current_value,
            due_month=1,
            direction=direction,  # type: ignore[arg-type]
            generation_notes=[],
            raw_generation_basis={},
        ),
    )


def _plan(plan_id: str, action: PlanAction, *, predicted_pd: float = 0.30) -> PlanRecord:
    return PlanRecord(
        plan_id=plan_id,
        customer_id="cust",
        run_id="run",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        predicted_pd=predicted_pd,
        plan_execution_probability=0.75,
        expected_pd_improvement=0.06,
        score=1.0,
        status="APPROVED",
        constraint_status="valid",
    )


def test_directional_hard_invalid_rules() -> None:
    installment = annotate_action_recommendation_validity(
        _action(
            feature_name="installment",
            current_value=278.6,
            target_value=455.5,
            metric_key="monthly_payment_amount",
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        )
    )
    utilization = annotate_action_recommendation_validity(
        _action(
            feature_name="revol_util",
            current_value=32.6,
            target_value=43.1,
            metric_key="credit_utilization_pct",
            direction="decrease",
            action_key="limit_credit_usage",
        )
    )
    income = annotate_action_recommendation_validity(
        _action(
            feature_name="annual_inc",
            current_value=56000.0,
            target_value=54000.0,
            metric_key="documented_income_amount",
            direction="increase",
            action_key="increase_regular_income",
        )
    )

    assert installment.recommendation_validity_status == "invalid"
    assert utilization.recommendation_validity_status == "invalid"
    assert income.recommendation_validity_status == "invalid"
    assert "directional_worsens_risk" in installment.recommendation_validity_codes
    assert "directional_worsens_risk" in utilization.recommendation_validity_codes
    assert "directional_worsens_risk" in income.recommendation_validity_codes


def test_no_effect_target_is_hard_invalid() -> None:
    action = annotate_action_recommendation_validity(
        _action(
            feature_name="loan_amnt",
            current_value=15000.0,
            target_value=15000.0,
            metric_key="requested_loan_amount",
            direction="decrease",
            action_key="adjust_requested_loan_amount",
            action_class="structural",
        )
    )

    assert action.recommendation_validity_status == "invalid"
    assert action.recommendation_validity_codes == ["no_effect_target"]


def test_credit_limit_adjustment_stays_valid_as_institution_condition() -> None:
    action = annotate_action_recommendation_validity(
        _action(
            feature_name="tot_hi_cred_lim",
            current_value=39850.0,
            target_value=40490.0,
            metric_key="total_high_credit_limit_amount",
            direction="increase",
            action_key="credit_limit_adjustment",
            action_class="institutional",
            requires_institutional_approval=True,
        )
    )

    assert action.recommendation_validity_status == "valid"
    assert action.recommendation_validity_codes == []


def test_economic_warning_rules() -> None:
    income = annotate_action_recommendation_validity(
        _action(
            feature_name="annual_inc",
            current_value=56000.0,
            target_value=70000.0,
            metric_key="documented_income_amount",
            direction="increase",
            action_key="increase_regular_income",
        )
    )
    utilization = annotate_action_recommendation_validity(
        _action(
            feature_name="revol_util",
            current_value=82.0,
            target_value=50.0,
            metric_key="credit_utilization_pct",
            direction="decrease",
            action_key="limit_credit_usage",
        ),
        customer_context={"revol_bal": 18000.0, "total_rev_hi_lim": 22000.0},
    )
    installment = annotate_action_recommendation_validity(
        _action(
            feature_name="installment",
            current_value=1000.0,
            target_value=300.0,
            metric_key="monthly_payment_amount",
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        )
    )
    loan_amount = annotate_action_recommendation_validity(
        _action(
            feature_name="loan_amnt",
            current_value=35000.0,
            target_value=20000.0,
            metric_key="requested_loan_amount",
            direction="decrease",
            action_key="adjust_requested_loan_amount",
            action_class="structural",
        )
    )
    dti = annotate_action_recommendation_validity(
        _action(
            feature_name="dti",
            current_value=35.0,
            target_value=20.0,
            metric_key="debt_to_income_pct",
            direction="decrease",
            action_key="reduce_spending",
        ),
        customer_context={"annual_inc": 120000.0},
    )

    for action in (income, utilization, installment, loan_amount, dti):
        assert action.recommendation_validity_status == "warning"
        assert action.recommendation_sanity_flag is True
        assert action.recommendation_warning_penalty > 0.0


def test_invalid_numeric_plans_are_filtered_from_selection() -> None:
    invalid_plan = annotate_plan_recommendation_validity(
        _plan(
            "invalid-plan",
            _action(
                feature_name="installment",
                current_value=278.6,
                target_value=455.5,
                metric_key="monthly_payment_amount",
                direction="decrease",
                action_key="refinance",
                action_class="structural",
            ),
            predicted_pd=0.29,
        )
    )
    valid_plan = annotate_plan_recommendation_validity(
        _plan(
            "valid-plan",
            _action(
                feature_name="installment",
                current_value=778.4,
                target_value=746.4,
                metric_key="monthly_payment_amount",
                direction="decrease",
                action_key="refinance",
                action_class="structural",
            ),
            predicted_pd=0.30,
        )
    )

    kept, removed = filter_invalid_numeric_plans([invalid_plan, valid_plan])
    assert [plan.plan_id for plan in kept] == ["valid-plan"]
    assert [plan.plan_id for plan in removed] == ["invalid-plan"]

    best = choose_best_plan([invalid_plan, valid_plan], base_pd=0.40, tau=0.35)
    assert best.plan_id == "valid-plan"


def test_warning_penalty_breaks_otherwise_close_tie() -> None:
    warning_plan = annotate_plan_recommendation_validity(
        _plan(
            "warning-plan",
            _action(
                feature_name="installment",
                current_value=1000.0,
                target_value=300.0,
                metric_key="monthly_payment_amount",
                direction="decrease",
                action_key="refinance",
                action_class="structural",
            ),
            predicted_pd=0.29,
        )
    )
    valid_plan = annotate_plan_recommendation_validity(
        _plan(
            "valid-plan",
            _action(
                feature_name="installment",
                current_value=778.4,
                target_value=746.4,
                metric_key="monthly_payment_amount",
                direction="decrease",
                action_key="refinance",
                action_class="structural",
            ),
            predicted_pd=0.30,
        )
    )

    best = choose_best_plan([warning_plan, valid_plan], base_pd=0.40, tau=0.35)
    assert best.plan_id == "valid-plan"
