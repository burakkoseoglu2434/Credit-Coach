from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass
class SplitResult:
    train_df: pd.DataFrame
    test_df: pd.DataFrame


@dataclass
class TrainCalibrationSplit:
    train_core_df: pd.DataFrame
    calibration_df: pd.DataFrame


def split_dataframe(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    time_column: str | None = None,
    out_of_time: bool = False,
) -> SplitResult:
    if out_of_time and time_column and time_column in df.columns:
        tmp = df.copy()
        tmp[time_column] = pd.to_datetime(tmp[time_column], errors="coerce")
        tmp = tmp.sort_values(time_column).reset_index(drop=True)
        cut = int(len(tmp) * (1.0 - test_size))
        cut = max(cut, 1)
        train_df = tmp.iloc[:cut].copy()
        test_df = tmp.iloc[cut:].copy()
        return SplitResult(train_df=train_df, test_df=test_df)

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[target_col] if target_col in df.columns else None,
    )
    return SplitResult(train_df=train_df.copy(), test_df=test_df.copy())


def split_train_calibration(
    train_df: pd.DataFrame,
    *,
    target_col: str,
    calibration_size: float = 0.20,
    random_state: int = 42,
    time_column: str | None = None,
    out_of_time: bool = False,
) -> TrainCalibrationSplit:
    calibration_size = float(max(0.05, min(0.5, calibration_size)))
    if out_of_time and time_column and time_column in train_df.columns:
        tmp = train_df.copy()
        tmp[time_column] = pd.to_datetime(tmp[time_column], errors="coerce")
        tmp = tmp.sort_values(time_column).reset_index(drop=True)
        cut = int(len(tmp) * (1.0 - calibration_size))
        cut = max(1, min(cut, len(tmp) - 1))
        train_core_df = tmp.iloc[:cut].copy()
        calibration_df = tmp.iloc[cut:].copy()
        return TrainCalibrationSplit(train_core_df=train_core_df, calibration_df=calibration_df)

    tr, cal = train_test_split(
        train_df,
        test_size=calibration_size,
        random_state=random_state,
        stratify=train_df[target_col] if target_col in train_df.columns else None,
    )
    return TrainCalibrationSplit(train_core_df=tr.copy(), calibration_df=cal.copy())
