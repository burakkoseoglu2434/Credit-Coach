"""E0 veri doğrulaması (docs/ecom/PLAN.md bölüm 6, E0).

Yalnızca veri: model, bölme dosyası, test kilidi yok.
Kullanım: python -m credit_coach.ecom.e0_data_check
(Criteo gz açılmaz, DuckDB ile doğrudan okunur.)

Disiplin (kullanıcı talimatı 2026-11-12): sonuç değişkenlerinin (visit, conversion, spend)
tedavi/kontrol kırılımı hesaplanmaz; yalnızca genel ortalama, eksik değer ve aralık.
SMD yalnızca özellikler içindir.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pandera.pandas as pa
import yaml

ROOT = Path(__file__).resolve().parents[4]
SOURCE_PATH = ROOT / "configs" / "ecom_data_source.yaml"
REPORT_PATH = ROOT / "docs" / "ecom" / "E0_data_check.md"

# Eşikler: PLAN.md bölüm 6, E0 (DONDURULDU, Kararlar Q9).
HILL_ROWS = 64_000
SEGMENT_SHARE = 1 / 3
SEGMENT_TOL = 0.01
CRITEO_ROWS = 13_979_592
CRITEO_P = 0.846
CRITEO_P_TOL = 0.005
SMD_MAX = 0.05

NO_EMAIL = "No E-Mail"
SEGMENTS = ("Mens E-Mail", "Womens E-Mail", NO_EMAIL)
HISTORY_SEGMENTS = (
    "1) $0 - $100",
    "2) $100 - $200",
    "3) $200 - $350",
    "4) $350 - $500",
    "5) $500 - $750",
    "6) $750 - $1,000",
    "7) $1,000 +",
)
ZIP_CODES = ("Rural", "Surburban", "Urban")  # "Surburban" kaynak dosyadaki yazımdır
CHANNELS = ("Multichannel", "Phone", "Web")

HILL_TYPES = {
    "recency": "BIGINT",
    "history_segment": "VARCHAR",
    "history": "DOUBLE",
    "mens": "BIGINT",
    "womens": "BIGINT",
    "zip_code": "VARCHAR",
    "newbie": "BIGINT",
    "channel": "VARCHAR",
    "segment": "VARCHAR",
    "visit": "BIGINT",
    "conversion": "BIGINT",
    "spend": "DOUBLE",
}
CRITEO_FEATURES = tuple(f"f{i}" for i in range(12))
CRITEO_TYPES = dict.fromkeys(CRITEO_FEATURES, "DOUBLE") | {
    "treatment": "BIGINT",
    "conversion": "BIGINT",
    "visit": "BIGINT",
    "exposure": "BIGINT",
}


def _sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def read_csv_sql(path: Path, types: dict[str, str]) -> str:
    cols = ", ".join(f"{_sql_str(k)}: {_sql_str(v)}" for k, v in types.items())
    return f"read_csv({_sql_str(str(path))}, header = true, columns = {{{cols}}})"


def hillstrom_features() -> list[tuple[str, str]]:
    """(ad, SQL ifadesi). Kategorikler one-hot."""
    feats = [(c, c) for c in ("recency", "history", "mens", "womens", "newbie")]
    for col, levels in (
        ("zip_code", ZIP_CODES),
        ("channel", CHANNELS),
        ("history_segment", HISTORY_SEGMENTS),
    ):
        feats += [(f"{col}={lv}", f"CAST({col} = {_sql_str(lv)} AS DOUBLE)") for lv in levels]
    return feats


def smd(m1: float, v1: float, m0: float, v0: float) -> float:
    """Standartlaştırılmış ortalama farkı: (m1 - m0) / sqrt((v1 + v0) / 2), örneklem varyansı."""
    pooled = math.sqrt((v1 + v0) / 2)
    if pooled == 0:
        return 0.0 if m1 == m0 else math.inf
    return (m1 - m0) / pooled


def smd_rows(
    con: duckdb.DuckDBPyConnection,
    relation: str,
    treat: str,
    features: list[tuple[str, str]],
    where: str = "TRUE",
) -> list[dict]:
    """Tek geçişte, DuckDB SQL ile her özelliğin T/C ortalaması, varyansı ve SMD'si."""
    parts = []
    for i, (_, expr) in enumerate(features):
        for g, cond in (("1", f"({treat})"), ("0", f"NOT ({treat})")):
            parts += [
                f"avg({expr}) FILTER (WHERE {cond}) AS m{g}_{i}",
                f"var_samp({expr}) FILTER (WHERE {cond}) AS v{g}_{i}",
            ]
    cur = con.execute(f"SELECT {', '.join(parts)} FROM {relation} WHERE {where}")
    row = cur.fetchone()
    r = dict(zip([d[0] for d in cur.description], row, strict=True))
    out = []
    for i, (name, _) in enumerate(features):
        m1, v1, m0, v0 = r[f"m1_{i}"], r[f"v1_{i}"], r[f"m0_{i}"], r[f"v0_{i}"]
        out.append({"ozellik": name, "ort_T": m1, "ort_C": m0, "smd": smd(m1, v1, m0, v0)})
    return out


