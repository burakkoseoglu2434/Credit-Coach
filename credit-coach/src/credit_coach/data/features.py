from __future__ import annotations

import pandas as pd


def get_xy(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> tuple[pd.DataFrame, pd.Series]:
    x = df[feature_cols].copy()
    y = df[target_col].astype(int).copy()
    return x, y
