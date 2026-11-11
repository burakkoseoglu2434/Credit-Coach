"""The default delta in the reports' titles/labels must be the catalog value. If
configs/catalog/demo_v0.yaml `delta.deger` changes, these tests fail until the reports are
regenerated (python -m credit_coach.portfolio_report / resilience_report / target_segment)."""

import dataclasses
import re

import yaml

from credit_coach.bundle import ROOT
from credit_coach.recourse import DEMO_CATALOG_PATH, load_demo_catalog
from credit_coach.report_deltas import (
    delta_etiketi,
    fmt,
    report_deltas,
    varsayilan_delta,
)

KAT = load_demo_catalog()
DOCS = ("demo_portfolio_report.md", "demo_resilience_labels.md", "demo_target_segment.md")
MARK = " (demo varsayılanı)"


def mismatches(kat) -> list[str]:
    """Every place where a report says something different from the catalog default."""
    errs: list[str] = []
    default = fmt(float(kat.delta))
    for name in DOCS:
        text = (ROOT / "docs" / name).read_text()
        title = text.splitlines()[0]
        if f"{varsayilan_delta(kat)})" not in title and f"; {varsayilan_delta(kat)})" not in title:
            errs.append(f"{name}: title does not state '{varsayilan_delta(kat)}'")
        if f"Demo varsayılan δ = {default} (" not in text:
            errs.append(f"{name}: intro note has a different default delta")
        marked = re.findall(r"\| (δ = [^|]*?)" + re.escape(MARK) + r" \|", text)
        if not marked:
            errs.append(f"{name}: no default-delta column")
        for label in set(marked):
            if label != f"δ = {default}" and not label.startswith("δ = 0 (band içi"):
                errs.append(
                    f"{name}: '{label}' is marked as default but the catalog says {default}"
                )
            if label.startswith("δ = 0 (band içi") and float(kat.delta) != 0.0:
                errs.append(f"{name}: band-inside column is marked as default")
        if f"δ = {default}{MARK}" not in text:
            errs.append(f"{name}: the column 'δ = {default}{MARK}' is missing")
    facts = (ROOT / "docs" / "demo_target_segment.md").read_text()
    if f"| Varsayılan δ | {float(kat.delta):g} (" not in facts:
        errs.append("demo_target_segment.md: 'Varsayılan δ' row differs from the catalog")
    return errs


def test_reports_state_the_catalog_default_delta():
    assert mismatches(KAT) == []


def test_the_check_fails_when_the_catalog_value_changes():
    changed = dataclasses.replace(KAT, delta=0.015)
    errs = mismatches(changed)
    assert errs and any("0,015" in e or "0.015" in e for e in errs)


def test_catalog_object_and_yaml_agree_and_the_label_comes_from_them():
    raw = yaml.safe_load(DEMO_CATALOG_PATH.read_text())
    assert KAT.delta == float(raw["delta"]["deger"])
    assert delta_etiketi(KAT.delta, KAT) == f"δ = {fmt(KAT.delta)}{MARK}"
    assert KAT.delta in report_deltas(KAT) and 0.0 in report_deltas(KAT)
    assert delta_etiketi(0.015, dataclasses.replace(KAT, delta=0.015)).endswith(MARK)
    assert not delta_etiketi(0.03, KAT).endswith(MARK) or KAT.delta == 0.03


def test_the_engine_uses_the_catalog_default_when_no_delta_is_passed():
    from credit_coach.decision_scenarios import in_support_basvuru
    from credit_coach.policy import load_policy
    from credit_coach.recourse import plan_bul
    from credit_coach.recourse_scorers import SyntheticScorer
    from credit_coach.support import load_support

    support, pol, sc = load_support(), load_policy("v1"), SyntheticScorer()
    b = in_support_basvuru(support)
    b.update(
        revol_util=95.0,
        revol_bal=20000.0,
        loan_amnt=15000.0,
        annual_inc=60000.0,
        fico_range_low=680.0,
        fico_range_high=684.0,
        total_bal_ex_mort=40000.0,
        tot_cur_bal=90000.0,
    )
    implicit = plan_bul(b, None, sc, pol, support, KAT)
    explicit = plan_bul(b, None, sc, pol, support, KAT, KAT.delta)
    assert implicit.sonuc == explicit.sonuc


def test_adr_007_states_the_catalog_value_and_the_computed_delta():
    adr = (ROOT / "docs" / "adr" / "007-safety-margin.md").read_text()
    assert f"Katalog değeri: {fmt(float(KAT.delta))}." in adr  # catalog changes -> this fails
    assert "δ = 0,012" in adr and "0,011832" in adr  # the measured result the value comes from
    assert KAT.delta == 0.012
