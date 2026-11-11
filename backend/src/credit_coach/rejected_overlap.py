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
from credit_coach.rejected_scale import archive_documents, monthly, observations
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


def render(res: dict[str, dict], sup: Support, src: dict, scores: dict | None = None) -> str:
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
    if scores is not None:
        L += render_ek(res, scores)
    return "\n".join(L) + "\n"


def _kutu(mean: str, not_mean: str) -> list[str]:
    return ["", f"Ne demek: {mean}", "", f"Ne DEMEK DEĞİL: {not_mean}", ""]


def _obs_line(label: str, o: dict) -> str:
    def span(v):
        return "yok" if v is None else f"ilk {v[0]}, son {v[1]}, {v[2]} ay"

    return (
        f"- {label}: {o['ay_sayisi']} ay; genel min {o['genel_min']:g}, genel maks "
        f"{o['genel_maks']:g}; aylık maks 850'yi aşan: {span(o['maks_850_ustu'])}; "
        f"aylık min 0 olan: {span(o['min_sifir'])}; "
        f"boş oranı %50'yi aşan: {span(o['bos_50_ustu'])}."
    )


def render_ek(res: dict[str, dict], scores: dict) -> list[str]:
    rj, ac = scores["aylar"]["reddedilen"], {r.ay: r for r in scores["aylar"]["kabul"]}
    f = lambda v: "-" if v is None else f"{v:g}"  # noqa: E731
    L = [
        "",
        "## Risk_Score ölçek kontrolü (aya göre)",
        "",
        "Reddedilen: Risk_Score, ay = 'Application Date' ayı. Kabul: fico_range_low, ay = "
        "'issue_d' ayı (kabul dosyasında başvuru tarihi yok). Boş = değer yok.",
        "",
        "| Ay | Red başvuru | Red boş % | Red min | Red medyan | Red maks | Kabul kayıt "
        "| Kabul boş % | Kabul min | Kabul medyan | Kabul maks |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rj:
        a = ac.get(r.ay)
        acc = (
            f"| {a.n:,} | {a.bos_yuzde:g} | {f(a.min)} | {f(a.medyan)} | {f(a.maks)} |"
            if a
            else "| - | - | - | - | - |"
        )
        L.append(
            f"| {r.ay} | {r.n:,} | {r.bos_yuzde:g} | {f(r.min)} | {f(r.medyan)} | {f(r.maks)} "
            + acc
        )
    L += _kutu(
        "her satır, o ayın skor değerlerinin en küçüğü, ortancası, en büyüğü ve boş payıdır.",
        "iki dosyanın skorlarının aynı ölçek olduğunun ya da olmadığının kanıtı değildir; "
        "kabul tarafındaki ay, başvuru ayı değil kredinin açıldığı aydır.",
    )
    L += ["Dağılımda gözlenenler (eşikler satırda yazılı):", ""]
    L += [_obs_line("Reddedilen Risk_Score", scores["gozlem"]["reddedilen"])]
    L += [_obs_line("Kabul fico_range_low", scores["gozlem"]["kabul"])]
    belge = scores["belgeler"]
    L += [
        "",
        "Arşiv klasöründe veri dosyaları dışındaki girdiler: "
        + (", ".join(belge) if belge else "yok")
        + ("." if belge else ". Skor kaynağını ya da ölçeğini tanımlayan bir belge bulunmadı."),
    ]
    L += _kutu(
        "satırlar yukarıdaki tablodan sayılan olgulardır.",
        "bir ölçek kırılmasının nedeni, skor kaynağı ya da eşleme kararı değildir; eşleme "
        "'işaretli' kalır.",
    )

    fields = [f_ for f_ in FIELDS if f_.ana]
    L += [
        "## Dönem bazında destek dışı oranı (2012-2013 ve 2014-2015)",
        "",
        "| Alan | Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı "
        "| Destek dışı oranı |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for fld in fields:
        for k in HALVES:
            r = res[k]
            ev, out = r[f"e_{fld.alan}"], r[f"x_{fld.alan}"]
            L.append(
                f"| {fld.alan} | {k} | {r['n']:,} | {r['n'] - ev:,} | {ev:,} | {ev - out:,} "
                f"| {out:,} | {_pct(out, ev)} |"
            )
    L += _kutu(
        "her satır, o dönemde o alanın değeri olan reddedilen başvurular içinde destek dışı "
        "olanların sayısı ve oranıdır.",
        "dönemler arası fark için bir neden değildir; skor alanında dönemler arası boş payı "
        "farklıdır, oran yalnızca değeri olan satırlar içindir.",
    )

    def joint(title, kind, note_mean, note_not):
        rows = [
            f"## {title}",
            "",
            "| Dönem | Başvuru | Değerlendirilen | Destek dışı | Oran |",
            "|---|---|---|---|---|",
        ]
        for k in HALVES:
            r = res[k]
            e, x = r[f"e_{kind}"], r[f"x_{kind}"]
            rows.append(f"| {k} | {r['n']:,} | {e:,} | {x:,} | {_pct(x, e)} |")
        return rows + _kutu(note_mean, note_not)

    L += joint(
        "Ortak sayım: yalnızca dti ve emp_length, en az biri değerlendirilebilen",
        "any2",
        "paydada dti ya da emp_length alanlarından en az biri dolu olan başvurular; sayı "
        "bunlardan en az birinde destek dışı olanlardır.",
        "risk skoru ve talep tutarı bu sayıma girmez; çok boyutlu destek değildir.",
    )
    L += joint(
        "Ortak sayım: yalnızca dti ve emp_length, ikisi de dolu",
        "all2",
        "paydada dti ve emp_length alanlarının ikisi de dolu olan başvurular; sayı bunlardan "
        "en az birinde destek dışı olanlardır.",
        "risk skoru ve talep tutarı bu sayıma girmez; çok boyutlu destek değildir.",
    )
    L += joint(
        "Ortak sayım: tüm ana alanlar (dti, risk_skoru, calisma_suresi, talep_tutari), "
        "en az biri değerlendirilebilen",
        "any",
        "paydada dört alandan en az biri dolu olan başvurular; sayı bunlardan en az birinde "
        "destek dışı olanlardır.",
        "risk skoru eşlemesi 'işaretli'dir; bu sayım o eşlemenin doğru olduğunu varsaymaz ya da "
        "göstermez.",
    )
    L += joint(
        "Ortak sayım: tüm ana alanlar, dördü de dolu",
        "all",
        "paydada dört alanın dördü de dolu olan başvurular; sayı bunlardan en az birinde destek "
        "dışı olanlardır.",
        "dolu olma koşulu, 2014-2015 için skor alanının boş payını dışarıda bırakır; temsil "
        "ettiği başvuru kümesi 'en az biri' sayımından farklıdır.",
    )
    return L


def main() -> int:
    src = load_sources()
    sup = load_support()
    rej = rejected_path(src)
    res = aggregate(rej, sup)
    acc = Path(src["lc_reddedilen"]["yan_dosya_accepted"]["yol"])
    aylar = monthly(rej, acc)
    scores = {
        "aylar": aylar,
        "gozlem": {k: observations(v) for k, v in aylar.items()},
        "belgeler": archive_documents(acc.parents[1]),
    }
    text = render(res, sup, src, scores)
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
