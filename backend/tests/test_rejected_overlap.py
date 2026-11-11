import pytest

from credit_coach.data_source import load_sources, rejected_path
from credit_coach.rejected_overlap import ALL, FIELDS, POOLED, aggregate, render
from credit_coach.support import Support

SUP = Support(
    sayisal={
        "dti": (0.0, 39.99),
        "fico_range_low": (660.0, 845.0),
        "fico_range_high": (664.0, 850.0),
        "loan_amnt": (1000.0, 35000.0),
    },
    kategorik={"emp_length": frozenset({"< 1 year", "5 years", "10+ years"})},
    sha256="x" * 64,
)
HEADER = (
    "Amount Requested,Application Date,Loan Title,Risk_Score,Debt-To-Income Ratio,"
    "Zip Code,State,Employment Length,Policy Code"
)
ROWS = [
    # inside everything
    "5000,2013-03-01,a,700,10%,100xx,NY,5 years,0",
    # dti out (high), others in
    "5000,2013-04-01,a,700,55%,100xx,NY,5 years,0",
    # dti negative -> out; fico below range -> out
    "5000,2014-04-01,a,600,-1%,100xx,NY,< 1 year,0",
    # empty fields: not counted either way; amount above range
    "99999,2015-01-01,a,,,100xx,NY,,0",
    # unseen category (2 years not in this tiny support) with the rest inside
    "5000,2015-06-01,a,800,0%,100xx,NY, 2 years,0",
    # outside the studied years
    "5000,2009-06-01,a,800,0%,100xx,NY,5 years,0",
]


@pytest.fixture()
def res(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text("\n".join([HEADER, *ROWS]) + "\n")
    return aggregate(p, SUP)


def test_per_year_counts(res):
    assert res["2013"]["n"] == 2 and res["2013"]["x_dti"] == 1 and res["2013"]["e_dti"] == 2
    assert res["2014"]["x_dti"] == 1 and res["2014"]["x_risk_skoru"] == 1
    assert res["2015"]["n"] == 2
    assert res["2015"]["e_dti"] == 1 and res["2015"]["e_risk_skoru"] == 1  # empties not evaluated
    assert res["2015"]["x_talep_tutari"] == 1  # 99999 > 35000
    assert res["2015"]["x_calisma_suresi"] == 1  # '2 years' unseen, padding stripped


def test_pooled_and_all_periods(res):
    assert res[POOLED]["n"] == 5 and res[ALL]["n"] == 6
    assert "2012" not in res  # no rows that year


def test_joint_counts_use_main_fields_only(res):
    r = res[POOLED]
    assert r["e_any"] == 5
    assert r["x_any"] == 4  # row 1 is fully inside
    # rows 1, 2, 3 and 5 have all four fields; 2, 3 and 5 are out
    assert r["e_all"] == 4 and r["x_all"] == 3


def test_sensitivity_row_is_not_part_of_joint():
    assert [f.alan for f in FIELDS if not f.ana] == ["risk_skoru_alt"]


def test_render_has_the_required_sections(res):
    text = render(res, SUP, load_sources())
    assert "## Ne demek" in text and "## Ne DEMEK DEĞİL" in text
    assert "## Alan eşlemesi" in text and "işaretli" in text
    assert "EMİN DEĞİLİM" in text


@pytest.mark.skipif(not rejected_path().exists(), reason="rejected file not available locally")
def test_real_file_has_the_recorded_columns():
    import duckdb

    cols = [
        r[0]
        for r in duckdb.sql(
            f"describe select * from read_csv('{rejected_path()}', header=true, all_varchar=true)"
        ).fetchall()
    ]
    assert cols == load_sources()["lc_reddedilen"]["sutunlar"]


def test_report_doc_is_locked_to_the_recorded_source_and_has_the_required_lines():
    from credit_coach.rejected_overlap import REPORT

    text = REPORT.read_text()
    assert load_sources()["lc_reddedilen"]["sha256"] in text
    assert "## Ne demek" in text and "## Ne DEMEK DEĞİL" in text
    assert "## Alan eşlemesi" in text and "2012-2015" in text


def test_half_periods_and_pair_joint(res):
    h1, h2 = res["2012-2013"], res["2014-2015"]
    assert h1["n"] == 2 and h2["n"] == 3  # 2013 x2 ; 2014 x1 + 2015 x2
    assert h1["n"] + h2["n"] == res[POOLED]["n"]
    # dti + emp_length only: 2013 rows (in, out) -> out 1 of 2 evaluable
    assert (h1["e_any2"], h1["x_any2"], h1["e_all2"], h1["x_all2"]) == (2, 1, 2, 1)
    # 2014: dti -1 (out). 2015: row with empties (not evaluable) and row 800/0%/2 years (emp out)
    assert (h2["e_any2"], h2["x_any2"], h2["e_all2"], h2["x_all2"]) == (2, 2, 2, 2)
