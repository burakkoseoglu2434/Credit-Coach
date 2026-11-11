"""Customer-facing wording guard: no outcome promises or causal claims in ADR, report, catalog
and template files. Quoted negations ("... denmez", "... yazılmaz") are allowed."""

import json
import re
from pathlib import Path

from credit_coach.features import MANIFEST_PATH

ROOT = MANIFEST_PATH.parents[1]
FORBIDDEN = json.loads((ROOT / "configs" / "forbidden_phrases.json").read_text())["ifadeler"]
NEGATIONS = ("denmez", "yazılmaz", "kullanılmaz", "demez", "yasak", "savunulamaz", "kaldırıldı")


def scanned_files() -> list[Path]:
    files = sorted((ROOT / "docs" / "adr").glob("*.md"))
    files += sorted((ROOT / "docs").glob("week*.md"))
    files += sorted((ROOT / "configs" / "catalog").glob("*.yaml"))
    files += [ROOT / "backend" / "src" / "credit_coach" / "schemas.py"]  # API field text
    files += [ROOT / "frontend" / "src" / "texts.json"]  # all UI texts
    files += [ROOT / "docs" / "CLAIMS.md", ROOT / "README.md"]
    files += [
        p
        for p in [
            ROOT / "docs" / "demo_portfolio_report.md",
            ROOT / "docs" / "demo_effect_share.md",
            ROOT / "docs" / "demo_resilience_labels.md",
        ]
        if p.exists()
    ]
    files += (
        sorted((ROOT / "configs" / "templates").glob("*"))
        if (ROOT / "configs" / "templates").exists()
        else []
    )
    return files


def offending_lines(text: str) -> list[str]:
    bad = []
    for line in text.splitlines():
        low = line.lower()
        if any(p in low for p in FORBIDDEN) and not any(n in low for n in NEGATIONS):
            bad.append(line.strip())
    return bad


def test_scan_covers_the_expected_files():
    names = {p.name for p in scanned_files()}
    assert {
        "003-approval-rule-and-hurdle.md",
        "005-recourse-catalog.md",
        "v1.yaml",
        "api_v0.yaml",
        "schemas.py",
        "texts.json",
        "CLAIMS.md",
        "README.md",
        "demo_effect_share.md",
        "demo_resilience_labels.md",
    } <= names


def test_detector_catches_forbidden_phrases():
    assert offending_lines("Bu adımla onaylanırsın.")
    assert offending_lines("Riskin düşecek.")
    assert offending_lines("Onay garantidir.")
    assert not offending_lines('"onaylanırsın" yazılmaz.')


def test_no_forbidden_wording_in_docs_and_catalog():
    found = {
        str(p.relative_to(ROOT)): offending_lines(p.read_text(encoding="utf-8"))
        for p in scanned_files()
    }
    assert {k: v for k, v in found.items() if v} == {}


def test_phrase_list_is_lowercase():
    assert all(p == p.lower() and not re.search(r"\s{2,}", p) for p in FORBIDDEN)
