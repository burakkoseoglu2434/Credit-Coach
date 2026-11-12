"""E2 — Criteo'da yeniden üretim (docs/ecom/PLAN.md bölüm 6, E2). Üç komut, bu sırayla:

  python -m credit_coach.ecom.e2_criteo split    # bölme; karma ve eğitim p'si yaml'a
  python -m credit_coach.ecom.e2_criteo select   # yalnızca doğrulama; E2_selection.md
  python -m credit_coach.ecom.e2_criteo test     # test kümesi TEK sefer; kilit + rapor

Tedavi = `treatment` (atamaya göre); birincil sonuç visit. gz açılmaz; DuckDB'den float32 sütun
matrisi olarak okunur (toplu pandas yok). Bekçi: tek model eğitimi 60 dk'yı ya da tepe bellek
fiziksel belleğin %80'ini aşarsa süreç durur (alt örneğe kendiliğinden geçilmez).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import numpy as np
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier

from credit_coach.ecom import uplift as U
from credit_coach.ecom.e0_data_check import CRITEO_FEATURES, ROOT, SOURCE_PATH, _sql_str
from credit_coach.ecom.e1_hillstrom import _f, _note

SELECTION_PATH = ROOT / "docs" / "ecom" / "E2_selection.md"
REPORT_PATH = ROOT / "docs" / "ecom" / "E2_criteo.md"
LOCK_PATH = ROOT / "docs" / "ecom" / "test_run_criteo.lock"
B = 1000
K_GRID = (0.0001, 0.0003, 0.001, 0.003, 0.01)
PRIMARY_K = 0.001
SUPPORT_Q = (0.005, 0.995)
TRIM = (0.01, 0.99)
# Kapı eşikleri: PLAN bölüm 6, E2 (DONDURULDU).
SLOPE_RANGE = (0.7, 1.3)
DECILE_TOL = 0.25
DECILES_NEEDED = 8
# Bekçi ve süre sınırları (kullanıcı talimatı 2026-11-12).
FIT_LIMIT_S = 3600
MEM_LIMIT = 0.80
BOOT_LIMIT_S = 2 * 3600  # öngörülen bootstrap süresi bunu aşarsa test çalıştırılmaz, sorulur
BENCH_ITERS = 20


# --- bekçi -------------------------------------------------------------------------------------


class Watchdog:
    """Tek model eğitimi FIT_LIMIT_S'yi ya da tepe RSS fiziksel belleğin %80'ini aşarsa durdurur."""

    def __init__(self):
        self.total = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        self.fit_start: float | None = None
        self.fit_name = ""
        self.peak = 0
        threading.Thread(target=self._loop, daemon=True).start()

    @staticmethod
    def rss_peak() -> int:
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r if sys.platform == "darwin" else r * 1024

    def _loop(self):
        while True:
            time.sleep(5)
            self.peak = self.rss_peak()
            if self.peak > MEM_LIMIT * self.total:
                print(f"DUR: tepe bellek {self.peak / 2**30:.2f} GiB > %80", flush=True)
                os._exit(3)
            if self.fit_start and time.perf_counter() - self.fit_start > FIT_LIMIT_S:
                print(f"DUR: {self.fit_name} eğitimi 60 dk'yı aştı", flush=True)
                os._exit(3)

    def fit(self, name, fn, *args, **kw):
        self.fit_name, self.fit_start = name, time.perf_counter()
        try:
            out = fn(*args, **kw)
        finally:
            dt = time.perf_counter() - self.fit_start
            self.fit_start = None
        print(f"  {name}: {dt:.1f} s, tepe bellek {self.rss_peak() / 2**30:.2f} GiB", flush=True)
        return out, dt


# --- veri --------------------------------------------------------------------------------------


def load_sources() -> dict:
    return yaml.safe_load(SOURCE_PATH.read_text())


def load_criteo(path: Path) -> dict[str, np.ndarray]:
    """Satır kimliği = dosya sırası (DuckDB ekleme sırasını korur). float32 özellik matrisi."""
    feats = ", ".join(f"{f}::FLOAT AS {f}" for f in CRITEO_FEATURES)
    sql = (
        f"SELECT {feats}, treatment::TINYINT AS t, visit::TINYINT AS visit, "
        f"conversion::TINYINT AS conversion FROM read_csv({_sql_str(str(path))}, header = true)"
    )
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order = true")
    cols = con.execute(sql).fetchnumpy()
    x = np.empty((len(cols["t"]), len(CRITEO_FEATURES)), dtype=np.float32)
    for j, f in enumerate(CRITEO_FEATURES):
        x[:, j] = cols.pop(f)
    return {
        "x": x,
        "t": cols["t"].astype(np.int64),
        "visit": cols["visit"].astype(np.float64),
        "conversion": cols["conversion"].astype(np.float64),
        "row_id": np.arange(len(x)),
    }


def make_split(a: dict) -> np.ndarray:
    return U.stratified_split(a["t"] * 2 + a["visit"].astype(np.int64))


def check_split(a: dict, sources: dict) -> np.ndarray:
    labels = make_split(a)
    want = (sources.get("bolme_criteo") or {}).get("karma")
    if want != U.split_hash(labels):
        raise SystemExit("bölme karması yaml ile uyuşmuyor ya da yok; önce `split`")
    return labels


def cmd_split() -> int:
    sources = load_sources()
    if "bolme_criteo" in sources:
        print("bolme_criteo zaten yaml'da; değiştirilmez")
        return 1
    a = load_criteo(Path(sources["criteo_uplift"]["yol"]))
    labels = make_split(a)
    tr = labels == U.TRAIN
    block = {
        "bolme_criteo": {
            "karma": U.split_hash(labels),
            "yontem": "tabaka (tedavi x visit) içinde seed'li permütasyon; satır kimliği = dosya sırası",  # noqa: E501
            "seed": U.SEED,
            "satir": {
                "egitim": int(tr.sum()),
                "dogrulama": int((labels == U.VALID).sum()),
                "test": int((labels == U.TEST).sum()),
            },
            "p_egitim": round(float(a["t"][tr].mean()), 6),
            "tedavi": "treatment (atamaya göre; exposure kullanılmaz)",
        }
    }
    with SOURCE_PATH.open("a", encoding="utf-8") as f:
        f.write("# E2 bölmesi (python -m credit_coach.ecom.e2_criteo split)\n")
        f.write(yaml.safe_dump(block, allow_unicode=True, sort_keys=False))
    print(json.dumps(block, ensure_ascii=False, indent=1))
    return 0


# --- select ------------------------------------------------------------------------------------

SEL_BEGIN, SEL_END = "<!-- SECIM-JSON-BASLANGIC -->", "<!-- SECIM-JSON-BITIS -->"


def fit_tau(wd, name, cfg, a, tr, ev, p, outcome="visit"):
    x_tr = a["x"][tr]
    return wd.fit(
        name, U.fit_predict_tau, cfg, x_tr, a[outcome][tr], a["t"][tr], p, a["x"][ev], True
    )


def boot_iteration(taus, orders, decs, y, t, w, extra_pis=(), p=0.85, conv=None):
    """Bir bootstrap adımının tüm hesapları (test komutunda da aynısı kullanılır)."""
    out = {}
    for k, tau in taus.items():
        tab = U.decile_table(tau, y, t, w, decs[k])
        out[k] = (
            U.qini(orders[k], y, t, w)[0],
            U.calibration_slope(tab),
            U.overall_gap(tau, y, t, w),
            tab["fark"],
        )
    pol = []
    for pi, k in extra_pis:
        v_all = U.policy_value(np.ones_like(conv), conv, t, w, p, 1.0, k)
        v_none = U.policy_value(np.zeros_like(conv), conv, t, w, p, 1.0, k)
        v_mod = U.policy_value(pi, conv, t, w, p, 1.0, k)
        pol.append((v_mod - v_all, v_mod - v_none))
    return out, pol


def cmd_select() -> int:
    t0 = time.perf_counter()
    if SELECTION_PATH.exists():
        print("E2_selection.md zaten var; seçim değiştirilmez")
        return 1
    wd = Watchdog()
    sources = load_sources()
    a = load_criteo(Path(sources["criteo_uplift"]["yol"]))
    print(f"veri okundu: {time.perf_counter() - t0:.1f} s", flush=True)
    labels = check_split(a, sources)
    p = sources["bolme_criteo"]["p_egitim"]
    tr, va = labels == U.TRAIN, labels == U.VALID
    y, t, rid = a["visit"][va], a["t"][va], a["row_id"][va]
    w = np.ones(len(y))
    rows, fit_times, taus_va = [], {}, {}
    for cfg in U.grid():
        tau, dt = fit_tau(wd, cfg.ad, cfg, a, tr, va, p)
        area, _ = U.qini(U.rank_order(tau, rid), y, t, w)
        rows.append((cfg, area))
        fit_times[cfg.ad] = dt
        taus_va[cfg.ad] = tau
        print(f"    doğrulama Qini {area:.6f}", flush=True)
    best = {f: max((r for r in rows if r[0].aile == f), key=lambda r: r[1]) for f in ("T", "TO")}
    chosen = max(best.values(), key=lambda r: r[1])[0]
    t2, _ = fit_tau(wd, chosen.ad + " (tekrar)", chosen, a, tr, va, p)
    same = bool(np.array_equal(taus_va[chosen.ad].view(np.uint64), t2.view(np.uint64)))
    if not same:
        print("belirlenimcilik başarısız")
        return 1

    # Desil dengesi (yalnızca tedavi ataması): yeni ve eski eşitlik kuralı, en büyük eşit blok.
    balance = {}
    for f in best:
        tau = taus_va[best[f][0].ad]
        balance[f] = {
            "ayar": best[f][0].ad,
            "en_buyuk_esit_blok": U.max_tie_share(tau),
            "kontrol_payi_anahtar": U.decile_control_share(U.rank_order(tau, rid), t).tolist(),
            "kontrol_payi_satir_kimligi": U.decile_control_share(
                U.rank_order(tau, rid, tiebreak="row_id"), t
            ).tolist(),
        }
    print(json.dumps(balance, indent=1), flush=True)

    # Bootstrap süre ölçümü (doğrulama kümesinde, aynı boyut ve aynı hesaplar).
    btaus = {f: taus_va[best[f][0].ad] for f in best}
    orders = {k: U.rank_order(v, rid) for k, v in btaus.items()}
    decs = {k: U.decile_of(o) for k, o in orders.items()}
    pis = [((btaus[chosen.aile] > k).astype(float), k) for k in K_GRID]
    tb = time.perf_counter()
    gen = U.bootstrap_weights(t, BENCH_ITERS, seed=1)
    for wb in gen:
        boot_iteration(btaus, orders, decs, y, t, wb, pis, p, a["conversion"][va])
    per_iter = (time.perf_counter() - tb) / BENCH_ITERS

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
        "bolme_karmasi": sources["bolme_criteo"]["karma"],
        "p_egitim": p,
        "egitim_sureleri_s": {k: round(v, 1) for k, v in fit_times.items()},
        "tepe_bellek_gib": round(Watchdog.rss_peak() / 2**30, 2),
        "desil_dengesi": balance,
        "kontrol_payi_genel": float(1 - t.mean()),
        "bootstrap_adim_s": round(per_iter, 3),
        "bootstrap_ongorulen_s": round(per_iter * B, 0),
    }
    runtime = time.perf_counter() - t0
    SELECTION_PATH.write_text(render_selection(rows, best, chosen, sel, runtime))
    print(
        json.dumps(
            {
                k: sel[k]
                for k in ("secilen", "aile_en_iyi", "tepe_bellek_gib", "bootstrap_ongorulen_s")
            },
            ensure_ascii=False,
        )
    )
    if per_iter * B > BOOT_LIMIT_S:
        print("DUR: öngörülen bootstrap süresi sınırı aşıyor; test çalıştırılmamalı")
        return 4
    return 0


def render_selection(rows, best, chosen, sel, runtime) -> str:
    L = [
        "# E2 — Model ve ayar seçimi (yalnızca doğrulama kümesi)\n",
        "Üretildi: `python -m credit_coach.ecom.e2_criteo select`. Bu belge test kümesi "
        "çalışmadan ÖNCE commit'lenir; commit sırası seçimin test sonucundan önce yapıldığının "
        "kanıtıdır. Test kümesi bu adımda okunmadı.\n",
        f"Bölme karması `{sel['bolme_karmasi']}`, eğitim kümesinde $p$ = "
        f"{_f(sel['p_egitim'], 6)}. Toplam çalışma süresi {_f(runtime / 60, 1)} dk; tepe bellek "
        f"{_f(sel['tepe_bellek_gib'], 2)} GiB (sınır: fiziksel belleğin %80'i).\n",
        "## Izgara ve doğrulama Qini'si\n",
        "E1 ile aynı ızgara: toplam 12 kombinasyon (2 aile × öğrenme hızı {0,05; 0,1} × yaprak "
        "{7; 15; 31}); `max_iter` = 200, erken durdurma kapalı, `random_state` = 20261111. Ölçüt: "
        "doğrulama Qini alanı. Eğitim süresi sütunu tek ayarın tüm eğitimidir (T ailesinde iki "
        "model); sınır 60 dk.\n",
        "| Ayar | Aile | Öğrenme hızı | Yaprak | Doğrulama Qini | Eğitim süresi (s) |"
        "\n|---|---|---|---|---|---|",
    ]
    for cfg, area in rows:
        mark = " **(seçilen)**" if cfg == chosen else ""
        L.append(
            f"| `{cfg.ad}`{mark} | {cfg.aile} | {_f(cfg.learning_rate, 2)} | "
            f"{cfg.max_leaf_nodes} | {_f(area, 6)} | {_f(sel['egitim_sureleri_s'][cfg.ad], 1)} |"
        )
    L.append(
        _note(
            "Her ayarın doğrulama kümesinde Qini alanı ve eğitim süresi; en yüksek Qini seçildi.",
            "Doğrulama Qini'si test sonucunu öngörmez; aynı küme hem ayar hem seçim için "
            "kullanıldığı için iyimser olabilir.",
        )
    )
    L += [
        "## Desil dengesi (doğrulama kümesi; yalnızca tedavi ataması)\n",
        "Eşitlik kuralı PLAN 2.1 sonradan notuna göre: sıralama $(-\\hat\\tau,\\ "
        "\\text{anahtar})$, anahtar = splitmix64(satır kimliği, seed 20261111). Karşılaştırma "
        "için eski kural (satır kimliği) da gösterilir. Genel kontrol payı "
        f"{_f(sel['kontrol_payi_genel'], 3)}.\n",
        "| Model | Ayar | En büyük eşit blok | Kural | "
        + " | ".join(f"D{d}" for d in range(1, 11))
        + " |\n|---|---|---|---|"
        + "---|" * 10,
    ]
    for f, bal in sel["desil_dengesi"].items():
        for kural, key in (
            ("anahtar (yeni)", "kontrol_payi_anahtar"),
            ("satır kimliği (eski)", "kontrol_payi_satir_kimligi"),
        ):
            L.append(
                f"| {f} | `{bal['ayar']}` | {_f(bal['en_buyuk_esit_blok'], 4)} | {kural} | "
                + " | ".join(_f(v, 3) for v in bal[key])
                + " |"
            )
    L.append(
        _note(
            "Doğrulama kümesinde tahmine göre sıralanmış desillerde kontrol grubunun payı; "
            "rastgele atamada her desilde genel paya yakın olması beklenir.",
            "Sonuç değişkeni kullanılmadı; bu tablo modelin isabeti hakkında bir şey söylemez, "
            "yalnızca sıralama kuralının tedaviyi desillere dengeli dağıtıp "
            "dağıtmadığını gösterir.",
        )
    )
    proj = sel["bootstrap_ongorulen_s"]
    L += [
        "## Seçim\n",
        f"- **Kapı modeli (tek):** `{chosen.ad}`.",
        f"- Ailelerin en iyileri (testte yan yana): T = `{best['T'][0].ad}`, TO = "
        f"`{best['TO'][0].ad}`.",
        "- Belirlenimcilik: seçilen ayar iki kez eğitildi; doğrulama tahminleri bit düzeyinde "
        f"aynı: **{'evet' if sel['belirlenimcilik_bit_esit'] else 'hayır'}**.",
        f"- Bootstrap süre ölçümü (doğrulama kümesi, {BENCH_ITERS} adım, testteki hesapların "
        f"aynısı): adım başına {_f(sel['bootstrap_adim_s'], 3)} s; B = {B} için öngörülen "
        f"{_f(proj / 60, 1)} dk. Sınır {BOOT_LIMIT_S // 3600} saat; aşarsa test çalıştırılmaz, "
        "kullanıcıya sorulur.",
        "",
        "## Test kümesinde yapılacaklar (önceden kayıt)\n",
        "- Modeller yalnızca eğitim kümesinde yukarıdaki ayarlarla yeniden eğitilir; test "
        "kümesi bir kez tahmin edilir; `docs/ecom/test_run_criteo.lock` yazılır, kilit varsa "
        "komut reddeder.",
        "- Kapı ölçütleri PLAN bölüm 6 E2 (DONDURULDU): Qini %95 alt sınırı > 0; kalibrasyon "
        "eğimi [0,7; 1,3]; en az 8/10 desilde $|\\Delta_d| \\le 0{,}25\\,|\\tau^{obs}_{test}|$ ya "
        "da $\\Delta_d$'nin %95 aralığı 0'ı içerir.",
        "- Bootstrap B = 1000, tabakalı, seed 20261111; desiller ham test kümesinde sabit.",
        "- Politika değeri tablosu (kapıya GİRMEZ, PLAN 2.3, 4.2): değer sonucu `conversion`, "
        "birim $m$ (dönüşüm başına değer); kapı modelinin ailesi ve ayarı `conversion` üzerinde "
        "yalnızca eğitimde, ayar yapılmadan eğitilir; $\\pi_{mod} = 1[\\hat\\tau_{conv} > k]$, "
        "destek dışı satırlarda 1; $k \\in \\{0{,}0001; 0{,}0003; 0{,}001; 0{,}003; 0{,}01\\}$, "
        "birincil $k = 0{,}001$.",
        "- İkincil duyarlılık analizi (kapıya GİRMEZ, ön kayıt `e54c9cd`): $\\hat p(x)$ eğitim "
        "kümesinde `HistGradientBoostingClassifier` (öğrenme hızı 0,1, `max_leaf_nodes` 31, "
        "`max_iter` 200, erken durdurma kapalı, `random_state` 20261111); test satırlarından "
        "$\\hat p(x) < 0{,}01$ ya da $> 0{,}99$ olanlar kırpılır, oran raporlanır; ağırlık "
        "tedavide $1/\\hat p$, kontrolde $1/(1-\\hat p)$. Raporlanan: özellik başına ham ve "
        "ağırlıklı SMD, ham ve ağırlıklı genel `visit` farkı, kapı modelinin ham (tüm test ve "
        "kırpılmış) ve ağırlıklı Qini alanı (nokta tahmini).",
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
    pat = re.escape(SEL_BEGIN) + r"\s*```json\s*(.*?)```\s*" + re.escape(SEL_END)
    m = re.search(pat, text, re.S)
    if not m:
        raise SystemExit("E2_selection.md içinde seçim bloğu yok")
    return json.loads(m.group(1))


def cfg_from(sel: dict, name: str) -> U.Config:
    d = sel["ayarlar"][name]
    return U.Config(d["aile"], d["learning_rate"], d["max_leaf_nodes"], d["max_iter"])


# --- test --------------------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_lock(sources: dict) -> dict:
    src = sources["criteo_uplift"]
    h = _file_sha256(Path(src["yol"]))
    if h != src["gz_sha256"]:
        raise SystemExit("veri SHA-256 yaml ile uyuşmuyor")
    lock = {
        "commit": _git("rev-parse", "HEAD"),
        "veri_gz_sha256": h,
        "bolme_karmasi": sources["bolme_criteo"]["karma"],
        "zaman_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with LOCK_PATH.open("x", encoding="utf-8") as f:
        f.write(json.dumps(lock, ensure_ascii=False, indent=1) + "\n")
    return lock


def support_mask(x_tr: np.ndarray, x_ev: np.ndarray) -> np.ndarray:
    lo, hi = np.quantile(x_tr, SUPPORT_Q, axis=0)
    return np.all((x_ev >= lo) & (x_ev <= hi), axis=1)


def weighted_smd(x: np.ndarray, t: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Ağırlıklı ortalama ve ağırlıklı (popülasyon) varyansla SMD; ağırlık 1 = ham."""
    out = []
    for j in range(x.shape[1]):
        v = x[:, j].astype(np.float64)
        m = []
        for g in (1, 0):
            ww = w * (t == g)
            mu = np.sum(ww * v) / np.sum(ww)
            var = np.sum(ww * (v - mu) ** 2) / np.sum(ww)
            m.append((mu, var))
        out.append((m[0][0] - m[1][0]) / np.sqrt((m[0][1] + m[1][1]) / 2))
    return np.array(out)


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
        print("E2_selection.md commit'lenmemiş")
        return 1
    sel = read_selection()
    if sel["bootstrap_ongorulen_s"] > BOOT_LIMIT_S:
        print("öngörülen bootstrap süresi sınırı aşıyor; kullanıcıya sor")
        return 4
    wd = Watchdog()
    sources = load_sources()
    a = load_criteo(Path(sources["criteo_uplift"]["yol"]))
    labels = check_split(a, sources)
    p = sources["bolme_criteo"]["p_egitim"]
    tr, te = labels == U.TRAIN, labels == U.TEST
    fams = {f: cfg_from(sel, n) for f, n in sel["aile_en_iyi"].items()}
    taus = {f: fit_tau(wd, f"test {c.ad}", c, a, tr, te, p)[0] for f, c in fams.items()}
    tau_conv = fit_tau(wd, "conversion", fams[sel["secilen_aile"]], a, tr, te, p, "conversion")[0]
    support = support_mask(a["x"][tr], a["x"][te])
    ps_model, _ = wd.fit(
        "p(x)",
        HistGradientBoostingClassifier(
            learning_rate=0.1,
            max_leaf_nodes=31,
            max_iter=200,
            early_stopping=False,
            random_state=U.SEED,
        ).fit,
        a["x"][tr],
        a["t"][tr],
    )
    ps = ps_model.predict_proba(a["x"][te])[:, 1]
    x_te = a["x"][te]
    lock = write_lock(sources)  # test etiketleri bundan sonra okunur
    print(f"kilit yazıldı {lock['zaman_utc']}", flush=True)

    y, t, rid, conv = a["visit"][te], a["t"][te], a["row_id"][te], a["conversion"][te]
    del a
    res = {f: evaluate_model(v, y, t, rid) for f, v in taus.items()}
    orders = {f: r["order"] for f, r in res.items()}
    decs = {f: r["dec"] for f, r in res.items()}
    pis = [(np.where(support, (tau_conv > k).astype(float), 1.0), k) for k in K_GRID]

    tb = time.perf_counter()
    boot = {f: {"qini": [], "slope": [], "gap": [], "fark": []} for f in res}
    pboot = {k: {"mod_hep": [], "mod_hic": []} for k in K_GRID}
    for i, w in enumerate(U.bootstrap_weights(t, B)):
        out, pol = boot_iteration(taus, orders, decs, y, t, w, pis, p, conv)
        for f, (q, s, g, fk) in out.items():
            boot[f]["qini"].append(q)
            boot[f]["slope"].append(s)
            boot[f]["gap"].append(g)
            boot[f]["fark"].append(fk)
        for (dh, dn), k in zip(pol, K_GRID, strict=True):
            pboot[k]["mod_hep"].append(dh)
            pboot[k]["mod_hic"].append(dn)
        if (i + 1) % 100 == 0:
            print(f"  bootstrap {i + 1}/{B}, {time.perf_counter() - tb:.0f} s", flush=True)
    boot_s = time.perf_counter() - tb
    for f, r in res.items():
        r["qini_ci"] = U.ci(boot[f]["qini"])
        r["slope_ci"] = U.ci(boot[f]["slope"])
        r["gap_ci"] = U.ci(boot[f]["gap"])
        r["fark_ci"] = np.percentile(np.array(boot[f]["fark"]), [2.5, 97.5], axis=0)

    w1 = np.ones(len(y))
    policy = {}
    for pi, k in pis:
        policy[k] = {
            "hep": U.policy_value(np.ones_like(conv), conv, t, w1, p, 1.0, k),
            "hic": U.policy_value(np.zeros_like(conv), conv, t, w1, p, 1.0, k),
            "mod": U.policy_value(pi, conv, t, w1, p, 1.0, k),
            "hedef_orani": float(pi.mean()),
            "mod_hep_ci": U.ci(pboot[k]["mod_hep"]),
            "mod_hic_ci": U.ci(pboot[k]["mod_hic"]),
        }

    # İkincil duyarlılık analizi (kapıya girmez).
    keep = (ps >= TRIM[0]) & (ps <= TRIM[1])
    wps = np.where(t == 1, 1 / ps, 1 / (1 - ps))[keep]
    yk, tk = y[keep], t[keep]
    kres = res[sel["secilen_aile"]]
    tau_k = taus[sel["secilen_aile"]][keep]
    order_k = U.rank_order(tau_k, rid[keep])
    sec = {
        "kirpilan_oran": float(1 - keep.mean()),
        "ps_min": float(ps.min()),
        "ps_max": float(ps.max()),
        "smd_ham": weighted_smd(x_te, t, w1),
        "smd_agirlikli": weighted_smd(x_te[keep], tk, wps),
        "fark_ham": float(y[t == 1].mean() - y[t == 0].mean()),
        "fark_agirlikli": float(
            np.average(yk, weights=wps * tk) - np.average(yk, weights=wps * (1 - tk))
        ),
        "qini_ham": kres["qini"],
        "qini_ham_kirpilmis": U.qini(order_k, yk, tk, np.ones(len(yk)))[0],
        "qini_agirlikli": U.qini(order_k, yk, tk, wps)[0],
    }

    obs = float(y[t == 1].mean() - y[t == 0].mean())  # ölçülen genel fark (test)
    k = kres
    lo_f, hi_f = k["fark_ci"]
    ok_dec = (np.abs(k["tab"]["fark"]) <= DECILE_TOL * abs(obs)) | ((lo_f <= 0) & (hi_f >= 0))
    crit = [
        (
            "1",
            "Qini alanı %95 alt sınırı > 0",
            f"alt sınır {_f(k['qini_ci'][0], 6)}",
            k["qini_ci"][0] > 0,
        ),
        (
            "2",
            "Kalibrasyon eğimi ∈ [0,7; 1,3]",
            f"eğim {_f(k['slope'], 3)} [%95: {_f(k['slope_ci'][0], 3)}; {_f(k['slope_ci'][1], 3)}]",
            SLOPE_RANGE[0] <= k["slope"] <= SLOPE_RANGE[1],
        ),
        (
            "3",
            "En az 8/10 desilde \\|Δ_d\\| ≤ 0,25·\\|τ_obs\\| ya da aralık 0'ı içerir",
            f"{int(ok_dec.sum())}/10 (τ_obs = {_f(obs, 5)})",
            int(ok_dec.sum()) >= DECILES_NEEDED,
        ),
    ]
    runtime = time.perf_counter() - t0
    REPORT_PATH.write_text(
        render_report(
            sel, res, policy, sec, crit, ok_dec, obs, support, lock, runtime, boot_s, wd, p, len(y)
        ),
        encoding="utf-8",
    )
    summary = {
        "sure_s": round(runtime, 1),
        "bootstrap_s": round(boot_s, 1),
        "secilen": sel["secilen"],
        "olcutler": {c[0]: c[3] for c in crit},
        "qini": [k["qini"], *k["qini_ci"]],
        "egim": [k["slope"], *k["slope_ci"]],
        "desil_ok": int(ok_dec.sum()),
        "kirpilan": sec["kirpilan_oran"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if all(c[3] for c in crit) else 2


def decision(crit) -> str:
    if all(c[3] for c in crit):
        return "E2 ölçütlerinin üçü de geçti. E3 ayrı bir adım; kullanıcı onayıyla başlar."
    failed = ", ".join(c[0] for c in crit if not c[3])
    return (
        f"Kalan ölçüt(ler): {failed}. Durdurma kuralı (PLAN bölüm 6, E2): test yeniden "
        "çalıştırılmaz, model değiştirilmez; E3 yalnızca Hillstrom için, kullanıcı onayıyla "
        "yapılır."
    )


def render_report(
    sel, res, policy, sec, crit, ok_dec, obs, support, lock, runtime, boot_s, wd, p, n_test
) -> str:
    k = res[sel["secilen_aile"]]
    L: list[str] = []
    a = L.append
    a("# E2 — Criteo: tahmin edilen ve ölçülen fark\n")
    a(
        "Üretildi: `python -m credit_coach.ecom.e2_criteo test` (test kümesi tek sefer). "
        f"Kilit: `docs/ecom/test_run_criteo.lock` (commit `{lock['commit'][:7]}`, "
        f"{lock['zaman_utc']}). Seçim test öncesi `docs/ecom/E2_selection.md`'de commit'lendi.\n"
    )
    a(
        f"Tedavi = `treatment` (atamaya göre), sonuç `visit`; test kümesi {n_test} satır; "
        f"eğitim $p$ = {_f(p, 6)}. Bootstrap B = {B}, tabakalı. Çalışma süresi "
        f"{_f(runtime / 60, 1)} dk (bootstrap {_f(boot_s / 60, 1)} dk); tepe bellek "
        f"{_f(Watchdog.rss_peak() / 2**30, 2)} GiB / fiziksel {_f(wd.total / 2**30, 1)} GiB. "
        "Alt örneğe geçilmedi; gz açılmadı.\n"
    )
    a("## Kapı ölçütleri (PLAN bölüm 6, E2; DONDURULDU)\n")
    a(f"Kapı modeli: `{sel['secilen']}`.\n")
    a("| Ölçüt | Tanım | Ölçülen | Sonuç |\n|---|---|---|---|")
    for c in crit:
        a(f"| {c[0]} | {c[1]} | {c[2]} | {'geçti' if c[3] else '**kaldı**'} |")
    a(f"\n**Karar (durdurma kuralı):** {decision(crit)}\n")
    a(
        _note(
            "Doğrulamada seçilen tek modelin test kümesinde, sonuç görülmeden dondurulmuş üç "
            "eşiğe göre durumu.",
            "Geçmek, reklamın başka bir kampanyada ya da kredide benzer bir fark yaratacağını "
            "göstermez; Criteo eşit olmayan alt örnekleme ve birden çok testin birleşimidir, "
            "mutlak oranlar gerçek kampanyayı temsil etmez.",
        )
    )

    a("## İki model ailesi yan yana\n")
    a(
        "| Model | Ayar | Qini alanı [%95] | Kalibrasyon eğimi [%95] | Genel düzey farkı [%95] |"
        "\n|---|---|---|---|---|"
    )
    for f in ("T", "TO"):
        r = res[f]
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
            "Ailelerden birinin genel olarak daha iyi olduğunu göstermez; seçim tek bir "
            "doğrulama kümesine dayanır.",
        )
    )

    a("## Qini eğrisi\n")
    a("$Q(\\phi)/N$; rastgele doğru $\\phi\\,Q(1)/N$. 100 noktanın 10'da biri.\n")
    a("| $\\phi$ | T: $Q/N$ | TO: $Q/N$ | Rastgele (T) |\n|---|---|---|---|")
    ct, cto = res["T"]["curve"], res["TO"]["curve"]
    for i in range(9, 100, 10):
        phi = (i + 1) / 100
        a(
            f"| {_f(phi, 1)} | {_f(ct[i] / n_test, 5)} | {_f(cto[i] / n_test, 5)} | "
            f"{_f(phi * ct[-1] / n_test, 5)} |"
        )
    a(
        _note(
            "Model sırasına göre en üstteki $\\phi$ oranı hedeflendiğinde test kümesinde ölçülen "
            "artımlı ziyaretin (kişi başına) rastgele sıralamayla karşılaştırması.",
            "Ziyaretin dönüşüme ya da kâra dönüştüğünü göstermez; tek bir test kümesidir.",
        )
    )

    a("## Desil tablosu (kapı modeli)\n")
    a(
        f"Desil 1 = en yüksek tahmin. Fark = tahmin edilen − ölçülen. Tolerans "
        f"$0{{,}}25\\,|\\tau^{{obs}}_{{test}}|$ = {_f(DECILE_TOL * abs(obs), 5)}.\n"
    )
    a(
        "| Desil | Satır | Tahmin edilen | Ölçülen | Fark | Fark %95 | Ölçüt 3 |"
        "\n|---|---|---|---|---|---|---|"
    )
    tab, fci = k["tab"], k["fark_ci"]
    for d in range(10):
        a(
            f"| {d + 1} | {int(tab['boyut'][d])} | {_f(tab['tau_hat'][d], 5)} | "
            f"{_f(tab['tau_obs'][d], 5)} | {_f(tab['fark'][d], 5)} | "
            f"[{_f(fci[0][d], 5)}; {_f(fci[1][d], 5)}] | {'uygun' if ok_dec[d] else 'değil'} |"
        )
    a(
        f"\nKalibrasyon eğimi: {_f(k['slope'], 3)} [{_f(k['slope_ci'][0], 3)}; "
        f"{_f(k['slope_ci'][1], 3)}]. Genel düzey: ortalama tahmin − ölçülen = {_f(k['gap'], 5)} "
        f"[{_f(k['gap_ci'][0], 5)}; {_f(k['gap_ci'][1], 5)}].\n"
    )
    a(
        _note(
            "Tahmin edilen ziyaret farkının aynı desildeki tedavi ve kontrol gruplarından "
            "ölçülen farkla karşılaştırması ve ölçüt 3'e uygunluğu.",
            "Ölçülen fark reklamın bu kişilerde ne yapacağını değil, bu test kümesinde ölçülen "
            "ortalama farkı verir; tek tek desiller karar dayanağı değildir.",
        )
    )

    a("## Politika değeri (kapıya GİRMEZ; E3 ızgarası)\n")
    a(
        "Değer = dönüşüm × $m$, maliyet $c = k\\,m$ (varsayım, PLAN 4.2); değerler müşteri "
        "başına $m$ biriminde × 1000, IPW ile. $\\pi_{mod} = 1[\\hat\\tau_{conv} > k]$; destek "
        f"dışı test satırı oranı {_f(1 - float(support.mean()), 4)} (bu satırlarda "
        "$\\pi_{mod} = 1$). Birincil hücre kalın.\n"
    )
    a(
        "| $k$ | Herkese | Hiçbirine | Modelle | Hedeflenen oran | Modelle − Herkese [%95] | "
        "Modelle − Hiçbirine [%95] |\n|---|---|---|---|---|---|---|"
    )
    for kk, v in policy.items():
        b = "**" if kk == PRIMARY_K else ""
        s = 1000
        a(
            f"| {b}{_f(kk, 4)}{b} | {_f(v['hep'] * s, 4)} | {_f(v['hic'] * s, 4)} | "
            f"{_f(v['mod'] * s, 4)} | {_f(v['hedef_orani'], 3)} | "
            f"{_f((v['mod'] - v['hep']) * s, 4)} [{_f(v['mod_hep_ci'][0] * s, 4)}; "
            f"{_f(v['mod_hep_ci'][1] * s, 4)}] | {_f((v['mod'] - v['hic']) * s, 4)} "
            f"[{_f(v['mod_hic_ci'][0] * s, 4)}; {_f(v['mod_hic_ci'][1] * s, 4)}] |"
        )
    a(
        _note(
            "Varsayılan maliyet oranıyla üç politikanın test kümesinde IPW ile tahmin edilen "
            "müşteri başına değeri (×1000) ve farkları.",
            "Bir kâr vaadi değildir; $k$ varsayımdır ve alt örnekleme yüzünden mutlak dönüşüm "
            "oranları gerçek kampanyayı temsil etmez. Kapı kararı bu tabloya dayanmaz.",
        )
    )

    a("## İkincil duyarlılık analizi: $\\hat p(x)$ ağırlıklandırma (kapıya GİRMEZ)\n")
    a(
        f"Ön kayıt `e54c9cd`. $\\hat p(x)$ aralığı [{_f(sec['ps_min'], 4)}; "
        f"{_f(sec['ps_max'], 4)}]; kırpılan test satırı oranı "
        f"**{_f(sec['kirpilan_oran'], 5)}** ($\\hat p < 0{{,}}01$ ya da $> 0{{,}}99$).\n"
    )
    a("| Ölçü | Ham | Ağırlıklı |\n|---|---|---|")
    a(
        f"| Genel `visit` farkı (tedavi − kontrol) | {_f(sec['fark_ham'], 5)} | "
        f"{_f(sec['fark_agirlikli'], 5)} |"
    )
    a(
        f"| Kapı modeli Qini alanı (tüm test / kırpılmış) | {_f(sec['qini_ham'], 6)} / "
        f"{_f(sec['qini_ham_kirpilmis'], 6)} | {_f(sec['qini_agirlikli'], 6)} |"
    )
    a(
        _note(
            "Özellik dengesizliğine karşı ters olasılık ağırlığıyla düzeltilmiş genel fark ve "
            "Qini'nin ham değerlerle karşılaştırması (nokta tahmini).",
            "Kapı kararını değiştirmez; $\\hat p(x)$ bir modeldir ve doğru olduğu bilinmez; "
            "aralık hesaplanmadı.",
        )
    )
    a("| Özellik | SMD ham (test) | SMD ağırlıklı (kırpılmış test) |\n|---|---|---|")
    order = np.argsort(-np.abs(sec["smd_ham"]))
    for j in order:
        a(f"| `{CRITEO_FEATURES[j]}` | {_f(sec['smd_ham'][j])} | {_f(sec['smd_agirlikli'][j])} |")
    a(
        _note(
            "Test kümesinde her özelliğin tedavi/kontrol SMD'si, ham ve $\\hat p(x)$ ağırlığıyla; "
            "en büyük ham SMD üstte.",
            "Ağırlıklı SMD'nin küçülmesi gözlenmeyen özelliklerde dengeyi göstermez.",
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
