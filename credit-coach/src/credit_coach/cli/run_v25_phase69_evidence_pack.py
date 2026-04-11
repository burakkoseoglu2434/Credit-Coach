from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


BANNED_LANGUAGE_PATTERNS = (
    r"\bcausal\b",
    r"\buplift\b",
    r"\bguarantee\b",
    r"\bproves\b",
    r"\bincreases approvals\b",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Phase 69 deterministic evidence pack (recoverable-heavy cohort).")
    p.add_argument("--phase69_cohort_dir", type=str, required=True, help="Directory containing Phase 69 cohort_metrics.json")
    p.add_argument(
        "--phase68_baseline_cohort_dir",
        type=str,
        required=True,
        help="Directory containing Phase 68 canonical cohort_metrics.json (baseline for comparison).",
    )
    p.add_argument(
        "--outcome_tables_dir",
        type=str,
        default="",
        help="Optional tables dir containing outcome_realization_evaluation.json (synthetic or observed; must be labeled).",
    )
    p.add_argument(
        "--planning_root",
        type=str,
        default="",
        help="Override output planning directory (default: .planning/phases/69-evidence-amplification).",
    )
    p.add_argument("--alpha", type=float, default=0.05, help="Alpha level for conservative intervals (default 0.05)")
    return p.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _format_pct(value: float | None, *, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * float(value):.{digits}f}%"


def _format_rate(value: float | None, *, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _z_from_alpha(alpha: float) -> float:
    a = float(alpha)
    if abs(a - 0.10) < 1e-12:
        return 1.6448536269514722
    if abs(a - 0.05) < 1e-12:
        return 1.959963984540054
    if abs(a - 0.01) < 1e-12:
        return 2.5758293035489004
    return 1.959963984540054


def _wilson_interval(k: int, n: int, *, alpha: float) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    if k < 0 or k > n:
        raise ValueError("k must satisfy 0 <= k <= n")
    z = _z_from_alpha(alpha)
    phat = k / n
    denom = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2.0 * n)) / denom
    radius = (z / denom) * math.sqrt((phat * (1.0 - phat) / n) + (z * z) / (4.0 * n * n))
    return max(0.0, center - radius), min(1.0, center + radius)


def _k_from_rate(p: float, n: int) -> int:
    if n <= 0:
        return 0
    k = int(round(float(p) * float(n)))
    return max(0, min(int(n), int(k)))


def _guard_scan(text: str) -> list[str]:
    import re

    hits: list[str] = []
    for pattern in BANNED_LANGUAGE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def _trust_counters(overall: dict[str, Any]) -> dict[str, int]:
    return {
        "selected_invalid_winner_count": _safe_int(overall.get("selected_invalid_winner_count", 0)),
        "selected_surface_drift_count": _safe_int(overall.get("selected_surface_drift_count", 0)),
        "operator_packet_contradiction_count": _safe_int(overall.get("operator_packet_contradiction_count", 0)),
    }


def _decision_classification(
    *,
    trust_clean: bool,
    cohort_n: int,
    min_sufficient_n: int,
    movement_delta_lb: float | None,
    strong_movement_delta_lb: float | None,
) -> str:
    if not trust_clean:
        return "inconclusive"
    if cohort_n <= 0:
        return "inconclusive"
    if cohort_n < min_sufficient_n:
        return "weak evidence"
    if movement_delta_lb is not None and strong_movement_delta_lb is not None and movement_delta_lb > 0.0 and strong_movement_delta_lb > 0.0:
        return "strong evidence"
    return "weak evidence"


