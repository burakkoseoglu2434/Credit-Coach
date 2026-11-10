import copy

import pytest

from credit_coach.catalog import load_catalog_raw, unit_errors
from credit_coach.features import load_manifest


def test_every_allowed_numeric_feature_has_unit():
    for c in load_manifest():
        if c.izin_verilen and c.tip in ("float", "int"):
            assert c.birim in {"yuzde", "oran", "adet", "dolar"}, c.ad


def test_revol_util_and_dti_are_percent():
    b = {c.ad: c.birim for c in load_manifest()}
    assert b["revol_util"] == "yuzde" and b["dti"] == "yuzde"


def test_catalog_units_match_manifest():
    assert unit_errors(load_catalog_raw()) == []


def test_revol_util_targets_are_percent_scale():
    cat = load_catalog_raw()
    util = next(e for e in cat["eylemler"] if e["id"] == "revolving_paydown")
    assert [s["revol_util_hedef"] for s in util["seviyeler"]] == [70, 50, 30]


def test_wrong_unit_declaration_fails():
    cat = copy.deepcopy(load_catalog_raw())
    cat["eylemler"][0]["hedef_birimleri"]["revol_util"] = "oran"
    assert any("revol_util" in e for e in unit_errors(cat))


def test_missing_unit_declaration_fails():
    cat = copy.deepcopy(load_catalog_raw())
    del cat["eylemler"][0]["hedef_birimleri"]
    assert unit_errors(cat)


def test_fraction_target_on_percent_feature_is_caught_by_range():
    # 0.70 is inside 0-100, so range alone cannot catch it; the declared unit mismatch does.
    cat = copy.deepcopy(load_catalog_raw())
    cat["eylemler"][0]["hedef_birimleri"]["revol_util"] = "oran"
    cat["eylemler"][0]["seviyeler"][0]["revol_util_hedef"] = 0.70
    assert unit_errors(cat)


def test_manifest_rejects_numeric_without_unit(tmp_path):
    p = tmp_path / "f.yaml"
    p.write_text(
        "version: 1\ncolumns:\n  - {ad: x, sinif: APPLICATION_TIME, tip: float,"
        " izin_verilen: true, gerekce: g}\n"
    )
    with pytest.raises(ValueError, match="birim"):
        load_manifest(p)
