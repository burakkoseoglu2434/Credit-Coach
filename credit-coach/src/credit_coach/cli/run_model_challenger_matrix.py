from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from credit_coach.model.registry import build_frozen_model_manifest, resolve_model_manifest
from credit_coach.ops.kpi_contract import (
    FAIRNESS_KPI_THRESHOLD_KEYS,
    LIFT_KPI_THRESHOLD_KEYS,
    RELIABILITY_KPI_THRESHOLD_KEYS,
    build_kpi_contract_snapshot,
    compute_kpi_violation_score,
    load_kpi_thresholds,
    map_release_decision_to_acceptance_status,
)
from credit_coach.ops.release_decision import (
    GO,
    aggregate_release_metrics,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_model_challenger_matrix")

_VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "variant_id": "control_logistic_isotonic",
        "force_backend": "logistic_regression",
        "calibration_method": "isotonic",
        "monotonic_constraints": {},
    },
    {
        "variant_id": "logistic_sigmoid",
        "force_backend": "logistic_regression",
        "calibration_method": "sigmoid",
        "monotonic_constraints": {},
    },
    {
        "variant_id": "xgboost_monotonic_isotonic",
        "force_backend": "xgboost",
        "calibration_method": "isotonic",
        "monotonic_constraints": {
            "annual_inc": -1,
            "dti": 1,
            "revol_util": 1,
            "last_fico_range_high": -1,
            "last_fico_range_low": -1,
            "acc_now_delinq": 1,
            "delinq_amnt": 1,
            "collections_12_mths_ex_med": 1,
        },
    },
    {
        "variant_id": "xgboost_monotonic_sigmoid",
        "force_backend": "xgboost",
        "calibration_method": "sigmoid",
        "monotonic_constraints": {
            "annual_inc": -1,
            "dti": 1,
            "revol_util": 1,
            "last_fico_range_high": -1,
            "last_fico_range_low": -1,
            "acc_now_delinq": 1,
            "delinq_amnt": 1,
            "collections_12_mths_ex_med": 1,
        },
    },
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run model/calibration challenger matrix with high-risk recourse KPIs")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/experiments/recourse_phaseb_hybrid_v2.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--n_customers", type=int, default=1000)
    p.add_argument("--sample_seeds", type=str, default="42,43,44,45,46")
    p.add_argument("--n_workers", type=int, default=5)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--execute", action="store_true")
    return p.parse_args()


def _parse_seeds(raw: str) -> list[int]:
    vals = [s.strip() for s in str(raw).split(",") if s.strip()]
    seeds = [int(v) for v in vals]
    if not seeds:
        raise ValueError("sample_seeds cannot be empty")
    return seeds


def _extract_run_id(log_text: str) -> str:
    matches = re.findall(r"artifacts/runs/([0-9]{8}_[0-9]{6}_[0-9a-f]+_[0-9a-f]+)", log_text)
    return matches[0] if matches else ""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _build_variant_model_cfg(
    *,
    base_model_cfg: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, Any]:
    out = deepcopy(base_model_cfg)
    model_cfg = out.get("model", {}) if isinstance(out.get("model", {}), dict) else {}
    model_cfg = dict(model_cfg)
    params = model_cfg.get("params", {}) if isinstance(model_cfg.get("params", {}), dict) else {}
    params = dict(params)

    backend = str(variant["force_backend"])
    if backend == "xgboost":
        model_cfg["type"] = "xgboost"
        params["allow_xgboost"] = True
        params["monotone_constraints"] = deepcopy(variant.get("monotonic_constraints", {}))
    else:
        model_cfg["type"] = "logistic_regression"
        params["allow_xgboost"] = False
        params["monotone_constraints"] = {}

    model_cfg["params"] = params
    out["model"] = model_cfg

    calibration_cfg = out.get("calibration", {}) if isinstance(out.get("calibration", {}), dict) else {}
    calibration_cfg = dict(calibration_cfg)
    calibration_cfg["method"] = str(variant["calibration_method"])
    out["calibration"] = calibration_cfg
    return out


