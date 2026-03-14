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
from credit_coach.ops.kpi_contract import load_kpi_thresholds
from credit_coach.ops.release_decision import (
    PRIMARY_FAIRNESS_METRIC,
    aggregate_release_metrics,
    build_pilot_guardrails,
    build_rollback_conditions,
    evaluate_fairness_seed_pass,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_phase_experiment_suite")


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


def _batch_cmd(args: argparse.Namespace, *, n_customers: int, seed: int) -> list[str]:
    return [
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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


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


def _render_release_review_summary(
    *,
    release_payload: dict[str, Any],
    aggregate: dict[str, Any],
    scale_df: pd.DataFrame,
) -> str:
    lines = [
        "# Release Review Summary",
        "",
        f"- Decision: {release_payload.get('decision', 'NO_GO')}",
        f"- Reason: {release_payload.get('decision_reason', '')}",
        f"- Fairness seed pass count: {aggregate.get('fairness_seed_pass_count', 0)}/{aggregate.get('fairness_seed_total', 0)}",
        f"- Dominant fail segment: {aggregate.get('dominant_fail_segment_key', '')}",
        f"- Dominant fail candidate source: {aggregate.get('dominant_fail_candidate_source', '')}",
        f"- Dominant fail segment share: {float(aggregate.get('dominant_fail_segment_share', 0.0)):.2f}",
        f"- Worst fairness gap: {float(aggregate.get('worst_fairness_gap', 0.0)):.6f}",
        "",
        "## Seed Summary",
        "",
        f"- Lift pass across seeds: {bool(aggregate.get('lift_pass', False))}",
        f"- Reliability pass across seeds: {bool(aggregate.get('reliability_pass', False))}",
        f"- Dominant fail reason: {aggregate.get('dominant_fail_reason', '')}",
        f"- Max fairness guard demotions: {int(scale_df.get('fairness_guard_demotion_count', pd.Series(dtype=int)).max() if 'fairness_guard_demotion_count' in scale_df.columns else 0)}",
        f"- Fairness guard stop reasons: {', '.join(sorted(set(scale_df['fairness_guard_stop_reason'].astype(str))) if 'fairness_guard_stop_reason' in scale_df.columns else [])}",
    ]
    if release_payload.get("decision") == "LIMITED_GO":
        lines.extend(
            [
                "",
                "## Limited Go Package",
                "",
                f"- Smoke pass: {bool(release_payload.get('smoke_pass', False))}",
                f"- Pilot eligible: {bool(release_payload.get('pilot_eligible', False))}",
                f"- Broad rollout allowed: {bool(release_payload.get('broad_rollout_allowed', False))}",
                f"- Max traffic pct: {int(release_payload.get('max_traffic_pct', 0))}",
                f"- Manual approval required: {bool(release_payload.get('manual_approval_required', False))}",
                f"- Rollback guard required: {bool(release_payload.get('rollback_guard_required', False))}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    seeds = _parse_seeds(args.scale_seeds)
    thresholds = load_kpi_thresholds(args.kpi_contract)
    root = _project_root()

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
            "quick_batch_cmd": _batch_cmd(args, n_customers=int(args.quick_n), seed=int(args.quick_seed)),
            "scale_batch_cmd_template": _batch_cmd(args, n_customers=int(args.scale_n), seed=seeds[0]),
            "scale_seeds": seeds,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
        }
        (run_ctx.tables_dir / "phase_suite_dry_run.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False), encoding="utf-8")
        run_ctx.save_metrics({"execute": False, "seed_count": len(seeds)})
        logger.info("Dry-run saved: %s", run_ctx.tables_dir / "phase_suite_dry_run.json")
        return

    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/mplcache")
    env.setdefault("TQDM_DISABLE", "1")

    train_run_id = ""
    if not bool(args.skip_train_before_batch):
        train_run_id, train_log = _run_cmd(
            cmd=_train_cmd(args),
            cwd=root,
            env=env,
            label="train_once",
        )
        (run_ctx.tables_dir / "train_once.log").write_text(train_log, encoding="utf-8")

    quick_run_id, quick_log = _run_cmd(
        cmd=_batch_cmd(args, n_customers=int(args.quick_n), seed=int(args.quick_seed)),
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
    }
    (run_ctx.tables_dir / "phase_quick_summary.json").write_text(json.dumps(quick_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    scale_rows: list[dict[str, Any]] = []
    seed_breakdowns: list[pd.DataFrame] = []
    for seed in seeds:
        run_id, run_log = _run_cmd(
            cmd=_batch_cmd(args, n_customers=int(args.scale_n), seed=int(seed)),
            cwd=root,
            env=env,
            label=f"scale_batch_seed_{seed}",
        )
        (run_ctx.tables_dir / f"scale_seed_{seed}.log").write_text(run_log, encoding="utf-8")

        summary = _load_json(root / "artifacts" / "runs" / run_id / "tables" / "batch_summary.json")
        fair_row = pd.read_csv(root / "artifacts" / "runs" / run_id / "tables" / "batch_fairness_change.csv").iloc[0].to_dict()
        breakdown_df = _load_csv(root / "artifacts" / "runs" / run_id / "tables" / "fairness_failure_breakdown.csv")
        snapshot = _seed_contract_snapshot(summary, fair_row, thresholds)
        scale_rows.append(
            {
                "seed": int(seed),
                "run_id": run_id,
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
            }
        )
        if not breakdown_df.empty:
            breakdown_df["seed"] = int(seed)
            breakdown_df["primary_fail_reason"] = str(snapshot["primary_fail_reason"])
            seed_breakdowns.append(breakdown_df)

    scale_df = pd.DataFrame(scale_rows).sort_values("seed").reset_index(drop=True)
    scale_path = run_ctx.tables_dir / "phase_scale_seed_summary.csv"
    scale_df.to_csv(scale_path, index=False)
    phase_breakdown_df = _build_phase_fairness_breakdown(seed_rows=scale_rows, seed_breakdowns=seed_breakdowns)
    phase_breakdown_path = run_ctx.tables_dir / "fairness_failure_breakdown.csv"
    phase_breakdown_df.to_csv(phase_breakdown_path, index=False)

    aggregate = {
        "seed_count": int(len(scale_df)),
        "pass_count": int(scale_df["all_pass"].sum()),
        **aggregate_release_metrics(
            scale_df.to_dict(orient="records"),
            thresholds=thresholds,
            breakdown_rows=phase_breakdown_df.to_dict(orient="records"),
        ),
        "mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
        "mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
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
    }
    (run_ctx.tables_dir / "phase_scale_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    release_payload = evaluate_release_decision(aggregate, thresholds)
    (run_ctx.tables_dir / "release_decision.json").write_text(
        json.dumps(release_payload, indent=2, ensure_ascii=False),
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
    (run_ctx.tables_dir / "release_review_summary.md").write_text(
        _render_release_review_summary(
            release_payload=release_payload,
            aggregate=aggregate,
            scale_df=scale_df,
        ),
        encoding="utf-8",
    )

    run_ctx.save_metrics(
        {
            "phase_name": str(args.phase_name),
            "train_run_id": train_run_id,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "quick_run_id": quick_run_id,
            "quick_all_pass": bool(quick_ok),
            "quick_lift_pass": bool(quick_snapshot["lift_pass"]),
            "quick_reliability_pass": bool(quick_snapshot["reliability_pass"]),
            "quick_fairness_seed_pass": bool(quick_snapshot["fairness_seed_pass"]),
            "scale_pass_count": int(scale_df["all_pass"].sum()),
            "scale_seed_count": int(len(scale_df)),
            "scale_fairness_seed_pass_count": int(aggregate["fairness_seed_pass_count"]),
            "release_decision": str(release_payload["decision"]),
            "scale_mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
            "scale_mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
            "scale_mean_equalized_odds_gap_delta": float(scale_df["equalized_odds_gap_delta"].mean()),
            "scale_mean_recourse_success_gap": float(scale_df["recourse_success_gap"].mean()),
            "scale_mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
            "scale_mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
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
