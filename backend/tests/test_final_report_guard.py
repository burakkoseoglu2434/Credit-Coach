import pytest

from credit_coach import final_test_report as f


def test_guard_refuses_when_report_exists(tmp_path, monkeypatch):
    fake = tmp_path / "week2_report.md"
    fake.write_text("done")
    monkeypatch.setattr(f, "REPORT", fake)
    with pytest.raises(SystemExit, match="already consumed"):
        f.guard()
