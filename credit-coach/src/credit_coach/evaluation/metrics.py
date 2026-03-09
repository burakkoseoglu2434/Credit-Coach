from __future__ import annotations

from typing import Any

import pandas as pd


def compute_recourse_metrics(plans_df: pd.DataFrame, tau: float) -> dict[str, float]:
    if plans_df.empty:
        return {
            "plan_count": 0.0,
            "validity": 0.0,
            "safe_rate": 0.0,
            "avg_cost": 0.0,
            "avg_risk_margin": 0.0,
            "avg_actions": 0.0,
            "avg_proximity": 0.0,
        }

    validity = float((plans_df["predicted_pd"] <= tau).mean())
    safe_rate = float((plans_df["status"] == "APPROVED").mean()) if "status" in plans_df.columns else 0.0
    avg_cost = float(plans_df.get("cost", pd.Series([0.0] * len(plans_df))).mean())
    avg_margin = float(plans_df.get("risk_margin", pd.Series([0.0] * len(plans_df))).mean())
    avg_actions = float(plans_df.get("action_count", pd.Series([0.0] * len(plans_df))).mean())
    avg_proximity = float(plans_df.get("proximity_l1", pd.Series([0.0] * len(plans_df))).mean())

    return {
        "plan_count": float(len(plans_df)),
        "validity": validity,
        "safe_rate": safe_rate,
        "avg_cost": avg_cost,
        "avg_risk_margin": avg_margin,
        "avg_actions": avg_actions,
        "avg_proximity": avg_proximity,
    }


def _ordered_plans(plans_df: pd.DataFrame, order_col: str | None = None) -> pd.DataFrame:
    df = plans_df.copy().reset_index(drop=True)
    if order_col and order_col in df.columns:
        if "date" in order_col.lower() or "time" in order_col.lower():
            parsed = pd.to_datetime(df[order_col], errors="coerce")
            if parsed.notna().any():
                df = df.assign(_order_tmp=parsed).sort_values("_order_tmp", kind="mergesort").drop(columns=["_order_tmp"])
            else:
                df = df.sort_values(order_col, kind="mergesort")
        else:
            df = df.sort_values(order_col, kind="mergesort")
    elif "week" in df.columns:
        df = df.sort_values("week", kind="mergesort")
    elif "created_at" in df.columns:
        parsed = pd.to_datetime(df["created_at"], errors="coerce")
        if parsed.notna().any():
            df = df.assign(_order_tmp=parsed).sort_values("_order_tmp", kind="mergesort").drop(columns=["_order_tmp"])
    return df.reset_index(drop=True)


def _rolling_ranges(n: int, window_size: int, step_size: int) -> list[tuple[int, int]]:
    n = int(max(0, n))
    if n == 0:
        return []
    w = int(max(1, window_size))
    s = int(max(1, step_size))
    if n <= w:
        return [(0, n)]
    ranges: list[tuple[int, int]] = []
    start = 0
    while start + w <= n:
        ranges.append((start, start + w))
        start += s
    if ranges and ranges[-1][1] < n:
        ranges.append((n - w, n))
    return ranges


def compute_rolling_window_recourse_metrics(
    plans_df: pd.DataFrame,
    tau: float,
    *,
    window_size: int = 10,
    step_size: int = 5,
    order_col: str | None = None,
) -> pd.DataFrame:
    if plans_df.empty:
        return pd.DataFrame(
            columns=[
                "window_id",
                "start_idx",
                "end_idx",
                "window_size",
                "plan_count",
                "validity",
                "safe_rate",
                "avg_cost",
                "avg_risk_margin",
                "avg_actions",
                "avg_proximity",
            ]
        )

    ordered = _ordered_plans(plans_df, order_col=order_col)
    ranges = _rolling_ranges(len(ordered), window_size=window_size, step_size=step_size)
    rows: list[dict[str, Any]] = []
    for i, (start, end) in enumerate(ranges, start=1):
        part = ordered.iloc[start:end]
        metrics = compute_recourse_metrics(part, tau=tau)
        rows.append(
            {
                "window_id": i,
                "start_idx": int(start),
                "end_idx": int(end - 1),
                "window_size": int(end - start),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def summarize_last_k_windows(
    rolling_df: pd.DataFrame,
    *,
    last_k: int = 3,
) -> dict[str, float]:
    if rolling_df.empty:
        return {
            "window_count": 0.0,
            "last_k_used": 0.0,
            "last_k_validity": 0.0,
            "last_k_safe_rate": 0.0,
            "last_k_avg_risk_margin": 0.0,
        }

    k = int(max(1, last_k))
    tail = rolling_df.sort_values("window_id").tail(k)
    return {
        "window_count": float(len(rolling_df)),
        "last_k_used": float(len(tail)),
        "last_k_validity": float(tail["validity"].mean()),
        "last_k_safe_rate": float(tail["safe_rate"].mean()),
        "last_k_avg_risk_margin": float(tail["avg_risk_margin"].mean()),
    }

