from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.utils.run_context import load_config


def load_feature_contract(config_path: str | Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    features = cfg.get("features", [])
    target_cfg = cfg.get("target", {})
    target = target_cfg.get("name", "target")
    rules = cfg.get("rules", {})
    return {
        "features": features,
        "target": target,
        "rules": {
            "fail_on_missing": bool(rules.get("fail_on_missing", True)),
            "drop_extra_columns": bool(rules.get("drop_extra_columns", True)),
            "min_rows": int(rules.get("min_rows", 1)),
        },
    }


def validate_and_select_columns(
    df: pd.DataFrame,
    features: list[str],
    target: str,
    fail_on_missing: bool = True,
    drop_extra_columns: bool = True,
) -> pd.DataFrame:
    required = features + [target]
    missing = [c for c in required if c not in df.columns]
    if missing and fail_on_missing:
        raise ValueError(f"Feature lock violation. Missing columns: {missing}")

    if not drop_extra_columns:
        return df

    keep = [c for c in required if c in df.columns]
    return df[keep].copy()


def load_raw_dataset(raw_csv: str | Path, nrows: int | None = None) -> pd.DataFrame:
    path = Path(raw_csv)
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")
    return pd.read_csv(path, nrows=nrows)


def ingest_data(
    raw_csv: str | Path,
    features_cfg_path: str | Path,
    nrows: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    contract = load_feature_contract(features_cfg_path)
    df = load_raw_dataset(raw_csv, nrows=nrows)

    if len(df) < contract["rules"]["min_rows"]:
        raise ValueError(
            f"Insufficient rows: {len(df)} < {contract['rules']['min_rows']}"
        )

    selected = validate_and_select_columns(
        df=df,
        features=contract["features"],
        target=contract["target"],
        fail_on_missing=contract["rules"]["fail_on_missing"],
        drop_extra_columns=contract["rules"]["drop_extra_columns"],
    )
    return selected, contract
