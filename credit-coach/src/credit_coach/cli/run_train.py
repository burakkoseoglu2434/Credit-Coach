from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from credit_coach.data.ingest import load_feature_contract
from credit_coach.data.features import get_xy
from credit_coach.data.split import split_train_calibration
from credit_coach.model.calibrate import calibrate_classifier
from credit_coach.model.evaluate import evaluate_binary_classifier
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import save_model_bundle
from credit_coach.model.train import get_training_backend_info, train_risk_model
from credit_coach.safety.statistical import normal_two_sided_half_width
from credit_coach.storage.db import get_session, init_db
from credit_coach.storage.repository import save_model_run
from credit_coach.utils.hashing import hash_config
from credit_coach.utils.run_context import create_run_context, load_config
from credit_coach.data.schema import ModelRunRecord

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_train")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Credit Coach model train CLI")
    parser.add_argument("--config", type=str, default="configs/model.yaml")
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def _merge_dict(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def check_imports() -> None:
    from credit_coach.utils.run_context import RunContext  # noqa: F401
    from credit_coach.utils.hashing import hash_file  # noqa: F401
    from credit_coach.storage.models import (  # noqa: F401
        CustomerSnapshotORM,
        MacroSnapshotORM,
        ModelRunORM,
        PlanRecordORM,
    )
    from credit_coach.recourse.action_space import ACTION_SPACE  # noqa: F401
    logger.info("All imports OK")


def check_db() -> None:
    init_db()
    with get_session() as session:
        result = session.execute(__import__("sqlalchemy").text("SELECT 1")).scalar()
        assert result == 1
    logger.info("Database connection OK")


def check_feature_lock(features_cfg_path: str) -> None:
    contract = load_feature_contract(features_cfg_path)
    count = len(contract["features"])
    if count <= 0:
        logger.error("Feature lock invalid. No features configured.")
        sys.exit(1)
    logger.info("Feature lock OK: %d features", count)


def dry_run(base_cfg: dict) -> None:
    logger.info("=" * 60)
    logger.info("CREDIT COACH - DRY RUN")
    logger.info("=" * 60)

    check_imports()
    check_db()
    check_feature_lock(base_cfg.get("features_config", "configs/features_48.yaml"))

    ctx = create_run_context(base_cfg, base_artifact_dir="artifacts/runs")
    logger.info("Dry run success. run_id=%s artifacts=%s", ctx.run_id, ctx.artifact_dir)


def train_pipeline(cfg: dict) -> None:
    paths = cfg.get("paths", {})
    features_cfg = cfg.get("features_config", "configs/features_48.yaml")
    contract = load_feature_contract(features_cfg)
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_dir = Path(paths.get("processed_data", "data/processed"))
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            "Processed train/test parquet not found. Run run_prepare_data first."
        )

    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)

    split_cfg = cfg.get("split_protocol", {}) if isinstance(cfg.get("split_protocol", {}), dict) else {}
    split_out_of_time = bool(split_cfg.get("out_of_time", False))
    split_time_column = str(split_cfg.get("time_column", "")).strip() or None
    calibration_size = float(cfg.get("calibration", {}).get("holdout_size", 0.20))
    split_parts = split_train_calibration(
        train_df,
        target_col=target_col,
        calibration_size=calibration_size,
        random_state=int(split_cfg.get("random_state", 42)),
        time_column=split_time_column,
        out_of_time=split_out_of_time,
    )
    train_core_df = split_parts.train_core_df
    calibration_df = split_parts.calibration_df

    x_train, y_train = get_xy(train_core_df, feature_cols, target_col)
    x_cal, y_cal = get_xy(calibration_df, feature_cols, target_col)
    x_test, y_test = get_xy(test_df, feature_cols, target_col)

    model_cfg = cfg.get("model", {})
    params = model_cfg.get("params", {})
    cal_cfg = cfg.get("calibration", {})
    tau = float(cfg.get("decision", {}).get("tau_0", 0.35))

    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    model, model_backend = train_risk_model(
        x_train=x_train,
        y_train=y_train,
        model_type=model_cfg.get("type", "xgboost"),
        params=params,
    )
    calibrator = calibrate_classifier(
        model=model,
        x_cal=x_cal,
        y_cal=y_cal,
        method=cal_cfg.get("method", "isotonic"),
    )

    y_prob = predict_proba_pd(model, calibrator, x_test)
    metrics = evaluate_binary_classifier(y_test, y_prob, tau=tau)
    metrics.update(
        {
            "train_rows": int(len(train_df)),
            "train_core_rows": int(len(train_core_df)),
            "calibration_rows": int(len(calibration_df)),
            "test_rows": int(len(test_df)),
            "feature_count": int(len(feature_cols)),
            "model_backend": model_backend,
            "split_protocol_compliant": 1.0,
        }
    )
    backend_info = get_training_backend_info(model)
    metrics.update(
        {
            "requested_backend": backend_info.get("requested_backend"),
            "backend_reason": backend_info.get("backend_reason"),
            "fallback_reason": backend_info.get("fallback_reason"),
        }
    )

    model_version = run_ctx.run_id
    registry_path = Path(cfg.get("registry", {}).get("path", "artifacts/models"))
    model_dir = registry_path / model_version
    model_dir.mkdir(parents=True, exist_ok=True)
    y_cal_arr = y_cal.to_numpy(dtype=float)
    y_prob_cal = np.asarray(predict_proba_pd(model, calibrator, x_cal), dtype=float)
    residuals = np.abs(y_cal_arr - y_prob_cal)
    alpha_grid = [0.01, 0.02, 0.05, 0.10]
    uncertainty_bins = int(max(4, int(cal_cfg.get("uncertainty_bins", 10))))
    raw_edges = np.quantile(y_prob_cal, np.linspace(0.0, 1.0, uncertainty_bins + 1))
    score_edges = np.unique(np.clip(raw_edges.astype(float), 0.0, 1.0))
    if len(score_edges) < 3:
        score_edges = np.asarray([0.0, 0.5, 1.0], dtype=float)
    if float(score_edges[0]) > 0.0:
        score_edges = np.concatenate([[0.0], score_edges])
    if float(score_edges[-1]) < 1.0:
        score_edges = np.concatenate([score_edges, [1.0]])

    score_bin_idx = np.digitize(y_prob_cal, score_edges[1:-1], right=True)
    score_bin_widths = {f"{a:.4f}": [] for a in alpha_grid}
    score_bin_counts: list[int] = []
    score_bin_gaps: list[float] = []
    score_bin_mean_prob: list[float] = []
    score_bin_mean_label: list[float] = []
    global_label_rate = float(np.mean(y_cal_arr)) if len(y_cal_arr) else 0.5
    for b in range(len(score_edges) - 1):
        mask = score_bin_idx == b
        count_b = int(np.sum(mask))
        if count_b > 0:
            mean_prob_b = float(np.mean(y_prob_cal[mask]))
            mean_label_b = float(np.mean(y_cal_arr[mask]))
        else:
            mean_prob_b = float((score_edges[b] + score_edges[b + 1]) / 2.0)
            mean_label_b = float(global_label_rate)
        gap_b = float(abs(mean_label_b - mean_prob_b))
        score_bin_counts.append(count_b)
        score_bin_gaps.append(gap_b)
        score_bin_mean_prob.append(mean_prob_b)
        score_bin_mean_label.append(mean_label_b)
        for a in alpha_grid:
            key = f"{a:.4f}"
            width_b = normal_two_sided_half_width(alpha=float(a), p_hat=mean_label_b, n=max(1, count_b))
            score_bin_widths[key].append(float(width_b))

    non_empty_gaps = [g for g, c in zip(score_bin_gaps, score_bin_counts) if c > 0]
    if not non_empty_gaps:
        non_empty_gaps = [0.0]
    conformal_payload = {
        "model_version": model_version,
        "sample_count": int(len(residuals)),
        "calibration_source": "calibration_split",
        "alpha_grid": [float(a) for a in alpha_grid],
        "residual_quantiles": {
            f"{a:.4f}": float(np.quantile(residuals, 1.0 - float(a)))
            for a in alpha_grid
        },
        "calibration_gap_quantiles": {
            f"{a:.4f}": float(np.quantile(non_empty_gaps, 1.0 - float(a)))
            for a in alpha_grid
        },
        "score_bin_edges": [float(v) for v in score_edges.tolist()],
        "score_bin_counts": score_bin_counts,
        "score_bin_gaps": [float(v) for v in score_bin_gaps],
        "score_bin_mean_prob": [float(v) for v in score_bin_mean_prob],
        "score_bin_mean_label": [float(v) for v in score_bin_mean_label],
        "score_bin_widths": score_bin_widths,
    }
    conformal_artifact_path = model_dir / "conformal_calibration.json"
    conformal_artifact_path.write_text(
        json.dumps(conformal_payload, indent=2),
        encoding="utf-8",
    )
    manifest = save_model_bundle(
        model=model,
        calibrator=calibrator,
        metrics=metrics,
        model_version=model_version,
        base_path=cfg.get("registry", {}).get("path", "artifacts/models"),
        extra_manifest_fields={"conformal_calibration_path": str(conformal_artifact_path)},
    )

    model_run = ModelRunRecord(
        run_id=run_ctx.run_id,
        model_version=model_version,
        run_type="train",
        config_hash=hash_config(cfg),
        metrics=metrics,
        tau_used=tau,
        notes="week3 train+calibration",
    )
    save_model_run(model_run)

    split_protocol_payload = {
        "protocol": "train_core/calibration/test",
        "out_of_time": bool(split_out_of_time),
        "time_column": split_time_column or "",
        "train_rows": int(len(train_df)),
        "train_core_rows": int(len(train_core_df)),
        "calibration_rows": int(len(calibration_df)),
        "test_rows": int(len(test_df)),
    }
    split_protocol_out = run_ctx.tables_dir / "split_protocol_report.json"
    split_protocol_out.write_text(json.dumps(split_protocol_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    run_ctx.save_metrics(metrics)

    logger.info("Training completed. model_version=%s", model_version)
    logger.info("AUC=%.4f PR-AUC=%.4f ECE=%.4f", metrics["auc"], metrics["pr_auc"], metrics["ece"])
    logger.info("Model manifest: %s", manifest)


def main() -> None:
    args = parse_args()
    base_cfg = load_config(args.base_config)
    override_cfg = load_config(args.config) if Path(args.config).exists() else {}
    cfg = _merge_dict(base_cfg, override_cfg)

    if args.dry_run:
        dry_run(cfg)
        return

    train_pipeline(cfg)


if __name__ == "__main__":
    main()
