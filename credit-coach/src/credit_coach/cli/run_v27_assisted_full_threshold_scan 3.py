from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml


@dataclass(frozen=True)
class ThresholdSelection:
    threshold_prob_min: float
    gap_closure_min: float
    gap_divide_epsilon: float
    achieved_share: float
    achieved_share_prob_only: float
    achieved_share_gap_only: float
    eligible_count: int
    suppressed_population_size: int
    population_size: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically scan a baseline customer_level_analysis.csv and lock assisted_full thresholds.",
    )
    parser.add_argument(
        "--customer_csv",
        type=str,
        required=True,
        help="Path to baseline customer_level_analysis.csv",
    )
    parser.add_argument(
        "--target_share_min",
        type=float,
        default=0.07,
        help="Minimum target assisted_full share (default: 0.07).",
    )
    parser.add_argument(
        "--target_share_max",
        type=float,
        default=0.12,
        help="Maximum target assisted_full share (default: 0.12).",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        required=True,
        help="Path to write locked thresholds JSON.",
    )
    return parser.parse_args()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp01(value: float) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    return float(value)


def _quantile_candidates(series: pd.Series, *, qs: Iterable[float], decimals: int) -> list[float]:
    numeric = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if numeric.empty:
        return []
    quantiles = numeric.quantile(list(qs), interpolation="linear").tolist()
    candidates = {round(_safe_float(v), decimals) for v in quantiles}
    return sorted(candidates)


def _pick_probability_signal(df: pd.DataFrame, *, suppressed_mask: pd.Series) -> pd.Series:
    if "pre_gate_threshold_reach_probability" in df.columns:
        return pd.to_numeric(df["pre_gate_threshold_reach_probability"], errors="coerce").fillna(0.0).astype(float).clip(0.0, 1.0)

    if "threshold_reach_probability" not in df.columns:
        raise ValueError(
            "Missing probability signal. Expected `pre_gate_threshold_reach_probability` or `threshold_reach_probability` column."
        )

    prob = pd.to_numeric(df["threshold_reach_probability"], errors="coerce").fillna(0.0).astype(float).clip(0.0, 1.0)
    suppressed_prob = prob[suppressed_mask]
    if not suppressed_prob.empty and float(suppressed_prob.max()) <= 1e-12:
        # In limited mode, selected-projection fields are intentionally blanked (set to 0).
        # Phase 72 requires the pre-gate shadow field so thresholds can be locked data-driven.
        raise ValueError(
            "CSV appears to have limited-mode blanked probability signal for the target population. "
            "Re-run cohort evaluation with pre-gate shadow fields (`pre_gate_threshold_reach_probability`) present."
        )
    return prob


def _pick_gap_signal(df: pd.DataFrame) -> tuple[pd.Series, float]:
    epsilon = 1e-6
    if "gap_divide_epsilon" in df.columns:
        values = pd.to_numeric(df["gap_divide_epsilon"], errors="coerce").dropna().astype(float)
        if not values.empty:
            epsilon = max(1e-9, float(values.median()))

    if "gap_closure_rate" in df.columns:
        gap = pd.to_numeric(df["gap_closure_rate"], errors="coerce").fillna(0.0).astype(float)
        return gap.clip(lower=0.0), epsilon

    if "max_gap_closure_rate" in df.columns:
        gap = pd.to_numeric(df["max_gap_closure_rate"], errors="coerce").fillna(0.0).astype(float)
        return gap.clip(lower=0.0), epsilon

    if {"best_possible_pd_improvement", "approval_gap"}.issubset(set(df.columns)):
        best_possible = pd.to_numeric(df["best_possible_pd_improvement"], errors="coerce").fillna(0.0).astype(float)
        approval_gap = pd.to_numeric(df["approval_gap"], errors="coerce").fillna(0.0).astype(float)
        denom = (approval_gap.clip(lower=0.0)).where(approval_gap >= epsilon, epsilon)
        gap = (best_possible.clip(lower=0.0) / denom).fillna(0.0).astype(float)
        return gap.clip(lower=0.0), epsilon

    raise ValueError(
        "Missing gap signal. Expected `gap_closure_rate` (preferred), `max_gap_closure_rate`, "
        "or `best_possible_pd_improvement`+`approval_gap`."
    )


def _segment_label(row: pd.Series) -> str:
    bucket = str(row.get("recoverability_bucket") or "").strip().lower()
    if bucket in {"near_threshold", "mid_risk"}:
        return bucket
    if bucket:
        return "hard_denied"

    risk_band = str(row.get("risk_band") or "").strip().lower()
    if risk_band == "near":
        return "near_threshold"
    if risk_band == "mid":
        return "mid_risk"
    return "hard_denied"


def _pick_base_population_mask(df: pd.DataFrame) -> tuple[pd.Series, str]:
    if "in_global_denied_population" in df.columns:
        col = pd.to_numeric(df["in_global_denied_population"], errors="coerce").fillna(0).astype(int)
        return (col == 1), "in_global_denied_population"
    return pd.Series([True] * int(df.shape[0])), "all_rows"


