from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from credit_coach.data.ingest import load_feature_contract
from credit_coach.data.features import get_xy
from credit_coach.model.registry import load_latest_model_bundle, save_model_bundle
from credit_coach.retraining.governance import evaluate_governance_workflow, governance_decision
from credit_coach.retraining.train_job import train_challenger
from credit_coach.utils.hashing import hash_config, hash_file
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_retrain")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train challenger and run governance")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--governance_config", type=str, default="configs/governance.yaml")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    gov_cfg = load_config(args.governance_config)

    run_ctx = create_run_context({"base": base_cfg, "model": model_cfg, "gov": gov_cfg}, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feat = contract["features"]
    target = contract["target"]

    processed = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    train_df = pd.read_parquet(processed / "train.parquet")
    test_df = pd.read_parquet(processed / "test.parquet")

    x_train, y_train = get_xy(train_df, feat, target)
    x_test, y_test = get_xy(test_df, feat, target)

    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    params = model_cfg.get("model", {}).get("params", {})
    model_type = model_cfg.get("model", {}).get("type", "xgboost")

    challenger_model, challenger_cal, challenger_metrics = train_challenger(
        x_train, y_train, x_test, y_test, model_type=model_type, params=params, tau=tau
    )

    _, _, champ_manifest, champ_metrics = load_latest_model_bundle(base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"))
    status, reasons = governance_decision(champ_metrics, challenger_metrics, gov_cfg.get("gates", {}))

    challenger_version = f"{run_ctx.run_id}_challenger"
    challenger_manifest = save_model_bundle(
        challenger_model,
        challenger_cal,
        challenger_metrics,
        model_version=challenger_version,
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
    )
    release_artifacts = {
        "model_hash": hash_file(challenger_manifest.get("model_path", "")) if challenger_manifest.get("model_path") else "",
        "config_hash": hash_config({"base": base_cfg, "model": model_cfg, "gov": gov_cfg}),
        "data_hash": hash_file(processed / "train.parquet"),
        "evidence_hash": hash_file(challenger_manifest.get("metrics_path", "")) if challenger_manifest.get("metrics_path") else "",
    }
    approvals_cfg = gov_cfg.get("approvals", {}) if isinstance(gov_cfg.get("approvals", {}), dict) else {}
    rollback_cfg = gov_cfg.get("rollback", {}) if isinstance(gov_cfg.get("rollback", {}), dict) else {}
    governance_eval = evaluate_governance_workflow(
        champion_metrics=champ_metrics,
        challenger_metrics=challenger_metrics,
        gates=gov_cfg.get("gates", {}),
        approvals=approvals_cfg,
        release_artifacts=release_artifacts,
        rollback_test_passed=bool(rollback_cfg.get("drill_passed", False)),
    )
    status = str(governance_eval.get("status", status))
    reasons = list(governance_eval.get("reasons", reasons))

    decision = {
        "status": status,
        "reasons": reasons,
        "champion": champ_manifest,
        "challenger": challenger_manifest,
        "champion_metrics": champ_metrics,
        "challenger_metrics": challenger_metrics,
        "governance_workflow": governance_eval,
        "release_artifacts": release_artifacts,
    }

    out = run_ctx.tables_dir / "governance_decision.json"
    out.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    run_ctx.save_metrics(
        {
            "status": status,
            "reason_count": len(reasons),
            "challenger_auc": challenger_metrics.get("auc", 0.0),
            "approval_compliance": float(governance_eval.get("approval_compliance", 0.0)),
            "release_artifact_completeness": float(governance_eval.get("release_artifact_completeness", 0.0)),
            "rollback_test_passed": bool(governance_eval.get("rollback_test_passed", False)),
        }
    )

    logger.info("Retrain governance status: %s", status)
    logger.info("Decision file: %s", out)


if __name__ == "__main__":
    main()
