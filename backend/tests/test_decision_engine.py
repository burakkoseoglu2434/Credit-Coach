import builtins
import random
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from credit_coach.contract import (
    DecisionInput,
    InvalidDecisionInput,
    OuterStatus,
    PublicDecision,
    parse_input,
)
from credit_coach.decision_engine import decide, to_public
from credit_coach.decision_scenarios import policy_variant, sample_basvuru, scenarios
from credit_coach.policy import load_policy


def make_input(p=(0.05, 0.05, 0.05), ham=0.05, plan=None, version="v1", **over) -> dict:
    data = {
        "basvuru": sample_basvuru(),
        "p_low": p[0],
        "p_point": p[1],
        "p_high": p[2],
        "ham_skor": ham,
        "politika_surumu": version,
        "plan_available": plan,
    }
    return {**data, **over}


@pytest.mark.parametrize("s", scenarios(), ids=lambda s: s.name)
def test_scenarios_produce_expected_decisions(s):
    pol = policy_variant(**dict(s.policy_updates))
    d = decide(parse_input(make_input(s.p, s.ham_skor, s.plan_available)), pol)
    assert d.dis_durum.value == s.expected_outer
    assert d.ic_durum.value == s.expected_inner
    assert tuple(r.value for r in d.tetiklenen_kurallar) == s.expected_rules
    assert len(d.gerekce_kodlari) >= 1


def test_needs_review_maps_to_conditional_data_issue_with_process_condition():
    s = next(x for x in scenarios() if x.name == "straddles_threshold")
    d = decide(parse_input(make_input(s.p, s.ham_skor)), load_policy("v1"))
    assert d.ic_durum.value == "NEEDS_REVIEW" and d.dis_durum is OuterStatus.CONDITIONAL
    assert d.conditional_type.value == "DATA_ISSUE"
    assert d.upgrade_condition == "HUMAN_REVIEW_COMPLETED"
    pub = to_public(d)
    assert "NEEDS_REVIEW" not in pub.model_dump_json()
    assert [c.value for c in pub.gerekce_kodlari] == [
        "REVIEW_REQUIRED"
    ]  # internal codes stay in the record


def test_public_decision_type_cannot_carry_needs_review_or_internal_codes():
    with pytest.raises(ValidationError):
        PublicDecision(dis_durum="NEEDS_REVIEW", gerekce_kodlari=(), politika_surumu="v1")
    with pytest.raises(ValidationError):
        PublicDecision(
            dis_durum="APPROVED",
            gerekce_kodlari=("INTERVAL_STRADDLES_THRESHOLD",),
            politika_surumu="v1",
        )


def test_decide_is_pure_no_clock_random_or_file_access(monkeypatch):
    girdi = parse_input(make_input((0.3, 0.3, 0.3), 0.3))
    pol = load_policy("v1")

    def boom(*a, **k):
        raise AssertionError("impure call inside decide()")

    for target, name in (
        (time, "time"),
        (random, "random"),
        (builtins, "open"),
        (Path, "read_text"),
        (Path, "open"),
    ):
        monkeypatch.setattr(target, name, boom)
    assert decide(girdi, pol).dis_durum is OuterStatus.REJECTED


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: {**d, "p_low": 0.3, "p_high": 0.2},
        lambda d: {**d, "p_point": 0.9},  # outside [p_low, p_high]
        lambda d: {**d, "p_low": float("nan")},
        lambda d: {**d, "p_high": float("inf")},
        lambda d: {**d, "ham_skor": 1.5},
        lambda d: {**d, "p_low": -0.1},
        lambda d: {**d, "p_low": "0.05"},
        lambda d: {k: v for k, v in d.items() if k != "ham_skor"},
        lambda d: {**d, "basvuru": {k: v for k, v in d["basvuru"].items() if k != "dti"}},
        lambda d: {**d, "basvuru": {**d["basvuru"], "ad_soyad": "x"}},
        lambda d: {**d, "plan_available": "yes"},
        lambda d: {**d, "politika_surumu": ""},
        lambda d: {**d, "extra": 1},
    ],
)
def test_invalid_input_raises_explicit_error(mutate):
    with pytest.raises(InvalidDecisionInput):
        parse_input(mutate(make_input((0.05, 0.05, 0.05))))


def test_unconstructed_invalid_input_is_still_caught_by_decide():
    bad = DecisionInput.model_construct(**{**make_input(), "basvuru": None, "p_low": 0.5})
    with pytest.raises(InvalidDecisionInput):
        decide(bad, load_policy("v1"))


def test_policy_version_mismatch_is_an_error_not_a_default():
    girdi = parse_input(make_input(version="v2"))
    with pytest.raises(InvalidDecisionInput, match="mismatch"):
        decide(girdi, load_policy("v1"))
