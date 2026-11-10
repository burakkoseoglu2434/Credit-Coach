"""Versioned decision policy. Policies are frozen objects; files are read only by load_policy."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from credit_coach.bundle import ROOT, sha256
from credit_coach.decision import approval_threshold, load_cost, total_hurdle

POLICY_DIR = ROOT / "configs" / "policy"
RULE_ORDER = (
    "R1_HARD_REJECT",
    "R2_THRESHOLD_BAND",
    "R3_WEAK_SUPPORT_NEAR",
    "R4_APPROVE",
    "R5_NOT_APPROVED_PLAN",
    "R6_NOT_APPROVED",
)


class UnknownPolicyVersion(ValueError):
    """The requested policy version does not exist. There is no default."""


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    surum: str
    kural_sirasi: tuple[str, ...]
    onay_esigi: float
    band: float
    zayif_destek_araliklari: tuple[tuple[float, float], ...]
    zayif_destek_yakinlik_carpani: float
    ret_esigi: float | None = None
    kaynak: dict | None = None

    @field_validator("onay_esigi")
    @classmethod
    def _unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("onay_esigi must be in [0, 1]")
        return v

    @field_validator("band", "zayif_destek_yakinlik_carpani")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("must be non-negative")
        return v

    @model_validator(mode="after")
    def _consistent(self) -> Policy:
        if self.kural_sirasi != RULE_ORDER:
            raise ValueError(f"kural_sirasi must be {RULE_ORDER}")
        if any(a > b for a, b in self.zayif_destek_araliklari):
            raise ValueError("weak-support range with start > end")
        if self.ret_esigi is not None and not self.ret_esigi > self.onay_esigi:
            raise ValueError("ret_esigi must exceed onay_esigi")
        return self


def load_policy(surum: str, policy_dir: Path = POLICY_DIR) -> Policy:
    if not re.fullmatch(r"v\d+", surum):
        raise UnknownPolicyVersion(f"invalid policy version: {surum!r}")
    path = policy_dir / f"{surum}.yaml"
    if not path.exists():
        raise UnknownPolicyVersion(f"unknown policy version: {surum!r}")
    return Policy(**yaml.safe_load(path.read_text()))


def derive_v1() -> dict:
    """Resolve the v1 policy numbers from cost.yaml and decision.yaml."""
    cost = load_cost()
    dec = yaml.safe_load((ROOT / "configs" / "decision.yaml").read_text())
    gain, loss, hurdle = (
        cost["saglam_kredi_getirisi"]["mean"],
        cost["temerrut_kaybi"]["mean"],
        total_hurdle(cost),
    )
    return {
        "surum": "v1",
        "kural_sirasi": list(RULE_ORDER),
        "onay_esigi": approval_threshold(gain, loss, hurdle),
        "band": dec["band"]["deger"],
        "zayif_destek_araliklari": dec["zayif_destek_skor_araliklari"],
        "zayif_destek_yakinlik_carpani": dec["zayif_destek_esik_yakinligi_carpani"],
        "ret_esigi": None,  # 4. haftada recourse fizibilitesinden türetilecek
        "kaynak": {
            "cost_yaml_sha256": sha256(ROOT / "configs" / "cost.yaml"),
            "decision_yaml_sha256": sha256(ROOT / "configs" / "decision.yaml"),
            "getiri": gain,
            "kayip": loss,
            "hurdle": hurdle,
        },
    }


def write_v1() -> None:
    path = POLICY_DIR / "v1.yaml"
    if path.exists():
        raise SystemExit("v1 is frozen: refusing to overwrite configs/policy/v1.yaml")
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    header = "# Politika v1 (ADR-004). Donduruldu: değiştirme, yeni sürüm ekle.\n"
    path.write_text(header + yaml.safe_dump(derive_v1(), allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    if sys.argv[1:] == ["write-v1"]:
        write_v1()
    else:
        raise SystemExit("usage: python -m credit_coach.policy write-v1")
