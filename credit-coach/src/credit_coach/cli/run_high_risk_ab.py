from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.ops.kpi_contract import load_kpi_thresholds
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_high_risk_ab")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="High-risk denied-target A/B batch experiment runner")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--control_recourse_config", type=str, default="configs/experiments/recourse_ab_control.yaml")
    p.add_argument("--treatment_recourse_config", type=str, default="configs/experiments/recourse_ab_highrisk_tuned.yaml")
    p.add_argument("--control_run_id", type=str, default="")
    p.add_argument("--treatment_run_id", type=str, default="")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--n_customers", type=int, default=1000)
    p.add_argument("--sample_seed", type=int, default=42)
    p.add_argument("--n_workers", type=int, default=5)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    return p.parse_args()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _extract_run_id(command_output: str) -> str:
    matches = re.findall(r"artifacts/runs/([0-9]{8}_[0-9]{6}_[0-9a-f]+_[0-9a-f]+)", command_output)
    if not matches:
        return ""
    return matches[0]


def _build_batch_cmd(*, args: argparse.Namespace, recourse_config: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "credit_coach.cli.run_batch_recourse_eval",
        "--n_customers",
        str(int(args.n_customers)),
        "--sample_seed",
        str(int(args.sample_seed)),
        "--log_every",
        str(int(args.log_every)),
        "--n_workers",
        str(int(args.n_workers)),
        "--base_config",
        str(args.base_config),
        "--model_config",
        str(args.model_config),
        "--recourse_config",
        str(recourse_config),
        "--causality_config",
        str(args.causality_config),
        "--safety_config",
        str(args.safety_config),
        "--macro_config",
        str(args.macro_config),
    ]


def _run_one_batch(*, cmd: list[str], cwd: Path, label: str) -> tuple[str, str]:
    logger.info("Running %s batch: %s", label, " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    combined = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    run_id = _extract_run_id(combined)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} batch failed (code={proc.returncode})\n{combined[-4000:]}")
    if not run_id:
        raise RuntimeError(f"{label} batch completed but run_id not found in logs.")
    return run_id, combined


def _load_batch_summary(run_id: str) -> dict[str, Any]:
    path = _project_root() / "artifacts" / "runs" / run_id / "tables" / "batch_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_risk_lifts(run_id: str) -> dict[str, float]:
    path = _project_root() / "artifacts" / "runs" / run_id / "tables" / "denied_lift_by_risk_band.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[str, float] = {}
    for _, row in df.iterrows():
        out[str(row.get("risk_band", "unknown"))] = float(row.get("denied_to_approved_lift", 0.0))
    return out


def _metric_rows(control: dict[str, Any], treatment: dict[str, Any]) -> pd.DataFrame:
    specs: list[tuple[str, str]] = [
        ("denied_to_approved_lift", "higher_better"),
        ("denied_high_risk_lift", "higher_better"),
        ("denied_reliability_violation_rate", "lower_better"),
        ("denied_ci_violation_rate", "lower_better"),
        ("denied_worst_margin_violation_rate", "lower_better"),
        ("latency_p95_ms", "lower_better"),
        ("latency_p99_ms", "lower_better"),
        ("error_rate", "lower_better"),
        ("fairness_approval_gap_after", "lower_better"),
        ("fairness_equalized_odds_gap_after", "lower_better"),
        ("recourse_success_gap", "lower_better"),
        ("recourse_cost_gap", "lower_better"),
    ]
    rows: list[dict[str, Any]] = []
    for metric, pref in specs:
        c = float(control.get(metric, 0.0))
        t = float(treatment.get(metric, 0.0))
        delta = float(t - c)
        improved = delta > 0.0 if pref == "higher_better" else delta < 0.0
        rows.append(
            {
                "metric": metric,
                "control": c,
                "treatment": t,
                "delta_treatment_minus_control": delta,
                "preference": pref,
                "improved": int(bool(improved)),
            }
        )
    return pd.DataFrame(rows)


def _riskband_rows(control_risk: dict[str, float], treatment_risk: dict[str, float]) -> pd.DataFrame:
    bands = sorted(set(control_risk.keys()) | set(treatment_risk.keys()))
    rows: list[dict[str, Any]] = []
    for b in bands:
        c = float(control_risk.get(b, 0.0))
        t = float(treatment_risk.get(b, 0.0))
        rows.append(
            {
                "risk_band": b,
                "control_lift": c,
                "treatment_lift": t,
                "delta_treatment_minus_control": float(t - c),
            }
        )
    return pd.DataFrame(rows)


def _kpi_gate_snapshot(summary: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "denied_to_approved_lift": float(summary.get("denied_to_approved_lift", 0.0))
        >= float(thresholds.get("min_denied_to_approved_lift", 0.05)),
        "denied_high_risk_lift": float(summary.get("denied_high_risk_lift", 0.0))
        >= float(thresholds.get("min_denied_high_risk_lift", 0.03)),
        "latency_p95_ms": float(summary.get("latency_p95_ms", 0.0))
        <= float(thresholds.get("max_p95_latency_ms", 500.0)),
        "latency_p99_ms": float(summary.get("latency_p99_ms", 0.0))
        <= float(thresholds.get("max_p99_latency_ms", 2000.0)),
        "error_rate": float(summary.get("error_rate", 0.0))
        <= float(thresholds.get("max_error_rate", 0.005)),
        "fairness_approval_gap_after": float(summary.get("fairness_approval_gap_after", 0.0))
        <= float(thresholds.get("max_fairness_gap", 0.1)),
    }
    return {
        "all_pass": bool(all(checks.values())),
        "checks": checks,
    }


