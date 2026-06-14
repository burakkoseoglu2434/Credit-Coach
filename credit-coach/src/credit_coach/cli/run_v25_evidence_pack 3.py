from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
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
    p = argparse.ArgumentParser(description="Build Phase 68 deterministic evidence pack (v2.5)")
    p.add_argument("--cohort_dir", type=str, required=True, help="Directory containing cohort_metrics.json")
    p.add_argument(
        "--outcome_run_tables_dir",
        type=str,
        default="",
        help="Directory containing outcome_realization_evaluation.json (optional)",
    )
    p.add_argument(
        "--planning_root",
        type=str,
        default="",
        help="Override repo `.planning` directory for tests (optional)",
    )
    p.add_argument("--alpha", type=float, default=0.05, help="Alpha level for conservative intervals (default 0.05)")
    return p.parse_args()


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".planning").exists():
            return candidate
    return start


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ratio(k: int, n: int) -> float:
    if n <= 0:
        return 0.0
    return float(k) / float(n)


def _format_pct(value: float | None, *, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * float(value):.{digits}f}%"


def _format_rate(value: float | None, *, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _format_int(value: Any) -> str:
    try:
        return str(int(value))
    except Exception:
        return "0"


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


def _z_from_alpha(alpha: float) -> float:
    # Conservative z-values for common alpha levels (two-sided).
    # Avoid scipy dependency; fall back to 1.96.
    a = float(alpha)
    if abs(a - 0.10) < 1e-12:
        return 1.6448536269514722
    if abs(a - 0.05) < 1e-12:
        return 1.959963984540054
    if abs(a - 0.01) < 1e-12:
        return 2.5758293035489004
    return 1.959963984540054


@dataclass(frozen=True)
class ProportionStat:
    k: int
    n: int
    p: float
    lb: float
    ub: float


def _proportion_from_rate(*, p: float, n: int, alpha: float) -> ProportionStat:
    n_int = int(n)
    if n_int <= 0:
        return ProportionStat(k=0, n=0, p=0.0, lb=0.0, ub=0.0)
    k = int(round(float(p) * n_int))
    k = max(0, min(n_int, k))
    lb, ub = _wilson_interval(k, n_int, alpha=alpha)
    return ProportionStat(k=k, n=n_int, p=float(p), lb=lb, ub=ub)


def _conservative_delta_bounds(a: ProportionStat, b: ProportionStat) -> tuple[float, float]:
    # Conservative bounds for delta = a - b using independent Wilson bounds.
    return a.lb - b.ub, a.ub - b.lb


def _guard_scan(text: str) -> list[str]:
    import re

    hits: list[str] = []
    for pattern in BANNED_LANGUAGE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def _decision_classification(
    *,
    sample_size: int,
    sampling_with_replacement: bool,
    recoverable_full_sample_size: int,
    trust_clean: bool,
    outcome_evidence_status: str | None,
) -> str:
    if not trust_clean:
        return "inconclusive"
    if (
        sample_size >= 500
        and (not sampling_with_replacement)
        and recoverable_full_sample_size >= 50
        and (outcome_evidence_status or "no_data") in {"partial", "sufficient"}
    ):
        return "strong evidence"
    return "weak evidence"


def build_evidence_pack(
    *,
    cohort_dir: Path,
    outcome_run_tables_dir: Path | None,
    planning_root: Path,
    alpha: float,
) -> dict[str, Path]:
    cohort_metrics_path = cohort_dir / "cohort_metrics.json"
    cohort = _load_json(cohort_metrics_path)

    evaluation = dict(cohort.get("evaluation", {}))
    sampling = dict(cohort.get("sampling", {}))
    overall = dict(cohort.get("overall", {}))
    populations = dict(cohort.get("population_metrics", {}))

    global_denied = dict(populations.get("global_denied", {}))
    recoverable_full = dict(populations.get("recoverable_full_mode", {}))
    limited_control = dict(populations.get("non_recoverable_limited_mode", {}))

    sample_size = int(evaluation.get("sample_size", overall.get("sample_size", 0)) or 0)
    unique_denied_available = int(sampling.get("unique_denied_available", 0) or 0)
    with_replacement = bool(sampling.get("with_replacement", False))
    recoverable_full_n = int(recoverable_full.get("sample_size", 0) or 0)

    trust_counters = {
        "selected_invalid_winner_count": int(overall.get("selected_invalid_winner_count", 0) or 0),
        "selected_surface_drift_count": int(overall.get("selected_surface_drift_count", 0) or 0),
        "operator_packet_contradiction_count": int(overall.get("operator_packet_contradiction_count", 0) or 0),
    }
    trust_clean = sum(trust_counters.values()) == 0

    global_movement = _proportion_from_rate(
        p=float(global_denied.get("movement_rate", 0.0) or 0.0),
        n=int(global_denied.get("sample_size", 0) or 0),
        alpha=alpha,
    )
    recov_movement = _proportion_from_rate(
        p=float(recoverable_full.get("movement_rate", 0.0) or 0.0),
        n=int(recoverable_full.get("sample_size", 0) or 0),
        alpha=alpha,
    )
    global_strong = _proportion_from_rate(
        p=float(global_denied.get("strong_movement_rate", 0.0) or 0.0),
        n=int(global_denied.get("sample_size", 0) or 0),
        alpha=alpha,
    )
    recov_strong = _proportion_from_rate(
        p=float(recoverable_full.get("strong_movement_rate", 0.0) or 0.0),
        n=int(recoverable_full.get("sample_size", 0) or 0),
        alpha=alpha,
    )
    movement_delta_lb, movement_delta_ub = _conservative_delta_bounds(recov_movement, global_movement)
    strong_delta_lb, strong_delta_ub = _conservative_delta_bounds(recov_strong, global_strong)

    outcome_summary: dict[str, Any] | None = None
    outcome_evidence_status: str | None = None
    outcome_paths: dict[str, str] = {}
    if outcome_run_tables_dir is not None:
        outcome_eval_path = outcome_run_tables_dir / "outcome_realization_evaluation.json"
        if outcome_eval_path.exists():
            outcome_summary = _load_json(outcome_eval_path)
            outcome_evidence_status = str(outcome_summary.get("overall", {}).get("evidence_status", "no_data"))
            outcome_paths = {
                "outcome_realization_evaluation_json": str(outcome_eval_path),
                "outcome_realization_report_md": str(outcome_run_tables_dir / "outcome_realization_report.md"),
                "outcome_realization_summary_json": str(outcome_run_tables_dir / "outcome_realization_summary.json"),
                "path_realization_summary_json": str(outcome_run_tables_dir / "path_realization_summary.json"),
                "action_execution_events_csv": str(outcome_run_tables_dir / "action_execution_events.csv"),
            }

    classification = _decision_classification(
        sample_size=sample_size,
        sampling_with_replacement=with_replacement,
        recoverable_full_sample_size=recoverable_full_n,
        trust_clean=trust_clean,
        outcome_evidence_status=outcome_evidence_status,
    )

    planning_root.mkdir(parents=True, exist_ok=True)
    report_path = planning_root / "68-COHORT-REPORT.md"
    executive_path = planning_root / "68-EXECUTIVE-SUMMARY.md"
    decision_path = planning_root / "68-DECISION.md"

    non_attribution_guardrails = [
        "## Descriptive Guardrails",
        "",
        "- This pack summarizes observed artifact outputs from the shipped runtime and does not make cause-and-effect claims.",
        "- Differences between slices are descriptive comparisons only; they do not establish downstream business outcomes.",
        "- Sparse or missing observations must be treated as incomplete evidence rather than success or failure.",
    ]

    dataset_limitation_lines = [
        "## Dataset Limitation",
        "",
        f"- Canonical denied cohort size under shipped runtime on `full_processed`: {sample_size} (full available denied population)",
        f"- Unique denied available: {unique_denied_available}",
        f"- Sampling mode: {'with_replacement' if with_replacement else 'without_replacement'}",
    ]

    trust_lines = [
        "## Trust Evidence",
        "",
        "- Trust counters (cohort overall):",
        f"  - selected_invalid_winner_count: {trust_counters['selected_invalid_winner_count']}",
        f"  - selected_surface_drift_count: {trust_counters['selected_surface_drift_count']}",
        f"  - operator_packet_contradiction_count: {trust_counters['operator_packet_contradiction_count']}",
    ]

    capability_lines = [
        "## Capability Evidence (Cohort Runner Outputs)",
        "",
        f"- global_denied sample_size: {_format_int(global_denied.get('sample_size', 0))}",
        f"- recoverable_full_mode sample_size: {_format_int(recoverable_full.get('sample_size', 0))}",
        f"- non_recoverable_limited_mode sample_size: {_format_int(limited_control.get('sample_size', 0))}",
        "",
        "### Headline Rates",
        "",
        f"- Recoverable customer rate (denied cohort): {_format_pct(float(overall.get('recoverable_customer_rate', 0.0) or 0.0))}",
        f"- Threshold reach possible rate (denied cohort): {_format_pct(float(overall.get('threshold_reach_possible_rate', 0.0) or 0.0))}",
        "",
        "### Targeted Slice Comparison (Recoverable Full vs Global Denied)",
        "",
        f"- Movement rate (global): {_format_pct(global_movement.p)} (k={global_movement.k}, n={global_movement.n}; Wilson {_format_pct(global_movement.lb)}..{_format_pct(global_movement.ub)})",
        f"- Movement rate (recoverable/full): {_format_pct(recov_movement.p)} (k={recov_movement.k}, n={recov_movement.n}; Wilson {_format_pct(recov_movement.lb)}..{_format_pct(recov_movement.ub)})",
        f"- Movement delta (recoverable/full - global): {_format_pct(recov_movement.p - global_movement.p)} (conservative {_format_pct(movement_delta_lb)}..{_format_pct(movement_delta_ub)})",
        "",
        f"- Strong movement rate (global): {_format_pct(global_strong.p)} (k={global_strong.k}, n={global_strong.n}; Wilson {_format_pct(global_strong.lb)}..{_format_pct(global_strong.ub)})",
        f"- Strong movement rate (recoverable/full): {_format_pct(recov_strong.p)} (k={recov_strong.k}, n={recov_strong.n}; Wilson {_format_pct(recov_strong.lb)}..{_format_pct(recov_strong.ub)})",
        f"- Strong movement delta (recoverable/full - global): {_format_pct(recov_strong.p - global_strong.p)} (conservative {_format_pct(strong_delta_lb)}..{_format_pct(strong_delta_ub)})",
    ]

    realized_lines: list[str] = [
        "## Realized-Outcome Evidence (Outcome Feedback Layer)",
        "",
    ]
    if outcome_summary is None:
        realized_lines.extend(
            [
                "- Outcome feedback artifacts: not provided to this run (no realized-outcome evidence included).",
            ]
        )
    else:
        overall_out = dict(outcome_summary.get("overall", {}))
        realized_lines.extend(
            [
                f"- Window days: {_format_int(outcome_summary.get('window_days', 90))}",
                f"- Decisions: {_format_int(outcome_summary.get('total_decisions', 0))}",
                f"- Observed decisions: {_format_int(overall_out.get('observed_decisions', 0))}",
                f"- Observation coverage: {_format_pct(float(overall_out.get('observation_coverage_rate', 0.0) or 0.0))}",
                f"- Evidence status: {str(overall_out.get('evidence_status', 'no_data'))}",
                "",
                "- Artifact paths:",
                *[f"  - {k}: {v}" for k, v in outcome_paths.items() if v],
            ]
        )

    limitations = [
        "## Limitations",
        "",
        "- The canonical denied cohort reflects the full available denied population under the shipped runtime on the provided `full_processed` dataset; it is not an expanded population run.",
        "- Recoverable/full slice size is small in this cohort; uncertainty bounds reflect that.",
        "- Realized-outcome observation coverage may be sparse; treat realized metrics as descriptive evidence only.",
    ]

    next_work = [
        "## Recommendation (Next Work)",
        "",
        "- Expand `full_processed` denied coverage to increase evidence strength under the shipped runtime (aim for a larger denied cohort without replacement).",
        "- Increase recoverable/full representation (or explicitly collect a recoverable-heavy denied cohort) to support stable comparisons.",
        "- Ingest real action execution events and delayed outcome signals for the cohort to improve observation coverage.",
    ]

    report_lines = [
        "# Phase 68 Evidence Pack — Cohort Report",
        "",
        "## Source Artifacts",
        "",
        f"- Cohort dir: {str(cohort_dir)}",
        f"- Cohort metrics: {str(cohort_metrics_path)}",
        f"- Outcome tables dir: {str(outcome_run_tables_dir) if outcome_run_tables_dir is not None else ''}",
        "",
        *dataset_limitation_lines,
        "",
        *non_attribution_guardrails,
        "",
        *capability_lines,
        "",
        *trust_lines,
        "",
        *realized_lines,
        "",
        *limitations,
        "",
        *next_work,
        "",
    ]
    report_text = "\n".join(report_lines)

    executive_lines = [
        "# Phase 68 Executive Summary",
        "",
        "## Scope",
        f"- Canonical denied cohort (full available denied under shipped runtime): {sample_size}",
        f"- Sampling mode: {'with_replacement' if with_replacement else 'without_replacement'}",
        f"- Trust counters: invalid_winner={trust_counters['selected_invalid_winner_count']}, surface_drift={trust_counters['selected_surface_drift_count']}, operator_packet_contradiction={trust_counters['operator_packet_contradiction_count']}",
        "",
        "## What This Pack Contains",
        "- Capability metrics from the cohort runner (movement and threshold reach signals).",
        "- Trust-counter evidence from the same runtime artifacts.",
        "- Realized-outcome summaries from the outcome feedback layer (when observed).",
        "",
        "## Key Limitations",
        f"- Recoverable/full slice size: {recoverable_full_n} (small).",
        "- Observation coverage in realized-outcome layer may be sparse.",
        "",
        "## Recommendation",
        "- Prioritize more denied coverage and richer realized-outcome ingestion for the canonical cohort.",
        "",
        *non_attribution_guardrails,
        "",
    ]
    executive_text = "\n".join(executive_lines)

    decision_lines = [
        "# Phase 68 Decision",
        "",
        f"**Classification: {classification}**",
        "",
        "## Basis",
        f"- Cohort size (canonical, full available denied): {sample_size}",
        f"- Sampling mode: {'with_replacement' if with_replacement else 'without_replacement'}",
        f"- Recoverable/full slice size: {recoverable_full_n}",
        f"- Trust counters (overall): {trust_counters}",
        f"- Realized-outcome evidence status: {outcome_evidence_status or 'no_data'}",
        "",
        "## Next Work",
        *[f"- {line[2:]}" if line.startswith("- ") else f"- {line}" for line in next_work[2:]],
        "",
    ]
    decision_text = "\n".join(decision_lines)

    for name, text in {
        "68-COHORT-REPORT.md": report_text,
        "68-EXECUTIVE-SUMMARY.md": executive_text,
        "68-DECISION.md": decision_text,
    }.items():
        hits = _guard_scan(text)
        if hits:
            raise ValueError(f"Banned language detected in {name}: {hits}")

    report_path.write_text(report_text, encoding="utf-8")
    executive_path.write_text(executive_text, encoding="utf-8")
    decision_path.write_text(decision_text, encoding="utf-8")

    return {
        "report": report_path,
        "executive_summary": executive_path,
        "decision": decision_path,
    }


def main() -> None:
    args = parse_args()
    cohort_dir = Path(args.cohort_dir).expanduser().resolve()
    outcome_dir = Path(args.outcome_run_tables_dir).expanduser().resolve() if str(args.outcome_run_tables_dir).strip() else None

    repo_root = _find_repo_root(Path(__file__).resolve())
    planning_root = (
        Path(args.planning_root).expanduser().resolve()
        if str(args.planning_root).strip()
        else repo_root / ".planning" / "phases" / "68-real-cohort-evidence-run"
    )

    outputs = build_evidence_pack(
        cohort_dir=cohort_dir,
        outcome_run_tables_dir=outcome_dir,
        planning_root=planning_root,
        alpha=float(args.alpha),
    )
    for key, path in outputs.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()