def _binary() -> pa.Column:
    return pa.Column(int, pa.Check.isin([0, 1]), nullable=False)


def hillstrom_schema() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "recency": pa.Column(int, pa.Check.ge(0), nullable=False),
            "history_segment": pa.Column(str, pa.Check.isin(HISTORY_SEGMENTS), nullable=False),
            "history": pa.Column(float, pa.Check.ge(0), nullable=False),
            "mens": _binary(),
            "womens": _binary(),
            "zip_code": pa.Column(str, pa.Check.isin(ZIP_CODES), nullable=False),
            "newbie": _binary(),
            "channel": pa.Column(str, pa.Check.isin(CHANNELS), nullable=False),
            "segment": pa.Column(str, pa.Check.isin(SEGMENTS), nullable=False),
            "visit": _binary(),
            "conversion": _binary(),
            "spend": pa.Column(float, pa.Check.ge(0), nullable=False),
        },
        strict=True,
        ordered=True,
    )


def criteo_schema() -> pa.DataFrameSchema:
    finite = pa.Check(lambda s: np.isfinite(s), name="sonlu")
    cols = {f: pa.Column(float, finite, nullable=False) for f in CRITEO_FEATURES}
    cols |= {c: _binary() for c in ("treatment", "conversion", "visit", "exposure")}
    return pa.DataFrameSchema(cols, strict=True, ordered=True)


def failing_rows(schema: pa.DataFrameSchema, df: pd.DataFrame) -> int:
    """Şemayı geçemeyen satır sayısı (sütun düzeyi hata = tüm satırlar)."""
    try:
        schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        if fc["index"].isna().any():
            return len(df)
        return int(fc["index"].nunique())
    return 0


def column_summary(con: duckdb.DuckDBPyConnection, relation: str, types: dict) -> list[dict]:
    """Sütun başına tür, eksik değer, en küçük ve en büyük değer (genel; kırılım yok)."""
    parts = []
    for c in types:
        parts += [f"count(*) - count({c})", f"min({c})", f"max({c})"]
    row = con.execute(f"SELECT {', '.join(parts)} FROM {relation}").fetchone()
    return [
        {"sutun": c, "tur": t, "eksik": row[3 * i], "min": row[3 * i + 1], "max": row[3 * i + 2]}
        for i, (c, t) in enumerate(types.items())
    ]