def main() -> None:
    args = parse_args()
    root = _project_root()

    control_run_id = str(args.control_run_id).strip()
    treatment_run_id = str(args.treatment_run_id).strip()
    control_log = ""
    treatment_log = ""

    if bool(args.execute):
        if not control_run_id:
            control_run_id, control_log = _run_one_batch(
                cmd=_build_batch_cmd(args=args, recourse_config=args.control_recourse_config),
                cwd=root,
                label="control",
            )
        if not treatment_run_id:
            treatment_run_id, treatment_log = _run_one_batch(
                cmd=_build_batch_cmd(args=args, recourse_config=args.treatment_recourse_config),
                cwd=root,
                label="treatment",
            )
    else:
        if not control_run_id or not treatment_run_id:
            raise ValueError("When --execute is not set, provide both --control_run_id and --treatment_run_id.")

    control_summary = _load_batch_summary(control_run_id)
    treatment_summary = _load_batch_summary(treatment_run_id)
    control_risk = _load_risk_lifts(control_run_id)
    treatment_risk = _load_risk_lifts(treatment_run_id)
    metric_df = _metric_rows(control_summary, treatment_summary)
    risk_df = _riskband_rows(control_risk, treatment_risk)

    thresholds = load_kpi_thresholds(args.kpi_contract)
    control_gate = _kpi_gate_snapshot(control_summary, thresholds)
    treatment_gate = _kpi_gate_snapshot(treatment_summary, thresholds)

    run_ctx = create_run_context(
        {
            "mode": "high_risk_ab",
            "args": vars(args),
            "control_run_id": control_run_id,
            "treatment_run_id": treatment_run_id,
        },
        base_artifact_dir="artifacts/runs",
    )

    metric_path = run_ctx.tables_dir / "ab_high_risk_metric_deltas.csv"
    risk_path = run_ctx.tables_dir / "ab_high_risk_riskband_deltas.csv"
    summary_path = run_ctx.tables_dir / "ab_high_risk_summary.json"
    metric_df.to_csv(metric_path, index=False)
    risk_df.to_csv(risk_path, index=False)

    summary_payload = {
        "control_run_id": control_run_id,
        "treatment_run_id": treatment_run_id,
        "control_gate_snapshot": control_gate,
        "treatment_gate_snapshot": treatment_gate,
        "key_deltas": {
            "denied_to_approved_lift_delta": float(
                treatment_summary.get("denied_to_approved_lift", 0.0) - control_summary.get("denied_to_approved_lift", 0.0)
            ),
            "denied_high_risk_lift_delta": float(
                treatment_summary.get("denied_high_risk_lift", 0.0) - control_summary.get("denied_high_risk_lift", 0.0)
            ),
            "latency_p99_ms_delta": float(treatment_summary.get("latency_p99_ms", 0.0) - control_summary.get("latency_p99_ms", 0.0)),
            "equalized_odds_after_delta": float(
                treatment_summary.get("fairness_equalized_odds_gap_after", 0.0)
                - control_summary.get("fairness_equalized_odds_gap_after", 0.0)
            ),
        },
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if control_log:
        (run_ctx.tables_dir / "ab_control_run.log").write_text(control_log, encoding="utf-8")
    if treatment_log:
        (run_ctx.tables_dir / "ab_treatment_run.log").write_text(treatment_log, encoding="utf-8")

    run_ctx.save_metrics(
        {
            "control_run_id": control_run_id,
            "treatment_run_id": treatment_run_id,
            "lift_control": float(control_summary.get("denied_to_approved_lift", 0.0)),
            "lift_treatment": float(treatment_summary.get("denied_to_approved_lift", 0.0)),
            "lift_delta": float(
                treatment_summary.get("denied_to_approved_lift", 0.0) - control_summary.get("denied_to_approved_lift", 0.0)
            ),
            "high_risk_lift_control": float(control_summary.get("denied_high_risk_lift", 0.0)),
            "high_risk_lift_treatment": float(treatment_summary.get("denied_high_risk_lift", 0.0)),
            "high_risk_lift_delta": float(
                treatment_summary.get("denied_high_risk_lift", 0.0) - control_summary.get("denied_high_risk_lift", 0.0)
            ),
            "treatment_all_gate_pass": bool(treatment_gate.get("all_pass", False)),
        }
    )

    logger.info("AB comparison ready.")
    logger.info("control_run_id=%s treatment_run_id=%s", control_run_id, treatment_run_id)
    logger.info("Outputs: %s %s %s", metric_path, risk_path, summary_path)


if __name__ == "__main__":
    main()
