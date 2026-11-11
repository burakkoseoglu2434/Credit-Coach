from credit_coach.bundle import ROOT

CLAIMS = (ROOT / "docs" / "CLAIMS.md").read_text()


def test_claims_has_the_three_sections_and_the_required_limits():
    for heading in ("## İddia ettiklerimiz", "## İddia etmediklerimiz", "## Bilinen sınırlar"):
        assert heading in CLAIMS
    for must in (
        "2012-01..2015-12",
        "tek fiyatlı kurgusal kredi veren",
        "Nedensel etki doğrulanmadı",
        "Denetim izi bu sürümde yok",
        "Veri kapsamı",
    ):
        assert must in CLAIMS, must


def test_claims_fits_one_page():
    assert len(CLAIMS.splitlines()) <= 60


def test_claims_mentions_min_phi_labels_and_evidence_classes():
    for must in (
        "min_phi",
        "GUCLU",
        "KOSULLU",
        "ZAYIF",
        "(K)",
        "(M)",
        "karşı teklif",
        "varsayımdır",
    ):
        assert must in CLAIMS, must
    assert "gerçekte işe yarayacağını" in CLAIMS  # listed under what we do not claim


def test_claims_states_the_missing_guclu_example_and_the_note_stays():
    sentence = (
        "198 örnek kayıtta δ = 0,02 iken GUCLU etiketli reddedilen kayıt çıkmadı; "
        "δ = 0,012'de (ADR-007) 4 kayıt çıkar. GUCLU örnek vakası eklenmedi (karar)."
    )
    assert sentence in CLAIMS
    cases = (ROOT / "docs" / "demo_example_cases.md").read_text()
    assert "**Bulunamadı:**" in cases  # the 'not found' note in demo_example_cases.md stays
    assert not any(
        c["anahtar"] == "ret_guclu"
        for c in __import__("json").loads((ROOT / "frontend" / "src" / "ornekler.json").read_text())
    )


def test_claims_states_how_delta_is_derived_and_that_it_is_an_assumption():
    from credit_coach.recourse import load_demo_catalog
    from credit_coach.report_deltas import fmt

    sentence = (
        f"- **Güvenlik payı δ bir varsayımdır.** δ = {fmt(load_demo_catalog().delta)}, "
        "kalibrasyon ve boşluk aylarındaki en büyük aylık |kalibre ortalama PD − gözlenen oran| "
        "değerinin 0,001'e yukarı yuvarlanmasıyla türetilir (ADR-007); "
        "ölçülmüş bir kapsama değildir."
    )
    assert sentence in CLAIMS  # the catalog value changes -> this fails until CLAIMS is updated
