"""Named decision scenarios: shared by tests and the rule-coverage report."""

from __future__ import annotations

from dataclasses import dataclass

from credit_coach.features import allowed_features, load_manifest
from credit_coach.policy import Policy, load_policy


def sample_basvuru() -> dict:
    kinds = {c.ad: c.tip for c in load_manifest()}
    return {n: (1.0 if kinds[n] == "float" else "x") for n in allowed_features()}


def in_support_basvuru(support) -> dict:
    """A plausible record inside the training support (numeric min, categorical first value)."""
    b = {n: (lo if lo > 0 else 0.0) for n, (lo, _hi) in support.sayisal.items()}
    b.update({"fico_range_low": 700.0, "fico_range_high": 704.0, "dti": 15.0, "revol_util": 40.0})
    b.update({n: sorted(v)[0] for n, v in support.kategorik.items()})
    b["earliest_cr_line"] = "Jan-2000"
    return {n: b.get(n) for n in sample_basvuru()}


def policy_variant(**updates) -> Policy:
    base = load_policy("v1").model_dump()
    return Policy(**{**base, **updates})


@dataclass(frozen=True)
class Scenario:
    name: str
    p: tuple[float, float, float]  # p_low, p_point, p_high
    ham_skor: float
    plan_available: bool | None
    expected_outer: str
    expected_inner: str
    expected_rules: tuple[str, ...]
    policy_updates: tuple[tuple[str, object], ...] = ()


def scenarios() -> list[Scenario]:
    thr = load_policy("v1").onay_esigi
    b = load_policy("v1").band
    weak = (("zayif_destek_araliklari", ((thr - 0.05, thr + 0.05),)),)
    return [
        Scenario(
            "approve_clear", (0.05, 0.05, 0.05), 0.05, None, "APPROVED", "APPROVED", ("R4_APPROVE",)
        ),
        Scenario(
            "straddles_threshold",
            (thr - 0.001, thr, thr + 0.001),
            0.1,
            None,
            "CONDITIONAL",
            "NEEDS_REVIEW",
            ("R2_THRESHOLD_BAND",),
        ),
        Scenario(
            "above_but_within_band",
            (thr + b / 2, thr + b / 2, thr + b / 2),
            0.1,
            None,
            "CONDITIONAL",
            "NEEDS_REVIEW",
            ("R2_THRESHOLD_BAND",),
        ),
        Scenario(
            "below_but_within_band",
            (thr - b / 2, thr - b / 2, thr - b / 2),
            0.1,
            None,
            "CONDITIONAL",
            "NEEDS_REVIEW",
            ("R2_THRESHOLD_BAND",),
        ),
        Scenario(
            "weak_support_near",
            (thr + 2 * b, thr + 2 * b, thr + 2 * b),
            thr,
            None,
            "CONDITIONAL",
            "NEEDS_REVIEW",
            ("R3_WEAK_SUPPORT_NEAR",),
            weak,
        ),
        Scenario(
            "weak_support_but_far",
            (0.02, 0.02, 0.02),
            thr,
            None,
            "APPROVED",
            "APPROVED",
            ("R4_APPROVE",),
            weak,
        ),
        Scenario(
            "not_approved_plan_unknown",
            (0.3, 0.3, 0.3),
            0.3,
            None,
            "REJECTED",
            "REJECTED",
            ("R6_NOT_APPROVED",),
        ),
        Scenario(
            "not_approved_no_plan",
            (0.3, 0.3, 0.3),
            0.3,
            False,
            "REJECTED",
            "REJECTED",
            ("R6_NOT_APPROVED",),
        ),
        Scenario(
            "not_approved_plan_available",
            (0.3, 0.3, 0.3),
            0.3,
            True,
            "CONDITIONAL",
            "CONDITIONAL",
            ("R5_NOT_APPROVED_PLAN",),
        ),
        Scenario(
            "hard_reject",
            (0.6, 0.6, 0.6),
            0.6,
            None,
            "REJECTED",
            "REJECTED",
            ("R1_HARD_REJECT",),
            (("ret_esigi", 0.5),),
        ),
    ]
