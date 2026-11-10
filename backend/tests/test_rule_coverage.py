from credit_coach.rule_coverage import REPORT, main, missing, render, run


def test_every_rule_and_reason_code_is_triggered_by_a_scenario():
    by_rule, by_code = run()
    assert missing(by_rule, by_code) == []


def test_committed_coverage_report_is_current():
    assert REPORT.exists(), "run `python -m credit_coach.rule_coverage` and commit the report"
    assert REPORT.read_text() == render(*run())
    assert main(["--check"]) == 0