def _batch_cmd(
    args: argparse.Namespace,
    *,
    seed: int,
    model_manifest: str,
) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "credit_coach.cli.run_batch_recourse_eval",
        "--n_customers",
        str(int(args.n_customers)),
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
    if str(model_manifest).strip():
        cmd.extend(["--model_manifest", str(model_manifest).strip()])
    return cmd


def _run_cmd(*, cmd: list[str], cwd: Path, env: dict[str, str], label: str) -> tuple[str, str]:
    logger.info("Running %s: %s", label, " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    log_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (code={proc.returncode})\n{log_text[-4000:]}")
    run_id = _extract_run_id(log_text)
    if not run_id:
        raise RuntimeError(f"{label} succeeded but run_id could not be parsed")
    return run_id, log_text


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _aggregate_variant_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "auc",
        "pr_auc",
        "denied_to_approved_lift",
        "denied_high_risk_lift",
        "high_risk_reachability_rate",
        "denied_reliability_violation_rate",
        "fairness_approval_gap_delta",
        "fairness_approval_gap_after",
        "fairness_equalized_odds_gap_delta",
        "fairness_equalized_odds_gap_after",
        "high_stress_approval_gap_after",
        "recourse_success_gap",
        "latency_p95_ms",
        "latency_p99_ms",
        "error_rate",
        "trajectory_gate_pass_rate_4w",
        "trajectory_gate_pass_rate_12w",
        "trajectory_gate_pass_rate_24w",
        "trajectory_partial_progress_rate",
        "trajectory_median_time_to_gate_pass_days",
    ]
    available = [c for c in metric_cols if c in df.columns]
    grouped = (
        df.groupby("variant_id", dropna=False)[available]
        .mean(numeric_only=True)
        .reset_index()
        .rename(columns={c: f"mean_{c}" for c in available})
    )
    grouped["seed_count"] = df.groupby("variant_id").size().values
    return grouped


def _gate_violation_score(row: pd.Series, thresholds: dict[str, Any]) -> tuple[float, int]:
    metrics = {
        "denied_to_approved_lift": row.get("mean_denied_to_approved_lift"),
        "denied_high_risk_lift": row.get("mean_denied_high_risk_lift"),
        "denied_reliability_violation_rate": row.get("mean_denied_reliability_violation_rate"),
        "approval_gap_delta": row.get("mean_fairness_approval_gap_delta"),
        "equalized_odds_gap_delta": row.get("mean_fairness_equalized_odds_gap_delta"),
        "fairness_gap_after": row.get("mean_fairness_approval_gap_after"),
        "high_stress_fairness_gap_after": row.get("mean_high_stress_approval_gap_after"),
        "recourse_success_gap": row.get("mean_recourse_success_gap"),
        "latency_p95_ms": row.get("mean_latency_p95_ms"),
        "latency_p99_ms": row.get("mean_latency_p99_ms"),
        "error_rate": row.get("mean_error_rate"),
        "trajectory_gate_pass_rate_4w": row.get("mean_trajectory_gate_pass_rate_4w"),
        "trajectory_gate_pass_rate_12w": row.get("mean_trajectory_gate_pass_rate_12w"),
        "trajectory_gate_pass_rate_24w": row.get("mean_trajectory_gate_pass_rate_24w"),
        "trajectory_partial_progress_rate": row.get("mean_trajectory_partial_progress_rate"),
        "trajectory_median_time_to_gate_pass_days": row.get("mean_trajectory_median_time_to_gate_pass_days"),
    }
    return compute_kpi_violation_score(
        metrics,
        thresholds,
        threshold_keys=(
            *LIFT_KPI_THRESHOLD_KEYS,
            *RELIABILITY_KPI_THRESHOLD_KEYS,
            *FAIRNESS_KPI_THRESHOLD_KEYS,
        ),
    )


