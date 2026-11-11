"""Demo v0 recourse report on the CALIBRATION split (ADR-006, step 3). The test split is never
loaded: `dev_frame` excludes it by construction.

For every rejected calibration record (v1 decision REJECTED, inside the training support) the
full scan runs for delta in {0, 0.01, 0.02, 0.03} x dti update {off, on}. Scores do not depend on
delta, so candidates are scored once per dti setting.

Usage: python -m credit_coach.recourse_report   (writes docs/demo_recourse_calibration.md)
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

import pandas as pd

from credit_coach.baseline import CSV
from credit_coach.bundle import LOCK_PATH, ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.features import allowed_features, load_manifest
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import (
    PATH_ORDER,
    LevelStatus,
    PlanVar,
    hazirla,
    load_demo_catalog,
    sec_from_scores,
)
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

DELTAS = (0.0, 0.01, 0.02, 0.03)
REPORT = ROOT / "docs" / "demo_recourse_calibration.md"


def _vektor(row, kinds: dict[str, str], names: list[str]) -> dict:
    """Same cleaning as golden._basvuru, without re-reading the manifest for every row."""
    out = {}
    for name in names:
        v = row[name]
        if v is None or (isinstance(v, float) and v != v):
            v = None
        elif hasattr(v, "item"):
            v = v.item()
        if v is not None and kinds[name] == "int":
            v = int(v)
        elif v is not None and kinds[name] == "float":
            v = float(v)
        out[name] = v
    return out


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "-"


def run(frame: pd.DataFrame | None = None) -> dict:
    policy, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    scorer = ModelScorer()
    kinds = {c.ad: c.tip for c in load_manifest()}
    names = allowed_features()
    if frame is None:
        dev = dev_frame(pd.read_csv(CSV))
        ca = dev[dev["split"] == "calibration"]
        assert set(ca["split"]) == {"calibration"}
    else:
        ca = frame
        assert "test" not in set(ca["split"]), "test split must never be loaded"

    counts: Counter = Counter(n_calibration=len(ca))
    # key (delta, dti) -> accumulators
    plan_n: dict = defaultdict(Counter)  # records with >=1 path / per-path availability / path sets
    costs: dict = defaultdict(list)
    levels: dict = defaultdict(Counter)

    for _month, grp in ca.groupby(ca["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        t0 = time.time()
        recs = [_vektor(r, kinds, names) for r in grp[names].to_dict("records")]
        base_scores = scorer.skorla_toplu(recs, tarih)
        rejected = []
        for b, s in zip(recs, base_scores, strict=True):
            if violations(b, support):
                counts["out_of_support"] += 1
                continue
            g = parse_input(
                {
                    "basvuru": b,
                    "p_low": s.p_low,
                    "p_point": s.p_point,
                    "p_high": s.p_high,
                    "ham_skor": s.ham_skor,
                    "politika_surumu": "v1",
                    "plan_available": None,
                }
            )
            d = decide_with_support(g, policy, support).dis_durum
            counts[f"base_{d.value}"] += 1
            if d is OuterStatus.REJECTED:
                rejected.append((b, s))
        counts["rejected"] += len(rejected)
        print(f"{_month}: {len(rejected)} rejected", file=sys.stderr, flush=True)

        for dti_on in (False, True):
            k = dataclasses.replace(kat, dti_guncelle=dti_on)
            hazir = [hazirla(b, k) for b, _ in rejected]
            flat = [a.vektor for _t, tum in hazir for a in tum]
            sk = scorer.skorla_toplu(flat, tarih) if flat else []
            pos = 0
            per_record = []
            for (b, bs), hz in zip(rejected, hazir, strict=True):
                n = len(hz[1])
                per_record.append((b, bs, hz, sk[pos : pos + n]))
                pos += n
            for d in DELTAS:
                key = (d, dti_on)
                for b, bs, hz, cs in per_record:
                    res = sec_from_scores(b, hz, bs, cs, policy, support, k, d)
                    plan_n[key]["n"] += 1
                    for (eid, sid), st in res.teshis.items():
                        levels[key][(eid, sid, st.value)] += 1
                    if isinstance(res.sonuc, PlanVar):
                        paths = tuple(y.yol_tipi for y in res.sonuc.yollar)
                        plan_n[key]["any"] += 1
                        plan_n[key][("set", paths)] += 1
                        for y in res.sonuc.yollar:
                            plan_n[key][("path", y.yol_tipi)] += 1
                            costs[(key, y.yol_tipi)].append(y.maliyet_usd)
                            for e, _s in y.eylemler:
                                plan_n[key][("action_in_cheapest", y.yol_tipi, e)] += 1
        print(f"  month done in {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
        counts["months"] += 1
        if os.environ.get("RECOURSE_REPORT_MONTHS") and counts["months"] >= int(
            os.environ["RECOURSE_REPORT_MONTHS"]
        ):
            break
    return {"counts": counts, "plan_n": plan_n, "costs": costs, "levels": levels, "kat": kat}


def render(r: dict) -> str:
    c, plan_n, costs, levels, kat = r["counts"], r["plan_n"], r["costs"], r["levels"], r["kat"]
    n_rej = c["rejected"]
    lock_sha = hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest()
    L = [
        "# Demo v0: recourse, kalibrasyon dilimi sayıları (ADR-006 adım 3)",
        "",
        KURGUSAL_VEREN,
        "",
        "Yalnızca kalibrasyon dilimi; test dilimi yüklenmedi. Maliyet ve süre varsayımdır.",
        f"bundle.lock.json sha256: `{lock_sha}`",
        "",
        "## Küme",
        "",
        "| Büyüklük | Sayı |",
        "|---|---|",
        f"| Kalibrasyon kaydı | {c['n_calibration']} |",
        f"| Destek dışı (dışarıda bırakıldı) | {c['out_of_support']} |",
    ]
    for d in ("APPROVED", "CONDITIONAL", "REJECTED"):
        L.append(f"| v1 temel karar {d} | {c[f'base_{d}']} |")
    L += ["", f"Reddedilen (v1 REJECTED, destek içi): **{n_rej}**", ""]

    L += [
        "## Geçerli planı olan reddedilen oranı ve yol dağılımı",
        "",
        "| δ | dti güncelleme | en az bir yolda plan | customer | hybrid | institution |",
        "|---|---|---|---|---|---|",
    ]
    for d in (0.0, 0.01, 0.02, 0.03):
        for dti in (False, True):
            p = plan_n[(d, dti)]
            L.append(
                f"| {d:g} | {'açık' if dti else 'kapalı'} | {_pct(p['any'], n_rej)} "
                + " ".join(f"| {_pct(p[('path', t)], n_rej)}" for t in PATH_ORDER)
                + " |"
            )

    L += ["", "## Yol kümesi dağılımı (kayıt başına hangi yollarda plan var)", ""]
    sets = sorted(
        {s[1] for p in plan_n.values() for s in p if isinstance(s, tuple) and s[0] == "set"}
    )
    L += ["| δ | dti | PLAN_YOK | " + " | ".join("+".join(s) for s in sets) + " |"]
    L += ["|---|---|---|" + "---|" * len(sets)]
    for d in DELTAS:
        for dti in (False, True):
            p = plan_n[(d, dti)]
            L.append(
                f"| {d:g} | {'açık' if dti else 'kapalı'} | {_pct(p['n'] - p['any'], n_rej)} "
                + " ".join(f"| {_pct(p[('set', s)], n_rej)}" for s in sets)
                + " |"
            )

    L += [
        "",
        "## Eylem seviyesi başına durum (tek seviye, reddedilenler içinde, kayıt payı)",
        "",
        "| δ | dti | eylem | seviye | " + " | ".join(s.value for s in LevelStatus) + " |",
        "|---|---|---|---|" + "---|" * len(LevelStatus),
    ]
    for d in DELTAS:
        for dti in (False, True):
            lv = levels[(d, dti)]
            for e in kat.eylemler:
                for s in e.seviyeler:
                    L.append(
                        f"| {d:g} | {'açık' if dti else 'kapalı'} | {e.id} | {s.id} "
                        + " ".join(
                            f"| {_pct(lv[(e.id, s.id, st.value)], n_rej)}" for st in LevelStatus
                        )
                        + " |"
                    )

    L += [
        "",
        "## Yol başına medyan USD maliyeti (plan olan kayıtlar, yolun en ucuz planı)",
        "",
        "| δ | dti | customer | hybrid | institution |",
        "|---|---|---|---|---|",
    ]
    for d in DELTAS:
        for dti in (False, True):
            cells = []
            for t in PATH_ORDER:
                v = costs.get(((d, dti), t), [])
                cells.append(f"{statistics.median(v):,.0f} (n={len(v)})" if v else "-")
            L.append(f"| {d:g} | {'açık' if dti else 'kapalı'} | " + " | ".join(cells) + " |")
    return "\n".join(L) + "\n"


def main() -> int:
    text = render(run())
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
