"""UI example cases, taken from the frozen real calibration records in tests/golden (no new
selection rule): for each category the FIRST record in file order whose /score result falls into
it. Categories are verified through the API itself. Needs the raw CSV (issue month lookup), so it
runs locally; CI re-verifies the committed cases (tests/test_ui_cases.py).

Out-of-support: if no real golden record is outside the training support, the first real record
is used with ONE field changed (application_type = "Joint App"), labelled as a variant.

Usage: python -m credit_coach.ui_cases   (writes frontend/src/ornekler.json and
frontend/public/ornek_toplu.csv)
"""

from __future__ import annotations

import json
import sys

import pandas as pd
from fastapi.testclient import TestClient

from credit_coach.app import app
from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT

GOLDEN = ROOT / "tests" / "golden" / "inputs_v1.jsonl"
CASES = ROOT / "frontend" / "src" / "ornekler.json"
CSV_OUT = ROOT / "frontend" / "public" / "ornek_toplu.csv"
ORDER = ("onay", "kosullu", "ret_plan", "ret_plan_yok", "destek_disi")
# Added later (rule: docs/demo_example_cases.md, written before the search):
# the first real record in file order that is REJECTED with a plan whose strongest path label is
# GUCLU / KOSULLU, at the API's default delta. Never relaxed: a missing record is reported.
EK_ORDER = ("ret_guclu", "ret_kosullu")
_LABEL_TO_EK = {"GUCLU": "ret_guclu", "KOSULLU": "ret_kosullu"}
_STRENGTH = {"GUCLU": 0, "KOSULLU": 1, "ZAYIF": 2}


def category(karar: dict) -> str | None:
    if karar["destek_ihlalleri"]:
        return "destek_disi"
    if karar["dis_durum"] == "APPROVED":
        return "onay"
    if karar["dis_durum"] == "CONDITIONAL":
        return "kosullu"
    if karar["dis_durum"] == "REJECTED":
        return "ret_plan" if karar["plan"]["durum"] == "PLAN" else "ret_plan_yok"
    return None


def category_ek(karar: dict) -> str | None:
    """ret_guclu / ret_kosullu: REJECTED, in support, with a plan whose strongest path label is
    GUCLU / KOSULLU (None otherwise)."""
    if karar["destek_ihlalleri"] or karar["dis_durum"] != "REJECTED":
        return None
    if karar["plan"]["durum"] != "PLAN":
        return None
    strongest = min((y["dayaniklilik"] for y in karar["plan"]["yollar"]), key=_STRENGTH.__getitem__)
    return _LABEL_TO_EK.get(strongest)


def real_records() -> list[dict]:
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines()]
    return [r for r in rows if r["id"].startswith("cal-")]


def issue_months(ids: list[str]) -> dict[str, str]:
    raw = pd.read_csv(CSV, usecols=["issue_d"])
    out = {}
    for i in ids:
        d = pd.to_datetime(raw.loc[int(i.removeprefix("cal-")), "issue_d"], format="%b-%Y")
        out[i] = d.strftime("%Y-%m-01")
    return out


def build() -> tuple[list[dict], list[dict]]:
    recs = real_records()
    dates = issue_months([r["id"] for r in recs])
    found: dict[str, dict] = {}
    others: list[dict] = []
    with TestClient(app) as client:
        for r in recs:
            b, d = r["girdi"]["basvuru"], dates[r["id"]]
            body = client.post("/score", json={"basvuru": b, "basvuru_tarihi": d}).json()["karar"]
            assert abs(body["skor"]["p_point"] - r["girdi"]["p_point"]) < 1e-9, r["id"]
            cat = category(body)
            item = {"kaynak_id": r["id"], "varyant": False, "basvuru": b, "basvuru_tarihi": d}
            if cat in ORDER and cat not in found:
                found[cat] = {**item, "anahtar": cat, "beklenen": expected(body)}
            else:
                others.append(item)
        if "destek_disi" not in found:
            src = found["ret_plan_yok"] if "ret_plan_yok" in found else next(iter(found.values()))
            b = {**src["basvuru"], "application_type": "Joint App"}
            body = client.post(
                "/score", json={"basvuru": b, "basvuru_tarihi": src["basvuru_tarihi"]}
            ).json()["karar"]
            assert category(body) == "destek_disi"
            found["destek_disi"] = {
                "anahtar": "destek_disi",
                "kaynak_id": src["kaynak_id"],
                "varyant": True,
                "basvuru": b,
                "basvuru_tarihi": src["basvuru_tarihi"],
                "beklenen": expected(body),
            }
    missing = [c for c in ORDER if c not in found]
    assert not missing, f"no golden record for {missing}"
    return [found[c] for c in ORDER], others


def build_ek() -> tuple[list[dict], list[str]]:
    """Apply the written rule: first matching real record per extra category, in file order.
    Returns (cases found, categories not found)."""
    recs = real_records()
    dates = issue_months([r["id"] for r in recs])
    found: dict[str, dict] = {}
    with TestClient(app) as client:
        for r in recs:
            b, d = r["girdi"]["basvuru"], dates[r["id"]]
            body = client.post("/score", json={"basvuru": b, "basvuru_tarihi": d}).json()["karar"]
            cat = category_ek(body)
            if cat and cat not in found:
                assert abs(body["skor"]["p_point"] - r["girdi"]["p_point"]) < 1e-9, r["id"]
                found[cat] = {
                    "anahtar": cat,
                    "kaynak_id": r["id"],
                    "varyant": False,
                    "basvuru": b,
                    "basvuru_tarihi": d,
                    "beklenen": expected(body),
                }
    return [found[c] for c in EK_ORDER if c in found], [c for c in EK_ORDER if c not in found]


def expected(karar: dict) -> dict:
    return {
        "dis_durum": karar["dis_durum"],
        "plan_durumu": karar["plan"]["durum"],
        "destek_ihlalleri": karar["destek_ihlalleri"],
    }


def main() -> int:
    cases, others = build()
    ek, missing = build_ek()
    # An extra case already frozen in ornekler.json keeps its record (chosen when it was added);
    # only categories not frozen yet are taken from the rule's current result.
    frozen = {c["anahtar"]: c for c in json.loads(CASES.read_text())} if CASES.exists() else {}
    by = {c["anahtar"]: c for c in ek}
    ek = [frozen.get(k) or by[k] for k in EK_ORDER if k in frozen or k in by]
    missing = [k for k in EK_ORDER if k not in frozen and k not in by]
    CASES.write_text(json.dumps([*cases, *ek], indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    for c in missing:
        print(f"NOT FOUND by the written rule: {c}")
    rows = [
        {**c["basvuru"], "basvuru_tarihi": c["basvuru_tarihi"], "kayit_id": c["kaynak_id"]}
        for c in (cases + others)[:10]
    ]
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(CSV_OUT, index=False)
    for c in cases:
        print(c["anahtar"], c["kaynak_id"], "VARIANT" if c["varyant"] else "real", c["beklenen"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
