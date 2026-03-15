from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from credit_coach.data.ingest import load_feature_contract
from credit_coach.ops.monitoring import compute_feature_psi_report, summarize_operational_health
from credit_coach.ops.telemetry import export_monitoring_telemetry
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_monitoring")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Operational monitoring snapshot")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--monitoring_config", type=str, default="configs/monitoring.yaml")
    p.add_argument("--plans_csv", type=str, default="")
    p.add_argument("--fairness_csv", type=str, default="")
    p.add_argument("--fairness_stress_csv", type=str, default="")
    p.add_argument("--shock_csv", type=str, default="")
    p.add_argument("--batch_summary_json", type=str, default="")
    return p.parse_args()


def _latest_or_fail(pattern: str) -> Path:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"No artifact found for pattern: {pattern}")
    return candidates[-1]


def _latest_or_none(pattern: str) -> Path | None:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        return None
    return candidates[-1]


def _resolve_plans_path(*, plans_csv_arg: str, batch_summary_path: Path | None) -> Path:
    if plans_csv_arg:
        return Path(plans_csv_arg)
    if batch_summary_path is not None:
        batch_results = batch_summary_path.parent / "batch_recourse_results.csv"
        if batch_results.exists():
            return batch_results
    latest_plans = _latest_or_none("*/tables/plans.csv")
    if latest_plans is not None:
        return latest_plans
    return _latest_or_fail("*/tables/batch_recourse_results.csv")


def _normalize_plans_df(plans_df: pd.DataFrame) -> pd.DataFrame:
    out = plans_df.copy()
    if "status" not in out.columns and "best_status" in out.columns:
        out["status"] = out["best_status"]
    if "risk_margin" not in out.columns and "best_worst_risk_margin" in out.columns:
        out["risk_margin"] = pd.to_numeric(out["best_worst_risk_margin"], errors="coerce").fillna(0.0)
    return out


