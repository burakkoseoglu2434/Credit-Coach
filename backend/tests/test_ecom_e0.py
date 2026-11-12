"""E-ticaret ecom alt paketi: kredi modüllerinden yalıtım (Karar Q7) ve E0 yardımcıları."""

import ast
import math
from pathlib import Path

import duckdb
import pandas as pd

from credit_coach.ecom import e0_data_check as e0

ECOM_DIR = Path(e0.__file__).parent


def test_ecom_does_not_import_credit_modules():
    bad = []
    for f in sorted(ECOM_DIR.rglob("*.py")):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.ImportFrom):
                if node.level > 1 or (
                    node.level == 0
                    and (node.module or "").startswith("credit_coach")
                    and not (node.module or "").startswith("credit_coach.ecom")
                ):
                    bad.append(f"{f.name}: from {'.' * node.level}{node.module}")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("credit_coach") and not a.name.startswith(
                        "credit_coach.ecom"
                    ):
                        bad.append(f"{f.name}: import {a.name}")
    assert bad == []


def test_smd_formula():
    assert e0.smd(1.0, 1.0, 0.0, 1.0) == 1.0
    assert e0.smd(0.5, 0.0, 0.5, 0.0) == 0.0
    assert math.isinf(e0.smd(1.0, 0.0, 0.0, 0.0))


def test_smd_rows_matches_pandas():
    df = pd.DataFrame(
        {
            "t": [1, 1, 1, 0, 0, 0, 0],
            "x": [1.0, 2.0, 4.0, 0.0, 1.0, 1.0, 3.0],
            "c": ["a", "b", "a", "b", "b", "a", "b"],
        }
    )
    con = duckdb.connect()
    con.register("d", df)
    rows = e0.smd_rows(con, "d", "t = 1", [("x", "x"), ("c=a", "CAST(c = 'a' AS DOUBLE)")])
    for r, col in zip(rows, [df["x"], (df["c"] == "a").astype(float)], strict=True):
        a, b = col[df.t == 1], col[df.t == 0]
        want = (a.mean() - b.mean()) / math.sqrt((a.var() + b.var()) / 2)
        assert math.isclose(r["smd"], want, rel_tol=1e-9)


def test_hillstrom_schema_rejects_bad_rows():
    good = {
        "recency": 1,
        "history_segment": e0.HISTORY_SEGMENTS[0],
        "history": 10.0,
        "mens": 1,
        "womens": 0,
        "zip_code": "Urban",
        "newbie": 0,
        "channel": "Web",
        "segment": "No E-Mail",
        "visit": 0,
        "conversion": 0,
        "spend": 0.0,
    }
    df = pd.DataFrame([good, good | {"visit": 2}, good | {"segment": "SMS"}])
    assert e0.failing_rows(e0.hillstrom_schema(), df) == 2
    assert e0.failing_rows(e0.hillstrom_schema(), df.iloc[:1]) == 0


def _h(smd_birlesik=0.01):
    rows = [{"ozellik": "x", "ort_T": 0, "ort_C": 0, "smd": smd_birlesik}]
    return {
        "satir": 64_000,
        "segment_pay": dict.fromkeys(e0.SEGMENTS, 1 / 3),
        "pandera_kalan": 0,
        "smd": {"birlesik_vs_yok": rows},
    }


def _c(smd=0.01, p=0.846):
    return {
        "satir": 13_979_592,
        "p_tedavi": p,
        "pandera_kalan": 0,
        "smd": [{"ozellik": "f0", "ort_T": 0, "ort_C": 0, "smd": smd}],
    }


def test_decision_follows_stop_rule():
    ok = e0.evaluate(_h(), _c())
    assert {o.kod: o.gecti for o in ok}["5"] is None
    assert "onayı bekliyor" in e0.decision(ok)
    assert "Criteo çıkarılır" in e0.decision(e0.evaluate(_h(), _c(smd=-0.2)))
    assert "modelleme yapılmaz" in e0.decision(e0.evaluate(_h(smd_birlesik=0.06), _c()))
    assert "modelleme yapılmaz" in e0.decision(e0.evaluate(_h(), _c(p=0.80)))
