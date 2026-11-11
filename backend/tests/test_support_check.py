import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from credit_coach.baseline import CSV
from credit_coach.contract import (
    ConditionalType,
    InnerStatus,
    OuterStatus,
    PublicReasonCode,
    ReasonCode,
    RuleId,
    SupportDecision,
    parse_input,
)
from credit_coach.decision_engine import decide, decide_with_support, to_public
from credit_coach.decision_scenarios import in_support_basvuru
from credit_coach.policy import load_policy
from credit_coach.support import load_support, violations

SUPPORT = load_support()
POLICY = load_policy("v1")
SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])


def girdi(basvuru, p=0.05, plan=True):
    return parse_input(
        {
            "basvuru": basvuru,
            "p_low": p,
            "p_point": p,
            "p_high": p,
            "ham_skor": p,
            "politika_surumu": "v1",
            "plan_available": plan,
        }
    )


def run(**changes):
    return decide_with_support(girdi({**in_support_basvuru(SUPPORT), **changes}), POLICY, SUPPORT)


def assert_not_evaluable(d, feature):
    assert isinstance(d, SupportDecision)
    assert d.dis_durum is OuterStatus.CONDITIONAL
    assert d.ic_durum is InnerStatus.NEEDS_REVIEW
    assert d.conditional_type is ConditionalType.DATA_ISSUE
    assert ReasonCode.OUT_OF_SUPPORT in d.gerekce_kodlari
    assert ReasonCode.PLAN_AVAILABLE not in d.gerekce_kodlari
    assert d.tetiklenen_kurallar == (RuleId.R0_SUPPORT_CHECK,)
    assert feature in d.destek_ihlalleri


# ---- acceptance (synthetic) ------------------------------------------------------------


def test_base_record_is_in_support():
    assert violations(in_support_basvuru(SUPPORT), SUPPORT) == ()


@pytest.mark.parametrize(
    ("changes", "feature"),
    [
        ({"fico_range_low": 600.0, "fico_range_high": 604.0}, "fico_range_low"),
        ({"dti": 55.0}, "dti"),
        ({"dti": 999.0}, "dti"),
        ({"application_type": "Joint App"}, "application_type"),
    ],
)
def test_acceptance_out_of_support_is_not_evaluable(changes, feature):
    assert_not_evaluable(run(**changes), feature)


def test_revol_util_150_is_inside_the_training_range_known_limit():
    # Training contains revol_util up to 892.3, so min/max support accepts 150. This is the
    # documented limit of the min/max rule (support.yaml bilinen_sinirlar), not a bug.
    assert SUPPORT.sayisal["revol_util"][1] > 150
    assert violations({**in_support_basvuru(SUPPORT), "revol_util": 150.0}, SUPPORT) == ()
    assert_not_evaluable(run(revol_util=SUPPORT.sayisal["revol_util"][1] + 0.1), "revol_util")


def test_public_view_has_no_internal_leak_and_shows_out_of_support():
    pub = to_public(run(dti=999.0))
    assert pub.dis_durum is OuterStatus.CONDITIONAL
    assert PublicReasonCode.OUT_OF_SUPPORT in pub.gerekce_kodlari
    assert pub.conditional_type is ConditionalType.DATA_ISSUE


def test_none_is_not_a_violation():
    assert violations({**in_support_basvuru(SUPPORT), "dti": None}, SUPPORT) == ()


def test_multiple_violations_are_sorted_and_all_listed():
    d = run(dti=999.0, application_type="Joint App", fico_range_low=600.0)
    assert d.destek_ihlalleri == ("application_type", "dti", "fico_range_low")


# ---- properties ------------------------------------------------------------------------


@st.composite
def in_support_records(draw):
    b = {}
    for n, (lo, hi) in SUPPORT.sayisal.items():
        b[n] = draw(st.floats(min_value=lo, max_value=hi, allow_nan=False, allow_infinity=False))
    for n, vals in SUPPORT.kategorik.items():
        b[n] = draw(st.sampled_from(sorted(vals)))
    b["earliest_cr_line"] = "Jan-2000"
    return b


probs = st.lists(st.floats(0, 1, allow_nan=False), min_size=3, max_size=3).map(sorted)


def _input(b, p, plan):
    lo, pt, hi = p
    return parse_input(
        {
            "basvuru": b,
            "p_low": lo,
            "p_point": pt,
            "p_high": hi,
            "ham_skor": pt,
            "politika_surumu": "v1",
            "plan_available": plan,
        }
    )


@SETTINGS
@given(in_support_records(), probs, st.sampled_from([True, False, None]))
def test_inside_support_behaviour_is_unchanged(b, p, plan):
    g = _input(b, p, plan)
    assert violations(b, SUPPORT) == ()
    assert decide_with_support(g, POLICY, SUPPORT) == decide(g, POLICY)


@st.composite
def one_violation(draw):
    b = draw(in_support_records())
    name = draw(st.sampled_from(sorted(SUPPORT.sayisal) + sorted(SUPPORT.kategorik)))
    if name in SUPPORT.sayisal:
        lo, hi = SUPPORT.sayisal[name]
        b[name] = draw(st.sampled_from([hi + 1.0 + abs(hi) * 0.01, lo - 1.0 - abs(lo) * 0.01]))
    else:
        b[name] = "UNSEEN_VALUE"
    return b, name


@SETTINGS
@given(one_violation(), probs, st.sampled_from([True, False, None]))
def test_outside_support_never_yields_a_plan(case, p, plan):
    b, name = case
    d = decide_with_support(_input(b, p, plan), POLICY, SUPPORT)
    assert_not_evaluable(d, name)
    assert d.conditional_type is not ConditionalType.PLAN_BASED


# ---- training records never trigger (raw data, local only) -----------------------------


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_no_training_record_triggers_the_check():
    import pandas as pd

    from credit_coach.features import allowed_features
    from credit_coach.modeling import dev_frame

    dev = dev_frame(pd.read_csv(CSV))
    train = dev[dev["split"] == "train"][allowed_features()]
    train = train.astype(object).where(train.notna(), None)
    bad = [i for i, r in enumerate(train.to_dict("records")) if violations(r, SUPPORT)]
    assert bad == []


def test_padding_in_categorical_values_does_not_matter():
    assert violations({**in_support_basvuru(SUPPORT), "term": "36 months"}, SUPPORT) == ()
    assert violations({**in_support_basvuru(SUPPORT), "term": " 36 months "}, SUPPORT) == ()
    assert violations({**in_support_basvuru(SUPPORT), "term": "60 months"}, SUPPORT) == ("term",)
