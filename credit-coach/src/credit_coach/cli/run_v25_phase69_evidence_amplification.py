from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.cli import run_v24_cohort_evaluation as cohort_eval
from credit_coach.evaluation.recoverability import resolve_recoverability_thresholds
from credit_coach.utils.run_context import load_config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 69: select recoverable-heavy cohort and rerun cohort evaluation (no sampling).")
    p.add_argument(
        "--canonical_cohort_dir",
        type=str,
        required=True,
        help="Phase 68 canonical cohort evaluation directory containing customer_level_analysis.csv",
    )
    p.add_argument(
        "--output_dir",
        type=str,
        default="",
        help="Output directory for Phase 69 cohort evaluation artifacts (default: artifacts/evaluations/<timestamped_dir>)",
    )
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--dataset_scope", type=str, default="full_processed", choices=["full_processed", "test_only"])
    p.add_argument("--min_desired_n", type=int, default=50, help="If near-threshold gap cutoff yields fewer than this, relax to mid cutoff.")
    p.add_argument("--sample_seed", type=int, default=42, help="Seed carried for run-id convention only (manifest mode does not sample).")
    return p.parse_args()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _cohort_output_dir(*, project_root: Path, output_dir: str) -> Path:
    if str(output_dir).strip():
        return Path(output_dir).expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (project_root / "artifacts" / "evaluations" / f"v25_phase69_recoverable_heavy_eval_{timestamp}").resolve()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[3]

    canonical_dir = Path(args.canonical_cohort_dir).expanduser().resolve()
    customer_level_path = canonical_dir / "customer_level_analysis.csv"
    if not customer_level_path.exists():
        raise FileNotFoundError(f"Missing canonical customer_level_analysis.csv: {customer_level_path}")

    rec_cfg = load_config(project_root / args.recourse_config)
    thresholds = resolve_recoverability_thresholds(rec_cfg.get("segment_caps", {}))
    near_upper = _safe_float(thresholds.get("near_upper"), 0.10)
    mid_upper = _safe_float(thresholds.get("mid_upper"), 0.25)

    df = pd.read_csv(customer_level_path)
    if df.empty:
        raise ValueError("Canonical customer_level_analysis.csv is empty.")
    if "source_customer_id" not in df.columns:
        raise ValueError("Canonical customer_level_analysis.csv must include `source_customer_id`.")
    if "threshold_reach_possible" not in df.columns or "approval_gap" not in df.columns:
        raise ValueError("Canonical customer_level_analysis.csv must include `threshold_reach_possible` and `approval_gap`.")

    df = df.copy()
    df["threshold_reach_possible"] = pd.to_numeric(df["threshold_reach_possible"], errors="coerce").fillna(0).astype(int)
    df["approval_gap"] = pd.to_numeric(df["approval_gap"], errors="coerce").fillna(0.0).astype(float)

    primary = df[df["threshold_reach_possible"].astype(int) == 1].copy()
    if primary.empty:
        raise ValueError("Phase 69 selection yielded zero customers for primary filter: threshold_reach_possible=true.")

    cutoff_label = "near_upper"
    cutoff_value = near_upper
    secondary = primary[primary["approval_gap"] <= cutoff_value].copy()
    if int(len(secondary)) < int(args.min_desired_n):
        cutoff_label = "mid_upper_relaxed"
        cutoff_value = mid_upper
        secondary = primary[primary["approval_gap"] <= cutoff_value].copy()

    output_root = _cohort_output_dir(project_root=project_root, output_dir=args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_path = output_root / "selected_customer_ids.csv"
    secondary = secondary.sort_values(["approval_gap", "source_customer_id"], ascending=[True, True], kind="stable").reset_index(drop=True)
    secondary[["source_customer_id", "approval_gap", "threshold_reach_possible"]].to_csv(manifest_path, index=False)

    selection_summary = {
        "phase": "69-evidence-amplification",
        "selection_rule_version": "phase_69_v1",
        "canonical_phase68_cohort_dir": str(canonical_dir),
        "canonical_denied_population_n": int(len(df)),
        "primary_filter": "threshold_reach_possible == true",
        "secondary_filter": "approval_gap cutoff (lowest-gap segment)",
        "near_upper": near_upper,
        "mid_upper": mid_upper,
        "min_desired_n": int(args.min_desired_n),
        "cutoff_label_used": cutoff_label,
        "cutoff_value_used": float(cutoff_value),
        "eligible_primary_n": int(len(primary)),
        "eligible_secondary_n": int(len(secondary)),
        "dataset_scope": str(args.dataset_scope),
        "dataset_limitation_note": "Phase 69 is a filtered cohort from the full available denied population under shipped runtime (Phase 68 canonical denied n).",
    }
    (output_root / "selection_summary.json").write_text(
        json.dumps(selection_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    eval_args = argparse.Namespace(
        base_config=str(args.base_config),
        model_config=str(args.model_config),
        recourse_config=str(args.recourse_config),
        causality_config=str(args.causality_config),
        safety_config=str(args.safety_config),
        macro_config=str(args.macro_config),
        dataset_scope=str(args.dataset_scope),
        n_customers=int(len(secondary)),
        sample_seed=int(args.sample_seed),
        model_version="",
        model_manifest="",
        output_dir=str(output_root),
        customer_manifest_csv=str(manifest_path),
    )
    cohort_eval.run(eval_args)

    print(str(output_root))


if __name__ == "__main__":
    main()

