"""Scoring service (demo v0): one decision path for /score and /batch.

Path per record: support check -> model -> calibrator -> decide (v1) -> recourse.
`/score` is a batch of one, so both endpoints run the same code. Out-of-support records are not
scored (the model has never seen such values) and get no plan. No clock, randomness or network;
the application date is part of the input.
"""

from __future__ import annotations

import csv
import functools
import io
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
import yaml
from pydantic import ValidationError

from credit_coach.bundle import LOCK_PATH, ROOT
from credit_coach.bundle import sha256 as file_sha256
from credit_coach.contract import Basvuru, OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support, destek_disi_karar, to_public
from credit_coach.features import allowed_features, load_manifest
from credit_coach.policy import POLICY_DIR, Policy, load_policy
from credit_coach.recourse import (
    DEMO_CATALOG_PATH,
    PATH_ORDER,
    Katalog,
    PlanGereksiz,
    PlanVar,
    PlanYok,
    hazirla,
    load_demo_catalog,
    sec_from_scores,
)
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.schemas import (
    BatchResponse,
    KovaSatiri,
    Notlar,
    PortfoyOzeti,
    SatirKarari,
    SatirSonucu,
    ScoreResponse,
    Skor3,
    Surumler,
)
from credit_coach.support import Support, load_support, violations

TEMPLATE_PATH = ROOT / "configs" / "templates" / "api_v0.yaml"
MAX_BATCH_ROWS = 10_000
DATE_COLUMN = "basvuru_tarihi"
ID_COLUMN = "kayit_id"

EDGES = [-1.0, 0.0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 9.0]
LABELS = [
    "< 0",
    "[0, 0,01)",
    "[0,01, 0,02)",
    "[0,02, 0,03)",
    "[0,03, 0,05)",
    "[0,05, 0,10)",
    "[0,10, 0,20)",
    ">= 0,20",
]


def bucket(x: float) -> str:
    for lo, hi, lab in zip(EDGES, EDGES[1:], LABELS, strict=True):
        if lo <= x < hi:
            return lab
    raise ValueError(x)


