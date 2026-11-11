import copy
import json
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from credit_coach import scoring_service
from credit_coach.app import app, get_servis
from credit_coach.ayarlar import DECISION_LOG_ENV, DecisionLogNotAvailable
from credit_coach.decision_scenarios import in_support_basvuru
from credit_coach.features import allowed_features
from credit_coach.support import load_support
from tests.test_forbidden_phrases import FORBIDDEN

SUPPORT = load_support()


@pytest.fixture(scope="module")
def client():
    get_servis.cache_clear()
    with TestClient(app) as c:
        yield c


def good(**changes):
    b = in_support_basvuru(SUPPORT)
    b.update(
        revol_util=95.0,
        revol_bal=20000.0,
        loan_amnt=15000.0,
        annual_inc=60000.0,
        fico_range_low=680.0,
        fico_range_high=684.0,
        total_bal_ex_mort=40000.0,
        tot_cur_bal=90000.0,
    )
    b.update(changes)
    return b


def records(n: int, seed: int = 7) -> list[dict]:
    """Deterministic synthetic test records (fixed seed; test data only)."""
    rng = np.random.RandomState(seed)
    out = []
    for i in range(n):
        fico = float(rng.randint(660, 800))
        out.append(
            {
                "basvuru": good(
                    revol_util=float(rng.uniform(0, 130)),
                    revol_bal=float(rng.uniform(0, 60000)),
                    loan_amnt=float(round(rng.uniform(1000, 35000), -2)),
                    annual_inc=float(rng.uniform(20000, 200000)),
                    dti=float(rng.uniform(0, 39)),
                    fico_range_low=fico,
                    fico_range_high=fico + 4,
                    total_bal_ex_mort=float(rng.uniform(0, 100000)),
                    tot_cur_bal=float(rng.uniform(0, 300000)),
                ),
                "basvuru_tarihi": ["2015-03-10", "2015-04-02", "2015-06-20", "2014-12-30"][i % 4],
                "kayit_id": f"r{i}",
            }
        )
    return out


def to_csv(recs: list[dict], drop: tuple[str, ...] = ()) -> str:
    rows = [
        {**r["basvuru"], "basvuru_tarihi": r["basvuru_tarihi"], "kayit_id": r["kayit_id"]}
        for r in recs
    ]
    df = pd.DataFrame(rows).drop(columns=list(drop))
    return df.to_csv(index=False)


def post_csv(client, text: str, ctype="text/csv"):
    return client.post("/batch", content=text.encode(), headers={"content-type": ctype})


# ---- /score ------------------------------------------------------------------------------


def test_score_returns_decision_plan_and_versions(client):
    r = client.post("/score", json={"basvuru": good(), "basvuru_tarihi": "2015-04-10"})
    assert r.status_code == 200
    body = r.json()
    assert body["karar"]["dis_durum"] in {"APPROVED", "CONDITIONAL", "REJECTED"}
    assert body["karar"]["plan"]["durum"] in {"PLAN", "PLAN_YOK", "PLAN_GEREKSIZ"}
    assert set(body["surumler"]) == {
        "politika_surumu",
        "politika_sha256",
        "katalog_surumu",
        "katalog_sha256",
        "bundle_sha256",
        "support_sha256",
    }
    assert body["notlar"]["etiket"] == "tek fiyatlı kurgusal kredi veren"


def test_score_plan_has_assumption_labels(client):
    plans = [
        client.post(
            "/score",
            json={**r, "kayit_id": None}
            if False
            else {"basvuru": r["basvuru"], "basvuru_tarihi": r["basvuru_tarihi"]},
        ).json()["karar"]["plan"]
        for r in records(40)
    ]
    found = [p for p in plans if p["durum"] == "PLAN"]
    assert found, "expected at least one plan among the synthetic records"
    for p in found:
        for y in p["yollar"]:
            assert y["maliyet_etiketi"] == "varsayım" and y["sure_etiketi"] == "varsayım"
    for p in plans:
        if p["durum"] == "PLAN_YOK":
            assert set(p) == {"durum", "bagli_kisitlar", "esige_uzaklik"}