def _select_champion(summary_df: pd.DataFrame, thresholds: dict[str, Any]) -> tuple[str, pd.DataFrame]:
    ranked = summary_df.copy()
    violation_scores: list[float] = []
    violation_counts: list[int] = []
    for _, row in ranked.iterrows():
        score, cnt = _gate_violation_score(row, thresholds)
        violation_scores.append(score)
        violation_counts.append(cnt)

    ranked["_gate_violation_score"] = violation_scores
    ranked["_gate_failed_check_count"] = violation_counts
    ranked["_gate_all_pass"] = ranked["_gate_failed_check_count"] == 0
    decision_rank = {"GO": 0, "LIMITED_GO": 1, "NO_GO": 2}
    if "release_decision" in ranked.columns:
        release_decisions = ranked["release_decision"].fillna("NO_GO").astype(str)
    else:
        release_decisions = pd.Series(["NO_GO"] * len(ranked), index=ranked.index, dtype="object")
    if "acceptance_eligible" in ranked.columns:
        acceptance_eligible = ranked["acceptance_eligible"].fillna(False).astype(bool)
    else:
        acceptance_eligible = pd.Series([True] * len(ranked), index=ranked.index, dtype="bool")
    if "promotion_eligible" in ranked.columns:
        promotion_eligible = ranked["promotion_eligible"].fillna(False).astype(bool)
    else:
        promotion_eligible = release_decisions == GO
    ranked["_release_rank"] = release_decisions.map(decision_rank).fillna(2).astype(int)
    ranked["_acceptance_eligible"] = acceptance_eligible
    ranked["_promotion_eligible"] = acceptance_eligible & promotion_eligible
    ranked["_score_a"] = -ranked.get("mean_denied_high_risk_lift", 0.0)
    ranked["_score_b"] = -ranked.get("mean_high_risk_reachability_rate", 0.0)
    ranked["_score_c"] = -ranked.get("mean_denied_to_approved_lift", 0.0)
    ranked["_score_d"] = ranked.get("mean_fairness_approval_gap_after", 1.0)
    ranked["_score_e"] = ranked.get("mean_latency_p99_ms", 999999.0)
    ranked = ranked.sort_values(
        [
            "_acceptance_eligible",
            "_release_rank",
            "_gate_all_pass",
            "_gate_failed_check_count",
            "_gate_violation_score",
            "_score_a",
            "_score_b",
            "_score_c",
            "_score_d",
            "_score_e",
        ],
        ascending=[False, True, False, True, True, True, True, True, True, True],
    ).reset_index(drop=True)
    return str(ranked.iloc[0]["variant_id"]), ranked


