"""Catalog unit validation (configs/catalog/*.yaml against configs/features.yaml `birim`).

Scope: only the unit check for demo v0. The recourse engine loader comes in week 4.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from credit_coach.features import MANIFEST_PATH, load_manifest

CATALOG_PATH = MANIFEST_PATH.parent / "catalog" / "v1.yaml"


def load_catalog_raw(path: Path = CATALOG_PATH) -> dict:
    return yaml.safe_load(path.read_text())


def unit_errors(catalog: dict, manifest=None) -> list[str]:
    """Every `<feature>_hedef` level key needs a declared unit equal to the manifest unit.

    A percent feature (revol_util, 0-100) must never get a 0-1 style target silently.
    """
    birim = {c.ad: c.birim for c in (manifest or load_manifest())}
    errors: list[str] = []
    for eylem in catalog["eylemler"]:
        declared = eylem.get("hedef_birimleri", {})
        for ozellik in eylem["ozellikler"]:
            if ozellik in declared and declared[ozellik] != birim.get(ozellik):
                errors.append(
                    f"{eylem['id']}.{ozellik}: katalog {declared[ozellik]!r}, "
                    f"manifest {birim.get(ozellik)!r}"
                )
        for sev in eylem["seviyeler"]:
            for key, value in sev.items():
                if not key.endswith("_hedef"):
                    continue
                f = key.removesuffix("_hedef")
                if f not in declared:
                    errors.append(f"{eylem['id']}.{sev['id']}: {f} için hedef_birimleri yok")
                elif birim.get(f) == "yuzde" and not 0 <= value <= 100:
                    errors.append(f"{eylem['id']}.{sev['id']}: yüzde hedefi 0-100 dışında")
                elif birim.get(f) == "oran" and not 0 <= value <= 1:
                    errors.append(f"{eylem['id']}.{sev['id']}: oran hedefi 0-1 dışında")
    return errors
