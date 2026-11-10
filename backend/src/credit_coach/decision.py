"""Approval threshold (analytic) and the interval decision rule. Pure, deterministic functions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import yaml

from credit_coach.features import MANIFEST_PATH

APPROVE = "onay"
HUMAN = "insana_git"
NOT_APPROVED = "onay_degil"  # below the approval bar; the decline threshold comes in week 4

COST_PATH = MANIFEST_PATH.parent / "cost.yaml"


def total_hurdle(cost_doc: dict) -> float:
    """asgari_marj + fon_maliyeti + isletme_gideri, as a fraction of funded_amnt. All required."""
    h = cost_doc["hurdle"]
    missing = [
        k for k in ("asgari_marj", "fon_maliyeti", "isletme_gideri") if h[k]["deger"] is None
    ]
    if missing:
        raise ValueError(f"hurdle assumptions not provided: {missing}")
    return float(sum(h[k]["deger"] for k in ("asgari_marj", "fon_maliyeti", "isletme_gideri")))


def approval_threshold(gain: float, loss: float, hurdle: float) -> float:
    """Largest PD satisfying (1-PD)*gain - PD*loss >= hurdle.

    (1-p)g - pL >= h  <=>  p <= (g - h) / (g + L). Clipped to [0, 1]; 0 means nobody qualifies.
    """
    if gain <= 0 or loss <= 0:
        raise ValueError("gain and loss must be positive")
    return float(min(max((gain - hurdle) / (gain + loss), 0.0), 1.0))


def expected_margin(pd_: np.ndarray, gain: float, loss: float) -> np.ndarray:
    return (1 - np.asarray(pd_)) * gain - np.asarray(pd_) * loss


@dataclass(frozen=True)
class DecisionConfig:
    threshold: float
    band: float
    weak_support_ranges: tuple[tuple[float, float], ...] = ()
    weak_near_multiplier: float = (
        3.0  # weak support only matters within this many bands of the threshold
    )


def decide(
    p_low: np.ndarray,
    p_high: np.ndarray,
    raw_score: np.ndarray,
    cfg: DecisionConfig,
    p_point: np.ndarray | None = None,
) -> np.ndarray:
    """Interval rule.

    HUMAN if the interval [p_low, p_high], widened by `band` on both sides, contains the threshold
    (this includes every straddling interval), OR if the raw score is in a weak-support range AND
    |PD - threshold| <= weak_near_multiplier * band (PD = p_point, default interval midpoint).
    Otherwise APPROVE if the whole interval is below the threshold, else NOT_APPROVED.
    """
    lo, hi, s = (np.asarray(a, dtype=float) for a in (p_low, p_high, raw_score))
    if (lo > hi).any():
        raise ValueError("p_low must not exceed p_high")
    pt = (lo + hi) / 2 if p_point is None else np.asarray(p_point, dtype=float)
    near = (lo - cfg.band <= cfg.threshold) & (hi + cfg.band >= cfg.threshold)
    in_weak = np.zeros(len(s), dtype=bool)
    for a, b in cfg.weak_support_ranges:
        in_weak |= (s >= a) & (s <= b)
    weak_near = in_weak & (np.abs(pt - cfg.threshold) <= cfg.weak_near_multiplier * cfg.band)
    out = np.where(hi < cfg.threshold, APPROVE, NOT_APPROVED).astype(object)
    out[near | weak_near] = HUMAN
    return out


def load_cost(path=COST_PATH) -> dict:
    return yaml.safe_load(path.read_text())
