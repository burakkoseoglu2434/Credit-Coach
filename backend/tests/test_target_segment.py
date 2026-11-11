import json

from credit_coach import baseline, target_segment
from credit_coach.bundle import ROOT
from credit_coach.recourse import load_demo_catalog
from credit_coach.resilience_report import DELTAS, PERIODS
from credit_coach.target_segment import delta_facts, render
from tests.test_recourse import POLICY


def test_render_breaks_labels_down_by_bucket_with_notes():
    recs = [
        ("[0, 0,01)", {"customer": "GUCLU"}),
        ("[0, 0,01)", {}),
        ("[0,10, 0,20)", {"hybrid": "ZAYIF", "customer": "KOSULLU"}),
        ("[0,10, 0,20)", {}),
    ]
    data = {p: {d: recs for d in DELTAS} for p in PERIODS}
    text = render(data, load_demo_catalog(), POLICY)
    assert text.count("Bu tablo ne demek") == 2 and text.count("Ne DEMEK DEĞİL") == 2
    assert "| 2 | 50.0% | 50.0% | 0.0% | 0.0% |" in text  # first bucket: half PLAN_YOK, half GUCLU
    assert "| 2 | 50.0% | 0.0% | 50.0% | 0.0% |" in text  # second bucket: KOSULLU is the strongest
    assert "| 4 | 50.0% | 25.0% | 25.0% | 0.0% |" in text  # all rows


def test_default_delta_facts_match_the_live_config_and_visibility():
    kat = load_demo_catalog()
    facts = "\n".join(delta_facts())
    assert f"{kat.delta:g}" in facts and "varsayım" in facts
    assert "configs/catalog/demo_v0.yaml" in facts and "007-safety-margin" in facts
    # the visibility claims are locked to the real files
    api = "guvenlik_payi" in (ROOT / "frontend" / "openapi.json").read_text()
    assert api and "`guvenlik_payi` alanı" in facts
    comp = ROOT / "frontend" / "src" / "components"
    for yer, dosya in (("sonuç sayfası", "Sonuc.tsx"), ("toplu özet", "Toplu.tsx")):
        uses = "guvenlik_payi" in (comp / dosya).read_text()
        assert (yer in facts.split("Arayüzde görünür mü")[1]) == uses, yer


def test_the_engine_default_is_what_the_service_uses():
    import inspect

    from credit_coach import scoring_service

    src = inspect.getsource(scoring_service.Servis.degerlendir)
    assert "sec_from_scores(" in src and "delta=" not in src  # no delta passed: catalog default


def test_missing_raw_data_gives_a_clear_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(baseline, "CSV", tmp_path / "yok.csv")
    monkeypatch.setattr(target_segment, "REPORT", tmp_path / "r.md")
    assert target_segment.main([]) == 2
    assert "Ham veri bulunamadı" in capsys.readouterr().err
    assert not (tmp_path / "r.md").exists()
    assert json.loads((ROOT / "configs" / "forbidden_phrases.json").read_text())["ifadeler"]
