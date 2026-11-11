from credit_coach import baseline, portfolio_report


def test_missing_raw_data_gives_a_clear_error_and_no_report(monkeypatch, tmp_path, capsys):
    missing = tmp_path / "yok" / "lending_club.csv"
    monkeypatch.setattr(baseline, "CSV", missing)
    monkeypatch.setattr(portfolio_report, "REPORT", tmp_path / "rapor.md")
    assert portfolio_report.main([]) == 2
    err = capsys.readouterr().err
    assert str(missing) in err and "Ham veri bulunamadı" in err
    assert not (tmp_path / "rapor.md").exists()


def test_report_text_states_the_test_split_is_not_rerun():
    import inspect

    src = inspect.getsource(portfolio_report)
    assert "docs/week2_report.md" in src and "yeniden çalıştırılmadı" in src
