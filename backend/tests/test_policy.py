import pytest
from pydantic import ValidationError

from credit_coach.decision import approval_threshold, load_cost, total_hurdle
from credit_coach.policy import (
    POLICY_DIR,
    RULE_ORDER,
    Policy,
    UnknownPolicyVersion,
    derive_v1,
    load_policy,
    write_v1,
)


def test_v1_loads_and_matches_derivation():
    p = load_policy("v1")
    cost = load_cost()
    expected = approval_threshold(
        cost["saglam_kredi_getirisi"]["mean"], cost["temerrut_kaybi"]["mean"], total_hurdle(cost)
    )
    assert p.surum == "v1" and p.ret_esigi is None
    assert p.onay_esigi == pytest.approx(expected, abs=0, rel=1e-12)
    assert p.kural_sirasi == RULE_ORDER


def test_v1_file_equals_fresh_derivation():
    assert load_policy("v1") == Policy(**derive_v1())


@pytest.mark.parametrize("bad", ["v999", "v0", "", "latest", "../v1", "V1", "v1.yaml"])
def test_unknown_or_malformed_version_raises_no_default(bad):
    with pytest.raises(UnknownPolicyVersion):
        load_policy(bad)


def test_v1_is_frozen_and_cannot_be_rewritten():
    assert (POLICY_DIR / "v1.yaml").exists()
    with pytest.raises(SystemExit, match="frozen"):
        write_v1()


def test_policy_is_immutable():
    p = load_policy("v1")
    with pytest.raises(ValidationError):
        p.onay_esigi = 0.5


def test_policy_validation_rules():
    base = derive_v1()
    with pytest.raises(ValidationError):
        Policy(**{**base, "ret_esigi": 0.01})  # below onay_esigi
    with pytest.raises(ValidationError):
        Policy(**{**base, "onay_esigi": 1.5})
    with pytest.raises(ValidationError):
        Policy(**{**base, "kural_sirasi": list(reversed(RULE_ORDER))})
    with pytest.raises(ValidationError):
        Policy(**{**base, "unexpected": 1})