@pytest.mark.parametrize(
    ("changes", "feature"),
    [
        ({"fico_range_low": 600.0, "fico_range_high": 604.0}, "fico_range_low"),
        ({"dti": 999.0}, "dti"),
        ({"application_type": "Joint App"}, "application_type"),
    ],
)
def test_out_of_support_is_not_scored_and_has_no_plan(client, changes, feature):
    r = client.post("/score", json={"basvuru": good(**changes), "basvuru_tarihi": "2015-04-10"})
    k = r.json()["karar"]
    assert k["dis_durum"] == "CONDITIONAL" and feature in k["destek_ihlalleri"]
    assert "OUT_OF_SUPPORT" in k["gerekce_kodlari"]
    assert k["skor"] is None
    assert k["plan"]["durum"] == "PLAN_YOK" and k["plan"]["esige_uzaklik"] is None


# ---- invalid input: 422, never a silent decision -------------------------------------------


def bad_bodies():
    base = {"basvuru": good(), "basvuru_tarihi": "2015-04-10"}
    missing = copy.deepcopy(base)
    del missing["basvuru"]["dti"]
    extra = copy.deepcopy(base)
    extra["basvuru"]["int_rate"] = 12.0  # forbidden feature must not be accepted
    wrong = copy.deepcopy(base)
    wrong["basvuru"]["dti"] = "high"
    nodate = {"basvuru": good()}
    baddate = {"basvuru": good(), "basvuru_tarihi": "not-a-date"}
    toplevel_extra = {**base, "plan_available": True}
    return [missing, extra, wrong, nodate, baddate, toplevel_extra, {}, {"basvuru": None}]


@pytest.mark.parametrize("body", bad_bodies())
def test_invalid_score_input_is_422_without_a_decision(client, body):
    r = client.post("/score", json=body)
    assert r.status_code == 422
    assert "karar" not in r.json()


def test_nan_and_inf_are_rejected(client):
    for token in ("NaN", "Infinity"):
        raw = json.dumps({"basvuru": good(), "basvuru_tarihi": "2015-04-10"}).replace("95.0", token)
        r = client.post(
            "/score", content=raw.encode(), headers={"content-type": "application/json"}
        )
        assert r.status_code == 422


# ---- /score == batch ---------------------------------------------------------------------


def test_score_and_batch_give_identical_results_on_the_same_records(client):
    recs = records(48) + [
        {"basvuru": good(dti=999.0), "basvuru_tarihi": "2015-04-10", "kayit_id": "oos1"},
        {
            "basvuru": good(application_type="Joint App"),
            "basvuru_tarihi": "2015-05-10",
            "kayit_id": "oos2",
        },
    ]
    batch = client.post(
        "/batch", content=to_csv(recs).encode(), headers={"content-type": "text/csv"}
    )
    assert batch.status_code == 200, batch.text
    rows = batch.json()["satirlar"]
    assert len(rows) == len(recs)
    for rec, row in zip(recs, rows, strict=True):
        assert row["kayit_id"] == rec["kayit_id"]
        single = client.post(
            "/score", json={"basvuru": rec["basvuru"], "basvuru_tarihi": rec["basvuru_tarihi"]}
        )
        assert single.json()["karar"] == row["karar"], rec["kayit_id"]
    assert batch.json()["surumler"] == single.json()["surumler"]


def test_batch_order_does_not_change_a_records_result(client):
    recs = records(24)
    a = post_csv(client, to_csv(recs)).json()["satirlar"]
    b = post_csv(client, to_csv(list(reversed(recs)))).json()["satirlar"]
    assert [r["karar"] for r in a] == [r["karar"] for r in reversed(b)]