def _seed_contract_from_challenger_row(row: pd.Series, thresholds: dict[str, Any]) -> dict[str, Any]:
    denied_count = float(row.get("denied_count", 0.0))
    denied_with_gate_pass_plan = float(row.get("denied_with_gate_pass_plan", 0.0))
    summary = {
        "denied_count": denied_count,
        "denied_with_gate_pass_plan": denied_with_gate_pass_plan,
        "denied_to_approved_lift": float(row.get("denied_to_approved_lift", 0.0)),
        "denied_high_risk_lift": float(row.get("denied_high_risk_lift", 0.0)),
        "denied_reliability_violation_rate": float(row.get("denied_reliability_violation_rate", 0.0)),
        "sync_latency_p95_ms": float(row.get("latency_p95_ms", 0.0)),
        "sync_latency_p99_ms": float(row.get("latency_p99_ms", 0.0)),
        "error_rate": float(row.get("error_rate", 0.0)),
        "fairness_approval_gap_after": float(row.get("fairness_approval_gap_after", 0.0)),
        "trajectory_gate_pass_rate_4w": float(row.get("trajectory_gate_pass_rate_4w", 0.0)),
        "trajectory_gate_pass_rate_12w": float(row.get("trajectory_gate_pass_rate_12w", 0.0)),
        "trajectory_gate_pass_rate_24w": float(row.get("trajectory_gate_pass_rate_24w", 0.0)),
        "trajectory_partial_progress_rate": float(row.get("trajectory_partial_progress_rate", 0.0)),
        "trajectory_median_time_to_gate_pass_days": float(row.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
    }
    fair_metrics = {
        "approval_gap_delta": float(row.get("fairness_approval_gap_delta", 0.0)),
        "equalized_odds_gap_delta": float(row.get("fairness_equalized_odds_gap_delta", 0.0)),
        "high_stress_fairness_gap_after": float(row.get("high_stress_approval_gap_after", 0.0)),
        "recourse_success_gap": float(row.get("recourse_success_gap", 0.0)),
        "fairness_gap_after": float(row.get("fairness_approval_gap_after", 0.0)),
    }
    return evaluate_seed_kpi_contract(summary, fair_metrics, thresholds)


def _build_variant_release_payloads(
    runs_df: pd.DataFrame,
    *,
    thresholds: dict[str, Any],
    breakdown_frames: list[pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant_id, variant_runs in runs_df.groupby("variant_id", dropna=False):
        seed_rows = [_seed_contract_from_challenger_row(row, thresholds) for _, row in variant_runs.iterrows()]
        breakdown_rows: list[dict[str, Any]] = []
        for frame in breakdown_frames:
            if frame.empty or str(frame["variant_id"].iloc[0]) != str(variant_id):
                continue
            breakdown_rows.extend(frame.to_dict(orient="records"))
        aggregate = aggregate_release_metrics(seed_rows, thresholds=thresholds, breakdown_rows=breakdown_rows)
        release_payload = evaluate_release_decision(aggregate, thresholds)
        seed_count = int(len(variant_runs))
        freeze_modes = {str(mode).strip() for mode in variant_runs.get("model_freeze_mode", pd.Series(dtype=object)).tolist() if str(mode).strip()}
        acceptance_eligible = bool(seed_count > 1 and all(mode != "implicit_latest" for mode in freeze_modes))
        evidence_level = "seeded_challenger" if seed_count > 1 else "single_run_fallback"
        evidence_status = "complete" if acceptance_eligible else "degraded"
        degraded_reason = ""
        if seed_count <= 1:
            degraded_reason = "insufficient_repeated_seeded_evidence"
        elif not acceptance_eligible:
            degraded_reason = "implicit_latest_model_freeze"
        broad_rollout_allowed = bool(release_payload.get("broad_rollout_allowed", False))
        if not acceptance_eligible:
            broad_rollout_allowed = False
        rows.append(
            {
                "variant_id": str(variant_id),
                "release_decision": str(release_payload["decision"]),
                "acceptance_status": map_release_decision_to_acceptance_status(str(release_payload["decision"])),
                "acceptance_eligible": acceptance_eligible,
                "evidence_level": evidence_level,
                "evidence_status": evidence_status,
                "degraded_reason": degraded_reason,
                "pilot_eligible": bool(release_payload["pilot_eligible"]),
                "promotion_eligible": bool(release_payload["decision"] == GO and acceptance_eligible),
                "broad_rollout_allowed": broad_rollout_allowed,
                "fairness_seed_pass_count": int(aggregate["fairness_seed_pass_count"]),
                "fairness_seed_total": int(aggregate["fairness_seed_total"]),
                "lift_pass": bool(aggregate["lift_pass"]),
                "reliability_pass": bool(aggregate["reliability_pass"]),
                "worst_fairness_gap": float(aggregate.get("worst_fairness_gap", 0.0)),
                "dominant_fail_segment_key": str(aggregate.get("dominant_fail_segment_key", "")),
                "dominant_fail_candidate_source": str(aggregate.get("dominant_fail_candidate_source", "")),
                "dominant_fail_segment_share": float(aggregate.get("dominant_fail_segment_share", 0.0)),
                "model_version": str(variant_runs.iloc[0].get("model_version", "")),
                "model_freeze_mode": str(variant_runs.iloc[0].get("model_freeze_mode", "")),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    seeds = _parse_seeds(args.sample_seeds)
    root = _project_root()

    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    recourse_cfg = load_config(args.recourse_config)
    causality_cfg = load_config(args.causality_config)
    safety_cfg = load_config(args.safety_config)
    macro_cfg = load_config(args.macro_config)
    kpi_thresholds = load_kpi_thresholds(args.kpi_contract)
    registry_path = Path(model_cfg.get("registry", {}).get("path", "artifacts/models"))
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    run_ctx = create_run_context(
        {
            "mode": "challenger_matrix",
            "seeds": seeds,
            "n_customers": int(args.n_customers),
            "variants": [v["variant_id"] for v in _VARIANTS],
            "execute": bool(args.execute),
            "kpi_contract": str(args.kpi_contract),
        },
        base_artifact_dir="artifacts/runs",
    )

    variant_plan_rows = []
    for v in _VARIANTS:
        variant_plan_rows.append(
            {
                "variant_id": str(v["variant_id"]),
                "backend": str(v["force_backend"]),
                "calibration_method": str(v["calibration_method"]),
                "seed_count": int(len(seeds)),
            }
        )
    variant_plan_df = pd.DataFrame(variant_plan_rows)
    variant_plan_path = run_ctx.tables_dir / "challenger_variant_plan.csv"
    variant_plan_df.to_csv(variant_plan_path, index=False)

    if not bool(args.execute):
        logger.info("Execution disabled. Variant plan exported: %s", variant_plan_path)
        run_ctx.save_metrics({"execute": False, "variant_count": int(len(_VARIANTS)), "seed_count": int(len(seeds))})
        return

    run_rows: list[dict[str, Any]] = []
    breakdown_frames: list[pd.DataFrame] = []
    frozen_variant_rows: list[dict[str, Any]] = []

    for variant in _VARIANTS:
        variant_id = str(variant["variant_id"])
        variant_model_cfg = _build_variant_model_cfg(base_model_cfg=model_cfg, variant=variant)
        variant_cfg_path = run_ctx.tables_dir / f"model_variant_{variant_id}.yaml"
        variant_cfg_path.write_text(yaml.safe_dump(variant_model_cfg, sort_keys=False, allow_unicode=False), encoding="utf-8")
        env = os.environ.copy()
        env["CREDIT_COACH_FORCE_BACKEND"] = str(variant["force_backend"])
        env["CREDIT_COACH_ALLOW_XGB"] = "1" if str(variant["force_backend"]) == "xgboost" else "0"

        train_cmd = [
            sys.executable,
            "-m",
            "credit_coach.cli.run_train",
            "--base_config",
            str(args.base_config),
            "--config",
            str(variant_cfg_path),
        ]
        train_run_id, train_log = _run_cmd(
            cmd=train_cmd,
            cwd=root,
            env=env,
            label=f"train[{variant_id}]",
        )
        resolved_model_manifest = resolve_model_manifest(
            base_path=registry_path,
            model_version=train_run_id,
        )
        frozen_model_manifest = build_frozen_model_manifest(
            resolved_model_manifest,
            project_root=root,
            resolved_by_runner="run_model_challenger_matrix",
            training_run_id=train_run_id,
        )
        frozen_variant_rows.append({"variant_id": variant_id, **frozen_model_manifest})
        (run_ctx.tables_dir / f"challenger_train_{variant_id}.log").write_text(train_log, encoding="utf-8")

        for seed in seeds:
            batch_run_id, batch_log = _run_cmd(
                cmd=_batch_cmd(
                    args,
                    seed=int(seed),
                    model_manifest=str(resolved_model_manifest.get("manifest_path", "")),
                ),
                cwd=root,
                env=env,
                label=f"batch[{variant_id}][seed={seed}]",
            )

            train_metrics_path = root / "artifacts" / "models" / train_run_id / "metrics.json"
            batch_metrics_path = root / "artifacts" / "runs" / batch_run_id / "metrics.json"
            batch_breakdown_path = root / "artifacts" / "runs" / batch_run_id / "tables" / "fairness_failure_breakdown.csv"
            train_metrics = _load_json(train_metrics_path)
            batch_metrics = _load_json(batch_metrics_path)
            if batch_breakdown_path.exists():
                breakdown_df = pd.read_csv(batch_breakdown_path)
                if not breakdown_df.empty:
                    breakdown_df["variant_id"] = variant_id
                    breakdown_df["seed"] = int(seed)
                    breakdown_frames.append(breakdown_df)
            raw_p95 = float(batch_metrics.get("latency_p95_ms", 0.0))
            raw_p99 = float(batch_metrics.get("latency_p99_ms", 0.0))
            sync_p95 = batch_metrics.get("sync_latency_p95_ms")
            sync_p99 = batch_metrics.get("sync_latency_p99_ms")
            use_sync_latency = (
                sync_p95 is not None
                and sync_p99 is not None
                and float(sync_p95) > 0.0
                and float(sync_p99) > 0.0
            )
            eff_p95 = float(sync_p95) if use_sync_latency else raw_p95
            eff_p99 = float(sync_p99) if use_sync_latency else raw_p99

            row = {
                "variant_id": variant_id,
                "seed": int(seed),
                "train_run_id": train_run_id,
                "model_version": str(resolved_model_manifest.get("model_version", "")),
                "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "explicit_model_version")),
                "model_manifest_path": str(resolved_model_manifest.get("manifest_path", "")),
                "batch_run_id": batch_run_id,
                "backend": str(variant["force_backend"]),
                "calibration_method": str(variant["calibration_method"]),
                "auc": float(train_metrics.get("auc", 0.0)),
                "pr_auc": float(train_metrics.get("pr_auc", 0.0)),
                "denied_count": float(batch_metrics.get("denied_count", 0.0)),
                "denied_with_gate_pass_plan": float(batch_metrics.get("denied_with_gate_pass_plan", 0.0)),
                "denied_to_approved_lift": float(batch_metrics.get("denied_to_approved_lift", 0.0)),
                "denied_high_risk_lift": float(batch_metrics.get("denied_high_risk_lift", 0.0)),
                "high_risk_reachability_rate": float(batch_metrics.get("high_risk_reachability_rate", 0.0)),
                "denied_reliability_violation_rate": float(batch_metrics.get("denied_reliability_violation_rate", 0.0)),
                "fairness_approval_gap_before": float(batch_metrics.get("fairness_approval_gap_before", 0.0)),
                "fairness_approval_gap_after": float(batch_metrics.get("fairness_approval_gap_after", 0.0)),
                "fairness_approval_gap_delta": float(
                    batch_metrics.get("fairness_approval_gap_after", 0.0)
                    - batch_metrics.get("fairness_approval_gap_before", 0.0)
                ),
                "fairness_equalized_odds_gap_before": float(
                    batch_metrics.get("fairness_equalized_odds_gap_before", 0.0)
                ),
                "fairness_equalized_odds_gap_after": float(batch_metrics.get("fairness_equalized_odds_gap_after", 0.0)),
                "fairness_equalized_odds_gap_delta": float(
                    batch_metrics.get("fairness_equalized_odds_gap_after", 0.0)
                    - batch_metrics.get("fairness_equalized_odds_gap_before", 0.0)
                ),
                "high_stress_approval_gap_after": float(batch_metrics.get("high_stress_approval_gap_after", 0.0)),
                "recourse_success_gap": float(batch_metrics.get("recourse_success_gap", 0.0)),
                "latency_p95_ms": eff_p95,
                "latency_p99_ms": eff_p99,
                "latency_mode": "sync" if use_sync_latency else "end_to_end",
                "latency_p95_ms_raw": raw_p95,
                "latency_p99_ms_raw": raw_p99,
                "error_rate": float(batch_metrics.get("error_rate", 0.0)),
                "trajectory_gate_pass_rate_4w": float(batch_metrics.get("trajectory_gate_pass_rate_4w", 0.0)),
                "trajectory_gate_pass_rate_12w": float(batch_metrics.get("trajectory_gate_pass_rate_12w", 0.0)),
                "trajectory_gate_pass_rate_24w": float(batch_metrics.get("trajectory_gate_pass_rate_24w", 0.0)),
                "trajectory_partial_progress_rate": float(batch_metrics.get("trajectory_partial_progress_rate", 0.0)),
                "trajectory_median_time_to_gate_pass_days": float(batch_metrics.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
            }
            run_rows.append(row)

            (run_ctx.tables_dir / f"challenger_batch_{variant_id}_{seed}.log").write_text(batch_log, encoding="utf-8")

    if frozen_variant_rows:
        (run_ctx.tables_dir / "challenger_variant_frozen_models.json").write_text(
            json.dumps(frozen_variant_rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    runs_df = pd.DataFrame(run_rows)
    runs_path = run_ctx.tables_dir / "challenger_matrix_runs.csv"
    runs_df.to_csv(runs_path, index=False)

    summary_df = _aggregate_variant_metrics(runs_df)
    if summary_df.empty:
        raise RuntimeError("No challenger summary rows produced")
    release_df = _build_variant_release_payloads(runs_df, thresholds=kpi_thresholds, breakdown_frames=breakdown_frames)
    if not release_df.empty:
        summary_df = summary_df.merge(release_df, on="variant_id", how="left")
    summary_path = run_ctx.tables_dir / "challenger_matrix_variant_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    champion_variant, ranked_summary_df = _select_champion(summary_df, kpi_thresholds)
    ranked_summary_path = run_ctx.tables_dir / "challenger_matrix_variant_summary_ranked.csv"
    ranked_summary_df.to_csv(ranked_summary_path, index=False)
    control_variant = "control_logistic_isotonic"
    control_row = ranked_summary_df[ranked_summary_df["variant_id"] == control_variant]
    champ_row = ranked_summary_df[ranked_summary_df["variant_id"] == champion_variant]

    deltas = {}
    if not control_row.empty and not champ_row.empty:
        c = control_row.iloc[0].to_dict()
        t = champ_row.iloc[0].to_dict()
        for key in (
            "mean_denied_high_risk_lift",
            "mean_high_risk_reachability_rate",
            "mean_denied_to_approved_lift",
            "mean_fairness_approval_gap_after",
            "mean_latency_p99_ms",
        ):
            deltas[f"{key}_delta_vs_control"] = float(t.get(key, 0.0) - c.get(key, 0.0))

    ranked_variants = []
    for _, r in ranked_summary_df.iterrows():
        ranked_variants.append(
            {
                "variant_id": str(r.get("variant_id", "")),
                "release_decision": str(r.get("release_decision", "NO_GO")),
                "acceptance_status": str(r.get("acceptance_status", "REJECTED")),
                "acceptance_eligible": bool(r.get("acceptance_eligible", False)),
                "evidence_level": str(r.get("evidence_level", "single_run_fallback")),
                "pilot_eligible": bool(r.get("pilot_eligible", False)),
                "promotion_eligible": bool(r.get("_promotion_eligible", False)),
                "broad_rollout_allowed": bool(r.get("broad_rollout_allowed", False)),
                "gate_all_pass": bool(r.get("_gate_all_pass", False)),
                "gate_failed_check_count": int(r.get("_gate_failed_check_count", 0)),
                "gate_violation_score": float(r.get("_gate_violation_score", 0.0)),
            }
        )

    summary_payload = {
        "champion_variant": champion_variant,
        "control_variant": control_variant,
        "variant_count": int(ranked_summary_df.shape[0]),
        "seed_count": int(len(seeds)),
        "kpi_contract": str(args.kpi_contract),
        "champion_release_decision": str(champ_row.iloc[0].get("release_decision", "NO_GO")) if not champ_row.empty else "NO_GO",
        "champion_acceptance_status": str(champ_row.iloc[0].get("acceptance_status", "REJECTED")) if not champ_row.empty else "REJECTED",
        "champion_acceptance_eligible": bool(champ_row.iloc[0].get("acceptance_eligible", False))
        if not champ_row.empty
        else False,
        "champion_evidence_level": str(champ_row.iloc[0].get("evidence_level", "single_run_fallback"))
        if not champ_row.empty
        else "single_run_fallback",
        "champion_pilot_eligible": bool(champ_row.iloc[0].get("pilot_eligible", False)) if not champ_row.empty else False,
        "champion_promotion_eligible": bool(champ_row.iloc[0].get("_promotion_eligible", False)) if not champ_row.empty else False,
        "champion_broad_rollout_allowed": bool(champ_row.iloc[0].get("broad_rollout_allowed", False))
        if not champ_row.empty
        else False,
        "champion_gate_all_pass": bool(champ_row.iloc[0].get("_gate_all_pass", False)) if not champ_row.empty else False,
        "champion_gate_failed_check_count": int(champ_row.iloc[0].get("_gate_failed_check_count", 0))
        if not champ_row.empty
        else 0,
        "champion_gate_violation_score": float(champ_row.iloc[0].get("_gate_violation_score", 0.0))
        if not champ_row.empty
        else 0.0,
        "deltas_vs_control": deltas,
        "ranked_variants": ranked_variants,
    }
    decision_path = run_ctx.tables_dir / "challenger_matrix_decision.json"
    decision_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    supporting_artifacts = {
        "challenger_matrix_runs_csv": "tables/challenger_matrix_runs.csv",
        "challenger_matrix_variant_summary_csv": "tables/challenger_matrix_variant_summary.csv",
        "challenger_matrix_variant_summary_ranked_csv": "tables/challenger_matrix_variant_summary_ranked.csv",
        "challenger_matrix_decision_json": "tables/challenger_matrix_decision.json",
    }
    if frozen_variant_rows:
        supporting_artifacts["challenger_variant_frozen_models_json"] = "tables/challenger_variant_frozen_models.json"
    if not champ_row.empty:
        champion_snapshot = build_kpi_contract_snapshot(
            runner_type="challenger",
            release_payload={
                "decision": str(champ_row.iloc[0].get("release_decision", "NO_GO")),
                "smoke_pass": bool(champ_row.iloc[0].get("release_decision", "NO_GO") == GO),
                "pilot_eligible": bool(champ_row.iloc[0].get("pilot_eligible", False)),
                "broad_rollout_allowed": bool(champ_row.iloc[0].get("broad_rollout_allowed", False)),
            },
            aggregate_metrics={
                "lift_pass": bool(champ_row.iloc[0].get("lift_pass", False)),
                "reliability_pass": bool(champ_row.iloc[0].get("reliability_pass", False)),
                "fairness_seed_pass_count": int(champ_row.iloc[0].get("fairness_seed_pass_count", 0)),
                "fairness_seed_total": int(champ_row.iloc[0].get("fairness_seed_total", 0)),
                "primary_fairness_metric": "equalized_odds_gap_delta",
                "worst_fairness_gap": float(champ_row.iloc[0].get("worst_fairness_gap", 0.0)),
                "dominant_fail_segment_key": str(champ_row.iloc[0].get("dominant_fail_segment_key", "")),
                "dominant_fail_candidate_source": str(champ_row.iloc[0].get("dominant_fail_candidate_source", "")),
            },
            evidence_level=str(champ_row.iloc[0].get("evidence_level", "single_run_fallback")),
            acceptance_eligible=bool(champ_row.iloc[0].get("acceptance_eligible", False)),
            supporting_artifacts=supporting_artifacts,
            model_version=str(champ_row.iloc[0].get("model_version", "")),
            model_freeze_mode=str(champ_row.iloc[0].get("model_freeze_mode", "")),
            evidence_status=str(champ_row.iloc[0].get("evidence_status", "degraded")),
            degraded_reason=str(champ_row.iloc[0].get("degraded_reason", "")),
            metadata={
                "champion_variant": champion_variant,
                "variant_count": int(ranked_summary_df.shape[0]),
            },
        )
        (run_ctx.tables_dir / "kpi_contract_snapshot.json").write_text(
            json.dumps(champion_snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    run_ctx.save_metrics(
        {
            "champion_variant": champion_variant,
            "variant_count": int(ranked_summary_df.shape[0]),
            "seed_count": int(len(seeds)),
            "champion_release_decision": str(summary_payload["champion_release_decision"]),
            "champion_acceptance_eligible": bool(summary_payload["champion_acceptance_eligible"]),
            "champion_mean_denied_high_risk_lift": float(
                champ_row.iloc[0].get("mean_denied_high_risk_lift", 0.0)
            )
            if not champ_row.empty
            else 0.0,
            "champion_gate_all_pass": bool(champ_row.iloc[0].get("_gate_all_pass", False))
            if not champ_row.empty
            else False,
            "champion_gate_violation_score": float(champ_row.iloc[0].get("_gate_violation_score", 0.0))
            if not champ_row.empty
            else 0.0,
        }
    )
    logger.info("Challenger matrix completed. champion=%s", champion_variant)
    logger.info("Outputs: %s %s %s %s", runs_path, summary_path, ranked_summary_path, decision_path)


if __name__ == "__main__":
    main()
