"""frontend/src/texts.json is the single place of UI text. It must stay consistent with the
contract (OpenAPI enums, feature manifest, support ranges, catalog) and free of forbidden
phrases (strict: no negation exemption here)."""

import json

import pytest
import yaml

from credit_coach.bundle import ROOT
from credit_coach.contract import Basvuru, OuterStatus, PublicReasonCode
from credit_coach.features import load_manifest
from credit_coach.recourse import PATH_ORDER, LevelStatus, load_demo_catalog
from credit_coach.support import load_support

TEXTS = json.loads((ROOT / "frontend" / "src" / "texts.json").read_text())
FORBIDDEN = json.loads((ROOT / "configs" / "forbidden_phrases.json").read_text())["ifadeler"]
WARNING = (
    "Model 2012-15 ABD (LendingClub) verisiyle eğitildi; güncel başvurular için kalibre değil. "
    "Plan modele göre geçerlidir, gerçek etkisi doğrulanmadı."
)


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def test_no_forbidden_phrase_in_any_ui_string():
    bad = [s for s in strings(TEXTS) if any(p in s.lower() for p in FORBIDDEN)]
    assert bad == []


def test_warning_strip_text_is_exact():
    assert TEXTS["uyari"] == WARNING


def test_every_api_field_has_a_label_and_a_unit_matching_the_manifest():
    assert set(TEXTS["alanlar"]) == set(Basvuru.model_fields)
    to_text = {"yuzde": "yüzde", "dolar": "dolar", "adet": "adet", "puan": "puan", None: "metin"}
    for c in load_manifest():
        if c.izin_verilen:
            assert TEXTS["alanlar"][c.ad]["birim"] == to_text[c.birim], c.ad


def test_form_sections_cover_every_field_exactly_once():
    listed = [a for fields in TEXTS["bolum_alanlari"].values() for a in fields]
    assert sorted(listed) == sorted(Basvuru.model_fields)
    assert set(TEXTS["bolum_alanlari"]) == set(TEXTS["bolumler"])


@pytest.mark.parametrize("name", sorted(load_support().kategorik))
def test_select_options_match_the_training_support(name):
    values = {o["deger"] for o in TEXTS["secenekler"][name]}
    seen = {v.strip() for v in load_support().kategorik[name]}
    assert seen <= values
    extra = values - seen
    assert extra <= ({"Joint App"} if name == "application_type" else set())


def test_enums_are_fully_covered_by_texts():
    assert set(TEXTS["gerekce"]) == {c.value for c in PublicReasonCode}
    assert set(TEXTS["karar"]) == {s.value for s in OuterStatus}
    assert set(TEXTS["dagilim"]) == {s.value for s in OuterStatus}
    assert set(TEXTS["yol"]) == set(PATH_ORDER)
    assert {s.value for s in LevelStatus} <= set(TEXTS["kisit"])
    assert set(TEXTS["plan_durumu"]) == {"PLAN", "PLAN_YOK", "PLAN_GEREKSIZ"}
    assert set(TEXTS["ornek_vakalar"]) == {
        "onay",
        "kosullu",
        "ret_plan",
        "ret_plan_yok",
        "destek_disi",
    }


def test_catalog_actions_and_levels_have_texts_with_the_right_target():
    kat = load_demo_catalog()
    for e in kat.eylemler:
        assert e.id in TEXTS["eylem"]
        for s in e.seviyeler:
            label = TEXTS["seviye"][s.id]
            target = s.hedef if e.id == "revolving_paydown" else round(s.hedef * 100)
            assert str(int(target)) in label, (s.id, label)
    assert TEXTS["eylem"]["loan_amount_reduction"].startswith("Karşı teklif")


def test_example_cases_all_have_texts():
    cases = json.loads((ROOT / "frontend" / "src" / "ornekler.json").read_text())
    assert {c["anahtar"] for c in cases} == set(TEXTS["ornek_vakalar"])


def test_support_file_is_the_source_of_the_options():
    raw = yaml.safe_load((ROOT / "configs" / "support.yaml").read_text())
    assert set(raw["kategorik"]) == set(load_support().kategorik)
