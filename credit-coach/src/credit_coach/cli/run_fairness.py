from __future__ import annotations

import argparse
import logging

import pandas as pd

from credit_coach.data.ingest import load_feature_contract
from credit_coach.evaluation.fairness import (
    build_fairness_stress_matrix,
    build_recourse_fairness_bundle,
    compute_multi_segment_fairness,
    compute_fairness_bundle,
    group_approval_rates,
)
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_latest_model_bundle
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_fairness")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fairness evaluation")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--group_feature", type=str, default="home_ownership")
    p.add_argument("--batch_results_csv", type=str, default="")
    return p.parse_args()


def _build_group_bucket(series: pd.Series) -> pd.Series:
    # Keep natural categories for low-cardinality groups; bin numeric high-cardinality groups.
    if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > 8:
        binned = pd.qcut(series, q=2, labels=["low", "high"], duplicates="drop")
        return binned.astype(str).fillna("unknown")
    return series.astype(str).fillna("unknown")


def main() -> None:
    args = parse_args()
    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    rec_cfg = load_config(args.recourse_config)
    macro_cfg = load_config(args.macro_config)
    cfg = {"base": base_cfg, "model": model_cfg, "macro": macro_cfg, "recourse": rec_cfg, "group_feature": args.group_feature}
    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]
    test_path = f"{base_cfg.get('paths', {}).get('processed_data', 'data/processed')}/test.parquet"
    test_df = pd.read_parquet(test_path)

    model, calibrator, _, _ = load_latest_model_bundle(base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"))
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))

    proba = pd.Series(predict_proba_pd(model, calibrator, test_df[feature_cols]), index=test_df.index, dtype=float)
    target_col = contract["target"]
    scored = test_df[[args.group_feature, target_col]].copy()
    scored = scored.rename(columns={target_col: "y_true"})
    scored["group_bucket"] = _build_group_bucket(scored[args.group_feature])
    scored["approve"] = (proba <= tau).astype(int)
    scored["pred_default"] = (proba > tau).astype(int)

    base_bundle = compute_fairness_bundle(scored, group_col="group_bucket", approval_col="approve", y_true_col="y_true", y_pred_col="pred_default")

    out = run_ctx.tables_dir / "fairness_report.csv"
    pd.DataFrame(
        [
            {
                "group_feature": args.group_feature,
                **base_bundle,
                "tau": tau,
            }
        ]
    ).to_csv(out, index=False)

    group_out = run_ctx.tables_dir / "fairness_group_rates.csv"
    group_approval_rates(scored, group_col="group_bucket", approval_col="approve").to_csv(group_out, index=False)

    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    segment_sets_raw = fairness_cfg.get("segment_sets")
    segment_sets: list[list[str]] = []
    if isinstance(segment_sets_raw, list):
        for entry in segment_sets_raw:
            if isinstance(entry, str):
                segment_sets.append([entry])
            elif isinstance(entry, list):
                segment_sets.append([str(c) for c in entry if str(c).strip()])
    if not segment_sets:
        segment_sets = [
            ["home_ownership"],
            ["income_band"],
            ["risk_band"],
            ["income_band", "risk_band"],
            ["home_ownership", "risk_band"],
        ]
    near_upper = float(
        rec_cfg.get("segment_caps", {}).get("risk_band_thresholds", {}).get("near_upper", 0.10)
    ) if isinstance(rec_cfg.get("segment_caps", {}), dict) else 0.10
    mid_upper = float(
        rec_cfg.get("segment_caps", {}).get("risk_band_thresholds", {}).get("mid_upper", 0.25)
    ) if isinstance(rec_cfg.get("segment_caps", {}), dict) else 0.25
    annual_inc = pd.to_numeric(test_df.get("annual_inc", pd.Series([0.0] * len(test_df))), errors="coerce").fillna(0.0)
    q1, q2, q3 = annual_inc.quantile([0.25, 0.50, 0.75]).tolist()
    income_band = pd.cut(
        annual_inc,
        bins=[-float("inf"), q1, q2, q3, float("inf")],
        labels=["q1", "q2", "q3", "q4"],
        include_lowest=True,
    ).astype(str)
    d = proba - float(tau)
    risk_band = pd.Series(
        ["near" if v <= near_upper else ("mid" if v <= mid_upper else "high") for v in d.astype(float)],
        index=scored.index,
    )
    multi_scored = scored[["y_true", "approve", "pred_default"]].copy()
    multi_scored["income_band"] = income_band.values
    multi_scored["risk_band"] = risk_band.values
    if "home_ownership" in test_df.columns:
        multi_scored["home_ownership"] = test_df["home_ownership"].astype(str).fillna("unknown").values
    min_segment_n = int(max(1, fairness_cfg.get("min_segment_n", 30)))
    multi_report = compute_multi_segment_fairness(
        multi_scored,
        segment_sets=segment_sets,
        min_segment_n=min_segment_n,
    )
    multi_out = run_ctx.tables_dir / "fairness_multi_segment_report.csv"
    multi_report.to_csv(multi_out, index=False)

    scenarios = macro_cfg.get("shock_scenarios", []) if isinstance(macro_cfg.get("shock_scenarios", []), list) else []
    threshold_shift = float(macro_cfg.get("event_impact", {}).get("threshold_shift_per_msi_unit", 0.0))
    high_stress_sev = float(macro_cfg.get("fairness", {}).get("high_stress_severity", 0.6))
    stress_matrix = build_fairness_stress_matrix(
        scored_base=scored[["group_bucket", "y_true"]],
        proba=proba,
        tau=tau,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        group_col="group_bucket",
        high_stress_severity=high_stress_sev,
    )
    stress_out = run_ctx.tables_dir / "fairness_stress_matrix.csv"
    stress_matrix.to_csv(stress_out, index=False)

    recourse_bundle: dict[str, float] = {}
    recourse_out = None
    if args.batch_results_csv:
        batch_df = pd.read_csv(args.batch_results_csv)
        recourse_scored = pd.DataFrame()
        if "source_row_index" in batch_df.columns:
            src_idx = pd.to_numeric(batch_df["source_row_index"], errors="coerce")
            valid = src_idx.notna() & (src_idx >= 0) & (src_idx < len(scored))
            if valid.any():
                picked = batch_df.loc[valid].reset_index(drop=True)
                picked_idx = src_idx.loc[valid].astype(int).to_numpy()
                recourse_scored = pd.DataFrame(
                    {
                        "group_bucket": scored.iloc[picked_idx]["group_bucket"].astype(str).values,
                        "denied_base": picked["denied_base"].astype(int).values,
                        "gate_pass_any_candidate": picked["gate_pass_any_candidate"].astype(int).values,
                        "best_cost_usd": picked.get("best_cost_usd", pd.Series([0.0] * len(picked))).astype(float).values,
                        "best_horizon_months": picked.get("best_horizon_months", pd.Series([0] * len(picked))).astype(int).values,
                    }
                )
        elif len(batch_df) == len(scored):
            recourse_scored = pd.DataFrame(
                {
                    "group_bucket": scored["group_bucket"].astype(str).values,
                    "denied_base": batch_df["denied_base"].astype(int).values,
                    "gate_pass_any_candidate": batch_df["gate_pass_any_candidate"].astype(int).values,
                    "best_cost_usd": batch_df.get("best_cost_usd", pd.Series([0.0] * len(batch_df))).astype(float).values,
                    "best_horizon_months": batch_df.get("best_horizon_months", pd.Series([0] * len(batch_df))).astype(int).values,
                }
            )

        if not recourse_scored.empty:
            recourse_bundle = build_recourse_fairness_bundle(recourse_scored, group_col="group_bucket")
            recourse_group = (
                recourse_scored[recourse_scored["denied_base"] == 1]
                .groupby("group_bucket", dropna=False)
                .agg(
                    denied_count=("denied_base", "size"),
                    recourse_success_rate=("gate_pass_any_candidate", "mean"),
                    avg_best_cost_usd=("best_cost_usd", "mean"),
                    avg_best_horizon_months=("best_horizon_months", "mean"),
                )
                .reset_index()
            )
            recourse_out = run_ctx.tables_dir / "fairness_recourse_group_report.csv"
            recourse_group.to_csv(recourse_out, index=False)

    high_stress_df = stress_matrix[stress_matrix["high_stress"] == 1]
    max_high_stress_gap = float(high_stress_df["approval_gap"].max()) if not high_stress_df.empty else 0.0

    run_ctx.save_metrics(
        {
            **base_bundle,
            "fairness_multi_max_approval_gap": float(multi_report["approval_gap"].max()) if not multi_report.empty else 0.0,
            "fairness_multi_max_equalized_odds_gap": float(multi_report["equalized_odds_gap"].max()) if not multi_report.empty else 0.0,
            "fairness_multi_segment_coverage_rate": float(multi_report["segment_coverage_rate"].min()) if not multi_report.empty else 0.0,
            "rows": len(scored),
            "stress_scenario_count": int(len(stress_matrix) - 1),  # exclude base row
            "max_stress_approval_gap": float(stress_matrix["approval_gap"].max()) if not stress_matrix.empty else 0.0,
            "max_high_stress_approval_gap": max_high_stress_gap,
            **recourse_bundle,
        }
    )
    logger.info("Fairness report saved: %s", out)
    logger.info("Fairness stress matrix saved: %s", stress_out)
    if recourse_out is not None:
        logger.info("Fairness recourse group report saved: %s", recourse_out)


if __name__ == "__main__":
    main()