class GirdiHatasi(ValueError):
    """Invalid input (HTTP 422). Never turned into a silent decision."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors[:5]))
        self.errors = errors


@dataclass(frozen=True)
class Kayit:
    basvuru: dict[str, Any]
    tarih: date
    kayit_id: str | None = None


def normalize(k: Kayit) -> Kayit:
    """Trim surrounding whitespace of string values (the raw data pads e.g. " 36 months"), so
    the support check and the model see the same text whatever the client sent."""
    b = {n: (v.strip() if isinstance(v, str) else v) for n, v in k.basvuru.items()}
    return Kayit(b, k.tarih, k.kayit_id)


class Servis:
    def __init__(
        self,
        scorer: Any,
        policy: Policy,
        support: Support,
        katalog: Katalog,
        notlar: Notlar,
        surumler: Surumler,
    ) -> None:
        self.scorer, self.policy, self.support = scorer, policy, support
        self.katalog, self.notlar, self.surumler = katalog, notlar, surumler

    @classmethod
    def varsayilan(cls) -> Servis:
        policy, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
        raw = yaml.safe_load(TEMPLATE_PATH.read_text())
        return cls(
            ModelScorer(),
            policy,
            support,
            kat,
            Notlar(**raw),
            Surumler(
                politika_surumu=policy.surum,
                politika_sha256=file_sha256(POLICY_DIR / f"{policy.surum}.yaml"),
                katalog_surumu=str(kat.raw["version"]),
                katalog_sha256=file_sha256(DEMO_CATALOG_PATH),
                bundle_sha256=file_sha256(LOCK_PATH),
                support_sha256=support.sha256,
            ),
        )

    # ---- the single decision path ------------------------------------------------------

    def degerlendir(self, kayitlar: Sequence[Kayit]) -> list[SatirKarari]:
        kayitlar = [normalize(k) for k in kayitlar]
        out: list[SatirKarari | None] = [None] * len(kayitlar)
        groups: dict[tuple[int, int], list[int]] = defaultdict(list)
        for i, k in enumerate(kayitlar):
            bad = violations(k.basvuru, self.support)
            if bad:
                d = to_public(destek_disi_karar(self.policy, bad))
                out[i] = SatirKarari(
                    dis_durum=d.dis_durum,
                    gerekce_kodlari=list(d.gerekce_kodlari),
                    conditional_type=d.conditional_type,
                    upgrade_condition=d.upgrade_condition,
                    destek_ihlalleri=list(bad),
                    skor=None,
                    plan=PlanYok(
                        bagli_kisitlar=(("BASVURU", ("DESTEK_DISI",)),), esige_uzaklik=None
                    ),
                )
            else:
                groups[(k.tarih.year, k.tarih.month)].append(i)

        for (yil, ay), idx in sorted(groups.items()):
            tarih = pd.Timestamp(year=yil, month=ay, day=1)
            recs = [kayitlar[i].basvuru for i in idx]
            base = self.scorer.skorla_toplu(recs, tarih)
            pend: list[tuple[int, dict[str, Any], Any, Any]] = []
            for i, b, s in zip(idx, recs, base, strict=True):
                g = parse_input(
                    {
                        "basvuru": b,
                        "p_low": s.p_low,
                        "p_point": s.p_point,
                        "p_high": s.p_high,
                        "ham_skor": s.ham_skor,
                        "politika_surumu": self.policy.surum,
                        "plan_available": None,
                    }
                )
                d = decide_with_support(g, self.policy, self.support)
                pub = to_public(d)
                satir = {
                    "dis_durum": pub.dis_durum,
                    "gerekce_kodlari": list(pub.gerekce_kodlari),
                    "conditional_type": pub.conditional_type,
                    "upgrade_condition": pub.upgrade_condition,
                    "destek_ihlalleri": [],
                    "skor": Skor3(p_low=s.p_low, p_point=s.p_point, p_high=s.p_high),
                }
                if d.dis_durum is OuterStatus.APPROVED:
                    out[i] = SatirKarari(**satir, plan=PlanGereksiz())
                else:
                    pend.append((i, b, s, satir))
            hz = [hazirla(b, self.katalog) for _i, b, _s, _sat in pend]
            flat = [a.vektor for _t, tum in hz for a in tum]
            sk = self.scorer.skorla_toplu(flat, tarih) if flat else []
            pos = 0
            for (i, b, s, satir), h in zip(pend, hz, strict=True):
                n = len(h[1])
                res = sec_from_scores(
                    b, h, s, sk[pos : pos + n], self.policy, self.support, self.katalog
                )
                pos += n
                out[i] = SatirKarari(**satir, plan=res.sonuc)
        return [o for o in out if o is not None]

    # ---- responses ---------------------------------------------------------------------

    def score(self, kayit: Kayit) -> ScoreResponse:
        (karar,) = self.degerlendir([kayit])
        return ScoreResponse(karar=karar, surumler=self.surumler, notlar=self.notlar)

    def batch(self, kayitlar: Sequence[Kayit]) -> BatchResponse:
        kararlar = self.degerlendir(kayitlar)
        satirlar = [
            SatirSonucu(satir_no=i + 1, kayit_id=k.kayit_id, karar=d)
            for i, (k, d) in enumerate(zip(kayitlar, kararlar, strict=True))
        ]
        return BatchResponse(
            satirlar=satirlar,
            ozet=self.ozet(kararlar),
            surumler=self.surumler,
            notlar=self.notlar,
        )

    def ozet(self, kararlar: Sequence[SatirKarari]) -> PortfoyOzeti:
        thr = self.policy.onay_esigi
        durum: dict[str, int] = defaultdict(int)
        plan: dict[str, int] = defaultdict(int)
        destek_disi = 0
        arayan = 0
        var = 0
        yol: dict[str, int] = defaultdict(int)
        kova: dict[str, list[int]] = {lab: [0, 0] for lab in LABELS}
        sira = {"GUCLU": 0, "KOSULLU": 1, "ZAYIF": 2}
        guclu: dict[str, int] = defaultdict(int)
        yol_et: dict[str, dict[str, int]] = {t: defaultdict(int) for t in PATH_ORDER}
        for d in kararlar:
            durum[d.dis_durum.value] += 1
            plan[d.plan.durum] += 1
            if d.destek_ihlalleri:
                destek_disi += 1
                continue
            if d.dis_durum is OuterStatus.APPROVED:
                continue
            arayan += 1
            k = kova[bucket(d.skor.p_point - thr)]  # type: ignore[union-attr]
            k[0] += 1
            if isinstance(d.plan, PlanVar):
                var += 1
                k[1] += 1
                for y in d.plan.yollar:
                    yol[y.yol_tipi] += 1
                    yol_et[y.yol_tipi][y.dayaniklilik] += 1
                guclu[min((y.dayaniklilik for y in d.plan.yollar), key=sira.__getitem__)] += 1
        return PortfoyOzeti(
            n=len(kararlar),
            dis_durum_dagilimi=dict(sorted(durum.items())),
            plan_durumu_dagilimi=dict(sorted(plan.items())),
            destek_disi=destek_disi,
            plan_arayan=arayan,
            gecerli_plan_orani=(var / arayan) if arayan else None,
            yol_orani={t: (yol[t] / arayan) if arayan else None for t in PATH_ORDER},
            dayaniklilik_dagilimi={k: guclu[k] for k in sira if guclu[k]},
            yol_dayaniklilik={
                t: {k: yol_et[t][k] for k in sira if yol_et[t][k]} for t in PATH_ORDER
            },
            kovalar=[
                KovaSatiri(kova=lab, n=n, gecerli_plan_orani=(v / n) if n else None)
                for lab, (n, v) in kova.items()
                if n
            ],
        )


# ---- CSV input ---------------------------------------------------------------------------


@functools.cache
def _kinds() -> dict[str, str]:
    return {c.ad: c.tip for c in load_manifest() if c.izin_verilen}


@functools.cache
def _names() -> tuple[str, ...]:
    return tuple(allowed_features())


def parse_csv(text: str) -> list[Kayit]:
    """CSV -> records. Header must be exactly the allowed features + basvuru_tarihi (+ kayit_id).
    Any bad row makes the whole request invalid (422): no partial or silent results."""
    names, kinds = _names(), _kinds()
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as e:
        raise GirdiHatasi(["boş dosya"]) from e
    expected = set(names) | {DATE_COLUMN}
    missing = sorted(expected - set(header))
    unknown = sorted(set(header) - expected - {ID_COLUMN})
    if missing or unknown or len(set(header)) != len(header):
        raise GirdiHatasi(
            [
                f"başlık hatası: eksik={missing}, bilinmeyen={unknown}, "
                f"tekrar={len(header) != len(set(header))}"
            ]
        )
    pos = {h: i for i, h in enumerate(header)}
    kayitlar: list[Kayit] = []
    errors: list[str] = []
    for n, row in enumerate(reader, start=1):
        if n > MAX_BATCH_ROWS:
            raise GirdiHatasi([f"en çok {MAX_BATCH_ROWS} satır kabul edilir"])
        if len(row) != len(header):
            errors.append(f"satır {n}: sütun sayısı {len(row)}, beklenen {len(header)}")
            continue
        b: dict[str, Any] = {}
        try:
            for name in names:
                v = row[pos[name]].strip()
                if v == "":
                    b[name] = None
                elif kinds[name] == "float":
                    f = float(v)
                    if not math.isfinite(f):
                        raise ValueError(f"{name}: sonlu olmayan sayı")
                    b[name] = f
                elif kinds[name] == "int":
                    b[name] = int(v)
                else:
                    b[name] = v
            Basvuru.model_validate(b)
            tarih = date.fromisoformat(row[pos[DATE_COLUMN]].strip())
        except (ValueError, ValidationError) as e:
            errors.append(f"satır {n}: {str(e).splitlines()[0]}")
            continue
        kid = row[pos[ID_COLUMN]].strip() if ID_COLUMN in pos else None
        kayitlar.append(Kayit(b, tarih, kid or None))
    if errors:
        raise GirdiHatasi(errors)
    if not kayitlar:
        raise GirdiHatasi(["veri satırı yok"])
    return kayitlar