def _pick_policy_suppressed_mask(df: pd.DataFrame) -> tuple[pd.Series, str]:
    if "recourse_mode" in df.columns:
        modes = df["recourse_mode"].astype(str).str.strip().str.lower()
        return (modes == "limited"), "recourse_mode==limited"
    if "in_non_recoverable_limited_mode_population" in df.columns:
        col = pd.to_numeric(df["in_non_recoverable_limited_mode_population"], errors="coerce").fillna(0).astype(int)
        return (col == 1), "in_non_recoverable_limited_mode_population"
    if "recoverable_flag" in df.columns:
        col = pd.to_numeric(df["recoverable_flag"], errors="coerce").fillna(0).astype(int)
        return (col == 0), "recoverable_flag==0"
    raise ValueError(
        "Cannot determine policy-suppressed population. Expected `recourse_mode`, "
        "`in_non_recoverable_limited_mode_population`, or `recoverable_flag` columns."
    )


def _choose_thresholds(
    *,
    prob: pd.Series,
    gap: pd.Series,
    base_population_mask: pd.Series,
    suppressed_mask: pd.Series,
    target_share_min: float,
    target_share_max: float,
    gap_divide_epsilon: float,
) -> ThresholdSelection:
    base_mask = base_population_mask.astype(bool)
    suppressed = (suppressed_mask.astype(bool)) & base_mask
    suppressed_prob = prob[suppressed].astype(float)
    suppressed_gap = gap[suppressed].astype(float)
    suppressed_n = int(suppressed_prob.shape[0])
    if suppressed_n <= 0:
        raise ValueError("Policy-suppressed population is empty; cannot scan thresholds.")

    base_n = int(base_mask.sum())
    if base_n <= 0:
        raise ValueError("Base population is empty; cannot scan thresholds.")

    target_min = float(target_share_min)
    target_max = float(target_share_max)
    if not (0.0 < target_min <= target_max < 1.0):
        raise ValueError(f"Invalid target share range: [{target_min}, {target_max}]")
    target_mid = 0.5 * (target_min + target_max)

    prob_candidates = sorted(
        {
            *_quantile_candidates(suppressed_prob, qs=[0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99], decimals=4),
            0.40,
            0.45,
            0.50,
            0.55,
            0.60,
            0.65,
            0.70,
            0.75,
            0.80,
            0.85,
            0.90,
            0.92,
            0.94,
            0.96,
            0.98,
        }
    )
    prob_candidates = [float(v) for v in prob_candidates if 0.0 <= float(v) <= 1.0]

    gap_candidates = sorted(
        {
            *_quantile_candidates(suppressed_gap, qs=[0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99], decimals=4),
            0.05,
            0.10,
            0.20,
            0.30,
            0.40,
            0.50,
            0.60,
            0.80,
            1.00,
            1.25,
            1.50,
            2.00,
        }
    )
    gap_candidates = [float(v) for v in gap_candidates if float(v) >= 0.0]

    best: ThresholdSelection | None = None
    best_key: tuple[float, float, float, float, float] | None = None

    for p in prob_candidates:
        prob_ok = suppressed_prob >= float(p)
        for g in gap_candidates:
            gap_ok = suppressed_gap >= float(g)
            eligible = prob_ok | gap_ok
            eligible_count = int(eligible.sum())
            share = float(eligible_count / float(base_n))

            prob_only = float(int((prob_ok & ~gap_ok).sum()) / float(base_n))
            gap_only = float(int((gap_ok & ~prob_ok).sum()) / float(base_n))

            inside = 1.0 if (target_min <= share <= target_max) else 0.0
            distance_to_mid = abs(share - target_mid)

            # Tie-breaks (deterministic):
            # 1) Prefer solutions inside range
            # 2) Prefer closer to mid
            # 3) Prefer fewer "gap-only" selections (more conservative)
            # 4) Prefer higher probability threshold (more conservative)
            # 5) Prefer higher gap threshold (more conservative)
            key = (-inside, distance_to_mid, gap_only, -float(p), -float(g))
            if best is None or key < best_key:  # type: ignore[operator]
                best = ThresholdSelection(
                    threshold_prob_min=float(p),
                    gap_closure_min=float(g),
                    gap_divide_epsilon=float(gap_divide_epsilon),
                    achieved_share=float(share),
                    achieved_share_prob_only=float(prob_only),
                    achieved_share_gap_only=float(gap_only),
                    eligible_count=int(eligible_count),
                    suppressed_population_size=int(suppressed_n),
                    population_size=int(base_n),
                )
                best_key = key

    if best is None:
        raise RuntimeError("Failed to select thresholds (unexpected).")

    return best


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping at {path}, got {type(payload)}")
    return dict(payload)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            payload,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=140,
        )


