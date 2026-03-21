"""
tests/test_action_space.py
==========================
Hafta 1 — Action space bütünlük testleri.

Test Senaryoları
---------------
1. test_action_space_has_48_entries       : Her feature için tanım var mı?
2. test_all_keys_are_strings              : Key'ler string mi?
3. test_actionable_flag_exists            : Her spec'te actionable alanı var mı?
4. test_some_features_are_actionable      : En az 1 actionable feature var mı?
5. test_some_features_are_immutable       : En az 1 immutable feature var mı?
6. test_direction_valid_values            : direction değerleri geçerli mi?
7. test_cost_weight_range                 : cost_weight 0-1 arasında mı?
8. test_time_months_positive              : time_months >= 1 mi?
9. test_coverage_against_48_yaml          : ACTION_SPACE, features_48.yaml'ı karşılıyor mu?
10. test_get_actionable_features           : Yardımcı fonksiyon çalışıyor mu?
"""

from __future__ import annotations

import pytest

from credit_coach.data.schema import PlanAction
from credit_coach.recourse.action_constraints import enforce_action_constraints
from credit_coach.recourse.action_space import (
    ACTION_CATALOG,
    ACTION_FAMILY_NUMERIC_DEFAULTS,
    ACTION_SPACE,
    FEATURE_NUMERIC_OVERRIDES,
    ActionSpec,
    derive_action_group_id,
    estimate_action_cost_usd,
    get_action_metadata,
    get_numeric_target_metadata,
    get_actionable_features,
    get_action_spec,
    get_action_template,
    validate_action_space_contract,
    validate_action_space_coverage,
)

VALID_DIRECTIONS = {"decrease", "increase", "any"}


class TestActionSpaceStructure:
    """ACTION_SPACE dict'inin yapısal bütünlüğünü doğrular."""

    def test_action_space_has_48_entries(self, feature_list_48: list[str]) -> None:
        """Her 48 feature için bir ActionSpec tanımı olmalı."""
        for feature in feature_list_48:
            assert feature in ACTION_SPACE, (
                f"ACTION_SPACE'te '{feature}' tanımı eksik. "
                "action_space.py güncellenmeli."
            )

    def test_all_keys_are_strings(self) -> None:
        """ACTION_SPACE key'leri string olmalı."""
        for key in ACTION_SPACE:
            assert isinstance(key, str), f"Key string değil: {key!r}"

    def test_all_values_are_action_spec(self) -> None:
        """ACTION_SPACE değerleri ActionSpec instance'ı olmalı."""
        for name, spec in ACTION_SPACE.items():
            assert isinstance(spec, ActionSpec), (
                f"'{name}' için ActionSpec bekleniyor, {type(spec)} bulundu."
            )

    def test_feature_name_matches_key(self) -> None:
        """spec.feature_name, dict key'i ile eşleşmeli."""
        for key, spec in ACTION_SPACE.items():
            assert spec.feature_name == key, (
                f"Tutarsızlık: key='{key}' ama spec.feature_name='{spec.feature_name}'"
            )


class TestActionableFlags:
    """Actionable/immutable ayrımının mantıksal bütünlüğünü test eder."""

    def test_some_features_are_actionable(self) -> None:
        """En az 10 actionable feature olmalı."""
        actionable = get_actionable_features()
        assert len(actionable) >= 10, (
            f"Çok az actionable feature: {len(actionable)}. En az 10 bekleniyor."
        )

    def test_some_features_are_immutable(self) -> None:
        """En az 5 immutable feature olmalı (loan_amnt, term, vb.)."""
        immutable = [name for name, spec in ACTION_SPACE.items() if not spec.actionable]
        assert len(immutable) >= 5, (
            f"Çok az immutable feature: {len(immutable)}."
        )

    def test_known_immutable_features(self) -> None:
        """Bilinen immutable feature'lar actionable=False olmalı."""
        # loan_amnt kasitli olarak actionable: urun/policy recourse ile
        # daha dusuk basvuru tutarina yonlendirme destekleniyor.
        known_immutable = ["funded_amnt", "term", "grade", "issue_d_year", "policy_code"]
        for feature in known_immutable:
            if feature in ACTION_SPACE:
                assert not ACTION_SPACE[feature].actionable, (
                    f"'{feature}' immutable olmalı ama actionable=True!"
                )

    def test_known_actionable_features(self) -> None:
        """Bilinen actionable feature'lar actionable=True olmalı."""
        known_actionable = ["dti", "annual_inc", "revol_util", "revol_bal"]
        for feature in known_actionable:
            if feature in ACTION_SPACE:
                assert ACTION_SPACE[feature].actionable, (
                    f"'{feature}' actionable olmalı ama actionable=False!"
                )


