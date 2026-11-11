"""Overlap of LendingClub REJECTED applications with the training support (configs/support.yaml).

For the fields both files share, count how many rejected applications fall inside / outside the
train min/max (numeric) or value set (categorical). No labels, no model, no test split: the only
inputs are the rejected file (configs/data_source.yaml) and support.yaml.

Usage: python -m credit_coach.rejected_overlap   (writes docs/rejected_overlap.md)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb

from credit_coach.data_source import ROOT, load_sources, rejected_path
from credit_coach.support import Support, load_support

REPORT = ROOT / "docs" / "rejected_overlap.md"
YEARS = (2012, 2013, 2014, 2015)
POOLED = "2012-2015"
HALVES = ("2012-2013", "2014-2015")
PAIR = ("dti", "calisma_suresi")  # second joint count: these two fields only
ALL = "tümü"


@dataclass(frozen=True)
class Field:
    alan: str  # key used in this report
    red_sutun: str  # column in the rejected file
    destek: str  # feature in support.yaml
    tur: str  # "sayisal" | "kategorik"
    guven: str  # "yüksek" | "orta" | "işaretli"
    not_: str
    ana: bool = True  # False = sensitivity row, not part of the joint count


FIELDS = (
    Field(
        "dti",
        "Debt-To-Income Ratio",
        "dti",
        "sayisal",
        "orta",
        "'%' atılır; yüzde ölçeği (0-100). Kabul edilenlerdeki dti ile aynı tanım olduğu "
        "doğrulanmadı.",
    ),
    Field(
        "risk_skoru",
        "Risk_Score",
        "fico_range_low",
        "sayisal",
        "işaretli",
        "Tek puan, destekte ise aralığın alt ucu. Kaynak skor (FICO / Vantage) dosyada "
        "belirtilmiyor. EMİN DEĞİLİM.",
    ),
    Field(
        "calisma_suresi",
        "Employment Length",
        "emp_length",
        "kategorik",
        "yüksek",
        "Değer kümesi aynı metin kalıbını kullanıyor; boşluk kırpılır.",
    ),
    Field(
        "talep_tutari",
        "Amount Requested",
        "loan_amnt",
        "sayisal",
        "orta",
        "Talep edilen tutar; destekte onaylanan tutar. Aynı büyüklük değil.",
    ),
    Field(
        "risk_skoru_alt",
        "Risk_Score",
        "fico_range_high",
        "sayisal",
        "işaretli",
        "Duyarlılık satırı: aynı skor, aralığın üst ucuna karşı. Ortak sayıma girmez.",
        ana=False,
    ),
)
NOT_MAPPED = (
    ("Loan Title", "Serbest metin; destekteki 'purpose' kümesiyle eşleşmiyor."),
    ("Zip Code", "Destekte karşılığı yok."),
    ("State", "Destekte karşılığı yok."),
    ("Policy Code", "Destekte karşılığı yok."),
    ("Application Date", "Yalnızca yıl bölümü için kullanılır; destek alanı değil."),
)


def _sql_value(f: Field) -> str:
    c = f'"{f.red_sutun}"'
    if f.alan == "dti":
        return f"try_cast(replace({c}, '%', '') as double)"
    if f.tur == "sayisal":
        return f"try_cast({c} as double)"
    return f"nullif(trim({c}), '')"


def _sql_out(f: Field, sup: Support) -> str:
    v = f"_{f.alan}"
    if f.tur == "sayisal":
        lo, hi = sup.sayisal[f.destek]
        return (
            f"case when {v} is null then null when {v} < {lo!r} or {v} > {hi!r} then 1 else 0 end"
        )
    vals = ", ".join(
        "'" + s.strip().replace("'", "''") + "'" for s in sorted(sup.kategorik[f.destek])
    )
    return f"case when {v} is null then null when {v} in ({vals}) then 0 else 1 end"


def aggregate(csv: Path, sup: Support) -> dict[str, dict]:
    """Counts per period key (str year, POOLED, ALL): n, per field eval/out, joint counts."""
    con = duckdb.connect()
    cols = ", ".join(f"{_sql_value(f)} as _{f.alan}" for f in FIELDS)
    con.execute(
        f'create view r as select cast(substr("Application Date", 1, 4) as int) as yil, {cols} '
        f"from read_csv('{csv}', header=true, all_varchar=true)"
    )
    outs = ", ".join(f"{_sql_out(f, sup)} as o_{f.alan}" for f in FIELDS)
    con.execute(f"create view o as select yil, {outs} from r")
    main = [f"o_{f.alan}" for f in FIELDS if f.ana]
    any_eval = " or ".join(f"{c} is not null" for c in main)
    all_eval = " and ".join(f"{c} is not null" for c in main)
    any_out = " or ".join(f"{c} = 1" for c in main)
    pair = [f"o_{a}" for a in PAIR]
    sel = ["yil", "count(*) as n"]
    for f in FIELDS:
        sel += [f"count(o_{f.alan}) as e_{f.alan}", f"coalesce(sum(o_{f.alan}), 0) as x_{f.alan}"]
    sel += [
        f"count(*) filter (where {any_eval}) as e_any",
        f"count(*) filter (where {any_out}) as x_any",
        f"count(*) filter (where {all_eval}) as e_all",
        f"count(*) filter (where ({all_eval}) and ({any_out})) as x_all",
        f"count(*) filter (where {' or '.join(c + ' is not null' for c in pair)}) as e_any2",
        f"count(*) filter (where {' or '.join(c + ' = 1' for c in pair)}) as x_any2",
        f"count(*) filter (where {' and '.join(c + ' is not null' for c in pair)}) as e_all2",
        f"count(*) filter (where ({' and '.join(c + ' is not null' for c in pair)}) "
        f"and ({' or '.join(c + ' = 1' for c in pair)})) as x_all2",
    ]
    cur = con.execute(f"select {', '.join(sel)} from o group by yil order by yil")
    names = [d[0] for d in cur.description]
    by_year = {
        row[0]: dict(zip(names[1:], (int(v) for v in row[1:]), strict=True))
        for row in cur.fetchall()
    }
    res: dict[str, dict] = {str(y): by_year[y] for y in YEARS if y in by_year}
    groups = (
        (HALVES[0], [y for y in (2012, 2013) if y in by_year]),
        (HALVES[1], [y for y in (2014, 2015) if y in by_year]),
        (POOLED, [y for y in YEARS if y in by_year]),
        (ALL, list(by_year)),
    )
    for key, years in groups:
        res[key] = {k: sum(by_year[y][k] for y in years) for k in names[1:]}
    return res


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "-"


def render(res: dict[str, dict], sup: Support, src: dict) -> str:
    e = src["lc_reddedilen"]
    periods = [str(y) for y in YEARS] + [POOLED, ALL]
    L = [
        "# Reddedilen başvurular ve eğitim desteği: örtüşme",
        "",
        f"Kaynak: {e['ad']} (yol ve sha256: configs/data_source.yaml; sha256 {e['sha256']}).",
        f"Destek: configs/support.yaml (yalnızca eğitim dilimi; içerik hash {sup.sha256}).",
        "Etiket, model ve test dilimi kullanılmadı.",
        "",
        "## Ne demek",
        "",
        "- Her oran, reddedilen başvurularda eşlenen bir alanın değerinin eğitim min/max "
        "aralığında (kategorikte eğitimde görülen değer kümesinde) olup olmadığının sayımıdır.",
        "- Boş değer ne içeride ne dışarıdadır; paydaya girmez, boş sayısı ayrı verilir.",
        "- Yıl, 'Application Date' alanının yılıdır.",
        "",
        "## Ne DEMEK DEĞİL",
        "",
        "- Reddin nedeni değildir.",
        "- Modelin bu başvurularda doğru çalışacağı ya da çalışmayacağı anlamına gelmez.",
        "- Çok boyutlu destek değildir; alanlar tek tek aralığa bakar.",
        "- Alan tanımlarının iki dosyada aynı olduğu kanıtlanmadı; 'güven' sütunu eşlemenin "
        "durumunu gösterir.",
        "- Kabul edilen başvurularla bir karşılaştırma değildir.",
        "",
        "## Alan eşlemesi",
        "",
        "| Alan | Reddedilen sütun | Destek özelliği | Tür | Destek aralığı / küme | Güven | Not |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in FIELDS:
        rng = (
            "{:g} - {:g}".format(*sup.sayisal[f.destek])
            if f.tur == "sayisal"
            else ", ".join(sorted(s.strip() for s in sup.kategorik[f.destek]))
        )
        L.append(
            f"| {f.alan} | {f.red_sutun} | {f.destek} | {f.tur} | {rng} | {f.guven} | {f.not_} |"
        )
    L += ["", "Eşlenmeyen sütunlar:", ""]
    L += [f"- {c}: {why}" for c, why in NOT_MAPPED]

    L += ["", "## Alan başına destek içi / destek dışı", ""]
    for f in FIELDS:
        L += [
            f"### {f.alan}" + ("" if f.ana else " (duyarlılık)"),
            "",
            "| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı "
            "| Destek dışı oranı |",
            "|---|---|---|---|---|---|---|",
        ]
        for k in periods:
            r = res.get(k)
            if not r:
                continue
            ev, out = r[f"e_{f.alan}"], r[f"x_{f.alan}"]
            L.append(
                f"| {k} | {r['n']:,} | {r['n'] - ev:,} | {ev:,} | {ev - out:,} | {out:,} "
                f"| {_pct(out, ev)} |"
            )
        L.append("")

    main = [f.alan for f in FIELDS if f.ana]
    L += [
        "## Ortak sayım (ana alanlar: " + ", ".join(main) + ")",
        "",
        "'En az bir alanda destek dışı': en az bir alanı değerlendirilebilen başvurular içinde. "
        "'Tüm alanlar dolu': dört alanı da dolu olan başvurular içinde.",
        "",
        "| Dönem | Başvuru | En az bir alan değerlendirilen | En az bir alanda destek dışı | oran "
        "| Tüm alanlar dolu | Bunlardan destek dışı | oran |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for k in periods:
        r = res.get(k)
        if r:
            L.append(
                f"| {k} | {r['n']:,} | {r['e_any']:,} | {r['x_any']:,} "
                f"| {_pct(r['x_any'], r['e_any'])} "
                f"| {r['e_all']:,} | {r['x_all']:,} | {_pct(r['x_all'], r['e_all'])} |"
            )
    return "\n".join(L) + "\n"


def main() -> int:
    src = load_sources()
    sup = load_support()
    res = aggregate(rejected_path(src), sup)
    text = render(res, sup, src)
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
