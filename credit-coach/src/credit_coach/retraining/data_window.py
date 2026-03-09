from __future__ import annotations

import pandas as pd


def select_rolling_window(df: pd.DataFrame, rolling_months: int = 12, time_col: str | None = None) -> pd.DataFrame:
    if time_col and time_col in df.columns:
        tmp = df.copy()
        tmp[time_col] = pd.to_datetime(tmp[time_col], errors="coerce")
        max_dt = tmp[time_col].max()
        if pd.notna(max_dt):
            cutoff = max_dt - pd.DateOffset(months=rolling_months)
            return tmp[tmp[time_col] >= cutoff].copy()
    return df.copy()
