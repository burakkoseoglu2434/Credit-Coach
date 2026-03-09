from __future__ import annotations

import pandas as pd
import pytest

from credit_coach.data.ingest import validate_and_select_columns
from credit_coach.data.preprocess import preprocess_dataframe
from credit_coach.data.split import split_dataframe, split_train_calibration


def test_validate_and_select_columns_missing_raises():
    df = pd.DataFrame({"a": [1], "target": [0]})
    with pytest.raises(ValueError):
        validate_and_select_columns(df, features=["a", "b"], target="target", fail_on_missing=True)


def test_preprocess_encodes_categorical_and_splits():
    df = pd.DataFrame(
        {
            "f1": [1.0, 2.0, None, 4.0, 5.0],
            "f2": ["a", "b", "a", None, "c"],
            "target": [0, 1, 0, 1, 0],
        }
    )
    out, art = preprocess_dataframe(df, ["f1", "f2"])
    assert out[["f1", "f2"]].isna().sum().sum() == 0
    assert "f2" in art.categorical_maps

    split = split_dataframe(out, target_col="target", test_size=0.4, random_state=42)
    assert len(split.train_df) + len(split.test_df) == len(df)


def test_split_train_calibration_contract():
    df = pd.DataFrame(
        {
            "f1": list(range(20)),
            "target": [0, 1] * 10,
        }
    )
    out = split_train_calibration(df, target_col="target", calibration_size=0.25, random_state=42)
    assert len(out.train_core_df) + len(out.calibration_df) == len(df)
    assert 0 < len(out.calibration_df) < len(df)