class TestActionSpecValues:
    """Her ActionSpec'in değer aralıklarını kontrol eder."""

    def test_direction_valid_values(self) -> None:
        """direction yalnızca 'decrease', 'increase', 'any' olabilir."""
        for name, spec in ACTION_SPACE.items():
            assert spec.direction in VALID_DIRECTIONS, (
                f"'{name}': geçersiz direction='{spec.direction}'. "
                f"Geçerli: {VALID_DIRECTIONS}"
            )

    def test_cost_weight_range(self) -> None:
        """cost_weight 0.0–1.0 arasında olmalı."""
        for name, spec in ACTION_SPACE.items():
            assert 0.0 <= spec.cost_weight <= 1.0, (
                f"'{name}': cost_weight={spec.cost_weight} aralık dışı [0, 1]."
            )

    def test_time_months_positive(self) -> None:
        """time_months >= 1 olmalı."""
        for name, spec in ACTION_SPACE.items():
            if spec.actionable:
                assert spec.time_months >= 1, (
                    f"'{name}': time_months={spec.time_months} geçersiz (min 1)."
                )

    def test_step_positive(self) -> None:
        """step > 0 olmalı."""
        for name, spec in ACTION_SPACE.items():
            assert spec.step > 0, f"'{name}': step={spec.step} sıfır veya negatif."

    def test_min_max_consistency(self) -> None:
        """min_val varsa max_val'dan küçük olmalı."""
        for name, spec in ACTION_SPACE.items():
            if spec.min_val is not None and spec.max_val is not None:
                assert spec.min_val < spec.max_val, (
                    f"'{name}': min_val={spec.min_val} >= max_val={spec.max_val}"
                )

    def test_actionable_specs_have_typed_action_metadata(self) -> None:
        """Actionable spec'ler explicit typed action metadata tasimali."""
        for name, spec in ACTION_SPACE.items():
            if not spec.actionable:
                continue
            assert spec.action_key, f"'{name}' icin action_key eksik."
            assert spec.action_class in {"behavioral", "structural", "institutional"}
            assert spec.action_family, f"'{name}' icin action_family eksik."
            assert spec.action_title, f"'{name}' icin action_title eksik."

    def test_action_space_contract_has_no_mapping_errors(self) -> None:
        """Actionable feature mapping kontrati Phase 30 sonrasinda temiz olmali."""
        assert validate_action_space_contract() == []