def test_batch_summary_adds_up(client):
    out = post_csv(client, to_csv(records(60))).json()
    o = out["ozet"]
    assert (
        o["n"]
        == 60
        == sum(o["dis_durum_dagilimi"].values())
        == sum(o["plan_durumu_dagilimi"].values())
    )
    assert sum(k["n"] for k in o["kovalar"]) == o["plan_arayan"]
    if o["plan_arayan"]:
        found = o["plan_durumu_dagilimi"].get("PLAN", 0)
        assert o["gecerli_plan_orani"] == pytest.approx(found / o["plan_arayan"])


# ---- /batch input errors -------------------------------------------------------------------


def test_batch_rejects_bad_files_with_422(client):
    recs = records(5)
    good_csv = to_csv(recs)
    assert post_csv(client, to_csv(recs, drop=("dti",))).status_code == 422  # missing column
    assert post_csv(client, good_csv.replace("r1", "r1,extra", 1)).status_code == 422  # ragged row
    assert post_csv(client, "").status_code == 422
    header_only = good_csv.splitlines()[0] + "\n"
    assert post_csv(client, header_only).status_code == 422
    bad_value = good_csv.replace(",95.0,", ",abc,", 1) if ",95.0," in good_csv else None
    if bad_value:
        assert post_csv(client, bad_value).status_code == 422
    r = post_csv(client, good_csv.replace("2015-03-10", "10/03/2015", 1))
    assert r.status_code == 422 and "satırlar" not in r.json()  # no partial result


def test_batch_rejects_more_than_10000_rows(client):
    one = to_csv(records(1)).splitlines()
    text = "\n".join([one[0]] + [one[1]] * 10_001) + "\n"
    r = post_csv(client, text)
    assert r.status_code == 422 and "10000" in r.json()["detail"][0]


def test_batch_wrong_content_type_is_415(client):
    assert post_csv(client, to_csv(records(2)), ctype="application/json").status_code == 415


# ---- performance: 10,000 rows --------------------------------------------------------------


def test_batch_10000_rows_parse_without_manifest_reads_and_run_fast(client, monkeypatch):
    import pathlib

    one = to_csv(records(40))
    lines = one.splitlines()
    text = "\n".join([lines[0]] + [lines[1 + (i % 40)] for i in range(10_000)]) + "\n"
    scoring_service.parse_csv(to_csv(records(2)))  # warm the cached manifest view
    reads = {"n": 0}
    orig = pathlib.Path.read_text

    def counting(p, *a, **k):
        reads["n"] += 1
        return orig(p, *a, **k)

    monkeypatch.setattr(pathlib.Path, "read_text", counting)
    t = time.perf_counter()
    recs = scoring_service.parse_csv(text)
    parse_s = time.perf_counter() - t
    assert len(recs) == 10_000 and reads["n"] == 0
    monkeypatch.undo()
    t = time.perf_counter()
    r = post_csv(client, text)
    total_s = time.perf_counter() - t
    assert r.status_code == 200 and r.json()["ozet"]["n"] == 10_000
    assert parse_s < 10.0 and total_s < 60.0, (parse_s, total_s)


# ---- wording and contract -----------------------------------------------------------------


def test_response_text_has_no_forbidden_phrases(client):
    out = client.post(
        "/score", json={"basvuru": good(), "basvuru_tarihi": "2015-04-10"}
    ).text.lower()
    assert not [p for p in FORBIDDEN if p in out]


def test_committed_openapi_matches_the_app():
    from pathlib import Path

    committed = (Path(__file__).resolve().parents[2] / "frontend" / "openapi.json").read_text()
    assert committed == json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def test_openapi_exposes_score_and_batch():
    paths = app.openapi()["paths"]
    assert "post" in paths["/score"] and "post" in paths["/batch"]
    assert "text/csv" in paths["/batch"]["post"]["requestBody"]["content"]


# ---- decision log is off by default and needs no database ----------------------------------


def test_decision_log_is_off_by_default_and_refused_when_enabled(monkeypatch):
    monkeypatch.delenv(DECISION_LOG_ENV, raising=False)
    monkeypatch.delenv("CREDIT_COACH_APP_DB_URL", raising=False)
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
    monkeypatch.setenv(DECISION_LOG_ENV, "1")
    with pytest.raises(DecisionLogNotAvailable), TestClient(app):
        pass


