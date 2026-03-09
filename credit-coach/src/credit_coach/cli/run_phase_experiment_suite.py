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

from credit_coach.ops.kpi_contract import load_kpi_thresholds
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


def _kpi_checks(summary: dict[str, Any], fair_row: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, str]:
    denied_count = max(1, int(summary.get("denied_count", 0)))
    denied_gate_pass_rate = float(summary.get("denied_with_gate_pass_plan", 0.0)) / float(denied_count)
    trajectory_gate_pass_rate_4w = float(summary.get("trajectory_gate_pass_rate_4w", 0.0))
    trajectory_gate_pass_rate_12w = float(summary.get("trajectory_gate_pass_rate_12w", 0.0))
    trajectory_gate_pass_rate_24w = float(summary.get("trajectory_gate_pass_rate_24w", 0.0))
    trajectory_partial_progress_rate = float(summary.get("trajectory_partial_progress_rate", 0.0))
    trajectory_median_time_to_gate_pass_days = float(summary.get("trajectory_median_time_to_gate_pass_days", 9_999.0))
    checks = {
        "denied_to_approved_lift": float(summary.get("denied_to_approved_lift", 0.0)) >= float(thresholds.get("min_denied_to_approved_lift", 0.09)),
        "denied_high_risk_lift": float(summary.get("denied_high_risk_lift", 0.0)) >= float(thresholds.get("min_denied_high_risk_lift", 0.03)),
        "denied_gate_pass_rate": denied_gate_pass_rate >= float(thresholds.get("min_denied_gate_pass_rate", 0.08)),
        "denied_reliability_violation_rate": float(summary.get("denied_reliability_violation_rate", 0.0)) <= float(thresholds.get("max_denied_reliability_violation_rate", 0.40)),
        "approval_gap_delta": float(fair_row.get("approval_gap_delta", 0.0)) <= float(thresholds.get("max_approval_gap_delta", 0.01)),
        "equalized_odds_gap_delta": float(fair_row.get("equalized_odds_gap_delta", 0.0)) <= float(thresholds.get("max_equalized_odds_gap_delta", 0.01)),
        "latency_p95_ms": float(summary.get("sync_latency_p95_ms", summary.get("latency_p95_ms", 0.0))) <= float(thresholds.get("max_p95_latency_ms", 500.0)),
        "latency_p99_ms": float(summary.get("sync_latency_p99_ms", summary.get("latency_p99_ms", 0.0))) <= float(thresholds.get("max_p99_latency_ms", 2000.0)),
        "error_rate": float(summary.get("error_rate", 0.0)) <= float(thresholds.get("max_error_rate", 0.005)),
        "fairness_gap_after": float(summary.get("fairness_approval_gap_after", 0.0)) <= float(thresholds.get("max_fairness_gap", 0.10)),
        "high_stress_fairness_gap_after": float(fair_row.get("high_stress_approval_gap_after", 0.0)) <= float(thresholds.get("max_high_stress_fairness_gap", 0.10)),
        "recourse_success_gap": float(fair_row.get("recourse_success_gap", 0.0)) <= float(thresholds.get("max_recourse_success_gap", 0.10)),
        "trajectory_gate_pass_rate_4w": trajectory_gate_pass_rate_4w >= float(thresholds.get("min_trajectory_gate_pass_rate_4w", 0.0)),
        "trajectory_gate_pass_rate_12w": trajectory_gate_pass_rate_12w >= float(thresholds.get("min_trajectory_gate_pass_rate_12w", 0.0)),
        "trajectory_gate_pass_rate_24w": trajectory_gate_pass_rate_24w >= float(thresholds.get("min_trajectory_gate_pass_rate_24w", 0.0)),
        "trajectory_partial_progress_rate": trajectory_partial_progress_rate >= float(thresholds.get("min_trajectory_partial_progress_rate", 0.0)),
        "trajectory_median_time_to_gate_pass_days": trajectory_median_time_to_gate_pass_days <= float(thresholds.get("max_trajectory_median_time_to_gate_pass_days", 9_999.0)),
    }
    failed = [k for k, ok in checks.items() if not ok]
    return bool(all(checks.values())), ";".join(failed)


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
    quick_ok, quick_failed = _kpi_checks(quick_summary, quick_fair, thresholds)
    quick_payload = {
        "run_id": quick_run_id,
        "smoke_run_id": quick_smoke_run_id,
        "all_pass": bool(quick_ok),
        "failed_checks": quick_failed,
    }
    (run_ctx.tables_dir / "phase_quick_summary.json").write_text(json.dumps(quick_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    scale_rows: list[dict[str, Any]] = []
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
        ok, failed = _kpi_checks(summary, fair_row, thresholds)
        scale_rows.append(
            {
                "seed": int(seed),
                "run_id": run_id,
                "all_pass": int(ok),
                "failed_checks": failed,
                "denied_to_approved_lift": float(summary.get("denied_to_approved_lift", 0.0)),
                "denied_high_risk_lift": float(summary.get("denied_high_risk_lift", 0.0)),
                "denied_reliability_violation_rate": float(summary.get("denied_reliability_violation_rate", 0.0)),
                "sync_latency_p95_ms": float(summary.get("sync_latency_p95_ms", summary.get("latency_p95_ms", 0.0))),
                "sync_latency_p99_ms": float(summary.get("sync_latency_p99_ms", summary.get("latency_p99_ms", 0.0))),
                "equalized_odds_gap_delta": float(fair_row.get("equalized_odds_gap_delta", 0.0)),
                "approval_gap_delta": float(fair_row.get("approval_gap_delta", 0.0)),
                "recourse_success_gap": float(fair_row.get("recourse_success_gap", 0.0)),
                "fairness_gap_after": float(summary.get("fairness_approval_gap_after", 0.0)),
                "high_stress_fairness_gap_after": float(fair_row.get("high_stress_approval_gap_after", 0.0)),
                "error_rate": float(summary.get("error_rate", 0.0)),
                "trajectory_gate_pass_rate_4w": float(summary.get("trajectory_gate_pass_rate_4w", 0.0)),
                "trajectory_gate_pass_rate_12w": float(summary.get("trajectory_gate_pass_rate_12w", 0.0)),
                "trajectory_gate_pass_rate_24w": float(summary.get("trajectory_gate_pass_rate_24w", 0.0)),
                "trajectory_partial_progress_rate": float(summary.get("trajectory_partial_progress_rate", 0.0)),
                "trajectory_median_time_to_gate_pass_days": float(summary.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
            }
        )

    scale_df = pd.DataFrame(scale_rows).sort_values("seed").reset_index(drop=True)
    scale_path = run_ctx.tables_dir / "phase_scale_seed_summary.csv"
    scale_df.to_csv(scale_path, index=False)

    aggregate = {
        "seed_count": int(len(scale_df)),
        "pass_count": int(scale_df["all_pass"].sum()),
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
        "mean_error_rate": float(scale_df["error_rate"].mean()),
        "mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
        "mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
        "mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
        "mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
        "mean_trajectory_median_time_to_gate_pass_days": float(scale_df["trajectory_median_time_to_gate_pass_days"].mean()),
    }
    (run_ctx.tables_dir / "phase_scale_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")

    run_ctx.save_metrics(
        {
            "phase_name": str(args.phase_name),
            "train_run_id": train_run_id,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "quick_run_id": quick_run_id,
            "quick_all_pass": bool(quick_ok),
            "scale_pass_count": int(scale_df["all_pass"].sum()),
            "scale_seed_count": int(len(scale_df)),
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
    logger.info("Outputs: %s %s", run_ctx.tables_dir / "phase_quick_summary.json", scale_path)


if __name__ == "__main__":
    main()
