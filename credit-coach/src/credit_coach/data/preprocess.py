from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PreprocessArtifacts:
    categorical_maps: dict[str, dict[str, int]]
    medians: dict[str, float]


def _encode_categorical(series: pd.Series) -> tuple[pd.Series, dict[str, int]]:
    values = series.fillna("UNKNOWN").astype(str)
    uniques = sorted(values.unique().tolist())
    mapping = {v: i for i, v in enumerate(uniques)}
    encoded = values.map(mapping).astype(float)
    return encoded, mapping


def preprocess_dataframe(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, PreprocessArtifacts]:
    out = df.copy()
    categorical_maps: dict[str, dict[str, int]] = {}
    medians: dict[str, float] = {}

    for col in feature_cols:
        s = out[col]
        if s.dtype == "O":
            encoded, mapping = _encode_categorical(s)
            out[col] = encoded
            categorical_maps[col] = mapping
            medians[col] = float(np.nanmedian(encoded.values))
            continue

        numeric = pd.to_numeric(s, errors="coerce")
        median = float(numeric.median()) if not numeric.dropna().empty else 0.0
        out[col] = numeric.fillna(median)
        medians[col] = median

    return out, PreprocessArtifacts(categorical_maps=categorical_maps, medians=medians)


def apply_preprocess(
    df: pd.DataFrame,
    feature_cols: list[str],
    artifacts: PreprocessArtifacts,
) -> pd.DataFrame:
    out = df.copy()
    for col in feature_cols:
        s = out[col]
        if col in artifacts.categorical_maps:
            mapping = artifacts.categorical_maps[col]
            out[col] = s.fillna("UNKNOWN").astype(str).map(mapping).fillna(-1).astype(float)
        else:
            med = artifacts.medians.get(col, 0.0)
            out[col] = pd.to_numeric(s, errors="coerce").fillna(med)
    return out
