"""The UI example cases are frozen real calibration records (tests/golden); the API itself must
still put each one into its category."""

import json

import pytest
from fastapi.testclient import TestClient

from credit_coach.app import app
from credit_coach.bundle import ROOT
from credit_coach.ui_cases import (
    CASES,
    CSV_OUT,
    EK_ORDER,
    GOLDEN,
    ORDER,
    category,
    category_ek,
)

CASES_DATA = json.loads(CASES.read_text())
GOLDEN_BY_ID = {
    json.loads(line)["id"]: json.loads(line) for line in GOLDEN.read_text().splitlines()
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_first_five_cases_are_unchanged_and_in_the_agreed_order():
    assert [c["anahtar"] for c in CASES_DATA[:5]] == list(ORDER)
    # the extras follow, only from the written rule's categories, in the rule's order
    extra = [c["anahtar"] for c in CASES_DATA[5:]]
    assert extra == [c for c in EK_ORDER if c in extra]


@pytest.mark.parametrize("case", CASES_DATA, ids=[c["anahtar"] for c in CASES_DATA])
def test_case_falls_into_its_category_through_the_api(client, case):
    r = client.post(
        "/score", json={"basvuru": case["basvuru"], "basvuru_tarihi": case["basvuru_tarihi"]}
    )
    karar = r.json()["karar"]
    if case["anahtar"] in EK_ORDER:  # rule: docs/demo_example_cases.md
        assert category_ek(karar) == case["anahtar"]
        assert not case["varyant"] and karar["dis_durum"] == "REJECTED"
    else:
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


def test_example_case_rule_facts_at_the_current_default_delta_are_documented():
    """Local-only: re-applies the written rule at the CURRENT default delta and checks that
    docs/demo_example_cases.md states the result (the cases were chosen at delta 0.02)."""
    from credit_coach.baseline import CSV

    if not CSV.exists():
        pytest.skip("raw data not available locally (issue months of the earlier records)")
    from credit_coach.recourse import load_demo_catalog
    from credit_coach.ui_cases import build_ek

    found, missing = build_ek()
    doc = (ROOT / "docs" / "demo_example_cases.md").read_text()
    delta = load_demo_catalog().delta
    assert delta == 0.012  # the documented addendum is about this default
    by = {c["anahtar"]: c["kaynak_id"] for c in found}
    assert by.get("ret_guclu") == "cal-261695" and "cal-261695" in doc
    assert by.get("ret_kosullu") == "cal-219812" and "cal-219812" in doc
    assert missing == []
    # the frozen extra case is still KOSULLU at the current default (category test above)
    assert any(c["kaynak_id"] == "cal-257109" for c in CASES_DATA)


def test_ret_kosullu_case_at_the_default_delta_label_and_min_phi(client):
    """Documented in docs/demo_example_cases.md: KOSULLU, min_phi 0.510 (0.718 at delta 0.02)."""
    case = next(c for c in CASES_DATA if c["anahtar"] == "ret_kosullu")
    karar = client.post(
        "/score", json={"basvuru": case["basvuru"], "basvuru_tarihi": case["basvuru_tarihi"]}
    ).json()["karar"]
    (yol,) = karar["plan"]["yollar"]
    assert case["kaynak_id"] == "cal-257109"
    assert yol["dayaniklilik"] == "KOSULLU"
    assert yol["min_phi"] == pytest.approx(0.5104, abs=5e-4)
