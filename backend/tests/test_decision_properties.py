import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from credit_coach.contract import (
    DecisionInput,
    InnerStatus,
    InvalidDecisionInput,
    OuterStatus,
    PublicDecision,
    parse_input,
)
from credit_coach.decision import (
    APPROVE,
    HUMAN,
    NOT_APPROVED,
    DecisionConfig,
)
from credit_coach.decision import decide as legacy_decide
from credit_coach.decision_engine import decide, to_public
from credit_coach.decision_scenarios import sample_basvuru
from credit_coach.policy import RULE_ORDER, Policy, UnknownPolicyVersion, load_policy

SETTINGS = settings(
    max_examples=120, derandomize=True, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
triples = st.lists(unit, min_size=3, max_size=3).map(sorted)
plans = st.sampled_from([None, True, False])


@st.composite
def policies(draw):
    thr = draw(unit)
    ranges = draw(st.lists(st.lists(unit, min_size=2, max_size=2).map(sorted), max_size=3))
    ret = draw(
        st.one_of(st.none(), st.floats(min_value=thr, max_value=1.0).filter(lambda r: r > thr))
    )
    return Policy(
        surum="v1",
        kural_sirasi=RULE_ORDER,
        onay_esigi=thr,
        band=draw(st.floats(min_value=0.0, max_value=0.2)),
        zayif_destek_araliklari=tuple(tuple(r) for r in ranges),
        zayif_destek_yakinlik_carpani=draw(st.floats(min_value=0.0, max_value=10.0)),
        ret_esigi=ret,
    )


def build(p, ham, plan, version="v1") -> DecisionInput:
    return parse_input(
        {
            "basvuru": sample_basvuru(),
            "p_low": p[0],
            "p_point": p[1],
            "p_high": p[2],
            "ham_skor": ham,
            "politika_surumu": version,
            "plan_available": plan,
        }
    )


@SETTINGS
@given(triples, unit, plans, policies())
def test_a_same_input_same_output_bytes(p, ham, plan, pol):
    g = build(p, ham, plan)
    a, b = decide(g, pol), decide(g, pol)
    assert a == b and a.model_dump_json() == b.model_dump_json()


RANK = {
    InnerStatus.APPROVED: 0,
    InnerStatus.NEEDS_REVIEW: 1,
    InnerStatus.CONDITIONAL: 2,
    InnerStatus.REJECTED: 2,
}


@SETTINGS
@given(triples, unit, plans, policies(), st.lists(unit, min_size=2, max_size=6))
def test_b_state_order_never_breaks_as_pd_rises(p, ham, plan, pol, shifts):
    room = 1.0 - p[2]
    ranks = []
    for d in sorted(s * room for s in shifts):
        q = [v + d for v in p]
        q = [min(v, 1.0) for v in q]
        ranks.append(RANK[decide(build(q, ham, plan), pol).ic_durum])
    assert ranks == sorted(ranks)


@SETTINGS
@given(triples, unit, plans, policies())
def test_c_needs_review_never_leaks_outside(p, ham, plan, pol):
    d = decide(build(p, ham, plan), pol)
    assert d.dis_durum in set(OuterStatus) and len(set(OuterStatus)) == 3
    pub = to_public(d)
    assert isinstance(pub, PublicDecision)
    assert "NEEDS_REVIEW" not in pub.model_dump_json()
    assert "INTERVAL_STRADDLES" not in pub.model_dump_json()
    if d.ic_durum is InnerStatus.NEEDS_REVIEW:
        assert d.dis_durum is OuterStatus.CONDITIONAL
        assert d.upgrade_condition == "HUMAN_REVIEW_COMPLETED"


@SETTINGS
@given(triples, unit, plans, policies())
def test_d_every_decision_has_reason_code_and_rule(p, ham, plan, pol):
    d = decide(build(p, ham, plan), pol)
    assert len(d.gerekce_kodlari) >= 1 and len(d.tetiklenen_kurallar) >= 1
    assert len(to_public(d).gerekce_kodlari) >= 1


@SETTINGS
@given(st.text(max_size=12).filter(lambda t: t != "v1"))
def test_e_unknown_policy_version_is_an_error_never_a_default(version):
    with pytest.raises(UnknownPolicyVersion):
        load_policy(version)
    if version:
        with pytest.raises(InvalidDecisionInput):
            decide(build((0.1, 0.1, 0.1), 0.1, None, version=version), load_policy("v1"))


@SETTINGS
@given(st.lists(st.tuples(triples, unit), min_size=1, max_size=40), policies())
def test_new_decide_agrees_with_legacy_vectorised_rule(rows, pol):
    pol = Policy(**{**pol.model_dump(), "ret_esigi": None})
    cfg = DecisionConfig(
        pol.onay_esigi, pol.band, pol.zayif_destek_araliklari, pol.zayif_destek_yakinlik_carpani
    )
    lo, pt, hi = (np.array([r[0][i] for r in rows]) for i in range(3))
    s = np.array([r[1] for r in rows])
    old = legacy_decide(lo, hi, s, cfg, pt)
    mapping = {
        APPROVE: InnerStatus.APPROVED,
        HUMAN: InnerStatus.NEEDS_REVIEW,
        NOT_APPROVED: InnerStatus.REJECTED,
    }
    new = [
        decide(build((a, b, c), x, None), pol).ic_durum
        for a, b, c, x in zip(lo, pt, hi, s, strict=True)
    ]
    assert new == [mapping[o] for o in old]