def build_phase69_evidence_pack(
    *,
    phase69_cohort_dir: Path,
    phase68_baseline_dir: Path,
    outcome_tables_dir: Path | None,
    planning_root: Path,
    alpha: float,
) -> dict[str, Path]:
    phase69_metrics = _load_json(phase69_cohort_dir / "cohort_metrics.json")
    phase68_metrics = _load_json(phase68_baseline_dir / "cohort_metrics.json")

    phase69_overall = dict(phase69_metrics.get("overall", {}) or {})
    phase68_overall = dict(phase68_metrics.get("overall", {}) or {})
    phase69_sampling = dict(phase69_metrics.get("sampling", {}) or {})
    phase68_sampling = dict(phase68_metrics.get("sampling", {}) or {})

    phase69_pop = dict(phase69_metrics.get("population_metrics", {}) or {})
    phase68_pop = dict(phase68_metrics.get("population_metrics", {}) or {})
    p69_global = dict(phase69_pop.get("global_denied", {}) or {})
    p68_global = dict(phase68_pop.get("global_denied", {}) or {})
    p69_recov = dict(phase69_pop.get("recoverable_full_mode", {}) or {})
    p68_recov = dict(phase68_pop.get("recoverable_full_mode", {}) or {})

    cohort_n = _safe_int(phase69_overall.get("sample_size", 0))
    baseline_n = _safe_int(phase68_overall.get("sample_size", 0))

    trust = _trust_counters(phase69_overall)
    trust_clean = sum(trust.values()) == 0

    manifest_path = phase69_cohort_dir / "selected_customer_ids.csv"
    selection_summary_path = phase69_cohort_dir / "selection_summary.json"
    selection_summary = _load_json(selection_summary_path) if selection_summary_path.exists() else {}
    manifest_hash = _sha256_file(manifest_path) if manifest_path.exists() else ""

    # Deltas vs Phase 68 baseline global denied (descriptive only).
    p69_movement = _safe_float(p69_global.get("movement_rate", 0.0))
    p68_movement = _safe_float(p68_global.get("movement_rate", 0.0))
    p69_strong = _safe_float(p69_global.get("strong_movement_rate", 0.0))
    p68_strong = _safe_float(p68_global.get("strong_movement_rate", 0.0))
    movement_delta = p69_movement - p68_movement
    strong_delta = p69_strong - p68_strong

    # Conservative bounds using independent Wilson bounds.
    p69_m_k = _k_from_rate(p69_movement, _safe_int(p69_global.get("sample_size", 0)))
    p68_m_k = _k_from_rate(p68_movement, _safe_int(p68_global.get("sample_size", 0)))
    p69_m_lb, p69_m_ub = _wilson_interval(p69_m_k, _safe_int(p69_global.get("sample_size", 0)), alpha=alpha)
    p68_m_lb, p68_m_ub = _wilson_interval(p68_m_k, _safe_int(p68_global.get("sample_size", 0)), alpha=alpha)
    movement_delta_lb = p69_m_lb - p68_m_ub
    movement_delta_ub = p69_m_ub - p68_m_lb

    p69_s_k = _k_from_rate(p69_strong, _safe_int(p69_global.get("sample_size", 0)))
    p68_s_k = _k_from_rate(p68_strong, _safe_int(p68_global.get("sample_size", 0)))
    p69_s_lb, p69_s_ub = _wilson_interval(p69_s_k, _safe_int(p69_global.get("sample_size", 0)), alpha=alpha)
    p68_s_lb, p68_s_ub = _wilson_interval(p68_s_k, _safe_int(p68_global.get("sample_size", 0)), alpha=alpha)
    strong_delta_lb = p69_s_lb - p68_s_ub
    strong_delta_ub = p69_s_ub - p68_s_lb

    min_sufficient_n = 50
    classification = _decision_classification(
        trust_clean=trust_clean,
        cohort_n=cohort_n,
        min_sufficient_n=min_sufficient_n,
        movement_delta_lb=movement_delta_lb,
        strong_movement_delta_lb=strong_delta_lb,
    )

    outcome_eval: dict[str, Any] | None = None
    if outcome_tables_dir is not None:
        p = outcome_tables_dir / "outcome_realization_evaluation.json"
        if p.exists():
            outcome_eval = _load_json(p)

    planning_root.mkdir(parents=True, exist_ok=True)
    report_path = planning_root / "69-COHORT-REPORT.md"
    executive_path = planning_root / "69-EXECUTIVE-SUMMARY.md"
    decision_path = planning_root / "69-DECISION.md"
    comparison_path = planning_root / "69-EVIDENCE-COMPARISON.md"

    dataset_lines = [
        "## Dataset Limitation",
        "",
        f"- Phase 68 canonical denied population under shipped runtime (`full_processed`): {baseline_n}",
        f"- Phase 69 cohort is a filtered subset of that denied population (selection is deterministic and auditable).",
        f"- Phase 69 cohort size (all eligible): {cohort_n}",
    ]
    selection_lines = [
        "## Cohort Selection (Deterministic)",
        "",
        f"- Canonical Phase 68 cohort dir: `{phase68_baseline_dir}`",
        f"- Selection summary: `{selection_summary_path}`" if selection_summary_path.exists() else "- Selection summary: n/a",
        f"- Manifest: `{manifest_path}`" if manifest_path.exists() else "- Manifest: n/a",
        f"- Manifest SHA256: `{manifest_hash}`" if manifest_hash else "- Manifest SHA256: n/a",
        "",
        f"- Primary filter: {selection_summary.get('primary_filter', 'threshold_reach_possible == true')}",
        f"- Secondary filter: {selection_summary.get('secondary_filter', 'approval_gap cutoff')}",
        f"- Cutoff used: {selection_summary.get('cutoff_label_used', '')} = {selection_summary.get('cutoff_value_used', '')}",
        f"- Eligible primary n: {_safe_int(selection_summary.get('eligible_primary_n', 0))}",
        f"- Eligible secondary n: {_safe_int(selection_summary.get('eligible_secondary_n', 0))}",
    ]
    trust_lines = [
        "## Trust Evidence",
        "",
        "- Trust counters (Phase 69 cohort overall):",
        f"  - selected_invalid_winner_count: {trust['selected_invalid_winner_count']}",
        f"  - selected_surface_drift_count: {trust['selected_surface_drift_count']}",
        f"  - operator_packet_contradiction_count: {trust['operator_packet_contradiction_count']}",
    ]

    outcome_lines: list[str] = [
        "## Realized-Outcome Evidence (Additive)",
        "",
        "- This section is descriptive and does not make cause-and-effect claims.",
        "- If the provided outcome tables are synthetic, they are labeled synthetic and must not be treated as observed outcomes.",
    ]
    if outcome_tables_dir is None:
        outcome_lines.append("- Outcome tables dir: not provided")
    else:
        outcome_lines.append(f"- Outcome tables dir: `{outcome_tables_dir}`")
        if outcome_eval is None:
            outcome_lines.append("- outcome_realization_evaluation.json: not found")
        else:
            overall = dict(outcome_eval.get("overall", {}) or {})
            outcome_lines.extend(
                [
                    f"- Decisions observed: {_safe_int(overall.get('total_decisions', 0))}",
                    f"- Observation coverage: {_format_pct(overall.get('observation_coverage_rate'))}",
                    f"- Realized movement rate: {_format_pct(overall.get('realized_movement_rate'))}",
                    f"- Threshold-reaching realization rate: {_format_pct(overall.get('threshold_reach_realization_rate'))}",
                    f"- Evidence status: {str(overall.get('evidence_status', 'no_data'))}",
                ]
            )

    rubric_lines = [
        "## Classification Rubric (Deterministic, Descriptive)",
        "",
        "- `inconclusive` if any trust counter is non-zero or if required artifacts are missing.",
        f"- `weak evidence` if trust-clean but Phase 69 cohort size < {min_sufficient_n} (insufficient population for stable conclusions).",
        f"- `strong evidence` requires (all): trust-clean, Phase 69 cohort size ≥ {min_sufficient_n}, and conservative lower-bounds for both movement-rate and strong-movement-rate deltas vs Phase 68 baseline are > 0 (descriptive concentration evidence only).",
        "",
        f"- Phase 69 cohort size: {cohort_n}",
        f"- Trust-clean: {trust_clean}",
        f"- Movement rate delta vs Phase 68 baseline (point): {_format_rate(movement_delta)}",
        f"- Movement rate delta bounds (conservative): [{_format_rate(movement_delta_lb)}, {_format_rate(movement_delta_ub)}]",
        f"- Strong movement rate delta vs Phase 68 baseline (point): {_format_rate(strong_delta)}",
        f"- Strong movement rate delta bounds (conservative): [{_format_rate(strong_delta_lb)}, {_format_rate(strong_delta_ub)}]",
    ]

    report = "\n".join(
        [
            "# Phase 69 Evidence Pack — Cohort Report",
            "",
            "This report is descriptive and does not make cause-and-effect claims.",
            "",
            *dataset_lines,
            "",
            *selection_lines,
            "",
            "## Capability Evidence (Phase 69 Cohort Metrics)",
            "",
            f"- Phase 69 cohort metrics: `{phase69_cohort_dir / 'cohort_metrics.json'}`",
            f"- movement_rate (global_denied): {_format_pct(p69_global.get('movement_rate'))}",
            f"- strong_movement_rate (global_denied): {_format_pct(p69_global.get('strong_movement_rate'))}",
            f"- threshold_reach_possible_rate (global_denied): {_format_pct(p69_global.get('threshold_reach_possible_rate'))}",
            f"- threshold_reach_priority_rate (global_denied): {_format_pct(p69_global.get('threshold_reach_priority_rate'))}",
            f"- recoverable_customer_rate (global_denied): {_format_pct(p69_global.get('recoverable_customer_rate'))}",
            f"- selected_path_movement_strength_distribution (global_denied): `{json.dumps(p69_global.get('selected_path_movement_strength_distribution', {}) or {}, ensure_ascii=False)}`",
            "",
            *trust_lines,
            "",
            *outcome_lines,
            "",
            *rubric_lines,
            "",
            "## Result",
            "",
            f"- Classification: **{classification}**",
            "",
        ]
    )

    executive = "\n".join(
        [
            "# Phase 69 Executive Summary",
            "",
            "Descriptive summary only (no cause-and-effect claims).",
            "",
            f"- Phase 68 canonical denied population (full available denied under shipped runtime): {baseline_n}",
            f"- Phase 69 cohort (filtered from Phase 68 denied): {cohort_n}",
            f"- Trust counters (Phase 69): {trust}",
            f"- Phase 69 movement_rate (global_denied): {_format_pct(p69_global.get('movement_rate'))}",
            f"- Phase 69 strong_movement_rate (global_denied): {_format_pct(p69_global.get('strong_movement_rate'))}",
            f"- Phase 69 threshold_reach_possible_rate (global_denied): {_format_pct(p69_global.get('threshold_reach_possible_rate'))}",
            f"- Phase 69 classification: {classification}",
            "",
            "No cause-and-effect or business-impact claims are made in this summary.",
            "",
        ]
    )

    decision = "\n".join(
        [
            "# Phase 69 Decision",
            "",
            f"- Classification: **{classification}**",
            f"- Trust-clean: {trust_clean}",
            f"- Cohort size: {cohort_n} (minimum sufficient n: {min_sufficient_n})",
            f"- Next work: expand eligible population (if possible) and re-run Phase 69 selection + evaluation; keep all runtime logic unchanged.",
            "",
        ]
    )

    comparison = "\n".join(
        [
            "# Phase 69 vs Phase 68 — Evidence Comparison (Descriptive)",
            "",
            "No cause-and-effect attribution is made in this comparison.",
            "",
            "## Cohort Sizes",
            "",
            f"- Phase 68 (canonical denied): {baseline_n}",
            f"- Phase 69 (recoverable-heavy filtered cohort): {cohort_n}",
            "",
            "## Like-for-like Metrics (Global Denied Slice)",
            "",
            f"- movement_rate: Phase 69 {_format_pct(p69_movement)} vs Phase 68 {_format_pct(p68_movement)} (delta {_format_pct(movement_delta, digits=1)})",
            f"- strong_movement_rate: Phase 69 {_format_pct(p69_strong)} vs Phase 68 {_format_pct(p68_strong)} (delta {_format_pct(strong_delta, digits=1)})",
            f"- threshold_reach_possible_rate: Phase 69 {_format_pct(p69_global.get('threshold_reach_possible_rate'))} vs Phase 68 {_format_pct(p68_global.get('threshold_reach_possible_rate'))}",
            f"- threshold_reach_priority_rate: Phase 69 {_format_pct(p69_global.get('threshold_reach_priority_rate'))} vs Phase 68 {_format_pct(p68_global.get('threshold_reach_priority_rate'))}",
            "",
            "## Recoverable / Full Mode Slice (Reference)",
            "",
            f"- Phase 69 recoverable_full_mode n: {_safe_int(p69_recov.get('sample_size', 0))}",
            f"- Phase 68 recoverable_full_mode n: {_safe_int(p68_recov.get('sample_size', 0))}",
            f"- Phase 69 recoverable_full_mode movement_rate: {_format_pct(p69_recov.get('movement_rate'))}",
            f"- Phase 68 recoverable_full_mode movement_rate: {_format_pct(p68_recov.get('movement_rate'))}",
            "",
        ]
    )

    report_hits = _guard_scan(report) + _guard_scan(executive) + _guard_scan(decision) + _guard_scan(comparison)
    if report_hits:
        raise ValueError(f"Banned language patterns detected in Phase 69 docs: {sorted(set(report_hits))}")

    report_path.write_text(report, encoding="utf-8")
    executive_path.write_text(executive, encoding="utf-8")
    decision_path.write_text(decision, encoding="utf-8")
    comparison_path.write_text(comparison, encoding="utf-8")

    return {
        "69-COHORT-REPORT.md": report_path,
        "69-EXECUTIVE-SUMMARY.md": executive_path,
        "69-DECISION.md": decision_path,
        "69-EVIDENCE-COMPARISON.md": comparison_path,
    }


def main() -> None:
    args = parse_args()
    phase69_dir = Path(args.phase69_cohort_dir).expanduser().resolve()
    phase68_dir = Path(args.phase68_baseline_cohort_dir).expanduser().resolve()
    outcome_tables_dir = Path(args.outcome_tables_dir).expanduser().resolve() if str(args.outcome_tables_dir).strip() else None
    planning_root = Path(args.planning_root).expanduser().resolve() if str(args.planning_root).strip() else (Path(__file__).resolve().parents[4] / ".planning" / "phases" / "69-evidence-amplification")
    build_phase69_evidence_pack(
        phase69_cohort_dir=phase69_dir,
        phase68_baseline_dir=phase68_dir,
        outcome_tables_dir=outcome_tables_dir,
        planning_root=planning_root,
        alpha=float(args.alpha),
    )
    print(str(planning_root))


if __name__ == "__main__":
    main()
