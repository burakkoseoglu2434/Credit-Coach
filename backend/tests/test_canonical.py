import json
import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from credit_coach.canonical import (
    NonCanonicalValue,
    canonical_bytes,
    canonical_text,
    model_canonical_text,
    sha256_hex,
)
from credit_coach.contract import DecisionInput, parse_input
from credit_coach.decision_engine import decide
from credit_coach.decision_scenarios import sample_basvuru
from credit_coach.policy import load_policy


def test_key_order_and_whitespace_do_not_matter():
    a = {"b": 1, "a": [1, 2, {"z": 1, "y": 2}]}
    b = {"a": [1, 2, {"y": 2, "z": 1}], "b": 1}
    assert canonical_text(a) == canonical_text(b) == '{"a":[1,2,{"y":2,"z":1}],"b":1}'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.1, "0.1"),
        (0.30000000000000004, "0.30000000000000004"),
        (1.0, "1.0"),
        (1e-7, "1e-07"),
        (1e22, "1e+22"),
        (5e-324, "5e-324"),
        (1.7976931348623157e308, "1.7976931348623157e+308"),
        (-0.0, "0.0"),
        (0.10917, "0.10917"),
    ],
)
def test_float_format_is_pinned(value, expected):
    assert canonical_text(value) == expected


def test_int_and_float_stay_distinct():
    assert canonical_text({"x": 1}) != canonical_text({"x": 1.0})


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, {1: 2}, {"a": {1, 2}}, b"x"])
def test_non_canonical_values_rejected(bad):
    with pytest.raises(NonCanonicalValue):
        canonical_text(bad)


def test_unicode_is_ascii_escaped_and_bytes_are_stable():
    assert canonical_text({"k": "ş"}) == '{"k":"\\u015f"}'
    assert canonical_bytes({"k": "ş"}) == b'{"k":"\\u015f"}'


@settings(max_examples=300, derandomize=True)
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_round_trip_is_exact(x):
    text = canonical_text(x)
    back = json.loads(text)
    assert back == x or (x == 0.0 and back == 0.0)
    assert canonical_text(back) == text


_json = st.recursive(
    st.none()
    | st.booleans()
    | st.integers(-(2**53), 2**53)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=8),
    lambda c: st.lists(c, max_size=4) | st.dictionaries(st.text(max_size=5), c, max_size=4),
    max_leaves=12,
)


@settings(max_examples=200, derandomize=True)
@given(_json)
def test_text_round_trip_is_a_fixed_point(obj):
    text = canonical_text(obj)
    assert canonical_text(json.loads(text)) == text


def _input() -> DecisionInput:
    return parse_input(
        {
            "basvuru": sample_basvuru(),
            "p_low": 0.0913,
            "p_point": 0.1042,
            "p_high": 0.1188,
            "ham_skor": 0.3300000000000001,
            "politika_surumu": "v1",
            "plan_available": None,
        }
    )


def test_decision_input_and_output_round_trip_through_text():
    girdi = _input()
    text = model_canonical_text(girdi)
    again = DecisionInput.model_validate(json.loads(text))
    assert model_canonical_text(again) == text
    out = decide(girdi, load_policy("v1"))
    out_text = model_canonical_text(out)
    assert canonical_text(json.loads(out_text)) == out_text


def test_same_input_gives_same_bytes_and_hash():
    p = load_policy("v1")
    t1 = model_canonical_text(decide(_input(), p))
    t2 = model_canonical_text(decide(_input(), p))
    assert t1 == t2
    assert sha256_hex(t1) == sha256_hex(t1.encode())
