from __future__ import annotations

import pandas as pd

from credit_coach.macro.reliability import scenario_severity, stressed_tau_for_scenario
from credit_coach.macro.shock_scenarios import scenario_pd_shift


def _safe_gap(rates: pd.Series) -> float:
    if rates.empty:
        return 0.0
    return float(rates.max() - rates.min())


def approval_gap(df: pd.DataFrame, group_col: str, approval_col: str) -> float:
    rates = df.groupby(group_col)[approval_col].mean()
    return _safe_gap(rates)


def cost_gap(df: pd.DataFrame, group_col: str, cost_col: str) -> float:
    costs = df.groupby(group_col)[cost_col].mean()
    if costs.empty:
        return 0.0
    return _safe_gap(costs)


def adverse_impact_ratio(df: pd.DataFrame, group_col: str, approval_col: str) -> float:
    rates = df.groupby(group_col)[approval_col].mean()
    if rates.empty:
        return 1.0
    max_rate = float(rates.max())
    min_rate = float(rates.min())
    if max_rate <= 0:
        return 1.0
    return float(min_rate / max_rate)


def true_positive_rate_gap(
    df: pd.DataFrame,
    group_col: str,
    y_true_col: str,
    y_pred_col: str,
    positive_label: int = 1,
) -> float:
    rows = df[df[y_true_col] == positive_label]
    if rows.empty:
        return 0.0
    rates = rows.groupby(group_col)[y_pred_col].mean()
    return _safe_gap(rates)


def false_positive_rate_gap(
    df: pd.DataFrame,
    group_col: str,
    y_true_col: str,
    y_pred_col: str,
    positive_label: int = 1,
) -> float:
    rows = df[df[y_true_col] != positive_label]
    if rows.empty:
        return 0.0
    rates = rows.groupby(group_col)[y_pred_col].mean()
    return _safe_gap(rates)


def equalized_odds_gap(
    df: pd.DataFrame,
    group_col: str,
    y_true_col: str,
    y_pred_col: str,
    positive_label: int = 1,
) -> float:
    tpr = true_positive_rate_gap(df, group_col, y_true_col, y_pred_col, positive_label)
    fpr = false_positive_rate_gap(df, group_col, y_true_col, y_pred_col, positive_label)
    return float(max(tpr, fpr))


def group_approval_rates(df: pd.DataFrame, group_col: str, approval_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "approval_rate", "count"])
    g = df.groupby(group_col)[approval_col].agg(["mean", "count"]).reset_index()
    g = g.rename(columns={"mean": "approval_rate"})
    return g


def build_composite_group(
    df: pd.DataFrame,
    *,
    group_cols: list[str],
    output_col: str = "group_bucket",
    sep: str = " x ",
) -> pd.DataFrame:
    out = df.copy()
    cols = [c for c in group_cols if c in out.columns]
    if not cols:
        out[output_col] = "unknown"
        return out
    normalized = [out[c].astype(str).fillna("unknown") for c in cols]
    combined = normalized[0]
    for s in normalized[1:]:
        combined = combined + sep + s
    out[output_col] = combined
    return out


def compute_multi_segment_fairness(
    scored_df: pd.DataFrame,
    *,
    segment_sets: list[list[str]] | None,
    approval_col: str = "approve",
    y_true_col: str = "y_true",
    y_pred_col: str = "pred_default",
    min_segment_n: int = 30,
) -> pd.DataFrame:
    if scored_df.empty:
        return pd.DataFrame(
            columns=[
                "segment_id",
                "group_cols",
                "reportable_group_count",
                "total_group_count",
                "segment_coverage_rate",
                "approval_gap",
                "equalized_odds_gap",
                "adverse_impact_ratio",
            ]
        )
    if not segment_sets:
        return pd.DataFrame(columns=["segment_id", "group_cols", "reportable_group_count", "total_group_count", "segment_coverage_rate", "approval_gap", "equalized_odds_gap", "adverse_impact_ratio"])

    rows: list[dict] = []
    for cols in segment_sets:
        if not isinstance(cols, list) or not cols:
            continue
        valid_cols = [c for c in cols if c in scored_df.columns]
        if not valid_cols:
            continue
        tmp = build_composite_group(scored_df, group_cols=valid_cols, output_col="segment_group")
        counts = tmp["segment_group"].value_counts(dropna=False)
        reportable_groups = counts[counts >= int(max(1, min_segment_n))].index.tolist()
        if reportable_groups:
            tmp_eval = tmp[tmp["segment_group"].isin(reportable_groups)].copy()
        else:
            tmp_eval = tmp.copy()

        bundle = compute_fairness_bundle(
            tmp_eval,
            group_col="segment_group",
            approval_col=approval_col,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
        )
        total_group_count = int(counts.shape[0])
        reportable_group_count = int(len(reportable_groups)) if reportable_groups else int(total_group_count)
        coverage = float(reportable_group_count / max(1, total_group_count))
        rows.append(
            {
                "segment_id": "|".join(valid_cols),
                "group_cols": ",".join(valid_cols),
                "reportable_group_count": reportable_group_count,
                "total_group_count": total_group_count,
                "segment_coverage_rate": coverage,
                "approval_gap": float(bundle.get("approval_gap", 0.0)),
                "equalized_odds_gap": float(bundle.get("equalized_odds_gap", 0.0)),
                "adverse_impact_ratio": float(bundle.get("adverse_impact_ratio", 1.0)),
            }
        )
    return pd.DataFrame(rows)