def check_hillstrom(path: Path) -> dict:
    con = duckdb.connect()
    rel = read_csv_sql(path, HILL_TYPES)
    # 64.000 satır; satır kimliği = dosya sırası (0'dan) = pandas indeksi
    df = con.execute(f"SELECT * FROM {rel}").df()
    n = len(df)
    seg = {s: int((df["segment"] == s).sum()) for s in SEGMENTS}
    feats = hillstrom_features()
    no = _sql_str(NO_EMAIL)
    pairs = {
        "birlesik_vs_yok": (f"segment <> {no}", "TRUE"),
        "womens_vs_yok": ("segment = 'Womens E-Mail'", f"segment IN ('Womens E-Mail', {no})"),
        "mens_vs_yok": ("segment = 'Mens E-Mail'", f"segment IN ('Mens E-Mail', {no})"),
    }
    smds = {k: smd_rows(con, rel, t, feats, w) for k, (t, w) in pairs.items()}
    outcomes = {
        c: {
            "ortalama": float(df[c].mean()),
            "eksik": int(df[c].isna().sum()),
            "min": float(df[c].min()),
            "max": float(df[c].max()),
        }
        for c in ("visit", "conversion", "spend")
    }
    return {
        "satir": n,
        "segment_sayi": seg,
        "segment_pay": {s: v / n for s, v in seg.items()},
        "p_birlesik": (n - seg[NO_EMAIL]) / n,
        "sutunlar": column_summary(con, rel, HILL_TYPES),
        "pandera_kalan": failing_rows(hillstrom_schema(), df),
        "smd": smds,
        "sonuc_genel": outcomes,
    }


def check_criteo(path: Path, vectors_per_chunk: int = 500) -> dict:
    """gz açılmaz; DuckDB doğrudan okur. Pandera ~1 M satırlık parçalarla."""
    con = duckdb.connect()
    rel = read_csv_sql(path, CRITEO_TYPES)
    t0 = time.perf_counter()
    agg = con.execute(
        f"SELECT count(*), avg(treatment), avg(visit), avg(conversion), avg(exposure) FROM {rel}"
    ).fetchone()
    cols = column_summary(con, rel, CRITEO_TYPES)
    smds = smd_rows(con, rel, "treatment = 1", [(f, f) for f in CRITEO_FEATURES])
    t_sql = time.perf_counter() - t0

    t0 = time.perf_counter()
    schema = criteo_schema()
    res = con.execute(f"SELECT * FROM {rel}")
    bad = seen = chunks = 0
    while True:
        chunk = res.fetch_df_chunk(vectors_per_chunk)
        if chunk.empty:
            break
        bad += failing_rows(schema, chunk)
        seen += len(chunk)
        chunks += 1
    t_pa = time.perf_counter() - t0
    return {
        "satir": int(agg[0]),
        "p_tedavi": float(agg[1]),
        "sutunlar": cols,
        "smd": smds,
        "pandera_kalan": bad,
        "pandera_gorulen": seen,
        "pandera_parca": chunks,
        "sonuc_genel": {
            "visit": float(agg[2]),
            "conversion": float(agg[3]),
            "exposure": float(agg[4]),
        },
        "sure_sql_s": t_sql,
        "sure_pandera_s": t_pa,
    }


@dataclass(frozen=True)
class Olcut:
    kod: str
    tanim: str
    deger: str
    gecti: bool | None  # None = karar bekliyor


def max_abs_smd(rows: list[dict]) -> tuple[str, float]:
    r = max(rows, key=lambda x: abs(x["smd"]))
    return r["ozellik"], abs(r["smd"])


