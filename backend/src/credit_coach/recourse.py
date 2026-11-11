"""Demo v0 recourse engine (ADR-006): full scan of <= max_eylem actions, deterministic.

Pure given (basvuru, scorer, policy, support, catalog, config). No clock, randomness or file
access in the selection path. Effects are computed only through the scorer (evidence class M).

Acceptance of a plan (all must hold):
  applicable, no level invalidated by the level ladder, result inside the training support,
  p_high_after < threshold - delta, p_after <= p_before, decide_with_support(result) == APPROVED.
Per path type (customer / hybrid / institution) the cheapest valid plan is shown; paths are
never ranked against each other.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, NamedTuple, Protocol

import yaml
from pydantic import BaseModel, ConfigDict

from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.features import MANIFEST_PATH
from credit_coach.policy import Policy
from credit_coach.support import Support, violations

DEMO_CATALOG_PATH = MANIFEST_PATH.parent / "catalog" / "demo_v0.yaml"
PATH_ORDER = ("customer", "hybrid", "institution")  # display order only, never a ranking


class Skor(NamedTuple):
    p_low: float
    p_point: float
    p_high: float
    ham_skor: float


class Scorer(Protocol):
    """Scores full feature vectors (dicts of the allowed features). Must be deterministic."""

    def skorla_toplu(self, vektorler: Sequence[Mapping[str, Any]], tarih: Any) -> list[Skor]: ...


Dayaniklilik = Literal["GUCLU", "KOSULLU", "ZAYIF"]  # closed set of resilience labels


class LevelStatus(StrEnum):
    UYGULANAMAZ = "UYGULANAMAZ"
    SEVIYE_GECERSIZ = "SEVIYE_GECERSIZ"
    DESTEK_DISI = "DESTEK_DISI"
    ETKI_YETERSIZ = "ETKI_YETERSIZ"
    GECERLI = "GECERLI"


# ---- configuration ---------------------------------------------------------------------


@dataclass(frozen=True)
class Seviye:
    id: str
    hedef: float  # revol_util target (percent) or loan multiplier
    sure: tuple[int, int]


@dataclass(frozen=True)
class Eylem:
    id: str
    aile: str
    sahip: str
    seviyeler: tuple[Seviye, ...]  # shallow -> deep


@dataclass(frozen=True)
class Katalog:
    eylemler: tuple[Eylem, ...]
    min_odeme_orani: float
    min_kredi_tutari: float
    max_eylem: int
    delta: float
    dti_guncelle: bool
    raw: Mapping[str, Any]
    guclu_en_fazla: float = 0.50  # varsayım: min_phi <= this -> GUCLU
    kosullu_en_fazla: float = 0.75  # varsayım: min_phi <= this -> KOSULLU, above -> ZAYIF


def load_demo_catalog(path: Path = DEMO_CATALOG_PATH) -> Katalog:
    raw = yaml.safe_load(path.read_text())
    eylemler = []
    for e in raw["eylemler"]:
        key = "revol_util_hedef" if e["id"] == "revolving_paydown" else "loan_amnt_carpan"
        eylemler.append(
            Eylem(
                e["id"],
                e["aile"],
                e["sahip"],
                tuple(
                    Seviye(s["id"], float(s[key]), tuple(s["sure_hafta"])) for s in e["seviyeler"]
                ),
            )
        )
    return Katalog(
        eylemler=tuple(eylemler),
        min_odeme_orani=float(raw["min_odeme_orani"]["deger"]),
        min_kredi_tutari=float(raw["min_kredi_tutari"]["deger"]),
        max_eylem=int(raw["max_eylem"]),
        delta=float(raw["delta"]["deger"]),
        dti_guncelle=bool(raw["dti_guncelle"]),
        raw=raw,
        guclu_en_fazla=float(raw["dayaniklilik"]["guclu_en_fazla"]),
        kosullu_en_fazla=float(raw["dayaniklilik"]["kosullu_en_fazla"]),
    )


# ---- effects ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Etki:
    """Result of one (action, level) on a vector."""

    guncel: Mapping[str, Any]  # changed fields only
    maliyet_usd: float
    kirpildi: tuple[str, ...]


def _revolving(b: Mapping[str, Any], hedef: float, k: Katalog) -> Etki | None:
    u, bal = b.get("revol_util"), b.get("revol_bal")
    if u is None or bal is None or not (u > hedef and bal > 0 and u > 0):
        return None
    yeni_bal = bal * hedef / u
    delta = bal - yeni_bal
    guncel: dict[str, Any] = {"revol_util": float(hedef), "revol_bal": yeni_bal}
    kirpildi: list[str] = []

    def dusur(ad: str, miktar: float) -> None:
        v = b.get(ad)
        if v is None:
            return
        yeni = v - miktar
        if yeni < 0:
            kirpildi.append(ad)
            yeni = 0.0
        guncel[ad] = yeni

    dusur("total_bal_ex_mort", delta)
    dusur("tot_cur_bal", delta)
    inc = b.get("annual_inc")
    if k.dti_guncelle and b.get("dti") is not None and inc is not None and inc > 0:
        dusur_dti = 100.0 * k.min_odeme_orani * delta / (inc / 12.0)
        yeni = b["dti"] - dusur_dti
        if yeni < 0:
            kirpildi.append("dti")
            yeni = 0.0
        guncel["dti"] = yeni
    return Etki(guncel, float(delta), tuple(sorted(kirpildi)))


def _loan(b: Mapping[str, Any], carpan: float, k: Katalog) -> Etki | None:
    ln = b.get("loan_amnt")
    if ln is None:
        return None
    yeni = float(round(ln * carpan / 100.0) * 100)
    if yeni < k.min_kredi_tutari or yeni >= ln:
        return None
    return Etki({"loan_amnt": yeni}, float(ln - yeni), ())


def etki(eylem: Eylem, seviye: Seviye, b: Mapping[str, Any], k: Katalog) -> Etki | None:
    if eylem.id == "revolving_paydown":
        return _revolving(b, seviye.hedef, k)
    if eylem.id == "loan_amount_reduction":
        return _loan(b, seviye.hedef, k)
    raise ValueError(f"unknown action {eylem.id}")


# ---- signature and path type -----------------------------------------------------------


def imza(eylem_idleri: Sequence[str], k: Katalog) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(owner set, action families): structure only, independent of scores, PD and levels."""
    by_id = {e.id: e for e in k.eylemler}
    owners = sorted({by_id[i].sahip for i in eylem_idleri})
    families = sorted({by_id[i].aile for i in eylem_idleri})
    return tuple(owners), tuple(families)