def build_group_advantage_penalties(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    approval_col: str = "approve",
    tolerance: float = 0.01,
) -> dict[str, float]:
    """
    Returns group-level penalties to avoid amplifying already-advantaged groups.
    penalty(g) = max(0, approval_rate(g) - min_group_rate - tolerance)
    """
    if scored_df.empty or group_col not in scored_df.columns or approval_col not in scored_df.columns:
        return {}
    rates = scored_df.groupby(group_col)[approval_col].mean()
    if rates.empty:
        return {}
    min_rate = float(rates.min())
    tol = max(0.0, float(tolerance))
    return {str(g): float(max(0.0, float(r) - min_rate - tol)) for g, r in rates.items()}


def lookup_group_penalty(group_value: object, penalties: dict[str, float] | None) -> float:
    if not penalties:
        return 0.0
    return float(max(0.0, float(penalties.get(str(group_value), 0.0))))


def compute_fairness_bundle(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    approval_col: str = "approve",
    y_true_col: str = "y_true",
    y_pred_col: str = "pred_default",
) -> dict[str, float]:
    gap = approval_gap(scored_df, group_col=group_col, approval_col=approval_col)
    air = adverse_impact_ratio(scored_df, group_col=group_col, approval_col=approval_col)
    tpr_gap = true_positive_rate_gap(scored_df, group_col=group_col, y_true_col=y_true_col, y_pred_col=y_pred_col)
    fpr_gap = false_positive_rate_gap(scored_df, group_col=group_col, y_true_col=y_true_col, y_pred_col=y_pred_col)
    eo_gap = equalized_odds_gap(scored_df, group_col=group_col, y_true_col=y_true_col, y_pred_col=y_pred_col)
    return {
        "approval_gap": float(gap),
        "adverse_impact_ratio": float(air),
        "tpr_gap": float(tpr_gap),
        "fpr_gap": float(fpr_gap),
        "equalized_odds_gap": float(eo_gap),
    }


def build_fairness_stress_matrix(
    scored_base: pd.DataFrame,
    proba: pd.Series | pd.DataFrame | pd.Index | list | tuple,
    *,
    tau: float,
    scenarios: list[dict],
    threshold_shift_per_msi_unit: float,
    group_col: str = "group_bucket",
    high_stress_severity: float = 0.6,
) -> pd.DataFrame:
    """
    Computes fairness metrics for base + each macro scenario.
    """
    p = pd.Series(proba, index=scored_base.index, dtype=float)
    rows: list[dict] = []

    all_scenarios = [{"name": "base", "changes": {}}] + list(scenarios or [])
    for s in all_scenarios:
        name = str(s.get("name", "scenario"))
        shift = float(scenario_pd_shift(s)) if name != "base" else 0.0
        severity = float(scenario_severity(s)) if name != "base" else 0.0
        tau_s = float(stressed_tau_for_scenario(tau, s, threshold_shift_per_msi_unit)) if name != "base" else float(tau)

        stressed_p = (p + shift).clip(0.0, 1.0)
        scored = scored_base.copy()
        scored["approve"] = (stressed_p <= tau_s).astype(int)
        scored["pred_default"] = (stressed_p > tau_s).astype(int)

        bundle = compute_fairness_bundle(scored, group_col=group_col, approval_col="approve", y_true_col="y_true", y_pred_col="pred_default")
        rows.append(
            {
                "scenario": name,
                "scenario_pd_shift": shift,
                "scenario_severity": severity,
                "high_stress": int(severity >= float(high_stress_severity)),
                "tau_used": tau_s,
                **bundle,
            }
        )

    return pd.DataFrame(rows)


def recourse_success_gap(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    denied_col: str = "denied_base",
    success_col: str = "gate_pass_any_candidate",
) -> float:
    if scored_df.empty:
        return 0.0
    denied = scored_df[scored_df[denied_col].astype(int) == 1]
    if denied.empty:
        return 0.0
    rates = denied.groupby(group_col)[success_col].mean()
    return _safe_gap(rates)


def recourse_cost_gap(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    denied_col: str = "denied_base",
    success_col: str = "gate_pass_any_candidate",
    cost_col: str = "best_cost_usd",
) -> float:
    if scored_df.empty:
        return 0.0
    denied = scored_df[(scored_df[denied_col].astype(int) == 1) & (scored_df[success_col].astype(int) == 1)]
    if denied.empty:
        return 0.0
    costs = denied.groupby(group_col)[cost_col].mean()
    return _safe_gap(costs)


def recourse_horizon_gap(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    denied_col: str = "denied_base",
    success_col: str = "gate_pass_any_candidate",
    horizon_col: str = "best_horizon_months",
) -> float:
    if scored_df.empty:
        return 0.0
    denied = scored_df[(scored_df[denied_col].astype(int) == 1) & (scored_df[success_col].astype(int) == 1)]
    if denied.empty:
        return 0.0
    horizons = denied.groupby(group_col)[horizon_col].mean()
    return _safe_gap(horizons)


def build_recourse_fairness_bundle(
    scored_df: pd.DataFrame,
    *,
    group_col: str,
    denied_col: str = "denied_base",
    success_col: str = "gate_pass_any_candidate",
    cost_col: str = "best_cost_usd",
    horizon_col: str = "best_horizon_months",
) -> dict[str, float]:
    return {
        "recourse_success_gap": recourse_success_gap(
            scored_df,
            group_col=group_col,
            denied_col=denied_col,
            success_col=success_col,
        ),
        "recourse_cost_gap": recourse_cost_gap(
            scored_df,
            group_col=group_col,
            denied_col=denied_col,
            success_col=success_col,
            cost_col=cost_col,
        ),
        "recourse_horizon_gap": recourse_horizon_gap(
            scored_df,
            group_col=group_col,
            denied_col=denied_col,
            success_col=success_col,
            horizon_col=horizon_col,
        ),
    }
