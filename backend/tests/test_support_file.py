import pandas as pd
import pytest
import yaml

from credit_coach.baseline import CSV
from credit_coach.support import (
    SUPPORT_PATH,
    SupportFileError,
    build,
    build_content,
    load_support,
)


def test_support_file_loads_and_hash_verifies():
    s = load_support()
    assert s.sayisal["fico_range_low"][0] == 660.0
    assert s.kategorik["application_type"] == frozenset({"Individual"})


def test_hand_edit_is_detected(tmp_path):
    raw = yaml.safe_load(SUPPORT_PATH.read_text())
    raw["sayisal"]["dti"]["max"] = 999.0
    p = tmp_path / "support.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(SupportFileError):
        load_support(p)


def test_known_limits_are_documented_in_file():
    text = " ".join(yaml.safe_load(SUPPORT_PATH.read_text())["bilinen_sinirlar"])
    assert "revol_util (max 892.3" in text and "annual_inc (max 7.5e+06" in text


def test_build_content_uses_given_rows_only():
    from credit_coach.features import allowed_features, load_manifest

    kinds = {c.ad: c for c in load_manifest()}
    row = {n: (1.0 if kinds[n].tip == "float" else "a") for n in allowed_features()}
    df = pd.DataFrame([row, {**row, "dti": 5.0}])
    c = build_content(df)
    assert c["sayisal"]["dti"] == {"min": 1.0, "max": 5.0}
    assert c["kategorik"]["purpose"] == ["a"]


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_committed_file_is_reproducible_from_train_split():
    assert build(write=False) == SUPPORT_PATH.read_text()