def yol_tipi(sig: tuple[tuple[str, ...], tuple[str, ...]]) -> str:
    owners = sig[0]
    if owners == ("customer",):
        return "customer"
    if owners == ("institution",):
        return "institution"
    return "hybrid"


# ---- candidates ------------------------------------------------------------------------


@dataclass(frozen=True)
class Aday:
    plan_id: str
    eylemler: tuple[tuple[str, str], ...]  # (action id, level id), sorted by action id
    vektor: Mapping[str, Any]
    maliyet_usd: float
    sure: tuple[int, int]
    kirpildi: tuple[str, ...]


def _combine(parts: Sequence[tuple[Eylem, Seviye, Etki]], b: Mapping[str, Any]) -> Aday:
    parts = sorted(parts, key=lambda p: p[0].id)
    vektor = dict(b)
    for _e, _s, et in parts:
        vektor.update(et.guncel)
    pairs = tuple((e.id, s.id) for e, s, _ in parts)
    return Aday(
        plan_id="+".join(f"{a}:{s}" for a, s in pairs),
        eylemler=pairs,
        vektor=vektor,
        maliyet_usd=float(sum(et.maliyet_usd for _, _, et in parts)),
        sure=(max(s.sure[0] for _, s, _ in parts), max(s.sure[1] for _, s, _ in parts)),
        kirpildi=tuple(sorted({x for _, _, et in parts for x in et.kirpildi})),
    )


def uygulanabilir_tekler(b: Mapping[str, Any], k: Katalog):
    """[(Eylem, Seviye, Etki|None)] for every level, shallow -> deep."""
    return [(e, s, etki(e, s, b, k)) for e in k.eylemler for s in e.seviyeler]


def adaylar(
    b: Mapping[str, Any], k: Katalog, gecersiz_seviyeler: frozenset[tuple[str, str]] = frozenset()
) -> list[Aday]:
    """All plans of 1..max_eylem actions (one level each) built from applicable, not-invalid
    levels. Order is deterministic (by plan id)."""
    tekler = [
        (e, s, et)
        for e, s, et in uygulanabilir_tekler(b, k)
        if et is not None and (e.id, s.id) not in gecersiz_seviyeler
    ]
    out: list[Aday] = []
    by_action: dict[str, list] = {}
    for t in tekler:
        by_action.setdefault(t[0].id, []).append(t)
    ids = sorted(by_action)
    for n in range(1, min(k.max_eylem, len(ids)) + 1):
        for combo in itertools.combinations(ids, n):
            for choice in itertools.product(*(by_action[i] for i in combo)):
                out.append(_combine(choice, b))
    return sorted(out, key=lambda a: a.plan_id)


# ---- result types ----------------------------------------------------------------------


class YolPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    yol_tipi: str
    imza: tuple[tuple[str, ...], tuple[str, ...]]
    plan_id: str
    eylemler: tuple[tuple[str, str], ...]
    maliyet_usd: float  # varsayım: nakit çıkışı veya karşılanmayan talep, 1 USD = 1 USD
    maliyet_etiketi: Literal["varsayım"] = "varsayım"
    min_phi: float  # share of the predicted drop needed, in [0, 1] ((p_before - cut) / Delta)
    dayaniklilik: Dayaniklilik
    dayaniklilik_etiketi: Literal["varsayım"] = "varsayım"  # the thresholds are assumptions
    sure_hafta: tuple[int, int]  # varsayım
    sure_etiketi: Literal["varsayım"] = "varsayım"
    p_low: float
    p_point: float
    p_high: float
    kirpildi: tuple[str, ...]


class PlanVar(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    durum: Literal["PLAN"] = "PLAN"
    yollar: tuple[YolPlan, ...]  # display order only; paths are not ranked


class PlanYok(BaseModel):
    """No plan. Carries NO plan, path, cost, duration or after-values: only closed-list
    binding constraints and today's measured distance to the threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    durum: Literal["PLAN_YOK"] = "PLAN_YOK"
    bagli_kisitlar: tuple[tuple[str, tuple[str, ...]], ...]  # (action id | BASVURU, reasons)
    esige_uzaklik: float | None  # current p_point - threshold; None when not scored


class PlanGereksiz(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    durum: Literal["PLAN_GEREKSIZ"] = "PLAN_GEREKSIZ"


@dataclass(frozen=True)
class Sonuc:
    sonuc: PlanVar | PlanYok | PlanGereksiz
    teshis: Mapping[tuple[str, str], LevelStatus]  # per single (action, level)
    gecerli: tuple[tuple[Aday, Skor], ...]  # every valid plan (all paths), for audits


def dayaniklilik_etiketi(min_phi: float, k: Katalog) -> Dayaniklilik:
    """GUCLU if min_phi <= guclu_en_fazla, KOSULLU if <= kosullu_en_fazla, else ZAYIF.
    Thresholds come from the catalog config and are assumptions."""
    if not 0.0 < k.guclu_en_fazla < k.kosullu_en_fazla <= 1.0:
        raise ValueError("dayaniklilik thresholds must satisfy 0 < guclu < kosullu <= 1")
    if min_phi <= k.guclu_en_fazla:
        return "GUCLU"
    if min_phi <= k.kosullu_en_fazla:
        return "KOSULLU"
    return "ZAYIF"


def kesim_noktasi(thr: float, delta: float, band: float) -> float:
    """Validity cut: a plan must end below threshold - max(delta, band) (R2 covers the band)."""
    return thr - max(delta, band)


def min_phi_formul(p_before: float, p_after: float, kesim: float) -> float | None:
    """Smallest share of the model-predicted risk drop that must materialise for the plan to
    reach the cut: (p_before - cut) / Delta, Delta = p_before - p_after (all p_high). None when
    the plan predicts no drop. Single source: the effect-share report uses the same formula."""
    dp = p_before - p_after
    if dp <= 0:
        return None
    return (p_before - kesim) / dp


def _plan_key(a: Aday) -> tuple:
    return (a.maliyet_usd, a.sure[1], len(a.eylemler), a.plan_id)


def _approved(vektor: Mapping[str, Any], s: Skor, politika: Policy, support: Support) -> bool:
    g = parse_input(
        {
            "basvuru": dict(vektor),
            "p_low": s.p_low,
            "p_point": s.p_point,
            "p_high": s.p_high,
            "ham_skor": s.ham_skor,
            "politika_surumu": politika.surum,
            "plan_available": None,
        }
    )
    return decide_with_support(g, politika, support).dis_durum is OuterStatus.APPROVED


def sec(
    b: Mapping[str, Any],
    baz: Skor,
    tekler: Mapping[tuple[str, str], Skor],
    cift_skorlari: Mapping[str, Skor],
    politika: Policy,
    support: Support,
    k: Katalog,
    delta: float | None = None,
) -> Sonuc:
    """Selection from already computed scores (no scorer inside, pure).

    `tekler`: score of each applicable single (action, level); `cift_skorlari`: score of every
    candidate plan id built by `adaylar` (singles included).
    """
    d = k.delta if delta is None else delta
    thr = politika.onay_esigi
    if violations(b, support):
        return Sonuc(
            PlanYok(bagli_kisitlar=(("BASVURU", ("DESTEK_DISI",)),), esige_uzaklik=None), {}, ()
        )
    if _approved(b, baz, politika, support):
        return Sonuc(PlanGereksiz(), {}, ())

    teshis: dict[tuple[str, str], LevelStatus] = {}
    gecersiz: set[tuple[str, str]] = set()
    for e in k.eylemler:
        onceki: float | None = None  # p_high of the nearest shallower applicable level
        for s in e.seviyeler:
            et = etki(e, s, b, k)
            key = (e.id, s.id)
            if et is None:
                teshis[key] = LevelStatus.UYGULANAMAZ
                continue
            sk = tekler[key]
            if sk.p_high > baz.p_high or (onceki is not None and sk.p_high > onceki):
                teshis[key] = LevelStatus.SEVIYE_GECERSIZ
                gecersiz.add(key)
                continue  # invalid level does not move the ladder reference
            onceki = sk.p_high
            vektor = {**b, **et.guncel}
            if violations(vektor, support):
                teshis[key] = LevelStatus.DESTEK_DISI
            elif not (sk.p_high < thr - d) or not _approved(vektor, sk, politika, support):
                teshis[key] = LevelStatus.ETKI_YETERSIZ
            else:
                teshis[key] = LevelStatus.GECERLI

    kesim = kesim_noktasi(thr, d, politika.band)
    mphi: dict[str, float] = {}
    gecerli: list[tuple[Aday, Skor]] = []
    for a in adaylar(b, k, frozenset(gecersiz)):
        sk = cift_skorlari[a.plan_id]
        if violations(a.vektor, support):
            continue
        if not (sk.p_high < thr - d) or sk.p_high > baz.p_high:
            continue
        if not _approved(a.vektor, sk, politika, support):
            continue
        mp = min_phi_formul(baz.p_high, sk.p_high, kesim)
        if mp is None or not 0.0 <= mp <= 1.0:  # outside [0, 1]: the plan is invalid
            continue
        mphi[a.plan_id] = mp
        gecerli.append((a, sk))

    if not gecerli:
        reasons: list[tuple[str, tuple[str, ...]]] = []
        for e in k.eylemler:
            rs = sorted({teshis[(e.id, s.id)].value for s in e.seviyeler})
            reasons.append((e.id, tuple(rs)))
        return Sonuc(
            PlanYok(bagli_kisitlar=tuple(reasons), esige_uzaklik=baz.p_point - thr), teshis, ()
        )

    best: dict[str, tuple[Aday, Skor]] = {}
    for a, sk in sorted(gecerli, key=lambda x: _plan_key(x[0])):
        best.setdefault(yol_tipi(imza([e for e, _ in a.eylemler], k)), (a, sk))
    yollar = tuple(
        YolPlan(
            yol_tipi=t,
            imza=imza([e for e, _ in best[t][0].eylemler], k),
            plan_id=best[t][0].plan_id,
            eylemler=best[t][0].eylemler,
            maliyet_usd=best[t][0].maliyet_usd,
            min_phi=mphi[best[t][0].plan_id],
            dayaniklilik=dayaniklilik_etiketi(mphi[best[t][0].plan_id], k),
            sure_hafta=best[t][0].sure,
            p_low=best[t][1].p_low,
            p_point=best[t][1].p_point,
            p_high=best[t][1].p_high,
            kirpildi=best[t][0].kirpildi,
        )
        for t in PATH_ORDER
        if t in best
    )
    return Sonuc(PlanVar(yollar=yollar), teshis, tuple(gecerli))


def hazirla(b: Mapping[str, Any], k: Katalog) -> tuple[list[tuple[str, str, Aday]], list[Aday]]:
    """Candidate set for one record: (single (action, level, Aday) list, all plans)."""
    tek = [
        (e.id, s.id, _combine([(e, s, et)], b))
        for e, s, et in uygulanabilir_tekler(b, k)
        if et is not None
    ]
    return tek, adaylar(b, k)  # all plans; ladder-invalid ones are filtered inside sec


def sec_from_scores(
    b: Mapping[str, Any],
    hazir: tuple[list[tuple[str, str, Aday]], list[Aday]],
    baz: Skor,
    aday_skorlari: Sequence[Skor],
    politika: Policy,
    support: Support,
    k: Katalog,
    delta: float | None = None,
) -> Sonuc:
    """`aday_skorlari` is aligned with hazir[1]."""
    tek, tum = hazir
    cift = {a.plan_id: sk for a, sk in zip(tum, aday_skorlari, strict=True)}
    tekler = {(e, s): cift[a.plan_id] for e, s, a in tek}
    return sec(b, baz, tekler, cift, politika, support, k, delta)


def plan_bul(
    b: Mapping[str, Any],
    tarih: Any,
    scorer: Scorer,
    politika: Policy,
    support: Support,
    k: Katalog,
    delta: float | None = None,
) -> Sonuc:
    """Score the baseline and every candidate (one batch), then select."""
    hazir = hazirla(b, k)
    skorlar = scorer.skorla_toplu([b] + [a.vektor for a in hazir[1]], tarih)
    return sec_from_scores(b, hazir, skorlar[0], skorlar[1:], politika, support, k, delta)
