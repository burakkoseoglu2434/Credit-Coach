from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.evaluation.fairness import build_canonical_segment_key
from credit_coach.model.registry import build_frozen_model_manifest, resolve_model_manifest
from credit_coach.ops.kpi_contract import (
    build_comparative_impact_summary,
    build_kpi_contract_snapshot,
    build_milestone_acceptance_summary,
    build_release_evidence_pack,
    load_kpi_thresholds,
    render_milestone_acceptance_review,
)
from credit_coach.ops.release_decision import (
    aggregate_release_metrics,
    build_pilot_guardrails,
    build_rollback_conditions,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_phase_experiment_suite")
_HIGH_RISK_ACTIVATION_FLOOR = 0.05


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run phase experiment suite (quick + 1000x5 scale)")
    p.add_argument("--phase_name", type=str, default="phase_exec")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/experiments/recourse_phaseb_hybrid_v2.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--quick_n", type=int, default=200)
    p.add_argument("--quick_seed", type=int, default=42)
    p.add_argument("--scale_n", type=int, default=1000)
    p.add_argument("--scale_seeds", type=str, default="42,43,44,45,46")
    p.add_argument("--n_workers", type=int, default=5)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument(
        "--skip_train_before_batch",
        action="store_true",
        help="If set, phase suite reuses current model artifacts and does not run train once at start.",
    )
    p.add_argument("--milestone", type=str, default="current")
    p.add_argument("--model_version", type=str, default="")
    p.add_argument("--model_manifest", type=str, default="")
    p.add_argument("--execute", action="store_true")
    return p.parse_args()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_seeds(raw: str) -> list[int]:
    vals = [x.strip() for x in str(raw).split(",") if x.strip()]
    seeds = [int(v) for v in vals]
    if not seeds:
        raise ValueError("scale_seeds cannot be empty")
    return seeds


def _extract_run_id(text: str) -> str:
    m = re.findall(r"artifacts/runs/([0-9]{8}_[0-9]{6}_[0-9a-f]+_[0-9a-f]+)", text)
    return m[0] if m else ""


def _latest_optional_artifact(pattern: str) -> Path | None:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        return None
    return candidates[-1]


def _mirror_artifact(source: Path | None, destination: Path) -> bool:
    if source is None or not source.exists():
        return False
    destination.write_bytes(source.read_bytes())
    return True


def _run_cmd(*, cmd: list[str], cwd: Path, env: dict[str, str], label: str) -> tuple[str, str]:
    logger.info("Running %s: %s", label, " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True, check=False)
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (code={proc.returncode})\n{out[-4000:]}")
    run_id = _extract_run_id(out)
    if not run_id:
        raise RuntimeError(f"{label} succeeded but run_id not found")
    return run_id, out


def _batch_cmd(
    args: argparse.Namespace,
    *,
    n_customers: int,
    seed: int,
    model_version: str = "",
    model_manifest: str = "",
) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "credit_coach.cli.run_batch_recourse_eval",
        "--n_customers",
        str(int(n_customers)),
        "--sample_seed",
        str(int(seed)),
        "--log_every",
        str(int(args.log_every)),
        "--n_workers",
        str(int(args.n_workers)),
        "--base_config",
        str(args.base_config),
        "--model_config",
        str(args.model_config),
        "--recourse_config",
        str(args.recourse_config),
        "--causality_config",
        str(args.causality_config),
        "--safety_config",
        str(args.safety_config),
        "--macro_config",
        str(args.macro_config),
    ]
    if str(model_version).strip():
        cmd.extend(["--model_version", str(model_version).strip()])
    if str(model_manifest).strip():
        cmd.extend(["--model_manifest", str(model_manifest).strip()])
    return cmd


def _train_cmd(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-m",
        "credit_coach.cli.run_train",
        "--base_config",
        str(args.base_config),
        "--config",
        str(args.model_config),
    ]


def _smoke_cmd(args: argparse.Namespace, *, batch_run_id: str) -> list[str]:
    root = _project_root()
    base = root / "artifacts" / "runs" / batch_run_id / "tables"
    return [
        sys.executable,
        "-m",
        "credit_coach.cli.run_production_smoke",
        "--kpi_contract",
        str(args.kpi_contract),
        "--batch_summary_json",
        str(base / "batch_summary.json"),
        "--batch_fairness_change_csv",
        str(base / "batch_fairness_change.csv"),
    ]


def _build_registry_path(root: Path, model_cfg_path: str) -> Path:
    model_cfg = load_config(model_cfg_path) if Path(model_cfg_path).exists() else {}
    registry_path = Path(model_cfg.get("registry", {}).get("path", "artifacts/models"))
    if not registry_path.is_absolute():
        registry_path = root / registry_path
    return registry_path


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _round_metric(value: Any, *, digits: int = 6) -> float:
    try:
        metric = float(value)
    except Exception:
        return 0.0
    if pd.isna(metric):
        return 0.0
    return round(metric, digits)


def _kpi_checks(summary: dict[str, Any], fair_row: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, str]:
    snapshot = _seed_contract_snapshot(summary, fair_row, thresholds)
    return bool(snapshot["all_pass"]), str(snapshot["failed_checks"])


def _seed_contract_snapshot(
    summary: dict[str, Any],
    fair_row: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    return evaluate_seed_kpi_contract(summary, fair_row, thresholds)


def _build_phase_fairness_breakdown(
    *,
    seed_rows: list[dict[str, Any]],
    seed_breakdowns: list[pd.DataFrame],
) -> pd.DataFrame:
    output_rows: list[dict[str, Any]] = []
    snapshots_by_seed = {int(row["seed"]): row for row in seed_rows if "seed" in row}

    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty:
            continue
        seed = int(breakdown_df["seed"].iloc[0])
        snapshot = snapshots_by_seed.get(seed, {})
        working = breakdown_df.copy()
        if "candidate_source" not in working.columns and "best_source" in working.columns:
            working["candidate_source"] = working["best_source"]
        if "stress_band" not in working.columns:
            working["stress_band"] = "base"
        if "canonical_segment_key" not in working.columns:
            working["canonical_segment_key"] = working.apply(
                lambda row: build_canonical_segment_key(
                    risk_band=row.get("risk_band", "unknown"),
                    income_band=row.get("income_band", "unknown"),
                    stress_band=row.get("stress_band", "base"),
                ),
                axis=1,
            )
        if "failure_weight" not in working.columns:
            working["failure_weight"] = working.get("failure_severity_score", 0.0)
        if "fairness_guard_demoted_rate" not in working.columns:
            working["fairness_guard_demoted_rate"] = 0.0
        working["seed"] = int(seed)
        working["breakdown_type"] = "segment_candidate_source"
        output_rows.extend(working.to_dict(orient="records"))

        segment_rollup = (
            working.groupby(["seed", "canonical_segment_key", "risk_band", "income_band", "stress_band"], dropna=False)
            .agg(
                n_rows=("n_rows", "sum"),
                denied_rows=("denied_rows", "sum"),
                failure_weight=("failure_weight", "sum"),
                failure_severity_score=("failure_severity_score", "sum"),
                fairness_guard_demoted_rate=("fairness_guard_demoted_rate", "mean"),
            )
            .reset_index()
        )
        for row in segment_rollup.to_dict(orient="records"):
            output_rows.append(
                {
                    **row,
                    "breakdown_type": "seed_segment",
                    "candidate_source": "",
                    "best_source": "",
                    "group_bucket": "",
                    "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                }
            )

        risk_source_rollup = (
            working.groupby(["seed", "risk_band", "candidate_source"], dropna=False)
            .agg(
                n_rows=("n_rows", "sum"),
                denied_rows=("denied_rows", "sum"),
                failure_weight=("failure_weight", "sum"),
                failure_severity_score=("failure_severity_score", "sum"),
            )
            .reset_index()
        )
        for row in risk_source_rollup.to_dict(orient="records"):
            output_rows.append(
                {
                    **row,
                    "breakdown_type": "risk_band_source_rollup",
                    "income_band": "",
                    "stress_band": "base",
                    "group_bucket": "",
                    "best_source": row.get("candidate_source", ""),
                    "canonical_segment_key": build_canonical_segment_key(
                        risk_band=row.get("risk_band", "unknown"),
                        income_band="all",
                        stress_band="base",
                    ),
                    "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                }
            )

        high_stress_weight = float(snapshot.get("high_stress_fairness_gap_after", 0.0))
        if high_stress_weight > 0.0:
            for row in segment_rollup.to_dict(orient="records"):
                output_rows.append(
                    {
                        **row,
                        "breakdown_type": "high_stress_segment",
                        "candidate_source": "",
                        "best_source": "",
                        "group_bucket": "",
                        "stress_band": "high_stress",
                        "canonical_segment_key": build_canonical_segment_key(
                            risk_band=row.get("risk_band", "unknown"),
                            income_band=row.get("income_band", "unknown"),
                            stress_band="high_stress",
                        ),
                        "failure_weight": float(row.get("failure_weight", 0.0)) * high_stress_weight,
                        "primary_fail_reason": "high_stress_fairness_gap_after",
                    }
                )

        dominant_row = working.sort_values(
            ["failure_weight", "n_rows", "canonical_segment_key"],
            ascending=[False, False, True],
        ).head(1)
        dominant_segment_key = ""
        dominant_candidate_source = ""
        if not dominant_row.empty:
            dominant_segment_key = str(dominant_row.iloc[0].get("canonical_segment_key", ""))
            dominant_candidate_source = str(dominant_row.iloc[0].get("candidate_source", ""))
        output_rows.append(
            {
                "seed": int(seed),
                "breakdown_type": "seed_primary_fail_reason",
                "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                "failure_weight": float(snapshot.get("worst_fairness_gap", 0.0)),
                "failure_severity_score": float(snapshot.get("worst_fairness_gap", 0.0)),
                "canonical_segment_key": dominant_segment_key,
                "candidate_source": dominant_candidate_source,
                "best_source": dominant_candidate_source,
                "risk_band": "",
                "income_band": "",
                "stress_band": "",
                "group_bucket": "",
                "n_rows": 0,
                "denied_rows": 0,
            }
        )

    if not output_rows:
        return pd.DataFrame(
            columns=[
                "seed",
                "breakdown_type",
                "canonical_segment_key",
                "candidate_source",
                "primary_fail_reason",
                "failure_weight",
            ]
        )

    return pd.DataFrame(output_rows)


def _build_phase_candidate_quality_summary(scale_df: pd.DataFrame) -> dict[str, Any]:
    metric_fields = (
        "candidate_pool_diversity_index",
        "candidate_source_entropy",
        "best_source_internal_rate",
        "best_source_dice_rate",
        "best_source_rule_rate",
        "best_source_fallback_rate",
    )
    secondary_fields = tuple(f"high_risk_denied_{field}" for field in metric_fields)
    if scale_df.empty:
        return {
            "candidate_quality_population": "denied",
            "candidate_quality_secondary_population": "high_risk_denied",
            "source_catalog": ["internal", "dice", "rule", "fallback"],
            "seed_count": 0,
            "canonical_metrics": {field: 0.0 for field in metric_fields},
            "secondary_metrics": {field.replace("high_risk_denied_", ""): 0.0 for field in secondary_fields},
        }
    canonical_metrics = {
        field: _round_metric(pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
        for field in metric_fields
    }
    secondary_metrics = {
        field.replace("high_risk_denied_", ""): _round_metric(
            pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        )
        for field in secondary_fields
    }
    return {
        "candidate_quality_population": str(scale_df.get("candidate_quality_population", pd.Series(["denied"])).iloc[0]),
        "candidate_quality_secondary_population": str(
            scale_df.get("candidate_quality_secondary_population", pd.Series(["high_risk_denied"])).iloc[0]
        ),
        "source_catalog": ["internal", "dice", "rule", "fallback"],
        "seed_count": int(len(scale_df)),
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
    }


def _build_phase_candidate_source_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=["seed", "population", "candidate_source", "count", "share", "population_size", "breakdown_type"]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty:
            continue
        working = breakdown_df.copy()
        if "seed" not in working.columns:
            continue
        working["breakdown_type"] = "seed_population_source"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=["seed", "population", "candidate_source", "count", "share", "population_size", "breakdown_type"]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", "candidate_source"], dropna=False)
        .agg(
            count=("count", "sum"),
            share=("share", "mean"),
            population_size=("population_size", "sum"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_source_rollup"
    if "share" in rollup.columns:
        rollup["share"] = pd.to_numeric(rollup["share"], errors="coerce").fillna(0.0).round(6)
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _seed_direction_consistent(values: pd.Series) -> bool:
    series = pd.to_numeric(values, errors="coerce").fillna(0.0)
    positive = int((series > 1e-9).sum())
    negative = int((series < -1e-9).sum())
    nonzero = positive + negative
    if nonzero == 0:
        return True
    return max(positive, negative) >= ((nonzero // 2) + 1)


def _build_phase_high_risk_tuning_summary(
    scale_df: pd.DataFrame,
    *,
    release_decision: str,
) -> dict[str, Any]:
    if scale_df.empty:
        return {
            "primary_metric": "denied_high_risk_lift",
            "primary_metric_value": 0.0,
            "high_risk_profile_applied_rate": 0.0,
            "activation_floor": _HIGH_RISK_ACTIVATION_FLOOR,
            "meaningful_activation": False,
            "directional_consistency": False,
            "positive_seed_count": 0,
            "negative_seed_count": 0,
            "evidence_status": "diagnostic_only",
            "diagnostic_reasons": ["missing_seeded_rows"],
            "supporting_metrics": {
                "high_risk_reachability_rate": 0.0,
                "trajectory_partial_progress_rate": 0.0,
            },
        }

    primary_series = pd.to_numeric(scale_df.get("denied_high_risk_lift", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    activation_rate = _round_metric(
        pd.to_numeric(scale_df.get("high_risk_profile_applied_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
    )
    supporting_metrics = {
        "high_risk_reachability_rate": _round_metric(
            pd.to_numeric(scale_df.get("high_risk_reachability_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        ),
        "trajectory_partial_progress_rate": _round_metric(
            pd.to_numeric(scale_df.get("trajectory_partial_progress_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        ),
    }
    positive_seed_count = int((primary_series > 1e-9).sum())
    negative_seed_count = int((primary_series < -1e-9).sum())
    diagnostic_reasons: list[str] = []
    if activation_rate < _HIGH_RISK_ACTIVATION_FLOOR:
        diagnostic_reasons.append("activation_below_min_floor")
    if not _seed_direction_consistent(primary_series):
        diagnostic_reasons.append("seed_direction_unstable")
    if str(release_decision).strip().upper() == "NO_GO":
        diagnostic_reasons.append("release_gate_not_satisfied")
    if supporting_metrics["high_risk_reachability_rate"] <= 0.0:
        diagnostic_reasons.append("reachability_signal_not_positive")
    if supporting_metrics["trajectory_partial_progress_rate"] <= 0.0:
        diagnostic_reasons.append("trajectory_signal_not_positive")
    return {
        "primary_metric": "denied_high_risk_lift",
        "primary_metric_value": _round_metric(primary_series.mean()),
        "high_risk_profile_applied_rate": activation_rate,
        "activation_floor": _HIGH_RISK_ACTIVATION_FLOOR,
        "meaningful_activation": bool(activation_rate >= _HIGH_RISK_ACTIVATION_FLOOR),
        "directional_consistency": _seed_direction_consistent(primary_series),
        "positive_seed_count": positive_seed_count,
        "negative_seed_count": negative_seed_count,
        "evidence_status": "strong_evidence" if not diagnostic_reasons else "diagnostic_only",
        "diagnostic_reasons": diagnostic_reasons,
        "supporting_metrics": supporting_metrics,
    }


def _build_suite_impact_attribution_summary(
    *,
    phase_name: str,
    aggregate: dict[str, Any],
    evidence_level: str,
    evidence_status: str,
    seed_count: int,
) -> dict[str, Any]:
    return build_comparative_impact_summary(
        subject_label=str(phase_name),
        baseline_label="control_variant_unavailable",
        subject_metrics={
            "denied_to_approved_lift": aggregate.get("mean_denied_to_approved_lift", 0.0),
            "denied_high_risk_lift": aggregate.get("mean_denied_high_risk_lift", 0.0),
            "equalized_odds_gap_delta": aggregate.get("mean_equalized_odds_gap_delta", 0.0),
            "denied_reliability_violation_rate": aggregate.get("mean_denied_reliability_violation_rate", 0.0),
            "high_risk_reachability_rate": aggregate.get("mean_high_risk_reachability_rate", 0.0),
            "trajectory_partial_progress_rate": aggregate.get("mean_trajectory_partial_progress_rate", 0.0),
            "candidate_source_entropy": aggregate.get("mean_candidate_source_entropy", 0.0),
        },
        baseline_metrics=None,
        evidence_level=evidence_level,
        evidence_status=evidence_status,
        seed_count=seed_count,
        baseline_type="control_variant",
        diagnostic_reason="control_variant_baseline_not_available_in_suite_runner",
        metadata={
            "source_mix_snapshot": {
                "best_source_internal_rate": _round_metric(aggregate.get("mean_best_source_internal_rate", 0.0)),
                "best_source_dice_rate": _round_metric(aggregate.get("mean_best_source_dice_rate", 0.0)),
                "best_source_rule_rate": _round_metric(aggregate.get("mean_best_source_rule_rate", 0.0)),
                "best_source_fallback_rate": _round_metric(aggregate.get("mean_best_source_fallback_rate", 0.0)),
            }
        },
    )


def _render_release_review_summary(
    *,
    milestone_acceptance_summary: dict[str, Any],
) -> str:
    return render_milestone_acceptance_review(milestone_acceptance_summary)


def main() -> None:
    args = parse_args()
    seeds = _parse_seeds(args.scale_seeds)
    thresholds = load_kpi_thresholds(args.kpi_contract)
    root = _project_root()
    registry_path = _build_registry_path(root, args.model_config)
    explicit_model_version = str(args.model_version).strip()
    explicit_model_manifest = str(args.model_manifest).strip()
    if (explicit_model_version or explicit_model_manifest) and not bool(args.skip_train_before_batch):
        raise ValueError("Explicit model selectors require --skip_train_before_batch so suite execution stays unambiguous")

    run_ctx = create_run_context(
        {
            "mode": "phase_experiment_suite",
            "phase_name": str(args.phase_name),
            "quick_n": int(args.quick_n),
            "quick_seed": int(args.quick_seed),
            "scale_n": int(args.scale_n),
            "scale_seeds": seeds,
            "execute": bool(args.execute),
            "recourse_config": str(args.recourse_config),
        },
        base_artifact_dir="artifacts/runs",
    )

    if not args.execute:
        dry = {
            "train_once_cmd": _train_cmd(args),
            "quick_batch_cmd": _batch_cmd(
                args,
                n_customers=int(args.quick_n),
                seed=int(args.quick_seed),
                model_version=explicit_model_version,
                model_manifest=explicit_model_manifest,
            ),
            "scale_batch_cmd_template": _batch_cmd(
                args,
                n_customers=int(args.scale_n),
                seed=seeds[0],
                model_version=explicit_model_version,
                model_manifest=explicit_model_manifest,
            ),
            "scale_seeds": seeds,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "requested_model_version": explicit_model_version,
            "requested_model_manifest": explicit_model_manifest,
        }
        (run_ctx.tables_dir / "phase_suite_dry_run.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False), encoding="utf-8")
        run_ctx.save_metrics({"execute": False, "seed_count": len(seeds)})
        logger.info("Dry-run saved: %s", run_ctx.tables_dir / "phase_suite_dry_run.json")
        return

    outcome_feedback_summary_source = _latest_optional_artifact("*/tables/outcome_feedback_summary.json")
    outcome_policy_summary_source = _latest_optional_artifact("*/tables/outcome_policy_summary.csv")
    outcome_policy_deltas_source = _latest_optional_artifact("*/tables/outcome_policy_deltas.json")
    mirrored_outcome_feedback = _mirror_artifact(
        outcome_feedback_summary_source,
        run_ctx.tables_dir / "outcome_feedback_summary.json",
    )
    mirrored_outcome_policy_summary = _mirror_artifact(
        outcome_policy_summary_source,
        run_ctx.tables_dir / "outcome_policy_summary.csv",
    )
    mirrored_outcome_policy_deltas = _mirror_artifact(
        outcome_policy_deltas_source,
        run_ctx.tables_dir / "outcome_policy_deltas.json",
    )
    outcome_feedback_summary = (
        json.loads((run_ctx.tables_dir / "outcome_feedback_summary.json").read_text(encoding="utf-8"))
        if mirrored_outcome_feedback
        else {}
    )

    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/mplcache")
    env.setdefault("TQDM_DISABLE", "1")

    train_run_id = ""
    resolved_model_manifest: dict[str, Any]
    if not bool(args.skip_train_before_batch):
        train_run_id, train_log = _run_cmd(
            cmd=_train_cmd(args),
            cwd=root,
            env=env,
            label="train_once",
        )
        (run_ctx.tables_dir / "train_once.log").write_text(train_log, encoding="utf-8")
        resolved_model_manifest = resolve_model_manifest(
            base_path=registry_path,
            model_version=train_run_id,
        )
    elif explicit_model_version or explicit_model_manifest:
        resolved_model_manifest = resolve_model_manifest(
            base_path=registry_path,
            model_version=explicit_model_version or None,
            manifest_path=explicit_model_manifest or None,
        )
    else:
        resolved_model_manifest = resolve_model_manifest(base_path=registry_path)
    frozen_model_manifest = build_frozen_model_manifest(
        resolved_model_manifest,
        project_root=root,
        resolved_by_runner="run_phase_experiment_suite",
        training_run_id=train_run_id or str(resolved_model_manifest.get("model_version", "")).strip(),
    )
    (run_ctx.tables_dir / "frozen_model_manifest.json").write_text(
        json.dumps(frozen_model_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    quick_run_id, quick_log = _run_cmd(
        cmd=_batch_cmd(
            args,
            n_customers=int(args.quick_n),
            seed=int(args.quick_seed),
            model_manifest=str(resolved_model_manifest.get("manifest_path", "")),
        ),
        cwd=root,
        env=env,
        label="quick_batch",
    )
    (run_ctx.tables_dir / "quick_batch.log").write_text(quick_log, encoding="utf-8")

    quick_smoke_run_id, quick_smoke_log = _run_cmd(
        cmd=_smoke_cmd(args, batch_run_id=quick_run_id),
        cwd=root,
        env=env,
        label="quick_smoke",
    )
    (run_ctx.tables_dir / "quick_smoke.log").write_text(quick_smoke_log, encoding="utf-8")

    quick_summary = _load_json(root / "artifacts" / "runs" / quick_run_id / "tables" / "batch_summary.json")
    quick_fair = pd.read_csv(root / "artifacts" / "runs" / quick_run_id / "tables" / "batch_fairness_change.csv").iloc[0].to_dict()
    quick_snapshot = _seed_contract_snapshot(quick_summary, quick_fair, thresholds)
    quick_ok = bool(quick_snapshot["all_pass"])
    quick_failed = str(quick_snapshot["failed_checks"])
    quick_payload = {
        "run_id": quick_run_id,
        "smoke_run_id": quick_smoke_run_id,
        "all_pass": bool(quick_ok),
        "failed_checks": quick_failed,
        "lift_pass": bool(quick_snapshot["lift_pass"]),
        "reliability_pass": bool(quick_snapshot["reliability_pass"]),
        "fairness_seed_pass": bool(quick_snapshot["fairness_seed_pass"]),
        "primary_fail_reason": str(quick_snapshot["primary_fail_reason"]),
        "worst_fairness_gap": float(quick_snapshot["worst_fairness_gap"]),
        "model_version": str(resolved_model_manifest.get("model_version", "")),
        "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
    }
    (run_ctx.tables_dir / "phase_quick_summary.json").write_text(json.dumps(quick_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    scale_rows: list[dict[str, Any]] = []
    seed_breakdowns: list[pd.DataFrame] = []
    seed_candidate_source_breakdowns: list[pd.DataFrame] = []
    for seed in seeds:
        run_id, run_log = _run_cmd(
            cmd=_batch_cmd(
                args,
                n_customers=int(args.scale_n),
                seed=int(seed),
                model_manifest=str(resolved_model_manifest.get("manifest_path", "")),
            ),
            cwd=root,
            env=env,
            label=f"scale_batch_seed_{seed}",
        )
        (run_ctx.tables_dir / f"scale_seed_{seed}.log").write_text(run_log, encoding="utf-8")

        summary = _load_json(root / "artifacts" / "runs" / run_id / "tables" / "batch_summary.json")
        fair_row = pd.read_csv(root / "artifacts" / "runs" / run_id / "tables" / "batch_fairness_change.csv").iloc[0].to_dict()
        breakdown_df = _load_csv(root / "artifacts" / "runs" / run_id / "tables" / "fairness_failure_breakdown.csv")
        candidate_quality_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "candidate_quality_summary.json"
        )
        candidate_source_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "candidate_source_breakdown.csv"
        )
        canonical_candidate_metrics = (
            candidate_quality_summary.get("canonical_metrics", {})
            if isinstance(candidate_quality_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        secondary_candidate_metrics = (
            candidate_quality_summary.get("secondary_metrics", {})
            if isinstance(candidate_quality_summary.get("secondary_metrics", {}), dict)
            else {}
        )
        snapshot = _seed_contract_snapshot(summary, fair_row, thresholds)
        scale_rows.append(
            {
                "seed": int(seed),
                "run_id": run_id,
                "model_version": str(summary.get("model_version", resolved_model_manifest.get("model_version", ""))),
                "model_freeze_mode": str(summary.get("model_freeze_mode", resolved_model_manifest.get("freeze_mode", "implicit_latest"))),
                "all_pass": int(snapshot["all_pass"]),
                "failed_checks": str(snapshot["failed_checks"]),
                "lift_pass": int(snapshot["lift_pass"]),
                "reliability_pass": int(snapshot["reliability_pass"]),
                "fairness_seed_pass": int(snapshot["fairness_seed_pass"]),
                "primary_fairness_metric": str(snapshot["primary_fairness_metric"]),
                "primary_fail_reason": str(snapshot["primary_fail_reason"]),
                "worst_fairness_gap": float(snapshot["worst_fairness_gap"]),
                "denied_to_approved_lift": float(summary.get("denied_to_approved_lift", 0.0)),
                "denied_high_risk_lift": float(summary.get("denied_high_risk_lift", 0.0)),
                "high_risk_reachability_rate": float(summary.get("high_risk_reachability_rate", 0.0)),
                "denied_reliability_violation_rate": float(summary.get("denied_reliability_violation_rate", 0.0)),
                "sync_latency_p95_ms": float(summary.get("sync_latency_p95_ms", summary.get("latency_p95_ms", 0.0))),
                "sync_latency_p99_ms": float(summary.get("sync_latency_p99_ms", summary.get("latency_p99_ms", 0.0))),
                "equalized_odds_gap_delta": float(snapshot["equalized_odds_gap_delta"]),
                "approval_gap_delta": float(snapshot["approval_gap_delta"]),
                "recourse_success_gap": float(snapshot["recourse_success_gap"]),
                "fairness_gap_after": float(snapshot["fairness_gap_after"]),
                "high_stress_fairness_gap_after": float(snapshot["high_stress_fairness_gap_after"]),
                "fairness_guard_demotion_count": int(summary.get("fairness_guard_demotion_count", 0)),
                "fairness_guard_stop_reason": str(summary.get("fairness_guard_stop_reason", "")),
                "error_rate": float(summary.get("error_rate", 0.0)),
                "trajectory_gate_pass_rate_4w": float(summary.get("trajectory_gate_pass_rate_4w", 0.0)),
                "trajectory_gate_pass_rate_12w": float(summary.get("trajectory_gate_pass_rate_12w", 0.0)),
                "trajectory_gate_pass_rate_24w": float(summary.get("trajectory_gate_pass_rate_24w", 0.0)),
                "trajectory_partial_progress_rate": float(summary.get("trajectory_partial_progress_rate", 0.0)),
                "trajectory_median_time_to_gate_pass_days": float(summary.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
                "high_risk_profile_applied_rate": float(summary.get("high_risk_profile_applied_rate", 0.0)),
                "candidate_quality_population": str(candidate_quality_summary.get("canonical_population", "denied")),
                "candidate_quality_secondary_population": str(
                    candidate_quality_summary.get("secondary_population", "high_risk_denied")
                ),
                "candidate_pool_diversity_index": float(
                    canonical_candidate_metrics.get("candidate_pool_diversity_index", summary.get("denied_candidate_pool_diversity_index", 0.0))
                ),
                "candidate_source_entropy": float(
                    canonical_candidate_metrics.get("candidate_source_entropy", summary.get("denied_candidate_source_entropy", 0.0))
                ),
                "best_source_internal_rate": float(
                    canonical_candidate_metrics.get("best_source_internal_rate", summary.get("denied_best_source_internal_rate", 0.0))
                ),
                "best_source_dice_rate": float(
                    canonical_candidate_metrics.get("best_source_dice_rate", summary.get("denied_best_source_dice_rate", 0.0))
                ),
                "best_source_rule_rate": float(
                    canonical_candidate_metrics.get("best_source_rule_rate", summary.get("denied_best_source_rule_rate", 0.0))
                ),
                "best_source_fallback_rate": float(
                    canonical_candidate_metrics.get("best_source_fallback_rate", summary.get("denied_best_source_fallback_rate", 0.0))
                ),
                "high_risk_denied_candidate_pool_diversity_index": float(
                    secondary_candidate_metrics.get(
                        "candidate_pool_diversity_index",
                        summary.get("high_risk_denied_candidate_pool_diversity_index", 0.0),
                    )
                ),
                "high_risk_denied_candidate_source_entropy": float(
                    secondary_candidate_metrics.get(
                        "candidate_source_entropy",
                        summary.get("high_risk_denied_candidate_source_entropy", 0.0),
                    )
                ),
                "high_risk_denied_best_source_internal_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_internal_rate",
                        summary.get("high_risk_denied_best_source_internal_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_dice_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_dice_rate",
                        summary.get("high_risk_denied_best_source_dice_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_rule_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_rule_rate",
                        summary.get("high_risk_denied_best_source_rule_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_fallback_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_fallback_rate",
                        summary.get("high_risk_denied_best_source_fallback_rate", 0.0),
                    )
                ),
            }
        )
        if not breakdown_df.empty:
            breakdown_df["seed"] = int(seed)
            breakdown_df["primary_fail_reason"] = str(snapshot["primary_fail_reason"])
            seed_breakdowns.append(breakdown_df)
        if not candidate_source_breakdown.empty:
            candidate_source_breakdown["seed"] = int(seed)
            seed_candidate_source_breakdowns.append(candidate_source_breakdown)

    scale_df = pd.DataFrame(scale_rows).sort_values("seed").reset_index(drop=True)
    scale_path = run_ctx.tables_dir / "phase_scale_seed_summary.csv"
    scale_df.to_csv(scale_path, index=False)
    phase_breakdown_df = _build_phase_fairness_breakdown(seed_rows=scale_rows, seed_breakdowns=seed_breakdowns)
    phase_breakdown_path = run_ctx.tables_dir / "fairness_failure_breakdown.csv"
    phase_breakdown_df.to_csv(phase_breakdown_path, index=False)
    phase_candidate_quality_summary = _build_phase_candidate_quality_summary(scale_df)
    candidate_quality_summary_path = run_ctx.tables_dir / "candidate_quality_summary.json"
    candidate_quality_summary_path.write_text(
        json.dumps(phase_candidate_quality_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_candidate_source_breakdown = _build_phase_candidate_source_breakdown(seed_candidate_source_breakdowns)
    candidate_source_breakdown_path = run_ctx.tables_dir / "candidate_source_breakdown.csv"
    phase_candidate_source_breakdown.to_csv(candidate_source_breakdown_path, index=False)

    aggregate = {
        "seed_count": int(len(scale_df)),
        "pass_count": int(scale_df["all_pass"].sum()),
        "model_version": str(resolved_model_manifest.get("model_version", "")),
        "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        "frozen_model_manifest_path": "tables/frozen_model_manifest.json",
        **aggregate_release_metrics(
            scale_df.to_dict(orient="records"),
            thresholds=thresholds,
            breakdown_rows=phase_breakdown_df.to_dict(orient="records"),
        ),
        "mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
        "mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
        "mean_high_risk_reachability_rate": float(scale_df["high_risk_reachability_rate"].mean()),
        "mean_denied_reliability_violation_rate": float(scale_df["denied_reliability_violation_rate"].mean()),
        "mean_sync_latency_p95_ms": float(scale_df["sync_latency_p95_ms"].mean()),
        "mean_sync_latency_p99_ms": float(scale_df["sync_latency_p99_ms"].mean()),
        "mean_equalized_odds_gap_delta": float(scale_df["equalized_odds_gap_delta"].mean()),
        "mean_approval_gap_delta": float(scale_df["approval_gap_delta"].mean()),
        "mean_recourse_success_gap": float(scale_df["recourse_success_gap"].mean()),
        "mean_fairness_gap_after": float(scale_df["fairness_gap_after"].mean()),
        "mean_high_stress_fairness_gap_after": float(scale_df["high_stress_fairness_gap_after"].mean()),
        "max_fairness_guard_demotion_count": int(scale_df["fairness_guard_demotion_count"].max()),
        "mean_error_rate": float(scale_df["error_rate"].mean()),
        "mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
        "mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
        "mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
        "mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
        "mean_trajectory_median_time_to_gate_pass_days": float(scale_df["trajectory_median_time_to_gate_pass_days"].mean()),
        "mean_high_risk_profile_applied_rate": float(scale_df["high_risk_profile_applied_rate"].mean()),
        "candidate_quality_population": str(phase_candidate_quality_summary["candidate_quality_population"]),
        "candidate_quality_secondary_population": str(
            phase_candidate_quality_summary["candidate_quality_secondary_population"]
        ),
        "mean_candidate_pool_diversity_index": float(scale_df["candidate_pool_diversity_index"].mean()),
        "mean_candidate_source_entropy": float(scale_df["candidate_source_entropy"].mean()),
        "mean_best_source_internal_rate": float(scale_df["best_source_internal_rate"].mean()),
        "mean_best_source_dice_rate": float(scale_df["best_source_dice_rate"].mean()),
        "mean_best_source_rule_rate": float(scale_df["best_source_rule_rate"].mean()),
        "mean_best_source_fallback_rate": float(scale_df["best_source_fallback_rate"].mean()),
        "mean_high_risk_denied_candidate_pool_diversity_index": float(
            scale_df["high_risk_denied_candidate_pool_diversity_index"].mean()
        ),
        "mean_high_risk_denied_candidate_source_entropy": float(
            scale_df["high_risk_denied_candidate_source_entropy"].mean()
        ),
        "mean_high_risk_denied_best_source_internal_rate": float(
            scale_df["high_risk_denied_best_source_internal_rate"].mean()
        ),
        "mean_high_risk_denied_best_source_dice_rate": float(scale_df["high_risk_denied_best_source_dice_rate"].mean()),
        "mean_high_risk_denied_best_source_rule_rate": float(scale_df["high_risk_denied_best_source_rule_rate"].mean()),
        "mean_high_risk_denied_best_source_fallback_rate": float(
            scale_df["high_risk_denied_best_source_fallback_rate"].mean()
        ),
    }
    (run_ctx.tables_dir / "phase_scale_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    release_payload = evaluate_release_decision(aggregate, thresholds)
    (run_ctx.tables_dir / "release_decision.json").write_text(
        json.dumps(release_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_high_risk_tuning_summary = _build_phase_high_risk_tuning_summary(
        scale_df,
        release_decision=str(release_payload["decision"]),
    )
    (run_ctx.tables_dir / "high_risk_tuning_summary.json").write_text(
        json.dumps(phase_high_risk_tuning_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if release_payload["decision"] == "LIMITED_GO":
        (run_ctx.tables_dir / "pilot_guardrails.json").write_text(
            json.dumps(build_pilot_guardrails(aggregate), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_ctx.tables_dir / "rollback_conditions.json").write_text(
            json.dumps(build_rollback_conditions(aggregate, thresholds), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    supporting_artifacts = {
        "phase_quick_summary_json": "tables/phase_quick_summary.json",
        "phase_scale_seed_summary_csv": "tables/phase_scale_seed_summary.csv",
        "phase_scale_aggregate_json": "tables/phase_scale_aggregate.json",
        "fairness_failure_breakdown_csv": "tables/fairness_failure_breakdown.csv",
        "candidate_quality_summary_json": "tables/candidate_quality_summary.json",
        "candidate_source_breakdown_csv": "tables/candidate_source_breakdown.csv",
        "high_risk_tuning_summary_json": "tables/high_risk_tuning_summary.json",
        "generator_policy_impact_json": "tables/generator_policy_impact.json",
        "release_decision_json": "tables/release_decision.json",
        "frozen_model_manifest_json": "tables/frozen_model_manifest.json",
        "release_evidence_pack_json": "tables/release_evidence_pack.json",
    }
    if mirrored_outcome_feedback:
        supporting_artifacts["outcome_feedback_summary_json"] = "tables/outcome_feedback_summary.json"
    if mirrored_outcome_policy_summary:
        supporting_artifacts["outcome_policy_summary_csv"] = "tables/outcome_policy_summary.csv"
    if mirrored_outcome_policy_deltas:
        supporting_artifacts["outcome_policy_deltas_json"] = "tables/outcome_policy_deltas.json"
    if release_payload["decision"] == "LIMITED_GO":
        supporting_artifacts["pilot_guardrails_json"] = "tables/pilot_guardrails.json"
        supporting_artifacts["rollback_conditions_json"] = "tables/rollback_conditions.json"

    seed_count = int(len(scale_df))
    evidence_level = "seeded_suite" if seed_count > 1 else "single_run_fallback"
    acceptance_eligible = bool(frozen_model_manifest.get("acceptance_eligible", False)) and seed_count > 1
    evidence_status = "complete"
    degraded_reason = ""
    missing_artifacts: list[str] = []
    if seed_count <= 1:
        evidence_level = "single_run_fallback"
        evidence_status = "degraded"
        acceptance_eligible = False
        degraded_reason = "insufficient_repeated_seeded_evidence"
        missing_artifacts.append("repeated_seeded_evidence")
    elif not bool(frozen_model_manifest.get("acceptance_eligible", False)):
        evidence_status = "degraded"
        degraded_reason = "implicit_latest_model_freeze"

    impact_attribution_summary = _build_suite_impact_attribution_summary(
        phase_name=str(args.phase_name),
        aggregate=aggregate,
        evidence_level=evidence_level,
        evidence_status=evidence_status,
        seed_count=seed_count,
    )
    (run_ctx.tables_dir / "generator_policy_impact.json").write_text(
        json.dumps(impact_attribution_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    kpi_contract_snapshot = build_kpi_contract_snapshot(
        runner_type="suite",
        release_payload=release_payload,
        aggregate_metrics=aggregate,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(resolved_model_manifest.get("model_version", "")),
        model_freeze_mode=str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        missing_artifacts=missing_artifacts,
        metadata={
            "phase_name": str(args.phase_name),
            "train_run_id": str(train_run_id),
            "frozen_model_manifest_path": "tables/frozen_model_manifest.json",
            "candidate_quality_summary": phase_candidate_quality_summary,
            "high_risk_tuning_summary": phase_high_risk_tuning_summary,
            "impact_attribution_summary": impact_attribution_summary,
            "outcome_feedback_summary": outcome_feedback_summary,
        },
    )
    (run_ctx.tables_dir / "kpi_contract_snapshot.json").write_text(
        json.dumps(kpi_contract_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    milestone_acceptance_summary = build_milestone_acceptance_summary(
        phase=str(args.phase_name),
        milestone=str(args.milestone),
        runner_type="suite",
        release_payload=release_payload,
        aggregate_metrics=aggregate,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(resolved_model_manifest.get("model_version", "")),
        model_freeze_mode=str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        missing_artifacts=missing_artifacts,
        metadata={
            "candidate_quality_summary": phase_candidate_quality_summary,
            "high_risk_tuning_summary": phase_high_risk_tuning_summary,
            "impact_attribution_summary": impact_attribution_summary,
            "outcome_feedback_summary": outcome_feedback_summary,
        },
    )
    milestone_acceptance_review = render_milestone_acceptance_review(milestone_acceptance_summary)
    (run_ctx.tables_dir / "milestone_acceptance_summary.json").write_text(
        json.dumps(milestone_acceptance_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "milestone_acceptance_review.md").write_text(
        milestone_acceptance_review,
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "release_review_summary.md").write_text(
        _render_release_review_summary(
            milestone_acceptance_summary=milestone_acceptance_summary,
        ),
        encoding="utf-8",
    )
    required_release_artifacts = {
        "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
        "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
        "phase_scale_seed_summary_csv": "tables/phase_scale_seed_summary.csv",
        "phase_scale_aggregate_json": "tables/phase_scale_aggregate.json",
        "fairness_failure_breakdown_csv": "tables/fairness_failure_breakdown.csv",
        "candidate_quality_summary_json": "tables/candidate_quality_summary.json",
        "candidate_source_breakdown_csv": "tables/candidate_source_breakdown.csv",
        "telemetry_export_json": "tables/telemetry_export.json",
        "milestone_acceptance_review_md": "tables/milestone_acceptance_review.md",
    }
    optional_release_artifacts = {
        "release_decision_json": "tables/release_decision.json",
        "release_review_summary_md": "tables/release_review_summary.md",
        "frozen_model_manifest_json": "tables/frozen_model_manifest.json",
        "high_risk_tuning_summary_json": "tables/high_risk_tuning_summary.json",
        "generator_policy_impact_json": "tables/generator_policy_impact.json",
    }
    if mirrored_outcome_feedback:
        optional_release_artifacts["outcome_feedback_summary_json"] = "tables/outcome_feedback_summary.json"
    if mirrored_outcome_policy_summary:
        optional_release_artifacts["outcome_policy_summary_csv"] = "tables/outcome_policy_summary.csv"
    if mirrored_outcome_policy_deltas:
        optional_release_artifacts["outcome_policy_deltas_json"] = "tables/outcome_policy_deltas.json"
    if release_payload["decision"] == "LIMITED_GO":
        optional_release_artifacts["pilot_guardrails_json"] = "tables/pilot_guardrails.json"
        optional_release_artifacts["rollback_conditions_json"] = "tables/rollback_conditions.json"
    release_evidence_pack = build_release_evidence_pack(
        runner_type="suite",
        phase=str(args.phase_name),
        milestone=str(args.milestone),
        release_decision=str(milestone_acceptance_summary["release_decision"]),
        acceptance_status=str(milestone_acceptance_summary["acceptance_status"]),
        evidence_level=str(milestone_acceptance_summary["evidence_level"]),
        evidence_status=str(milestone_acceptance_summary["evidence_status"]),
        acceptance_eligible=bool(milestone_acceptance_summary["acceptance_eligible"]),
        required_artifacts=required_release_artifacts,
        optional_artifacts=optional_release_artifacts,
        existing_artifacts=[
            f"tables/{path.name}"
            for path in run_ctx.tables_dir.iterdir()
            if path.is_file()
        ],
    )
    (run_ctx.tables_dir / "release_evidence_pack.json").write_text(
        json.dumps(release_evidence_pack, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    milestone_acceptance_summary["release_pack_summary"] = {
        "pack_status": str(release_evidence_pack["pack_status"]),
        "pack_acceptance_eligible": bool(release_evidence_pack["pack_acceptance_eligible"]),
        "required_artifacts": dict(release_evidence_pack["required_artifacts"]),
        "optional_artifacts": dict(release_evidence_pack["optional_artifacts"]),
        "missing_artifacts": list(release_evidence_pack["missing_artifacts"]),
    }
    milestone_acceptance_review = render_milestone_acceptance_review(milestone_acceptance_summary)
    (run_ctx.tables_dir / "milestone_acceptance_summary.json").write_text(
        json.dumps(milestone_acceptance_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "milestone_acceptance_review.md").write_text(
        milestone_acceptance_review,
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "release_review_summary.md").write_text(
        _render_release_review_summary(
            milestone_acceptance_summary=milestone_acceptance_summary,
        ),
        encoding="utf-8",
    )

    run_ctx.save_metrics(
        {
            "phase_name": str(args.phase_name),
            "train_run_id": train_run_id,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "model_version": str(resolved_model_manifest.get("model_version", "")),
            "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
            "quick_run_id": quick_run_id,
            "quick_all_pass": bool(quick_ok),
            "quick_lift_pass": bool(quick_snapshot["lift_pass"]),
            "quick_reliability_pass": bool(quick_snapshot["reliability_pass"]),
            "quick_fairness_seed_pass": bool(quick_snapshot["fairness_seed_pass"]),
            "scale_pass_count": int(scale_df["all_pass"].sum()),
            "scale_seed_count": int(len(scale_df)),
            "scale_fairness_seed_pass_count": int(aggregate["fairness_seed_pass_count"]),
            "release_decision": str(release_payload["decision"]),
            "acceptance_status": str(milestone_acceptance_summary["acceptance_status"]),
            "acceptance_eligible": bool(milestone_acceptance_summary["acceptance_eligible"]),
            "evidence_level": str(milestone_acceptance_summary["evidence_level"]),
            "scale_mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
            "scale_mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
            "scale_mean_equalized_odds_gap_delta": float(scale_df["equalized_odds_gap_delta"].mean()),
            "scale_mean_recourse_success_gap": float(scale_df["recourse_success_gap"].mean()),
            "scale_mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
            "scale_mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
            "scale_mean_high_risk_profile_applied_rate": float(scale_df["high_risk_profile_applied_rate"].mean()),
            "scale_mean_candidate_pool_diversity_index": float(scale_df["candidate_pool_diversity_index"].mean()),
            "scale_mean_candidate_source_entropy": float(scale_df["candidate_source_entropy"].mean()),
        }
    )

    logger.info("Phase experiment suite completed. quick_run_id=%s", quick_run_id)
    logger.info(
        "Outputs: %s %s %s %s",
        run_ctx.tables_dir / "phase_quick_summary.json",
        scale_path,
        phase_breakdown_path,
        run_ctx.tables_dir / "release_decision.json",
    )


if __name__ == "__main__":
    main()
