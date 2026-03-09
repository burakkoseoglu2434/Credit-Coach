from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from credit_coach.evaluation.metrics import (
    compute_recourse_metrics,
    compute_rolling_window_recourse_metrics,
    summarize_last_k_windows,
)
from credit_coach.evaluation.tables import save_table
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_benchmark")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Our vs baseline benchmark")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--plans_csv", type=str, default="")
    p.add_argument("--baseline_csv", type=str, default="")
    p.add_argument("--window_size", type=int, default=3)
    p.add_argument("--window_step", type=int, default=1)
    p.add_argument("--last_k_windows", type=int, default=3)
    p.add_argument("--window_order_col", type=str, default="")
    p.add_argument("--min_last_k_validity", type=float, default=0.85)
    p.add_argument("--min_last_k_safe_rate", type=float, default=0.60)
    p.add_argument("--min_last_k_avg_risk_margin", type=float, default=0.0)
    return p.parse_args()


def _latest_plans_csv() -> Path:
    candidates = sorted(Path("artifacts/runs").glob("*/tables/plans.csv"))
    if not candidates:
        raise FileNotFoundError("No plans.csv found. Run run_recourse first.")
    return candidates[-1]


def _load_baseline(plans_path: Path, our_df: pd.DataFrame, tau: float, baseline_csv: str) -> tuple[pd.DataFrame, str]:
    baseline_method = "baseline_proxy"
    if baseline_csv:
        baseline_path = Path(baseline_csv)
    else:
        sibling = plans_path.parent / "dice_plans.csv"
        baseline_path = sibling if sibling.exists() else None

    if baseline_path is not None and baseline_path.exists():
        baseline_df = pd.read_csv(baseline_path)
        baseline_method = "baseline_dice"
    else:
        baseline_df = our_df.copy()
        baseline_df["predicted_pd"] = (baseline_df["predicted_pd"] + 0.03).clip(0, 1)
        if "risk_margin" in baseline_df.columns:
            baseline_df["risk_margin"] = tau - baseline_df["predicted_pd"]
        if "status" in baseline_df.columns:
            baseline_df["status"] = (baseline_df["predicted_pd"] <= tau).map({True: "APPROVED", False: "NEEDS_REVIEW"})
    return baseline_df, baseline_method


def _gate_result(lastk: dict[str, float], args: argparse.Namespace) -> dict[str, bool]:
    return {
        "validity_gate_pass": float(lastk.get("last_k_validity", 0.0)) >= float(args.min_last_k_validity),
        "safe_rate_gate_pass": float(lastk.get("last_k_safe_rate", 0.0)) >= float(args.min_last_k_safe_rate),
        "risk_margin_gate_pass": float(lastk.get("last_k_avg_risk_margin", -1e9)) >= float(args.min_last_k_avg_risk_margin),
    }


def main() -> None:
    args = parse_args()
    model_cfg = load_config(args.model_config)
    run_ctx = create_run_context({"model": model_cfg, "benchmark": vars(args)}, base_artifact_dir="artifacts/runs")

    plans_path = Path(args.plans_csv) if args.plans_csv else _latest_plans_csv()
    our_df = pd.read_csv(plans_path)
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    baseline_df, baseline_method = _load_baseline(plans_path, our_df, tau=tau, baseline_csv=args.baseline_csv)

    our_metrics = compute_recourse_metrics(our_df, tau=tau)
    base_metrics = compute_recourse_metrics(baseline_df, tau=tau)
    cmp = pd.DataFrame(
        [
            {"method": "our", **our_metrics},
            {"method": baseline_method, **base_metrics},
        ]
    )
    out_cmp = save_table(cmp, run_ctx.tables_dir / "benchmark_comparison.csv")

    order_col = args.window_order_col.strip() or None
    our_roll = compute_rolling_window_recourse_metrics(
        our_df,
        tau=tau,
        window_size=args.window_size,
        step_size=args.window_step,
        order_col=order_col,
    )
    our_roll["method"] = "our"
    base_roll = compute_rolling_window_recourse_metrics(
        baseline_df,
        tau=tau,
        window_size=args.window_size,
        step_size=args.window_step,
        order_col=order_col,
    )
    base_roll["method"] = baseline_method
    rolling = pd.concat([our_roll, base_roll], ignore_index=True)
    out_roll = save_table(rolling, run_ctx.tables_dir / "benchmark_rolling_windows.csv")

    our_lastk = summarize_last_k_windows(our_roll, last_k=args.last_k_windows)
    base_lastk = summarize_last_k_windows(base_roll, last_k=args.last_k_windows)
    our_gates = _gate_result(our_lastk, args)
    base_gates = _gate_result(base_lastk, args)
    summary = pd.DataFrame(
        [
            {"method": "our", **our_lastk, **our_gates},
            {"method": baseline_method, **base_lastk, **base_gates},
        ]
    )
    out_lastk = save_table(summary, run_ctx.tables_dir / "benchmark_lastk_summary.csv")

    run_ctx.save_metrics(
        {
            "rows": len(cmp),
            "our_validity": our_metrics["validity"],
            "baseline_validity": base_metrics["validity"],
            "baseline_method": baseline_method,
            "window_size": int(args.window_size),
            "window_step": int(args.window_step),
            "last_k_windows": int(args.last_k_windows),
            "our_last_k_validity": float(our_lastk.get("last_k_validity", 0.0)),
            "our_last_k_safe_rate": float(our_lastk.get("last_k_safe_rate", 0.0)),
            "our_last_k_avg_risk_margin": float(our_lastk.get("last_k_avg_risk_margin", 0.0)),
            "our_validity_gate_pass": bool(our_gates["validity_gate_pass"]),
            "our_safe_rate_gate_pass": bool(our_gates["safe_rate_gate_pass"]),
            "our_risk_margin_gate_pass": bool(our_gates["risk_margin_gate_pass"]),
        }
    )

    logger.info("Benchmark saved: %s", out_cmp)
    logger.info("Benchmark rolling windows saved: %s", out_roll)
    logger.info("Benchmark last-k summary saved: %s", out_lastk)


if __name__ == "__main__":
    main()

