"""E1 — Hillstrom (docs/ecom/PLAN.md bölüm 6, E1). Üç ayrı komut, bu sırayla:

  python -m credit_coach.ecom.e1_hillstrom split    # bölme; karma ve eğitim p'si yaml'a
  python -m credit_coach.ecom.e1_hillstrom select   # yalnızca doğrulama; E1_selection.md
  python -m credit_coach.ecom.e1_hillstrom test     # test kümesi TEK sefer; kilit + rapor

Tedavi = iki e-posta kolu birleşik (Karar Q2); birincil sonuç visit (Q3).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import yaml

from credit_coach.ecom import uplift as U
from credit_coach.ecom.e0_data_check import (
    CHANNELS,
    HILL_TYPES,
    HISTORY_SEGMENTS,
    NO_EMAIL,
    ROOT,
    SOURCE_PATH,
    ZIP_CODES,
    read_csv_sql,
)

SELECTION_PATH = ROOT / "docs" / "ecom" / "E1_selection.md"
REPORT_PATH = ROOT / "docs" / "ecom" / "E1_hillstrom.md"
LOCK_PATH = ROOT / "docs" / "ecom" / "test_run_hillstrom.lock"
B = 1000
G_GRID = (0.20, 0.30, 0.40)
C_GRID = (0.01, 0.10, 0.50)
PRIMARY_CELL = (0.30, 0.10)
SUPPORT_Q = (0.005, 0.995)
# Kapı eşikleri: PLAN bölüm 6, E1 (DONDURULDU).
SLOPE_RANGE = (0.5, 1.5)


# --- veri --------------------------------------------------------------------------------------


def load_sources() -> dict:
    return yaml.safe_load(SOURCE_PATH.read_text())


def load_hillstrom(path: Path) -> pd.DataFrame:
    """Satır kimliği = dosya sırası (0'dan) = DataFrame indeksi."""
    df = duckdb.connect().execute(f"SELECT * FROM {read_csv_sql(path, HILL_TYPES)}").df()
    df.index.name = "row_id"
    return df


def encode(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cols = {c: df[c].astype(float) for c in ("recency", "history", "mens", "womens", "newbie")}
    for col, levels in (
        ("zip_code", ZIP_CODES),
        ("channel", CHANNELS),
        ("history_segment", HISTORY_SEGMENTS),
    ):
        for lv in levels:
            cols[f"{col}={lv}"] = (df[col] == lv).astype(float)
    x = pd.DataFrame(cols)
    return x.to_numpy(), list(x.columns)


def arrays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    x, names = encode(df)
    return {
        "x": x,
        "names": names,
        "t": (df["segment"] != NO_EMAIL).to_numpy().astype(np.int64),
        "visit": df["visit"].to_numpy().astype(float),
        "spend": df["spend"].to_numpy().astype(float),
        "row_id": df.index.to_numpy(),
    }


def make_split(a: dict) -> np.ndarray:
    return U.stratified_split(a["t"] * 2 + a["visit"].astype(np.int64))


def check_split(a: dict, sources: dict) -> np.ndarray:
    labels = make_split(a)
    want = (sources.get("bolme_hillstrom") or {}).get("karma")
    if want != U.split_hash(labels):
        raise SystemExit("bölme karması yaml ile uyuşmuyor ya da yok; önce `split`")
    return labels


# --- split -------------------------------------------------------------------------------------


def cmd_split() -> int:
    sources = load_sources()
    if "bolme_hillstrom" in sources:
        print("bolme_hillstrom zaten yaml'da; değiştirilmez")
        return 1
    a = arrays(load_hillstrom(Path(sources["hillstrom"]["yol"])))
    labels = make_split(a)
    tr = labels == U.TRAIN
    p = float(a["t"][tr].mean())
    block = {
        "bolme_hillstrom": {
            "karma": U.split_hash(labels),
            "yontem": "tabaka (tedavi x visit) içinde seed'li permütasyon; satır kimliği = dosya sırası",  # noqa: E501
            "seed": U.SEED,
            "satir": {
                "egitim": int(tr.sum()),
                "dogrulama": int((labels == U.VALID).sum()),
                "test": int((labels == U.TEST).sum()),
            },
            "p_egitim": round(p, 6),
            "tedavi": "iki e-posta kolu birleşik vs No E-Mail (Karar Q2)",
        }
    }
    with SOURCE_PATH.open("a", encoding="utf-8") as f:
        f.write("# E1 bölmesi (python -m credit_coach.ecom.e1_hillstrom split)\n")
        f.write(yaml.safe_dump(block, allow_unicode=True, sort_keys=False))
    print(json.dumps(block, ensure_ascii=False, indent=1))
    return 0


# --- select ------------------------------------------------------------------------------------

SEL_BEGIN, SEL_END = "<!-- SECIM-JSON-BASLANGIC -->", "<!-- SECIM-JSON-BITIS -->"


def _fit_tau(cfg, a, tr, ev, p, outcome="visit"):
    return U.fit_predict_tau(
        cfg, a["x"][tr], a[outcome][tr], a["t"][tr], p, a["x"][ev], binary=outcome == "visit"
    )


def cmd_select() -> int:
    t0 = time.perf_counter()
    sources = load_sources()
    if SELECTION_PATH.exists():
        print("E1_selection.md zaten var; seçim değiştirilmez")
        return 1
    a = arrays(load_hillstrom(Path(sources["hillstrom"]["yol"])))
    labels = check_split(a, sources)
    p = sources["bolme_hillstrom"]["p_egitim"]
    tr, va = labels == U.TRAIN, labels == U.VALID
    order_rows = a["row_id"][va]
    w = np.ones(int(va.sum()))
    rows = []
    for cfg in U.grid():
        tau = _fit_tau(cfg, a, tr, va, p)
        area, _ = U.qini(U.rank_order(tau, order_rows), a["visit"][va], a["t"][va], w)
        rows.append((cfg, area))
    best = {f: max((r for r in rows if r[0].aile == f), key=lambda r: r[1]) for f in ("T", "TO")}
    chosen = max(best.values(), key=lambda r: r[1])[0]  # eşitlikte ızgara sırası (T önce)
    # Belirlenimcilik: seçilen ayar iki kez, bit düzeyinde karşılaştırma (doğrulama kümesi).
    t1, t2 = _fit_tau(chosen, a, tr, va, p), _fit_tau(chosen, a, tr, va, p)
    same = bool(np.array_equal(t1.view(np.uint64), t2.view(np.uint64)))
    if not same:
        print("belirlenimcilik başarısız: tau iki çalıştırmada farklı")
        return 1
    sel = {
        "secilen": chosen.ad,
        "secilen_aile": chosen.aile,
        "aile_en_iyi": {f: best[f][0].ad for f in best},
        "ayarlar": {
            r[0].ad: {
                "aile": r[0].aile,
                "learning_rate": r[0].learning_rate,
                "max_leaf_nodes": r[0].max_leaf_nodes,
                "max_iter": r[0].max_iter,
            }
            for r in rows
        },
        "belirlenimcilik_bit_esit": same,
        "bolme_karmasi": sources["bolme_hillstrom"]["karma"],
        "p_egitim": p,
    }
    SELECTION_PATH.write_text(render_selection(rows, best, chosen, sel, time.perf_counter() - t0))
    print(json.dumps({k: sel[k] for k in ("secilen", "aile_en_iyi")}, ensure_ascii=False))
    return 0


def _f(x: float, nd: int = 4) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _note(means: str, not_means: str) -> str:
    return f"\n> **Bu tablo ne demek:** {means}\n>\n> **Ne DEMEK DEĞİL:** {not_means}\n"


def render_selection(rows, best, chosen, sel, runtime) -> str:
    L = [
        "# E1 — Model ve ayar seçimi (yalnızca doğrulama kümesi)\n",
        "Üretildi: `python -m credit_coach.ecom.e1_hillstrom select`. Bu belge test kümesi "
        "çalışmadan ÖNCE commit'lenir; commit sırası seçimin test sonucundan önce yapıldığının "
        "kanıtıdır. Test kümesi bu adımda okunmadı.\n",
        f"Bölme karması `{sel['bolme_karmasi']}`, eğitim kümesinde $p$ = {_f(sel['p_egitim'], 6)}. "
        f"Çalışma süresi {_f(runtime, 1)} s.\n",
        "## Izgara ve doğrulama Qini'si\n",
        "Toplam 12 kombinasyon: 2 aile × öğrenme hızı {0,05; 0,1} × yaprak sayısı {7; 15; 31}; "
        "`max_iter` = 200, erken durdurma kapalı, `random_state` = 20261111. Ölçüt: doğrulama "
        "kümesinde Qini alanı (PLAN 2.2, yamuk kuralı, 100 nokta, N ile bölünmüş).\n",
        "| Ayar | Aile | Öğrenme hızı | Yaprak | Doğrulama Qini |\n|---|---|---|---|---|",
    ]
    for cfg, area in rows:
        mark = " **(seçilen)**" if cfg == chosen else ""
        L.append(
            f"| `{cfg.ad}`{mark} | {cfg.aile} | {_f(cfg.learning_rate, 2)} | "
            f"{cfg.max_leaf_nodes} | {_f(area, 6)} |"
        )
    L.append(
        _note(
            "Her ayarın doğrulama kümesinde Qini alanı; en yüksek olan seçildi (eşitlikte "
            "ızgara sırası).",
            "Doğrulama Qini'si test sonucunu öngörmez; aynı küme hem ayar hem seçim için "
            "kullanıldığı için iyimser olabilir.",
        )
    )
    L += [
        "## Seçim\n",
        f"- **Kapı modeli (tek):** `{chosen.ad}`.",
        f"- Ailelerin en iyileri (testte yan yana raporlanır, kapıya yalnızca kapı modeli "
        f"girer): T = `{best['T'][0].ad}`, TO = `{best['TO'][0].ad}`.",
        f"- Belirlenimcilik: seçilen ayar aynı veri ve seed ile iki kez eğitildi; doğrulama "
        "tahminleri bit düzeyinde aynı: "
        f"**{'evet' if sel['belirlenimcilik_bit_esit'] else 'hayır'}**.",
        "",
        "## Test kümesinde yapılacaklar (önceden kayıt)\n",
        "- Modeller yalnızca eğitim kümesinde (doğrulama eklenmeden) yukarıdaki ayarlarla "
        "yeniden eğitilir; test kümesi bir kez tahmin edilir; `docs/ecom/test_run_hillstrom.lock` "
        "yazılır, kilit varsa komut reddeder.",
        "- Kapı ölçütleri PLAN bölüm 6 E1 (DONDURULDU): Qini %95 alt sınırı > 0; kalibrasyon "
        "eğimi [0,5; 1,5] ve alt sınırı > 0; genel düzey farkı aralığı 0'ı içerir.",
        "- Bootstrap B = 1000, tabakalı (tedavi ve kontrol ayrı), seed 20261111; desiller ham "
        "test kümesinde tau sırasına göre sabitlenir.",
        "- Politika değeri tablosu (kapıya GİRMEZ, PLAN 2.3 ve 4.1): değer sonucu `spend`; "
        "kapı modelinin ailesi ve ayarı `spend` sonucunda (T ailesinde regresyon) yalnızca "
        "eğitim kümesinde ayar yapılmadan eğitilir; $\\pi_{mod} = 1[g\\,\\hat\\tau_{spend} - c "
        "> 0]$; destek dışı satırlarda (eğitimdeki %0,5–%99,5 aralığı dışında bir özellik) "
        "$\\pi_{mod} = 1$; ızgara $g \\in \\{0{,}2; 0{,}3; 0{,}4\\}$, $c \\in \\{0{,}01; 0{,}10; "
        "0{,}50\\}$; birincil hücre $g = 0{,}30$, $c = 0{,}10$.",
        "",
        SEL_BEGIN,
        "```json",
        json.dumps(sel, ensure_ascii=False, indent=1),
        "```",
        SEL_END,
        "",
    ]
    return "\n".join(L)


def read_selection() -> dict:
    text = SELECTION_PATH.read_text()
    m = re.search(
        re.escape(SEL_BEGIN) + r"\s*```json\s*(.*?)```\s*" + re.escape(SEL_END), text, re.S
    )
    if not m:
        raise SystemExit("E1_selection.md içinde seçim bloğu yok")
    return json.loads(m.group(1))


def cfg_from(sel: dict, name: str) -> U.Config:
    d = sel["ayarlar"][name]
    return U.Config(d["aile"], d["learning_rate"], d["max_leaf_nodes"], d["max_iter"])


# --- test --------------------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def write_lock(sources: dict) -> dict:
    h = hashlib.sha256(Path(sources["hillstrom"]["yol"]).read_bytes()).hexdigest()
    if h != sources["hillstrom"]["sha256"]:
        raise SystemExit("veri SHA-256 yaml ile uyuşmuyor")
    lock = {
        "commit": _git("rev-parse", "HEAD"),
        "veri_sha256": h,
        "bolme_karmasi": sources["bolme_hillstrom"]["karma"],
        "zaman_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with LOCK_PATH.open("x", encoding="utf-8") as f:  # "x": varsa hata
        f.write(json.dumps(lock, ensure_ascii=False, indent=1) + "\n")
    return lock


def support_mask(x_tr: np.ndarray, x_ev: np.ndarray) -> np.ndarray:
    lo, hi = np.quantile(x_tr, SUPPORT_Q, axis=0)
    return np.all((x_ev >= lo) & (x_ev <= hi), axis=1)


def evaluate_model(tau, y, t, row_id):
    order = U.rank_order(tau, row_id)
    dec = U.decile_of(order)
    w1 = np.ones(len(y))
    area, curve = U.qini(order, y, t, w1)
    tab = U.decile_table(tau, y, t, w1, dec)
    return {
        "order": order,
        "dec": dec,
        "qini": area,
        "curve": curve,
        "tab": tab,
        "slope": U.calibration_slope(tab),
        "gap": U.overall_gap(tau, y, t, w1),
        "n": len(y),
    }


def cmd_test() -> int:
    t0 = time.perf_counter()
    if LOCK_PATH.exists():
        print(f"kilit var ({LOCK_PATH.name}); test kümesi ikinci kez çalıştırılmaz")
        return 1
    if _git("status", "--porcelain", "--untracked-files=no"):
        print("çalışma ağacı temiz değil; önce seçimi commit'le")
        return 1
    if _git("log", "-1", "--format=%H", "--", str(SELECTION_PATH.relative_to(ROOT))) == "":
        print("E1_selection.md commit'lenmemiş")
        return 1
    sources = load_sources()
    sel = read_selection()
    a = arrays(load_hillstrom(Path(sources["hillstrom"]["yol"])))
    labels = check_split(a, sources)
    p = sources["bolme_hillstrom"]["p_egitim"]
    tr, te = labels == U.TRAIN, labels == U.TEST
    names = {"kapi": sel["secilen"], **{f"aile_{k}": v for k, v in sel["aile_en_iyi"].items()}}
    cfgs = {k: cfg_from(sel, v) for k, v in names.items()}

    # Modeller yalnızca eğitimde; test özellikleri tahmin için.
    taus = {k: _fit_tau(c, a, tr, te, p) for k, c in cfgs.items()}
    tau_spend = _fit_tau(cfgs["kapi"], a, tr, te, p, outcome="spend")
    support = support_mask(a["x"][tr], a["x"][te])
    lock = write_lock(sources)  # test etiketleri bundan sonra okunur

    y, t, rid, spend = a["visit"][te], a["t"][te], a["row_id"][te], a["spend"][te]
    res = {k: evaluate_model(v, y, t, rid) for k, v in taus.items() if k != "kapi"}
    res["kapi"] = res[f"aile_{sel['secilen_aile']}"]
    cells = [(g, c) for g in G_GRID for c in C_GRID]
    pis = {(g, c): np.where(support, (g * tau_spend - c > 0).astype(float), 1.0) for g, c in cells}

    boot = {k: {"qini": [], "slope": [], "gap": [], "fark": []} for k in res if k != "kapi"}
    pboot = {cell: {"all": [], "mod_all": [], "mod_none": []} for cell in cells}
    for w in U.bootstrap_weights(t, B):
        for k in boot:
            r = res[k]
            boot[k]["qini"].append(U.qini(r["order"], y, t, w)[0])
            tab = U.decile_table(taus[k], y, t, w, r["dec"])
            boot[k]["slope"].append(U.calibration_slope(tab))
            boot[k]["gap"].append(U.overall_gap(taus[k], y, t, w))
            boot[k]["fark"].append(tab["fark"])
        for g, c in cells:
            v_all = U.policy_value(np.ones_like(spend), spend, t, w, p, g, c)
            v_none = U.policy_value(np.zeros_like(spend), spend, t, w, p, g, c)
            v_mod = U.policy_value(pis[(g, c)], spend, t, w, p, g, c)
            pboot[(g, c)]["all"].append(v_all)
            pboot[(g, c)]["mod_all"].append(v_mod - v_all)
            pboot[(g, c)]["mod_none"].append(v_mod - v_none)
    for k in boot:
        r = res[k]
        r["qini_ci"] = U.ci(boot[k]["qini"])
        r["slope_ci"] = U.ci(boot[k]["slope"])
        r["gap_ci"] = U.ci(boot[k]["gap"])
        f = np.array(boot[k]["fark"])
        r["fark_ci"] = np.percentile(f, [2.5, 97.5], axis=0)
    w1 = np.ones(len(y))
    policy = {}
    for g, c in cells:
        pi = pis[(g, c)]
        v = {
            "hep": U.policy_value(np.ones_like(spend), spend, t, w1, p, g, c),
            "hic": U.policy_value(np.zeros_like(spend), spend, t, w1, p, g, c),
            "mod": U.policy_value(pi, spend, t, w1, p, g, c),
            "hedef_orani": float(pi.mean()),
            "mod_hep_ci": U.ci(pboot[(g, c)]["mod_all"]),
            "mod_hic_ci": U.ci(pboot[(g, c)]["mod_none"]),
        }
        policy[(g, c)] = v
    k = res["kapi"]
    lo_s, hi_s = k["slope_ci"]
    crit = [
        (
            "1",
            "Qini alanı %95 alt sınırı > 0",
            f"alt sınır {_f(k['qini_ci'][0], 6)}",
            k["qini_ci"][0] > 0,
        ),
        (
            "2",
            "Kalibrasyon eğimi ∈ [0,5; 1,5] ve %95 alt sınırı > 0",
            f"eğim {_f(k['slope'], 3)} [{_f(lo_s, 3)}; {_f(hi_s, 3)}]",
            SLOPE_RANGE[0] <= k["slope"] <= SLOPE_RANGE[1] and lo_s > 0,
        ),
        (
            "3",
            "Genel düzey farkı %95 aralığı 0'ı içerir",
            f"fark {_f(k['gap'], 5)} [{_f(k['gap_ci'][0], 5)}; {_f(k['gap_ci'][1], 5)}]",
            k["gap_ci"][0] <= 0 <= k["gap_ci"][1],
        ),
    ]
    runtime = time.perf_counter() - t0
    REPORT_PATH.write_text(
        render_report(sel, res, policy, crit, support, lock, runtime, p, len(y)), encoding="utf-8"
    )
    summary = {
        "sure_s": round(runtime, 1),
        "secilen": sel["secilen"],
        "olcutler": {c[0]: c[3] for c in crit},
        "qini": [k["qini"], *k["qini_ci"]],
        "egim": [k["slope"], lo_s, hi_s],
        "genel_fark": [k["gap"], *k["gap_ci"]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if all(c[3] for c in crit) else 2


def decision(crit) -> str:
    if all(c[3] for c in crit):
        return "E1 ölçütlerinin üçü de geçti. E2 ayrı bir adım; kullanıcı onayıyla başlar."
    failed = ", ".join(c[0] for c in crit if not c[3])
    msg = f"Kalan ölçüt(ler): {failed}. Durdurma kuralı: test yeniden çalıştırılmaz, model "
    msg += "değiştirilmez"
    if any(c[0] == "1" and not c[3] for c in crit):
        msg += "; E2 yalnızca kullanıcı onayıyla yapılabilir"
    return msg + "."


def render_report(sel, res, policy, crit, support, lock, runtime, p, n_test) -> str:
    k = res["kapi"]
    fam = {"T": "aile_T", "TO": "aile_TO"}
    L: list[str] = []
    a = L.append
    a("# E1 — Hillstrom: tahmin edilen ve ölçülen fark\n")
    a(
        "Üretildi: `python -m credit_coach.ecom.e1_hillstrom test` (test kümesi tek sefer). "
        f"Kilit: `docs/ecom/test_run_hillstrom.lock` (commit `{lock['commit'][:7]}`, "
        f"{lock['zaman_utc']}). Seçim test öncesi `docs/ecom/E1_selection.md`'de commit'lendi.\n"
    )
    a(
        f"Tedavi = iki e-posta kolu birleşik, kontrol = No E-Mail; sonuç `visit`; test kümesi "
        f"{n_test} satır; eğitim $p$ = {_f(p, 6)}. Bootstrap B = {B}, tabakalı. Çalışma süresi "
        f"{_f(runtime, 1)} s.\n"
    )
    a("## Kapı ölçütleri (PLAN bölüm 6, E1; DONDURULDU)\n")
    a(f"Kapı modeli: `{sel['secilen']}`.\n")
    a("| Ölçüt | Tanım | Ölçülen | Sonuç |\n|---|---|---|---|")
    for c in crit:
        a(f"| {c[0]} | {c[1]} | {c[2]} | {'geçti' if c[3] else '**kaldı**'} |")
    a(f"\n**Karar (durdurma kuralı):** {decision(crit)}\n")
    a(
        _note(
            "Doğrulamada seçilen tek modelin test kümesinde, sonuç görülmeden dondurulmuş üç "
            "eşiğe göre durumu.",
            "Geçmek, e-postanın başka bir kampanyada ya da kredide benzer bir fark yaratacağını "
            "göstermez; kalmak modelin hiçbir bilgi taşımadığını kanıtlamaz (Hillstrom küçük, "
            "güç düşük).",
        )
    )

    a("## İki model ailesi yan yana\n")
    a(
        "| Model | Ayar | Qini alanı [%95] | Kalibrasyon eğimi [%95] | Genel düzey farkı [%95] |"
        "\n|---|---|---|---|---|"
    )
    for f, key in fam.items():
        r = res[key]
        tag = " (kapı)" if f == sel["secilen_aile"] else ""
        a(
            f"| {f}{tag} | `{sel['aile_en_iyi'][f]}` | {_f(r['qini'], 6)} "
            f"[{_f(r['qini_ci'][0], 6)}; {_f(r['qini_ci'][1], 6)}] | {_f(r['slope'], 3)} "
            f"[{_f(r['slope_ci'][0], 3)}; {_f(r['slope_ci'][1], 3)}] | {_f(r['gap'], 5)} "
            f"[{_f(r['gap_ci'][0], 5)}; {_f(r['gap_ci'][1], 5)}] |"
        )
    a(
        _note(
            "Her ailenin doğrulamada en iyi ayarının test kümesindeki üç ölçüsü; kapıya yalnızca "
            "kapı modeli girer.",
            "Ailelerden birinin daha iyi olduğu sonucunu desteklemez; aralıklar örtüşebilir ve "
            "seçim tek bir doğrulama kümesine dayanır.",
        )
    )

    a("## Qini eğrisi\n")
    a(
        "$Q(\\phi)/N$ değerleri; rastgele sıralama doğrusu $\\phi\\,Q(1)/N$. Eğri 100 noktada "
        "hesaplandı, burada 10'da biri gösteriliyor.\n"
    )
    a("| $\\phi$ | T: $Q/N$ | TO: $Q/N$ | Rastgele: $\\phi Q(1)/N$ (T) |\n|---|---|---|---|")
    ct, cto = res["aile_T"]["curve"], res["aile_TO"]["curve"]
    for i in range(9, 100, 10):
        phi = (i + 1) / 100
        a(
            f"| {_f(phi, 1)} | {_f(ct[i] / n_test, 5)} | {_f(cto[i] / n_test, 5)} | "
            f"{_f(phi * ct[-1] / n_test, 5)} |"
        )
    a(
        _note(
            "Model sırasına göre en üstteki $\\phi$ oranına gönderildiğinde, test kümesinde "
            "ölçülen artımlı ziyaret sayısının (kişi başına) rastgele sıralamayla karşılaştırması.",
            "Eğrinin rastgele doğrunun üstünde olması tek bir test kümesinde sıralamanın bilgi "
            "taşıdığını gösterir; ziyaretin satışa ya da kâra dönüştüğünü göstermez.",
        )
    )

    a("## Desil tablosu (kapı modeli)\n")
    a("Desil 1 = en yüksek tahmin. Fark = tahmin edilen − ölçülen; aralık bootstrap %95.\n")
    a(
        "| Desil | Satır | Tahmin edilen fark | Ölçülen fark | Fark | Fark %95 |"
        "\n|---|---|---|---|---|---|"
    )
    tab, fci = k["tab"], k["fark_ci"]
    for d in range(10):
        a(
            f"| {d + 1} | {int(tab['boyut'][d])} | {_f(tab['tau_hat'][d])} | "
            f"{_f(tab['tau_obs'][d])} | {_f(tab['fark'][d])} | "
            f"[{_f(fci[0][d])}; {_f(fci[1][d])}] |"
        )
    a(
        f"\nKalibrasyon eğimi (10 nokta, satır ağırlıklı): {_f(k['slope'], 3)} "
        f"[{_f(k['slope_ci'][0], 3)}; {_f(k['slope_ci'][1], 3)}]. Genel düzey: ortalama tahmin "
        f"− ölçülen = {_f(k['gap'], 5)} [{_f(k['gap_ci'][0], 5)}; {_f(k['gap_ci'][1], 5)}].\n"
    )
    a(
        _note(
            "Tahmin edilen ziyaret farkının, aynı desildeki tedavi ve kontrol gruplarından "
            "ölçülen farkla karşılaştırması.",
            "Desil başına kontrol grubu küçüktür (yaklaşık 430 kişi); tek tek desil aralıkları "
            "geniştir ve tek başına karar dayanağı değildir. Ölçülen fark e-postanın bu "
            "kişilerde ne yapacağını değil, bu test kümesinde ölçülen ortalama farkı verir.",
        )
    )

    a("## Politika değeri (kapıya GİRMEZ; E3 ızgarası)\n")
    a(
        "Değer = $g \\cdot$ spend, maliyet $c$ \\$ / e-posta (varsayım, PLAN 4.1). "
        "$\\pi_{mod}$: kapı modelinin ailesi/ayarıyla `spend` üzerinde eğitilen modelin "
        "$g\\hat\\tau_{spend} - c > 0$ kuralı; destek dışı test satırı oranı "
        f"{_f(1 - float(support.mean()), 4)} (bu satırlarda $\\pi_{{mod}} = 1$). "
        "Değerler müşteri başına \\$, IPW ile. Birincil hücre kalın.\n"
    )
    a(
        "| $g$ | $c$ | Herkese | Hiçbirine | Modelle | Hedeflenen oran | "
        "Modelle − Herkese [%95] | Modelle − Hiçbirine [%95] |\n|---|---|---|---|---|---|---|---|"
    )
    for (g, c), v in policy.items():
        b = "**" if (g, c) == PRIMARY_CELL else ""
        a(
            f"| {b}{_f(g, 2)}{b} | {b}{_f(c, 2)}{b} | {_f(v['hep'], 4)} | {_f(v['hic'], 4)} | "
            f"{_f(v['mod'], 4)} | {_f(v['hedef_orani'], 3)} | {_f(v['mod'] - v['hep'], 4)} "
            f"[{_f(v['mod_hep_ci'][0], 4)}; {_f(v['mod_hep_ci'][1], 4)}] | "
            f"{_f(v['mod'] - v['hic'], 4)} [{_f(v['mod_hic_ci'][0], 4)}; "
            f"{_f(v['mod_hic_ci'][1], 4)}] |"
        )
    a(
        _note(
            "Varsayılan marj ve maliyetle üç gönderim politikasının test kümesinde ters olasılık "
            "ağırlığıyla tahmin edilen müşteri başına değeri ve farkları.",
            "Bir kâr vaadi değildir; $g$ ve $c$ varsayımdır, gerçek bir şirketin marjı ya da "
            "maliyeti değildir. Kapı kararı ve E3 değerlendirmesi bu tabloya dayanmaz; E3 ayrı "
            "bir adımdır.",
        )
    )
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    cmds = {"split": cmd_split, "select": cmd_select, "test": cmd_test}
    if len(argv) != 1 or argv[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[0]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