def _int_tr(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def evaluate(h: dict, c: dict) -> list[Olcut]:
    seg_ok = all(abs(v - SEGMENT_SHARE) <= SEGMENT_TOL for v in h["segment_pay"].values())
    seg_txt = ", ".join(f"{k}: {_fmt(v)}" for k, v in h["segment_pay"].items())
    h_name, h_smd = max_abs_smd(h["smd"]["birlesik_vs_yok"])
    c_name, c_smd = max_abs_smd(c["smd"])
    p_ok = abs(c["p_tedavi"] - CRITEO_P) <= CRITEO_P_TOL
    return [
        Olcut("1a", "Hillstrom satır = 64.000", _int_tr(h["satir"]), h["satir"] == HILL_ROWS),
        Olcut("1b", "Her segment payı 1/3 ± 0,01", seg_txt, seg_ok),
        Olcut("2a", "Criteo satır = 13.979.592", _int_tr(c["satir"]), c["satir"] == CRITEO_ROWS),
        Olcut("2b", "Criteo tedavi oranı 0,846 ± 0,005", _fmt(c["p_tedavi"], 5), p_ok),
        Olcut(
            "3a",
            "Hillstrom Pandera: satırların %100'ü geçer",
            f"kalan satır {h['pandera_kalan']}",
            h["pandera_kalan"] == 0,
        ),
        Olcut(
            "3b",
            "Criteo Pandera: satırların %100'ü geçer",
            f"kalan satır {c['pandera_kalan']}",
            c["pandera_kalan"] == 0,
        ),
        Olcut(
            "4a",
            "Hillstrom \\|SMD\\| < 0,05 (birleşik iki kol vs e-posta yok)",
            f"en büyük {_fmt(h_smd)} ({h_name})",
            h_smd < SMD_MAX,
        ),
        Olcut(
            "4b",
            "Criteo \\|SMD\\| < 0,05 (treatment 1 vs 0)",
            f"en büyük {_fmt(c_smd)} ({c_name})",
            c_smd < SMD_MAX,
        ),
        Olcut("5", "Lisans notu kullanıcı onayı", "kullanıcı onayı bekliyor", None),
    ]


def decision(criteria: list[Olcut]) -> str:
    """Planın durdurma kuralı (bölüm 6 E0 + Kararlar Q9). Ölçüt 5 ayrı karar bekler."""
    failed = {o.kod for o in criteria if o.gecti is False}
    if not failed:
        return "1–4 geçti; ölçüt 5 (lisans) kullanıcı onayı bekliyor. E1 başlamaz, onay beklenir."
    if failed == {"4b"}:
        return (
            "Yalnızca Criteo SMD kaldı: Kararlar Q9 gereği Criteo çıkarılır, "
            "Hillstrom'la devam (kullanıcı onayıyla)."
        )
    return (
        f"Kalan ölçüt(ler): {', '.join(sorted(failed))}. "
        "Durdurma kuralı: modelleme yapılmaz, kullanıcıya sorulur."
    )


def _fmt(x: float, nd: int = 4) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _note(means: str, not_means: str) -> str:
    return f"\n> **Bu tablo ne demek:** {means}\n>\n> **Ne DEMEK DEĞİL:** {not_means}\n"


NOTES = {
    "olcut": (
        "Her E0 ölçütünün, sonuç görülmeden dondurulmuş eşiğe göre geçip geçmediği.",
        "Verinin uplift modellemeye uygun olduğunu ya da E1/E2'nin geçeceğini göstermez; "
        "yalnızca dosyanın belgelenen kaynakla tutarlı olduğunu ve atamanın özelliklerde "
        "dengeli göründüğünü söyler.",
    ),
    "dosya": (
        "Doğrulanan dosyaların kimliği; değerler `configs/ecom_data_source.yaml` ile aynıdır.",
        "Dosyaların içeriğinin doğru ya da eksiksiz olduğunu göstermez; yalnızca aynı dosyanın "
        "kullanıldığını sabitler.",
    ),
    "satir": (
        "Dosyadaki satır sayısı ve tedavi gruplarının payları; Hillstrom'da birincil "
        "karşılaştırmanın tedavi payı $p$.",
        "Payların tasarımla uyumlu olması atamanın rastgele yapıldığını tek başına kanıtlamaz; "
        "SMD tablosu ayrı bir kontroldür.",
    ),
    "sutun": (
        "Okuma şemasında beklenen sütunlar, türleri, eksik değer sayısı ve genel aralık "
        "(tedavi kırılımı yok).",
        "Aralık değerleri bir sonuç ölçümü değildir; sonuç sütunlarının en küçük/en büyük "
        "değeri yalnızca kodlama kontrolüdür.",
    ),
    "pandera": (
        "Tür, eksik değer, ikili (0/1) kodlama, kategori listesi, negatif olmama ve (Criteo) "
        "sonlu değer kurallarını geçemeyen satır sayısı.",
        "Değerlerin anlamca doğru olduğunu göstermez; Criteo özellikleri anonim olduğu için "
        "yalnızca sonlu sayı oldukları denetlenebilir.",
    ),
    "smd_h": (
        "Her özelliğin e-posta alan ve almayan gruplarda ortalama farkı, ortak standart sapma "
        "biriminde; kapı yalnızca birleşik sütuna bakar.",
        "Küçük SMD gözlenmeyen özelliklerde de denge olduğunu göstermez; bilgi sütunları kapı "
        "kararına girmez.",
    ),
    "smd_c": (
        "Anonim özelliklerin tedavi ve kontrol gruplarında ortalama farkı, ortak standart "
        "sapma biriminde.",
        "Criteo birden çok testin birleşimi olduğu için genel denge, testlerin her birinde "
        "denge olduğunu göstermez (test kimliği yok).",
    ),
    "sonuc": (
        "Sonuç değişkenlerinin tüm dosyadaki ortalaması ve kodlama kontrolü.",
        "Tedavi ile kontrol arasındaki fark burada bilerek hesaplanmadı; bu tablo hamlenin "
        "etkisi hakkında hiçbir şey söylemez.",
    ),
    "lisans": (
        "Lisans bilgisinin bulunduğu kaynak ve bu çalışmanın ticari olmayan iç doğrulama "
        "olarak sınırlandığı.",
        "Hukuki değerlendirme değildir; HF etiketi birincil kaynakta doğrulanmadı.",
    ),
}

INTRO = (
    "Üretildi: `python -m credit_coach.ecom.e0_data_check` (dal `ecom-e0-data-check`). "
    "Yalnızca veri doğrulaması: model eğitilmedi, bölme dosyası üretilmedi, test kilidi "
    "oluşturulmadı. Criteo gz açılmadı, DuckDB ile doğrudan okundu.\n\n"
    "Disiplin: sonuç değişkenlerinin (visit, conversion, spend) tedavi/kontrol kırılımı "
    "**hesaplanmadı**; yalnızca genel ortalama, eksik değer ve aralık verildi (E1/E2'nin "
    "sorusu önceden etkilenmesin diye).\n"
)

SMD_INTRO = (
    "Tanım: $\\text{SMD} = (\\bar x_T - \\bar x_C) / \\sqrt{(s_T^2 + s_C^2)/2}$, örneklem "
    "varyansı; kategorikler (`zip_code`, `channel`, `history_segment`) one-hot. Hesap DuckDB "
    "SQL'de yapıldı. Hillstrom'da kapıya giren çift: birleşik iki e-posta kolu vs e-posta "
    "yok (Kararlar Q2); Womens–yok ve Mens–yok yalnızca bilgi.\n"
)


def render(h: dict, c: dict, criteria: list[Olcut], sources: dict, runtime_s: float) -> str:
    L: list[str] = []
    a = L.append
    hs, cs = sources["hillstrom"], sources["criteo_uplift"]
    a("# E0 — Veri ve lisans doğrulaması\n")
    a(INTRO)
    a(
        f"Toplam çalışma süresi: {_fmt(runtime_s, 1)} s (Criteo SQL geçişleri "
        f"{_fmt(c['sure_sql_s'], 1)} s, Criteo Pandera {_fmt(c['sure_pandera_s'], 1)} s).\n"
    )

    a("## Ölçüt tablosu (PLAN bölüm 6, E0; eşikler DONDURULDU)\n")
    a("| Ölçüt | Tanım | Ölçülen | Sonuç |\n|---|---|---|---|")
    for o in criteria:
        if o.gecti is None:
            res = "kullanıcı onayı bekliyor"
        else:
            res = "geçti" if o.gecti else "**kaldı**"
        a(f"| {o.kod} | {o.tanim} | {o.deger} | {res} |")
    a(f"\n**Karar (durdurma kuralı):** {decision(criteria)}\n")
    a(_note(*NOTES["olcut"]))

    a("## Dosyalar\n")
    a("| Set | Dosya | Bayt | SHA-256 |\n|---|---|---|---|")
    a(f"| Hillstrom | `{Path(hs['yol']).name}` | {hs['boyut_bayt']} | `{hs['sha256']}` |")
    a(f"| Criteo | `{Path(cs['yol']).name}` | {cs['gz_boyut_bayt']} | `{cs['gz_sha256']}` (gz) |")
    a(_note(*NOTES["dosya"]))

    a("## Satır sayıları ve tedavi payları\n")
    a("| Set | Satır | Grup | Sayı | Pay |\n|---|---|---|---|---|")
    for s in SEGMENTS:
        n_s, p_s = h["segment_sayi"][s], _fmt(h["segment_pay"][s])
        a(f"| Hillstrom | {h['satir']} | {s} | {n_s} | {p_s} |")
    n_email = h["satir"] - h["segment_sayi"][NO_EMAIL]
    a(
        f"| Hillstrom | {h['satir']} | birleşik e-posta (T=1, Karar Q2) | {n_email} | "
        f"{_fmt(h['p_birlesik'])} |"
    )
    nt = round(c["p_tedavi"] * c["satir"])
    a(f"| Criteo | {c['satir']} | treatment = 1 | {nt} | {_fmt(c['p_tedavi'], 5)} |")
    a(
        f"| Criteo | {c['satir']} | treatment = 0 | {c['satir'] - nt} | "
        f"{_fmt(1 - c['p_tedavi'], 5)} |"
    )
    a("")
    a(
        f"**25M çelişkisi:** İndirilen dosya (`{Path(cs['yol']).name}`, gz SHA-256 Hugging Face "
        f'LFS kaydıyla aynı) {c["satir"]} veri satırı içeriyor. Kaynak kartında geçen "25M" '
        "(TFDS: 25.309.483) bu dosyanın satır sayısı değildir; hangi sürüme ait olduğu bu "
        "dosyadan **doğrulanamadı**.\n"
    )
    a(
        "Not: Plan bölüm 2.1 ve Q2 notu $p$'nin eğitim kümesinde sabitleneceğini söyler; E0'da "
        "bölme yapılmadığı için burada tüm dosyadaki oran verilir, eğitim kümesindeki değer "
        "E1/E2'de bölmeden sonra sabitlenir.\n"
    )
    a(_note(*NOTES["satir"]))

    for name, s in (("Hillstrom", h), ("Criteo", c)):
        a(f"## Sütunlar — {name}\n")
        a("| Sütun | DuckDB türü | Eksik | Min | Maks |\n|---|---|---|---|---|")
        for r in s["sutunlar"]:
            a(f"| `{r['sutun']}` | {r['tur']} | {r['eksik']} | {r['min']} | {r['max']} |")
        a(_note(*NOTES["sutun"]))

    a("## Pandera şeması\n")
    a("| Set | Satır | Şemayı geçemeyen satır | Yöntem |\n|---|---|---|---|")
    a(
        f"| Hillstrom | {h['satir']} | {h['pandera_kalan']} | tüm tablo tek seferde "
        "(`strict`, `ordered`) |"
    )
    a(
        f"| Criteo | {c['pandera_gorulen']} | {c['pandera_kalan']} | DuckDB'den "
        f"{c['pandera_parca']} parça (~1 M satır), her parça ayrı doğrulandı; tamamı "
        "belleğe alınmadı |"
    )
    a(_note(*NOTES["pandera"]))

    a("## Denge (SMD)\n")
    a(SMD_INTRO)
    a("### Hillstrom\n")
    a(
        "| Özellik | Ort. T (birleşik) | Ort. C | SMD birleşik (kapı) | SMD Womens–yok (bilgi) "
        "| SMD Mens–yok (bilgi) |\n|---|---|---|---|---|---|"
    )
    hb, hw, hm = (h["smd"][k] for k in ("birlesik_vs_yok", "womens_vs_yok", "mens_vs_yok"))
    for b, w, m in zip(hb, hw, hm, strict=True):
        vals = [b["ort_T"], b["ort_C"], b["smd"], w["smd"], m["smd"]]
        a(f"| `{b['ozellik']}` | " + " | ".join(_fmt(v) for v in vals) + " |")
    a(_note(*NOTES["smd_h"]))
    a("### Criteo\n")
    a("| Özellik | Ort. T | Ort. C | SMD |\n|---|---|---|---|")
    for r in c["smd"]:
        a(f"| `{r['ozellik']}` | {_fmt(r['ort_T'])} | {_fmt(r['ort_C'])} | {_fmt(r['smd'])} |")
    a("\n`exposure` atamadan sonra oluştuğu için özellik değildir; SMD'ye girmez.\n")
    n1 = round(c["p_tedavi"] * c["satir"])
    se = math.sqrt(1 / n1 + 1 / (c["satir"] - n1))
    c_name, c_smd = max_abs_smd(c["smd"])
    a(
        f"**Gözlem (karar değişmez):** En büyük \\|SMD\\| {_fmt(c_smd)} (`{c_name}`) eşiğe "
        f"(0,05) yakın. Bu örneklem büyüklüğünde SMD'nin rastgele atama altındaki yaklaşık "
        f"standart hatası $\\sqrt{{1/n_T + 1/n_C}} \\approx$ {_fmt(se)}; birkaç özellikteki "
        "fark bunun çok üstünde. Nedeni (ör. birden çok testin birleşimi ya da eşit olmayan alt "
        "örnekleme) bu dosyadan **doğrulanamadı**. Kapı ölçütü dondurulmuş eşiktir; bu gözlem "
        "E2 raporunda sınır olarak yazılır.\n"
    )
    a(_note(*NOTES["smd_c"]))

    a("## Sonuç değişkenleri — yalnızca genel\n")
    a("| Set | Değişken | Genel ortalama | Eksik | Min | Maks |\n|---|---|---|---|---|---|")
    for k, v in h["sonuc_genel"].items():
        a(f"| Hillstrom | `{k}` | {_fmt(v['ortalama'])} | {v['eksik']} | {v['min']} | {v['max']} |")
    cmap = {r["sutun"]: r for r in c["sutunlar"]}
    for k, v in c["sonuc_genel"].items():
        r = cmap[k]
        a(f"| Criteo | `{k}` | {_fmt(v, 5)} | {r['eksik']} | {r['min']} | {r['max']} |")
    a(_note(*NOTES["sonuc"]))

    a("## Lisans (ölçüt 5)\n")
    a("| Set | Not | Durum |\n|---|---|---|")
    a(
        f"| Hillstrom | {hs['lisans']} (kaynak sayfada şart yok); kullanım: {hs['kullanim']} "
        "| kullanıcı onayı bekliyor |"
    )
    a(
        f"| Criteo | {cs['lisans']}; kullanım: {cs['kullanim']}; atıf: {cs['atif']} "
        "| kullanıcı onayı bekliyor |"
    )
    a(_note(*NOTES["lisans"]))
    return "\n".join(L) + "\n"


def main() -> int:
    t0 = time.perf_counter()
    sources = yaml.safe_load(SOURCE_PATH.read_text())
    h = check_hillstrom(Path(sources["hillstrom"]["yol"]))
    c = check_criteo(Path(sources["criteo_uplift"]["yol"]))
    criteria = evaluate(h, c)
    runtime = time.perf_counter() - t0
    REPORT_PATH.write_text(render(h, c, criteria, sources, runtime), encoding="utf-8")
    hn, hv = max_abs_smd(h["smd"]["birlesik_vs_yok"])
    cn, cv = max_abs_smd(c["smd"])
    summary = {
        "sure_s": round(runtime, 1),
        "hillstrom_satir": h["satir"],
        "hillstrom_p_birlesik": h["p_birlesik"],
        "criteo_satir": c["satir"],
        "criteo_p": c["p_tedavi"],
        "max_smd_hillstrom": [hn, hv],
        "max_smd_criteo": [cn, cv],
        "olcutler": {o.kod: o.gecti for o in criteria},
        "karar": decision(criteria),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if all(o.gecti is not False for o in criteria) else 1


if __name__ == "__main__":
    sys.exit(main())
