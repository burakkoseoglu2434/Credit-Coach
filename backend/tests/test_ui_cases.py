"""The UI example cases are frozen real calibration records (tests/golden); the API itself must
still put each one into its category."""

import json

import pytest
from fastapi.testclient import TestClient

from credit_coach.app import app
from credit_coach.bundle import ROOT
from credit_coach.ui_cases import CASES, CSV_OUT, GOLDEN, ORDER, category

CASES_DATA = json.loads(CASES.read_text())
GOLDEN_BY_ID = {
    json.loads(line)["id"]: json.loads(line) for line in GOLDEN.read_text().splitlines()
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_five_cases_in_the_agreed_order():
    assert [c["anahtar"] for c in CASES_DATA] == list(ORDER)


@pytest.mark.parametrize("case", CASES_DATA, ids=[c["anahtar"] for c in CASES_DATA])
def test_case_falls_into_its_category_through_the_api(client, case):
    r = client.post(
        "/score", json={"basvuru": case["basvuru"], "basvuru_tarihi": case["basvuru_tarihi"]}
    )
    karar = r.json()["karar"]
    assert category(karar) == case["anahtar"]
    assert {
        "dis_durum": karar["dis_durum"],
        "plan_durumu": karar["plan"]["durum"],
        "destek_ihlalleri": karar["destek_ihlalleri"],
    } == case["beklenen"]


@pytest.mark.parametrize("case", CASES_DATA, ids=[c["anahtar"] for c in CASES_DATA])
def test_case_is_a_frozen_golden_record(client, case):
    g = GOLDEN_BY_ID[case["kaynak_id"]]
    assert g["id"].startswith("cal-")  # real calibration record
    if not case["varyant"]:
        assert case["basvuru"] == g["girdi"]["basvuru"]
        r = client.post(
            "/score", json={"basvuru": case["basvuru"], "basvuru_tarihi": case["basvuru_tarihi"]}
        )
        assert r.json()["karar"]["skor"]["p_point"] == pytest.approx(
            g["girdi"]["p_point"], abs=1e-9
        )
    else:  # a variant differs from its source record in exactly one field
        diff = {k for k in case["basvuru"] if case["basvuru"][k] != g["girdi"]["basvuru"][k]}
        assert diff == {"application_type"}


def test_sample_csv_has_ten_rows_and_runs_through_batch(client):
    text = CSV_OUT.read_text()
    assert len(text.strip().splitlines()) == 11  # header + 10
    r = client.post("/batch", content=text.encode(), headers={"content-type": "text/csv"})
    assert r.status_code == 200 and r.json()["ozet"]["n"] == 10


def test_repo_root_is_consistent():
    assert (ROOT / "frontend" / "src" / "ornekler.json").exists()
