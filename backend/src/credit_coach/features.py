"""Feature manifest (configs/features.yaml) and the Pandera schema generated from it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandera.pandas as pa
import yaml

MANIFEST_PATH = Path(__file__).resolve().parents[3] / "configs" / "features.yaml"

CLASSES = frozenset(
    {"APPLICATION_TIME", "PRICING", "POST_ORIGINATION", "TARGET_SOURCE", "ID_OR_META"}
)
TYPES = {"float": float, "int": int, "str": str}
BIRIMLER = frozenset({"yuzde", "oran", "adet", "dolar", "puan"})


@dataclass(frozen=True)
class Column:
    ad: str
    sinif: str
    tip: str
    izin_verilen: bool
    gerekce: str
    birim: str | None = None


def load_manifest(path: Path = MANIFEST_PATH) -> list[Column]:
    raw = yaml.safe_load(path.read_text())
    cols = [Column(**c) for c in raw["columns"]]
    names = [c.ad for c in cols]
    if len(names) != len(set(names)):
        raise ValueError("duplicate column in manifest")
    for c in cols:
        if c.sinif not in CLASSES:
            raise ValueError(f"{c.ad}: unknown class {c.sinif}")
        if c.tip not in TYPES:
            raise ValueError(f"{c.ad}: unknown type {c.tip}")
        if c.izin_verilen and c.sinif != "APPLICATION_TIME":
            raise ValueError(f"{c.ad}: only APPLICATION_TIME columns may be allowed")
        if c.izin_verilen and c.tip in ("float", "int"):
            if c.birim not in BIRIMLER:
                raise ValueError(f"{c.ad}: allowed numeric feature needs a valid birim")
        elif c.birim is not None:
            raise ValueError(f"{c.ad}: birim only for allowed numeric features")
        if not c.gerekce.strip():
            raise ValueError(f"{c.ad}: empty rationale")
    return cols


def allowed_features(manifest: list[Column] | None = None) -> list[str]:
    return [c.ad for c in (manifest or load_manifest()) if c.izin_verilen]


def build_schema(manifest: list[Column] | None = None) -> pa.DataFrameSchema:
    cols = manifest or load_manifest()
    return pa.DataFrameSchema(
        {c.ad: pa.Column(TYPES[c.tip], nullable=c.sinif != "TARGET_SOURCE") for c in cols},
        strict=True,
    )
