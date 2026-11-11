import pytest

from credit_coach import baseline, safety_margin
from credit_coach.bundle import ROOT
from credit_coach.safety_margin import aylik_kayma, delta_kurali, render


def test_monthly_drift_is_absolute():
    assert aylik_kayma(0.15, 0.14) == pytest.approx(0.01)
    assert aylik_kayma(0.14, 0.15) == pytest.approx(0.01)


def test_rule_takes_the_largest_drift_and_rounds_up_to_0_001():
    assert delta_kurali([0.0015, 0.011832, 0.0046]) == 0.012
    assert delta_kurali([0.0120001]) == 0.013  # strictly above 0.012 rounds up
    assert delta_kurali([0.012]) == 0.012  # exactly on the grid stays
    assert delta_kurali([0.0230000000001]) == 0.023  # float noise does not push it up
    assert delta_kurali([0.0001]) == 0.001
    assert delta_kurali([0.02]) == 0.02


def test_render_states_the_rule_with_the_computed_value():
    rows = [
        {
            "ay": "2015-01",
            "dilim": "boşluk",
            "n": 10,
            "kalibre_ort": 0.15,
            "gozlenen": 0.14,
            "kayma": 0.01,
            "isaret": 0.01,
        },
        {
            "ay": "2015-02",
            "dilim": "boşluk",
            "n": 10,
            "kalibre_ort": 0.153,
            "gozlenen": 0.1412,
            "kayma": 0.0118,
            "isaret": 0.0118,
        },
    ]
    text = render(rows)
    assert "ceil(1000 × 0.011800) / 1000 = **0.012**" in text
    assert text.startswith(safety_margin.START) and text.rstrip().endswith(safety_margin.END)


def test_adr_states_the_rule_and_the_months():
    adr = (ROOT / "docs" / "adr" / "007-safety-margin.md").read_text()
    assert "0,001'e yukarı yuvarlanır" in adr
    assert "2015-03..06" in adr and "2015-01, 02, 07, 08" in adr
    assert "Test dilimi" in adr


def test_missing_raw_data_gives_a_clear_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(baseline, "CSV", tmp_path / "yok.csv")
    assert safety_margin.main([]) == 2
    assert "Ham veri bulunamadı" in capsys.readouterr().err