def test_all_allowed_features_are_required_in_the_csv_header():
    assert set(allowed_features()) <= set(to_csv(records(1)).splitlines()[0].split(","))


def test_padded_strings_give_the_same_decision_as_trimmed_ones(client):
    a = good(purpose="debt_consolidation", term="36 months")
    b = good(purpose=" debt_consolidation ", term=" 36 months")
    ra = client.post("/score", json={"basvuru": a, "basvuru_tarihi": "2015-04-10"}).json()
    rb = client.post("/score", json={"basvuru": b, "basvuru_tarihi": "2015-04-10"}).json()
    assert ra["karar"]["destek_ihlalleri"] == [] and ra == rb


def test_plans_expose_min_phi_label_percent_and_evidence(client):
    import math

    plans = [
        client.post(
            "/score", json={"basvuru": r["basvuru"], "basvuru_tarihi": r["basvuru_tarihi"]}
        ).json()["karar"]["plan"]
        for r in records(40)
    ]
    found = [y for p in plans if p["durum"] == "PLAN" for y in p["yollar"]]
    assert found
    for y in found:
        assert 0.0 <= y["min_phi"] <= 1.0
        assert y["gereken_etki_yuzdesi"] == math.ceil(100 * y["min_phi"])
        assert y["dayaniklilik"] in {"GUCLU", "KOSULLU", "ZAYIF"}
        assert y["dayaniklilik_etiketi"] == "varsayım"
        assert [k["eylem"] for k in y["eylem_kanitlari"]] == [e for e, _ in y["eylemler"]]
        assert all(k["risk_etkisi"] == "M" for k in y["eylem_kanitlari"])


def test_batch_summary_has_the_label_distribution_and_it_adds_up(client):
    out = post_csv(client, to_csv(records(80))).json()
    o = out["ozet"]
    with_plan = o["plan_durumu_dagilimi"].get("PLAN", 0)
    assert sum(o["dayaniklilik_dagilimi"].values()) == with_plan
    per_row = [
        min(
            (y["dayaniklilik"] for y in r["karar"]["plan"]["yollar"]),
            key=["GUCLU", "KOSULLU", "ZAYIF"].index,
        )
        for r in out["satirlar"]
        if r["karar"]["plan"]["durum"] == "PLAN"
    ]
    for k, v in o["dayaniklilik_dagilimi"].items():
        assert per_row.count(k) == v
    for tip, dist in o["yol_dayaniklilik"].items():
        n = sum(
            1
            for r in out["satirlar"]
            if r["karar"]["plan"]["durum"] == "PLAN"
            for y in r["karar"]["plan"]["yollar"]
            if y["yol_tipi"] == tip
        )
        assert sum(dist.values()) == n
    assert "dayaniklilik_notu" in out["notlar"] and "kanit_notu" in out["notlar"]


def test_responses_carry_the_safety_margin_with_label_and_source(client):
    from credit_coach.recourse import load_demo_catalog

    delta = load_demo_catalog().delta
    one = client.post("/score", json={"basvuru": good(), "basvuru_tarihi": "2015-04-10"}).json()
    many = post_csv(client, to_csv(records(6))).json()
    for body in (one, many):
        assert body["guvenlik_payi"] == {"deger": delta, "etiket": "varsayım", "kaynak": "ADR-007"}
    # the response value is the one the engine used (catalog), not a separate number
    from credit_coach.app import get_servis

    assert get_servis().katalog.delta == delta


def test_safety_margin_is_in_the_openapi_contract():
    from credit_coach.app import app

    schemas = app.openapi()["components"]["schemas"]
    gp = schemas["GuvenlikPayi"]["properties"]
    assert set(gp) == {"deger", "etiket", "kaynak"}
    assert gp["etiket"]["const"] == "varsayım" and gp["kaynak"]["const"] == "ADR-007"
    assert "guvenlik_payi" in schemas["ScoreResponse"]["properties"]
    assert "guvenlik_payi" in schemas["BatchResponse"]["properties"]