class TestTypedActionCatalog:
    """Phase 12 typed action taxonomy kontratini test eder."""

    def test_action_catalog_contains_locked_examples(self) -> None:
        for action_key in (
            "reduce_spending",
            "debt_consolidation",
            "refinance",
            "installment_plan",
            "settlement_discount",
        ):
            assert action_key in ACTION_CATALOG, f"'{action_key}' ACTION_CATALOG icinde olmali."

    def test_action_catalog_spans_all_three_classes(self) -> None:
        classes = {template.action_class for template in ACTION_CATALOG.values()}
        assert classes == {"behavioral", "structural", "institutional"}

    def test_action_catalog_exposes_families_for_all_templates(self) -> None:
        assert all(template.action_family for template in ACTION_CATALOG.values())
        families = {template.action_family for template in ACTION_CATALOG.values()}
        assert "debt_restructuring" in families
        assert "hardship_relief" in families

    def test_numeric_target_defaults_exist_for_all_action_families(self) -> None:
        families = {template.action_family for template in ACTION_CATALOG.values()}
        assert families <= set(ACTION_FAMILY_NUMERIC_DEFAULTS.keys())

    def test_get_action_template_returns_catalog_entry(self) -> None:
        template = get_action_template("refinance")
        assert template.action_class == "structural"
        assert template.action_family == "debt_restructuring"
        assert {"int_rate", "installment"} <= set(template.feature_names)
        assert template.primary_target_feature_name == "installment"

    def test_action_metadata_builds_shared_group_for_composite_actions(self) -> None:
        first = get_action_metadata("int_rate", action_month=3)
        second = get_action_metadata("installment", action_month=3)
        assert first["action_key"] == "refinance"
        assert first["action_family"] == "debt_restructuring"
        assert first["action_group_id"] == second["action_group_id"]
        assert derive_action_group_id("refinance", 3) == "refinance:phase_2_build"
        assert derive_action_group_id("refinance", 3) == first["action_group_id"]
        assert first["composite_action"] is True
        assert first["primary_numeric_target"]["metric_key"] == "interest_rate_pct"
        assert first["primary_numeric_target"]["unit"] == "percentage_points"
        assert first["primary_numeric_target"]["is_primary_target"] is False
        assert second["primary_numeric_target"]["metric_key"] == "monthly_payment_amount"
        assert second["primary_numeric_target"]["is_primary_target"] is True

    def test_numeric_target_metadata_uses_family_defaults_and_feature_overrides(self) -> None:
        annual_inc = get_numeric_target_metadata("annual_inc")
        dti = get_numeric_target_metadata("dti")
        int_rate = get_numeric_target_metadata("int_rate", action_month=3)
        installment = get_numeric_target_metadata("installment", action_month=3)
        assert annual_inc["metric_key"] == "documented_income_amount"
        assert annual_inc["unit"] == "currency"
        assert annual_inc["is_primary_target"] is True
        assert dti["metric_key"] == "debt_to_income_pct"
        assert dti["unit"] == "percentage_points"
        assert int_rate["metric_key"] == FEATURE_NUMERIC_OVERRIDES["int_rate"].metric_key
        assert int_rate["unit"] == "percentage_points"
        assert int_rate["due_month"] == 3
        assert int_rate["is_primary_target"] is False
        assert installment["metric_key"] == "monthly_payment_amount"
        assert installment["is_primary_target"] is True

    def test_action_catalog_exposes_dependency_and_provider_tags(self) -> None:
        refinance = get_action_template("refinance")
        income = get_action_template("increase_regular_income")
        settlement = get_action_template("settlement_discount")
        assert "stable_income" in refinance.prerequisite_tags
        assert "stable_income" in income.provides_tags
        assert "installment_plan" in settlement.conflict_tags

    def test_institutional_offer_actions_expose_offer_metadata(self) -> None:
        settlement = get_action_template("settlement_discount")
        installment = get_action_template("installment_plan")
        installment_meta = get_action_metadata("delinq_amnt", action_month=2)
        assert settlement.offer_type == "discount_offer"
        assert settlement.requires_acceptance is True
        assert installment.offer_type == "installment_terms"
        assert installment.offer_policy_arm == "installment_terms_policy_v1"
        assert installment_meta["offer_type"] == "installment_terms"
        assert installment_meta["requires_acceptance"] is True
        assert installment_meta["institutional_approval_state"] == "approved"

    def test_enforce_action_constraints_repairs_conflicting_groups(self) -> None:
        conflicting = [
            PlanAction(
                feature_name="revol_bal",
                current_value=12_000.0,
                target_value=10_500.0,
                delta=-1_500.0,
                time_months=2,
                estimated_cost_usd=40.0,
                action_key="debt_consolidation",
                action_class="structural",
                action_title="Consolidate revolving debt",
                action_group_id="debt_consolidation:phase_2_build",
                conflict_tags=["settlement_discount"],
            ),
            PlanAction(
                feature_name="tot_coll_amt",
                current_value=3_000.0,
                target_value=2_400.0,
                delta=-600.0,
                time_months=2,
                estimated_cost_usd=15.0,
                action_key="settlement_discount",
                action_class="institutional",
                action_title="Negotiate settlement discount",
                action_group_id="settlement_discount:phase_2_build",
                requires_institutional_approval=True,
                approval_pending_semantic_only=True,
                conflict_tags=["installment_plan"],
            ),
        ]

        result = enforce_action_constraints(conflicting, action_context={"annual_inc": 55_000.0, "dti": 22.0})

        assert result.status == "repaired"
        assert len(result.actions) == 1
        assert result.actions[0].action_key == "debt_consolidation"
        assert any(entry["event_type"] == "repair_dropped" for entry in result.trace)
        assert any(str(entry["reason_code"]).startswith("conflict_with:") for entry in result.trace)

    def test_enforce_action_constraints_supports_prerequisite_provider_and_provisional_status(self) -> None:
        actions = [
            PlanAction(
                feature_name="annual_inc",
                current_value=45_000.0,
                target_value=49_000.0,
                delta=4_000.0,
                time_months=3,
                estimated_cost_usd=20.0,
                action_key="increase_regular_income",
                action_class="behavioral",
                action_title="Increase regular income",
                action_group_id="increase_regular_income:phase_2_build",
            ),
            PlanAction(
                feature_name="int_rate",
                current_value=19.0,
                target_value=17.0,
                delta=-2.0,
                time_months=3,
                estimated_cost_usd=10.0,
                action_key="refinance",
                action_class="structural",
                action_title="Refinance or restructure debt",
                action_group_id="refinance:phase_2_build",
                prerequisite_tags=["stable_income"],
            ),
            PlanAction(
                feature_name="total_rev_hi_lim",
                current_value=6_000.0,
                target_value=7_500.0,
                delta=1_500.0,
                time_months=3,
                estimated_cost_usd=8.0,
                action_key="credit_limit_adjustment",
                action_class="institutional",
                action_title="Request or negotiate credit limit adjustment",
                action_group_id="credit_limit_adjustment:phase_2_build",
                requires_institutional_approval=True,
            ),
        ]

        result = enforce_action_constraints(actions, action_context={"annual_inc": 25_000.0, "dti": 39.0})

        assert result.status == "provisional"
        assert len(result.actions) == 3
        assert any(action.action_key == "refinance" for action in result.actions)
        provisional = next(action for action in result.actions if action.action_key == "credit_limit_adjustment")
        assert provisional.action_status == "provisional"
        assert "requires_institutional_approval" in provisional.diagnostic_flags


