"""Training-support ranges (configs/support.yaml) and the pre-decision support check.

Support = min/max of each numeric feature and the set of values seen for each categorical
feature, computed ONLY from the train split (never calibration or test). A value outside it is
"out of support": the model has never seen it, so no decision or plan is produced for it.

Usage: python -m credit_coach.support build | verify
"""

from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from credit_coach.canonical import canonical_text, sha256_hex
from credit_coach.features import MANIFEST_PATH, load_manifest

ROOT = MANIFEST_PATH.parents[1]
SUPPORT_PATH = ROOT / "configs" / "support.yaml"
# Categorical string features checked by value set. earliest_cr_line is a date; its derived
# credit_history_months needs the application date, so it is not part of this check (limit).
CATEGORICAL = ("term", "purpose", "application_type", "emp_length", "home_ownership")
NOT_CHECKED = {"earliest_cr_line": "tarih; türev credit_history_months başvuru tarihi gerektirir"}


class SupportFileError(ValueError):
    pass


@dataclass(frozen=True)
class Support:
    sayisal: dict[str, tuple[float, float]]
    kategorik: dict[str, frozenset[str]]
    sha256: str


def _content_hash(sayisal: dict, kategorik: dict) -> str:
    return sha256_hex(canonical_text({"kategorik": kategorik, "sayisal": sayisal}))


def build_content(train) -> dict:
    """Pure function of the train frame (a pandas DataFrame of raw allowed columns)."""
    cols = {c.ad: c for c in load_manifest()}
    sayisal, kategorik, wide = {}, {}, []
    for name, c in cols.items():
        if not c.izin_verilen:
            continue
        if c.tip == "float":
            s = train[name].dropna()
            sayisal[name] = {"min": float(s.min()), "max": float(s.max())}
            p99 = float(s.quantile(0.99))
            if p99 > 0 and float(s.max()) > 5 * p99:
                wide.append(f"{name} (max {float(s.max()):g}, 99. yüzdelik {p99:g})")
        elif name in CATEGORICAL:
            kategorik[name] = sorted(str(v) for v in train[name].dropna().unique())
    return {"sayisal": sayisal, "kategorik": kategorik, "wide": wide, "n": len(train)}


def render(content: dict, sources: dict) -> str:
    sayisal, kategorik = content["sayisal"], content["kategorik"]
    doc = {
        "surum": 1,
        "tanim": "Destek = yalnızca EĞİTİM diliminden sayısal min/max ve kategorik görülen değer "
        "kümesi. Dışındaki değer için karar/plan üretilmez (DEĞERLENDİRİLEMEZ).",
        "kaynak": {**sources, "egitim_satir_sayisi": content["n"]},
        "icerik_sha256": _content_hash(sayisal, kategorik),
        "bilinen_sinirlar": [
            "Aralık eğitim uç değerleriyle genişler: "
            + "; ".join(content["wide"])
            + ". Bu uç değerler 'destek içi' sayılır, yüzdelik kırpma bilerek yok.",
            "Boş (None) değerler ihlal sayılmaz; model eksik değeri kendi işler.",
            "Kontrol yalnızca aralık/küme üyeliğine bakar; özelliklerin birlikte görülmemişliği "
            "(çok boyutlu destek) denetlenmez.",
            "Denetlenmeyen: " + "; ".join(f"{k} ({v})" for k, v in NOT_CHECKED.items()),
        ],
        "sayisal": sayisal,
        "kategorik": kategorik,
    }
    return "# Üretilir: python -m credit_coach.support build. Elle düzenlenmez.\n" + yaml.safe_dump(
        doc, sort_keys=True, allow_unicode=True, width=100
    )


def load_support(path: Path = SUPPORT_PATH) -> Support:
    raw = yaml.safe_load(path.read_text())
    sayisal = {k: (v["min"], v["max"]) for k, v in raw["sayisal"].items()}
    expected = _content_hash(raw["sayisal"], raw["kategorik"])
    if raw["icerik_sha256"] != expected:
        raise SupportFileError("support.yaml content hash mismatch (edited by hand?)")
    return Support(
        sayisal=sayisal,
        kategorik={k: frozenset(v) for k, v in raw["kategorik"].items()},
        sha256=raw["icerik_sha256"],
    )


def violations(basvuru: dict, support: Support) -> tuple[str, ...]:
    """Sorted names of features outside the training support. None is not a violation."""
    out = []
    for name, (lo, hi) in support.sayisal.items():
        v = basvuru.get(name)
        if v is not None and (not math.isfinite(v) or v < lo or v > hi):
            out.append(name)
    for name, allowed in support.kategorik.items():
        v = basvuru.get(name)
        # raw data carries padding (" 36 months"); compare on stripped values
        if v is not None and str(v).strip() not in {a.strip() for a in allowed}:
            out.append(name)
    return tuple(sorted(out))


def _file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(write: bool = True) -> str:
    import pandas as pd

    from credit_coach.baseline import CSV
    from credit_coach.modeling import dev_frame
    from credit_coach.split import SPLIT_CONFIG_PATH

    dev = dev_frame(pd.read_csv(CSV))
    train = dev[dev["split"] == "train"]
    text = render(
        build_content(train),
        {
            "split": "train",
            "ham_veri_sha256": _file_sha(CSV),
            "features_yaml_sha256": _file_sha(MANIFEST_PATH),
            "split_yaml_sha256": _file_sha(SPLIT_CONFIG_PATH),
        },
    )
    if write:
        SUPPORT_PATH.write_text(text)
    return text


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "verify"
    if cmd == "build":
        build()
        print(f"wrote {SUPPORT_PATH}")
        return 0
    if cmd == "verify":
        load_support()
        print("support.yaml ok", load_support().sha256)
        return 0
    print("usage: support build|verify")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