def main() -> None:
    args = parse_args()
    base_cfg = load_config(args.base_config)
    mon_cfg = load_config(args.monitoring_config)
    run_ctx = create_run_context({"base": base_cfg, "monitoring": mon_cfg}, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]

    processed = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    train_df = pd.read_parquet(processed / "train.parquet")
    test_df = pd.read_parquet(processed / "test.parquet")

    if args.batch_summary_json:
        batch_summary_path = Path(args.batch_summary_json)
    else:
        batch_summary_path = _latest_or_none("*/tables/batch_summary.json")
    plans_path = _resolve_plans_path(plans_csv_arg=args.plans_csv, batch_summary_path=batch_summary_path)
    fairness_path = Path(args.fairness_csv) if args.fairness_csv else _latest_or_fail("*/tables/fairness_report.csv")
    if args.fairness_stress_csv:
        fairness_stress_path = Path(args.fairness_stress_csv)
    else:
        stress_candidates = sorted(Path("artifacts/runs").glob("*/tables/fairness_stress_matrix.csv"))
        fairness_stress_path = stress_candidates[-1] if stress_candidates else None
    shock_path = Path(args.shock_csv) if args.shock_csv else _latest_or_fail("*/tables/shock_reliability.csv")

    plans_df = _normalize_plans_df(pd.read_csv(plans_path))
    fairness_df = pd.read_csv(fairness_path)
    fairness_stress_df = pd.read_csv(fairness_stress_path) if fairness_stress_path is not None and fairness_stress_path.exists() else pd.DataFrame()
    shock_df = pd.read_csv(shock_path)
    batch_summary_payload: dict = {}
    if batch_summary_path is not None and batch_summary_path.exists():
        try:
            batch_summary_payload = json.loads(batch_summary_path.read_text(encoding="utf-8"))
        except Exception:
            batch_summary_payload = {}

    psi_bins = int(mon_cfg.get("psi", {}).get("bins", 10))
    psi_report = compute_feature_psi_report(train_df, test_df, feature_cols=feature_cols, bins=psi_bins)

    thresholds = mon_cfg.get("thresholds", {})
    summary, alerts = summarize_operational_health(
        plans_df=plans_df,
        fairness_df=fairness_df,
        shock_df=shock_df,
        psi_report=psi_report,
        thresholds=thresholds,
        fairness_stress_df=fairness_stress_df,
    )
    # Enrich monitoring summary with latest batch KPIs to keep telemetry
    # payload aligned with release gate metrics.
    for key in ("denied_to_approved_lift", "latency_p95_ms", "latency_p99_ms", "error_rate"):
        if key in batch_summary_payload:
            try:
                summary[key] = float(batch_summary_payload.get(key))
            except Exception:
                continue
    if "model_version" in batch_summary_payload:
        summary["model_version"] = str(batch_summary_payload.get("model_version"))
    if "config_hash" in batch_summary_payload:
        summary["config_hash"] = str(batch_summary_payload.get("config_hash"))

    summary_df = pd.DataFrame([summary])
    alerts_df = pd.DataFrame(alerts)
    summary_path = run_ctx.tables_dir / "monitoring_summary.csv"
    alerts_path = run_ctx.tables_dir / "monitoring_alerts.csv"
    psi_path = run_ctx.tables_dir / "psi_feature_report.csv"
    telemetry_path = run_ctx.tables_dir / "telemetry_export.json"
    summary_df.to_csv(summary_path, index=False)
    alerts_df.to_csv(alerts_path, index=False)
    psi_report.to_csv(psi_path, index=False)

    telemetry_cfg = mon_cfg.get("telemetry", {}) if isinstance(mon_cfg.get("telemetry", {}), dict) else {}
    telemetry_cfg_eff = dict(telemetry_cfg)
    base_labels = telemetry_cfg_eff.get("labels", {}) if isinstance(telemetry_cfg_eff.get("labels", {}), dict) else {}
    labels = dict(base_labels)
    labels["run_id"] = run_ctx.run_id
    if "model_version" in summary:
        labels["model_version"] = str(summary["model_version"])
    if "config_hash" in summary:
        labels["config_hash"] = str(summary["config_hash"])
    telemetry_cfg_eff["labels"] = labels
    telemetry_result = export_monitoring_telemetry(
        summary=summary,
        alert_count=int(len(alerts_df)),
        high_alert_count=int((alerts_df.get("severity", pd.Series(dtype=str)) == "HIGH").sum()) if not alerts_df.empty else 0,
        exporter_cfg=telemetry_cfg_eff,
    )
    telemetry_result["send_success_rate"] = 1.0 if bool(telemetry_result.get("exported", False)) else 0.0
    telemetry_result["ingest_lag_s_p95"] = float(
        telemetry_cfg_eff.get("ingest_lag_s_p95", telemetry_result.get("ingest_lag_s_p95", 0.0))
    )
    telemetry_result["telemetry_status"] = str(
        telemetry_result.get("telemetry_status", telemetry_result.get("status", "unknown"))
    )
    telemetry_result["telemetry_failure_reason"] = str(telemetry_result.get("telemetry_failure_reason", ""))
    telemetry_result["telemetry_artifact_path"] = "tables/telemetry_export.json"
    telemetry_path.write_text(json.dumps(telemetry_result, indent=2, ensure_ascii=False), encoding="utf-8")

    run_ctx.save_metrics(
        {
            **summary,
            "alert_count": int(len(alerts_df)),
            "high_alert_count": int((alerts_df.get("severity", pd.Series(dtype=str)) == "HIGH").sum()) if not alerts_df.empty else 0,
            "telemetry_exported": bool(telemetry_result.get("exported", False)),
            "telemetry_status": str(telemetry_result.get("status", "unknown")),
            "telemetry_mode": str(telemetry_result.get("mode", "")),
        }
    )
    logger.info("Monitoring summary saved: %s", summary_path)
    logger.info("Monitoring alerts saved: %s", alerts_path)
    logger.info("PSI report saved: %s", psi_path)
    logger.info("Telemetry export status: mode=%s status=%s", telemetry_result.get("mode"), telemetry_result.get("status"))


if __name__ == "__main__":
    main()
