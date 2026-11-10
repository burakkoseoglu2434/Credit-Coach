"""Rule coverage report: every rule and reason code must be triggered by at least one scenario.

Usage: python -m credit_coach.rule_coverage [--check]   (exit 1 if coverage is incomplete or the
committed report is stale)
"""

from __future__ import annotations

import sys
from collections import defaultdict

from credit_coach.bundle import ROOT
from credit_coach.contract import ReasonCode, RuleId, parse_input
from credit_coach.decision_engine import decide
from credit_coach.decision_scenarios import policy_variant, sample_basvuru, scenarios

REPORT = ROOT / "docs" / "week3_rule_coverage.md"


def run() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    by_rule: dict[str, list[str]] = defaultdict(list)
    by_code: dict[str, list[str]] = defaultdict(list)
    for s in scenarios():
        girdi = parse_input(
            {
                "basvuru": sample_basvuru(),
                "p_low": s.p[0],
                "p_point": s.p[1],
                "p_high": s.p[2],
                "ham_skor": s.ham_skor,
                "politika_surumu": "v1",
                "plan_available": s.plan_available,
            }
        )
        d = decide(girdi, policy_variant(**dict(s.policy_updates)))
        label = s.name + (" (politika varyantı)" if s.policy_updates else "")
        for r in d.tetiklenen_kurallar:
            by_rule[r.value].append(label)
        for c in d.gerekce_kodlari:
            by_code[c.value].append(label)
    return by_rule, by_code


def render(by_rule: dict[str, list[str]], by_code: dict[str, list[str]]) -> str:
    lines = [
        "# Hafta 3: kural kapsama raporu",
        "",
        "Her kural ve gerekçe kodu en az bir senaryoyla tetiklenmelidir. "
        '"politika varyantı" işaretli senaryolar v1\'in kendisiyle değil, ret eşiği veya '
        "zayıf destek aralığı değiştirilmiş bir politikayla çalışır "
        "(v1'de R1 pasif, R3 bu eşikte hiç tetiklenmez).",
        "",
        "| Kural | Tetikleyen senaryolar |",
        "|---|---|",
    ]
    lines += [f"| {r.value} | {', '.join(by_rule.get(r.value, [])) or '**YOK**'} |" for r in RuleId]
    lines += ["", "| Gerekçe kodu | Tetikleyen senaryolar |", "|---|---|"]
    lines += [
        f"| {c.value} | {', '.join(by_code.get(c.value, [])) or '**YOK**'} |" for c in ReasonCode
    ]
    return "\n".join(lines) + "\n"


def missing(by_rule, by_code) -> list[str]:
    return [r.value for r in RuleId if r.value not in by_rule] + [
        c.value for c in ReasonCode if c.value not in by_code
    ]


def main(argv: list[str]) -> int:
    by_rule, by_code = run()
    text = render(by_rule, by_code)
    gaps = missing(by_rule, by_code)
    if "--check" in argv:
        stale = not REPORT.exists() or REPORT.read_text() != text
        if gaps or stale:
            print("coverage gaps:", gaps, "| report stale:", stale)
            return 1
        return 0
    REPORT.write_text(text)
    print(text)
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
