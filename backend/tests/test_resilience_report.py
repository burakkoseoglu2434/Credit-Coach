from credit_coach import baseline, resilience_report
from credit_coach.recourse import load_demo_catalog
from credit_coach.resilience_report import DELTAS, PERIODS, render, strongest
from tests.test_recourse import POLICY


def test_strongest_label_per_record():
    assert strongest({}) == "PLAN_YOK"
    assert strongest({"customer": "ZAYIF", "hybrid": "GUCLU"}) == "GUCLU"
    assert strongest({"customer": "ZAYIF", "institution": "KOSULLU"}) == "KOSULLU"


def test_render_counts_and_notes():
    recs = [{}, {"customer": "GUCLU"}, {"customer": "ZAYIF", "hybrid": "KOSULLU"}, {}]
    data = {p: {d: recs for d in DELTAS} for p in PERIODS}
    text = render(data, load_demo_catalog(), POLICY)
    assert text.count("Bu tablo ne demek") == 3 and text.count("Ne DEMEK DEĞİL") == 3
    assert "| 4 | 2 (50.0%) | 1 (25.0%) | 1 (25.0%) | 0 (0.0%) |" in text
    assert "varsayım" in text and "tek fiyatlı kurgusal kredi veren" in text


def test_missing_raw_data_gives_a_clear_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(baseline, "CSV", tmp_path / "yok.csv")
    monkeypatch.setattr(resilience_report, "REPORT", tmp_path / "r.md")
    assert resilience_report.main([]) == 2
    assert "Ham veri bulunamadı" in capsys.readouterr().err
    assert not (tmp_path / "r.md").exists()
