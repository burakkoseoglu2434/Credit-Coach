from datetime import date

import pandas as pd
import pytest

from credit_coach.split import (
    SplitConfig,
    Window,
    assign_split,
    build_target,
    cohort,
    load_split_config,
    split_report,
    validate_config,
)
from tests.test_features import CSV


def _frame() -> pd.DataFrame:
    months = pd.period_range("2011-10", "2016-03", freq="M")
    rows = []
    for p in months:
        for term in (" 36 months", " 60 months"):
            rows.append({"issue_d": p.strftime("%b-%Y"), "term": term, "target": len(rows) % 2})
    return pd.DataFrame(rows)


def test_config_valid_and_ordered_with_gaps():
    cfg = load_split_config()
    s = cfg.splits
    assert s["train"].end < s["calibration"].start
    assert s["calibration"].end < s["test"].start
    assert s["test"].start > s["train"].end


def test_overlapping_or_gapless_config_rejected():
    cfg = load_split_config()
    bad = SplitConfig(
        cfg.term,
        cfg.issue_d_min,
        cfg.issue_d_max,
        2,
        {**cfg.splits, "calibration": Window(date(2015, 1, 1), date(2015, 6, 1))},
    )
    with pytest.raises(ValueError):
        validate_config(bad)


def test_cohort_excludes_60_month_and_out_of_range():
    c = cohort(_frame())
    assert (c["term"].str.strip() == "36 months").all()
    assert c["issue_date"].min() >= pd.Timestamp("2012-01-01")
    assert c["issue_date"].max() <= pd.Timestamp("2015-12-01")


def test_splits_do_not_overlap_and_test_is_after_train():
    df = _frame()
    c = cohort(df)
    label = assign_split(df)
    dates = {
        n: c.loc[label[label == n].index, "issue_date"] for n in ("train", "calibration", "test")
    }
    assert all(len(v) > 0 for v in dates.values())
    assert dates["train"].max() < dates["calibration"].min()
    assert dates["calibration"].max() < dates["test"].min()
    assert dates["test"].min() > dates["train"].max()
    assert label.index.is_unique


def test_report_counts_sum_to_cohort():
    df = _frame()
    rep = split_report(df)
    assert rep["rows"].sum() == len(cohort(df))
    assert list(rep.index) == ["train", "calibration", "test", "gap"]


def test_build_target_rejects_non_binary():
    with pytest.raises(ValueError):
        build_target(pd.DataFrame({"target": [0, 2]}))


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_real_data_report():
    df = pd.read_csv(CSV, usecols=["term", "issue_d", "target"])
    rep = split_report(df)
    print(rep)
    assert rep["rows"].sum() == 589_488
    assert (rep.loc[["train", "calibration", "test"], "rows"] > 0).all()