class TestHelperFunctions:
    """Yardımcı fonksiyonları test eder."""

    def test_get_actionable_features_returns_list(self) -> None:
        """get_actionable_features() list döndürmeli."""
        result = get_actionable_features()
        assert isinstance(result, list)

    def test_get_actionable_features_all_actionable(self) -> None:
        """Dönen liste sadece actionable feature'lar içermeli."""
        result = get_actionable_features()
        for name in result:
            assert ACTION_SPACE[name].actionable, f"'{name}' actionable değil!"

    def test_get_action_spec_known_feature(self) -> None:
        """Bilinen feature için get_action_spec() ActionSpec döndürmeli."""
        spec = get_action_spec("dti")
        assert isinstance(spec, ActionSpec)
        assert spec.feature_name == "dti"

    def test_get_action_spec_unknown_raises(self) -> None:
        """Bilinmeyen feature → KeyError."""
        with pytest.raises(KeyError):
            get_action_spec("this_feature_does_not_exist_xyz")

    def test_get_action_spec_hard_fails_for_unmapped_actionable_feature(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original = ACTION_SPACE["dti"]
        monkeypatch.setitem(
            ACTION_SPACE,
            "dti",
            ActionSpec(
                feature_name="dti",
                actionable=True,
                direction="decrease",
                action_key=None,
                action_class=None,
                action_family=None,
                action_title="",
                step=1.0,
                cost_weight=0.6,
                time_months=1,
            ),
        )

        with pytest.raises(ValueError, match="canonical action_key eksik"):
            get_action_spec("dti")

        monkeypatch.setitem(ACTION_SPACE, "dti", original)

    def test_validate_coverage_no_missing(self, feature_list_48: list[str]) -> None:
        """features_48.yaml listesi ACTION_SPACE tarafından tam kapsanmalı."""
        missing = validate_action_space_coverage(feature_list_48)
        assert not missing, (
            f"ACTION_SPACE'te şu feature'lar eksik: {missing}"
        )

    def test_estimate_action_cost_usd_is_scale_normalized(self) -> None:
        """Ayni relatif degisim farkli olceklerde benzer maliyet uretmeli."""
        spec = get_action_spec("annual_inc")
        c_small = estimate_action_cost_usd(10_000.0, 12_000.0, spec)
        c_large = estimate_action_cost_usd(100_000.0, 120_000.0, spec)
        assert abs(c_small - c_large) < 1e-6
