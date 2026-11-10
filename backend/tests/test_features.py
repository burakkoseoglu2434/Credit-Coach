import pandas as pd
import pandera.pandas as pa
import pytest

from credit_coach.features import (
    MANIFEST_PATH,
    TYPES,
    allowed_features,
    build_schema,
    load_manifest,
)

CSV = (
    MANIFEST_PATH.parents[1]
    / "credit-coach/data/lending_club/lending_club_48_features_20251026_114053.csv"
)
FORBIDDEN = {
    "int_rate",
    "grade",
    "sub_grade",
    "debt_settlement_flag",
    "installment",
    "funded_amnt",
    "last_fico_range_low",
    "last_fico_range_high",
}


def test_manifest_has_48_unique_columns_and_no_unclassified():
    m = load_manifest()
    assert len(m) == 48
    assert all(c.sinif and c.gerekce for c in m)


def test_forbidden_columns_are_never_allowed():
    allowed = set(allowed_features())
    assert not (allowed & FORBIDDEN)
    assert {"target", "issue_d"}.isdisjoint(allowed)


def test_only_application_time_may_be_allowed():
    for c in load_manifest():
        assert (not c.izin_verilen) or c.sinif == "APPLICATION_TIME"


def _synthetic() -> pd.DataFrame:
    row = {}
    for c in load_manifest():
        row[c.ad] = [{"float": 1.0, "int": 0, "str": "x"}[c.tip]]
    return pd.DataFrame(row)


def test_schema_accepts_matching_frame():
    build_schema().validate(_synthetic())


def test_schema_rejects_extra_or_missing_column():
    df = _synthetic()
    with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
        build_schema().validate(df.assign(surprise=1))
    with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
        build_schema().validate(df.drop(columns=["target"]))


def test_schema_types_come_from_manifest():
    assert set(TYPES) == {"float", "int", "str"}


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_manifest_matches_raw_header():
    header = pd.read_csv(CSV, nrows=0).columns.tolist()
    assert header == [c.ad for c in load_manifest()]