def run(args: argparse.Namespace) -> dict[str, Any]:
    customer_csv = Path(args.customer_csv).expanduser().resolve()
    if not customer_csv.is_file():
        raise FileNotFoundError(f"Missing customer CSV: {customer_csv}")

    output_json = Path(args.output_json).expanduser().resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(customer_csv)
    base_population_mask, base_population_source = _pick_base_population_mask(df)
    suppressed_mask, suppressed_source = _pick_policy_suppressed_mask(df)
    suppressed_mask = (suppressed_mask.astype(bool)) & (base_population_mask.astype(bool))

    prob = _pick_probability_signal(df, suppressed_mask=suppressed_mask)
    gap, gap_epsilon = _pick_gap_signal(df)

    selection = _choose_thresholds(
        prob=prob,
        gap=gap,
        base_population_mask=base_population_mask,
        suppressed_mask=suppressed_mask,
        target_share_min=float(args.target_share_min),
        target_share_max=float(args.target_share_max),
        gap_divide_epsilon=float(gap_epsilon),
    )

    segments = df.apply(_segment_label, axis=1)
    base_segments = segments[base_population_mask.astype(bool)]
    base_prob = prob[suppressed_mask.astype(bool)]
    base_gap = gap[suppressed_mask.astype(bool)]

    prob_ok = base_prob >= float(selection.threshold_prob_min)
    gap_ok = base_gap >= float(selection.gap_closure_min)
    eligible = (prob_ok | gap_ok).astype(bool)

    base_segment_totals = base_segments.value_counts(dropna=False).to_dict()
    eligible_segment_counts = segments[suppressed_mask.astype(bool)][eligible].value_counts(dropna=False).to_dict()

    report: dict[str, Any] = {
        "version": "v27_assisted_full_threshold_scan",
        "inputs": {
            "customer_csv": str(customer_csv),
            "target_share_min": float(args.target_share_min),
            "target_share_max": float(args.target_share_max),
            "base_population_source": base_population_source,
            "policy_suppressed_source": suppressed_source,
            "signals": {
                "probability": "pre_gate_threshold_reach_probability"
                if "pre_gate_threshold_reach_probability" in df.columns
                else "threshold_reach_probability",
                "gap": "gap_closure_rate"
                if "gap_closure_rate" in df.columns
                else ("max_gap_closure_rate" if "max_gap_closure_rate" in df.columns else "best_possible_pd_improvement/approval_gap"),
            },
        },
        "locked_thresholds": {
            "threshold_prob_min": round(float(selection.threshold_prob_min), 6),
            "gap_closure_rate_min": round(float(selection.gap_closure_min), 6),
            "epsilon": round(float(selection.gap_divide_epsilon), 12),
        },
        "achieved": {
            "assisted_full_share": round(float(selection.achieved_share), 6),
            "assisted_full_share_prob_only": round(float(selection.achieved_share_prob_only), 6),
            "assisted_full_share_gap_only": round(float(selection.achieved_share_gap_only), 6),
            "eligible_count": int(selection.eligible_count),
            "suppressed_population_size": int(selection.suppressed_population_size),
            "population_size": int(selection.population_size),
        },
        "segment_counts": {
            "total": {k: int(v) for k, v in sorted(base_segment_totals.items())},
            "eligible": {k: int(v) for k, v in sorted(eligible_segment_counts.items())},
        },
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    # Derive a fully-resolved locked recourse config.
    repo_root = customer_csv.parents[2] if (customer_csv.parent.name == "evaluations") else Path(__file__).resolve().parents[3]
    # Most invocations run from credit-coach/, so keep it simple: resolve relative to that project root.
    credit_coach_root = repo_root if (repo_root / "configs" / "recourse.yaml").is_file() else Path.cwd().resolve()
    base_recourse_path = (credit_coach_root / "configs" / "recourse.yaml").resolve()
    locked_yaml_path = (credit_coach_root / "configs" / "recourse_assisted_full_w2a_locked.yaml").resolve()

    base_recourse = _read_yaml(base_recourse_path)
    gate_cfg = base_recourse.get("recourse_gate", {})
    gate_cfg = gate_cfg if isinstance(gate_cfg, dict) else {}
    assisted_cfg = {
        "enabled": True,
        "threshold_prob_min": float(report["locked_thresholds"]["threshold_prob_min"]),
        "gap_closure_min": float(report["locked_thresholds"]["gap_closure_rate_min"]),
        "gap_divide_epsilon": float(report["locked_thresholds"]["epsilon"]),
        # Phase 72 Wave 1 allowlist (customer-only; minimal single-step):
        "allowlisted_action_keys": [
            "adjust_requested_loan_amount",
            "limit_credit_usage",
            "reduce_spending",
        ],
        "action_preference_order": [
            "adjust_requested_loan_amount",
            "limit_credit_usage",
            "reduce_spending",
        ],
    }
    gate_cfg["assisted_full"] = assisted_cfg
    base_recourse["recourse_gate"] = gate_cfg

    _write_yaml(locked_yaml_path, base_recourse)

    report["outputs"] = {
        "output_json": str(output_json),
        "locked_recourse_yaml": str(locked_yaml_path),
    }
    return report


def main() -> None:
    report = run(parse_args())
    print(report["outputs"]["output_json"])


if __name__ == "__main__":
    main()
