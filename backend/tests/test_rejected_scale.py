from credit_coach.rejected_scale import archive_documents, monthly, observations

REJ = (
    "Amount Requested,Application Date,Loan Title,Risk_Score,Debt-To-Income Ratio,Zip Code,"
    "State,Employment Length,Policy Code\n"
    "1000,2013-09-01,a,0,1%,1xx,NY,5 years,0\n"
    "1000,2013-09-02,a,700,1%,1xx,NY,5 years,0\n"
    "1000,2013-09-03,a,,1%,1xx,NY,5 years,0\n"
    "1000,2013-11-01,a,990,1%,1xx,NY,5 years,0\n"
    "1000,2013-11-02,a,300,1%,1xx,NY,5 years,0\n"
)
ACC = (
    "id,issue_d,fico_range_low,fico_range_high\n"
    "1,Sep-2013,660,664\n"
    "2,Sep-2013,700,704\n"
    "3,Nov-2013,845,849\n"
)


def _files(tmp_path):
    r, a = tmp_path / "r.csv", tmp_path / "a.csv"
    r.write_text(REJ)
    a.write_text(ACC)
    return r, a


def test_monthly_stats(tmp_path):
    m = monthly(*_files(tmp_path))
    sep, nov = m["reddedilen"]
    assert (sep.ay, sep.n, sep.bos_yuzde, sep.min, sep.maks) == ("2013-09", 3, 33.3, 0.0, 700.0)
    assert (nov.ay, nov.min, nov.medyan, nov.maks) == ("2013-11", 300.0, 645.0, 990.0)
    assert [(x.ay, x.min, x.maks) for x in m["kabul"]] == [
        ("2013-09", 660.0, 700.0),
        ("2013-11", 845.0, 845.0),
    ]


def test_observations_are_plain_facts(tmp_path):
    m = monthly(*_files(tmp_path))
    o = observations(m["reddedilen"])
    assert o["maks_850_ustu"] == ("2013-11", "2013-11", 1)
    assert o["min_sifir"] == ("2013-09", "2013-09", 1)
    assert o["bos_50_ustu"] is None
    assert observations(m["kabul"])["maks_850_ustu"] is None


def test_archive_documents_lists_non_data_entries(tmp_path):
    for n in ("rejected_2007_to_2018Q4.csv.gz", "accepted_2007_to_2018q4.csv", ".DS_Store"):
        (tmp_path / n).write_text("x")
    assert archive_documents(tmp_path) == []
    (tmp_path / "LCDataDictionary.xlsx").write_text("x")
    assert archive_documents(tmp_path) == ["LCDataDictionary.xlsx"]
