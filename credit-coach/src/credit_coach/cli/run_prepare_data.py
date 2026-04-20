from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from credit_coach.data.ingest import ingest_data
from credit_coach.data.preprocess import preprocess_dataframe
from credit_coach.data.split import split_dataframe
from credit_coach.utils.hashing import hash_file
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_prepare_data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prepare dataset with feature lock")
    p.add_argument("--config", type=str, default="configs/default.yaml")
    p.add_argument("--sample_rows", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    prep_cfg = cfg.get("prepare_data", {})

    raw_csv = cfg.get("paths", {}).get(
        "raw_csv", "data/lending_club/lending_club_48_features_20251026_114053.parquet"
    )
    features_cfg = cfg.get("features_config", "configs/features_48.yaml")
    sample_rows = args.sample_rows if args.sample_rows is not None else prep_cfg.get("sample_rows")

    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    df, contract = ingest_data(raw_csv=raw_csv, features_cfg_path=features_cfg, nrows=sample_rows)
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_df, artifacts = preprocess_dataframe(df, feature_cols)

    split = split_dataframe(
        processed_df,
        target_col=target_col,
        test_size=float(prep_cfg.get("test_size", 0.2)),
        random_state=int(prep_cfg.get("random_state", 42)),
        time_column=cfg.get("time_column"),
        out_of_time=bool(prep_cfg.get("out_of_time", False)),
    )

    processed_dir = Path(cfg.get("paths", {}).get("processed_data", "data/processed"))
    split_dir = Path(cfg.get("paths", {}).get("splits", "data/splits"))
    processed_dir.mkdir(parents=True, exist_ok=True)
    split_dir.mkdir(parents=True, exist_ok=True)

    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    split.train_df.to_parquet(train_path, index=False)
    split.test_df.to_parquet(test_path, index=False)

    split_index = {
        "train_rows": len(split.train_df),
        "test_rows": len(split.test_df),
        "feature_count": len(feature_cols),
        "target": target_col,
    }
    (split_dir / "split_summary.json").write_text(json.dumps(split_index, indent=2), encoding="utf-8")

    metrics = {
        "rows_total": len(processed_df),
        "rows_train": len(split.train_df),
        "rows_test": len(split.test_df),
        "feature_count": len(feature_cols),
        "raw_hash": hash_file(raw_csv),
        "categorical_encoded": len(artifacts.categorical_maps),
    }
    run_ctx.save_metrics(metrics)

    logger.info("Data prepared: train=%s test=%s", train_path, test_path)
    logger.info("Summary: %s", split_dir / "split_summary.json")


if __name__ == "__main__":
    main()
