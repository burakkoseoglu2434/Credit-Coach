from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.ops.kpi_contract import (
    ALL_KPI_THRESHOLD_KEYS,
    apply_kpi_thresholds_to_args,
    build_kpi_contract_snapshot,
    build_kpi_snapshot,
    extract_kpi_thresholds,
    load_kpi_thresholds,
)
from credit_coach.ops.release_decision import (
    aggregate_release_metrics,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.storage.repository import verify_audit_chain
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_production_smoke")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run production smoke gates from latest artifacts")
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--batch_summary_json", type=str, default="")
    p.add_argument("--batch_fairness_change_csv", type=str, default="")
    p.add_argument("--benchmark_summary_csv", type=str, default="")
    p.add_argument("--monitoring_summary_csv", type=str, default="")
    p.add_argument("--fairness_csv", type=str, default="")
    p.add_argument("--fairness_stress_csv", type=str, default="")
    p.add_argument("--telemetry_json", type=str, default="")
    p.add_argument("--phase_scale_aggregate_json", type=str, default="")
    p.add_argument("--milestone_acceptance_json", type=str, default="")
    p.add_argument("--min_denied_to_approved_lift", type=float, default=None)
    p.add_argument("--min_denied_high_risk_lift", type=float, default=None)
    p.add_argument("--min_denied_gate_pass_rate", type=float, default=None)
    p.add_argument("--max_denied_reliability_violation_rate", type=float, default=None)
    p.add_argument("--max_approval_gap_delta", type=float, default=None)
    p.add_argument("--max_equalized_odds_gap_delta", type=float, default=None)
    p.add_argument("--max_p95_latency_ms", type=float, default=None)
    p.add_argument("--max_p99_latency_ms", type=float, default=None)
    p.add_argument("--max_error_rate", type=float, default=None)
    p.add_argument("--min_last_k_validity", type=float, default=None)
    p.add_argument("--min_last_k_safe_rate", type=float, default=None)
    p.add_argument("--min_last_k_avg_risk_margin", type=float, default=None)
    p.add_argument("--max_fairness_gap", type=float, default=None)
    p.add_argument("--max_high_stress_fairness_gap", type=float, default=None)
    p.add_argument("--max_recourse_success_gap", type=float, default=None)
    p.add_argument("--max_recourse_cost_gap", type=float, default=None)
    p.add_argument("--min_trajectory_gate_pass_rate_4w", type=float, default=None)
    p.add_argument("--min_trajectory_gate_pass_rate_12w", type=float, default=None)
    p.add_argument("--min_trajectory_gate_pass_rate_24w", type=float, default=None)
    p.add_argument("--min_trajectory_partial_progress_rate", type=float, default=None)
    p.add_argument("--max_trajectory_median_time_to_gate_pass_days", type=float, default=None)
    p.add_argument("--min_approval_rate", type=float, default=None)
    p.add_argument("--max_psi", type=float, default=None)
    p.add_argument("--min_avg_reliability", type=float, default=None)
    p.add_argument("--min_telemetry_success_rate", type=float, default=None)
    p.add_argument("--max_telemetry_ingest_lag_s", type=float, default=None)
    p.add_argument("--require_telemetry_enabled", dest="require_telemetry_enabled", action="store_true")
    p.add_argument("--allow_telemetry_disabled", dest="require_telemetry_enabled", action="store_false")
    p.set_defaults(require_telemetry_enabled=None)
    return p.parse_args()


def _latest_or_fail(pattern: str, *, hint: str) -> Path:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"Missing artifact for {hint}. Run corresponding pipeline first.")
    return candidates[-1]


def _resolve_path(raw: str, *, pattern: str, hint: str) -> Path:
    return Path(raw) if raw else _latest_or_fail(pattern, hint=hint)


def _resolve_optional_path(raw: str) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    return path if path.exists() else None


def _safe_float(row: pd.Series, key: str, default: float = 0.0) -> float:
    v = row.get(key, default)
    if pd.isna(v):
        return default
    return float(v)


def _safe_float_map(payload: dict, key: str, default: float = 0.0) -> float:
    v = payload.get(key, default)
    try:
        return float(v)
    except Exception:
        return float(default)


def _gate_row(gate_id: str, checks: dict[str, bool], values: dict[str, float | int | str]) -> dict:
    status = "PASS" if all(bool(v) for v in checks.values()) else "FAIL"
    failed_checks = [k for k, ok in checks.items() if not ok]
    return {
        "gate_id": gate_id,
        "status": status,
        "failed_checks": ",".join(failed_checks),
        "details_json": json.dumps(values, ensure_ascii=False),
    }


def build_smoke_gate_rows(
    *,
    batch_summary: dict,
    batch_fairness_change_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    monitoring_df: pd.DataFrame,
    fairness_df: pd.DataFrame,
    fairness_stress_df: pd.DataFrame,
    telemetry_payload: dict,
    audit_ok: bool,
    audit_issue_count: int,
    args: argparse.Namespace,
) -> list[dict]:
    rows: list[dict] = []
    if benchmark_df.empty:
        raise ValueError("benchmark summary is empty")
    if monitoring_df.empty:
        raise ValueError("monitoring summary is empty")
    if fairness_df.empty:
        raise ValueError("fairness summary is empty")

    fair_delta_row = batch_fairness_change_df.iloc[0] if not batch_fairness_change_df.empty else pd.Series(dtype=float)
    approval_gap_delta = _safe_float(fair_delta_row, "approval_gap_delta")
    equalized_odds_gap_delta = _safe_float(fair_delta_row, "equalized_odds_gap_delta")
    recourse_success_gap = _safe_float(fair_delta_row, "recourse_success_gap")
    recourse_cost_gap = _safe_float(fair_delta_row, "recourse_cost_gap")
    denied_lift = _safe_float_map(batch_summary, "denied_to_approved_lift")
    denied_high_risk_lift = _safe_float_map(batch_summary, "denied_high_risk_lift")
    denied_count = max(0, int(_safe_float_map(batch_summary, "denied_count", 0.0)))
    denied_with_gate_pass = max(0, int(_safe_float_map(batch_summary, "denied_with_gate_pass_plan", 0.0)))
    denied_gate_pass_rate = (
        float(denied_with_gate_pass / denied_count) if denied_count > 0 else 1.0
    )
    denied_reliability_violation_rate = _safe_float_map(
        batch_summary,
        "denied_reliability_violation_rate",
        0.0,
    )
    trajectory_gate_pass_rate_4w = _safe_float_map(batch_summary, "trajectory_gate_pass_rate_4w", 0.0)
    trajectory_gate_pass_rate_12w = _safe_float_map(batch_summary, "trajectory_gate_pass_rate_12w", 0.0)
    trajectory_gate_pass_rate_24w = _safe_float_map(batch_summary, "trajectory_gate_pass_rate_24w", 0.0)
    trajectory_partial_progress_rate = _safe_float_map(batch_summary, "trajectory_partial_progress_rate", 0.0)
    trajectory_median_time_to_gate_pass_days = _safe_float_map(
        batch_summary,
        "trajectory_median_time_to_gate_pass_days",
        9999.0,
    )
    sync_p95 = _safe_float_map(batch_summary, "sync_latency_p95_ms", float("nan"))
    sync_p99 = _safe_float_map(batch_summary, "sync_latency_p99_ms", float("nan"))
    if pd.notna(sync_p95) and pd.notna(sync_p99):
        p95 = float(sync_p95)
        p99 = float(sync_p99)
        latency_mode = "sync"
    else:
        p95 = _safe_float_map(batch_summary, "latency_p95_ms")
        p99 = _safe_float_map(batch_summary, "latency_p99_ms")
        latency_mode = "end_to_end"
    error_rate = _safe_float_map(batch_summary, "error_rate")
    rows.append(
        _gate_row(
            "G0_BATCH_RECOURSE_KPI",
            checks={
                "denied_to_approved_lift": denied_lift >= float(args.min_denied_to_approved_lift),
                "denied_high_risk_lift": denied_high_risk_lift >= float(args.min_denied_high_risk_lift),
                "approval_gap_delta": approval_gap_delta <= float(args.max_approval_gap_delta),
                "equalized_odds_gap_delta": equalized_odds_gap_delta <= float(args.max_equalized_odds_gap_delta),
                "latency_p95_ms": p95 <= float(args.max_p95_latency_ms),
                "latency_p99_ms": p99 <= float(args.max_p99_latency_ms),
                "error_rate": error_rate <= float(args.max_error_rate),
            },
            values={
                "denied_to_approved_lift": denied_lift,
                "denied_high_risk_lift": denied_high_risk_lift,
                "approval_gap_delta": approval_gap_delta,
                "equalized_odds_gap_delta": equalized_odds_gap_delta,
                "latency_p95_ms": p95,
                "latency_p99_ms": p99,
                "latency_mode": latency_mode,
                "error_rate": error_rate,
            },
        )
    )
    rows.append(
        _gate_row(
            "G0B_RECOURSE_FUNNEL",
            checks={
                "denied_gate_pass_rate": denied_gate_pass_rate >= float(args.min_denied_gate_pass_rate),
                "denied_reliability_violation_rate": (
                    denied_reliability_violation_rate <= float(args.max_denied_reliability_violation_rate)
                ),
            },
            values={
                "denied_count": denied_count,
                "denied_with_gate_pass_plan": denied_with_gate_pass,
                "denied_gate_pass_rate": denied_gate_pass_rate,
                "denied_reliability_violation_rate": denied_reliability_violation_rate,
            },
        )
    )
    rows.append(
        _gate_row(
            "G0C_TRAJECTORY",
            checks={
                "trajectory_gate_pass_rate_4w": (
                    trajectory_gate_pass_rate_4w >= float(args.min_trajectory_gate_pass_rate_4w)
                ),
                "trajectory_gate_pass_rate_12w": (
                    trajectory_gate_pass_rate_12w >= float(args.min_trajectory_gate_pass_rate_12w)
                ),
                "trajectory_gate_pass_rate_24w": (
                    trajectory_gate_pass_rate_24w >= float(args.min_trajectory_gate_pass_rate_24w)
                ),
                "trajectory_partial_progress_rate": (
                    trajectory_partial_progress_rate >= float(args.min_trajectory_partial_progress_rate)
                ),
                "trajectory_median_time_to_gate_pass_days": (
                    trajectory_median_time_to_gate_pass_days
                    <= float(args.max_trajectory_median_time_to_gate_pass_days)
                ),
            },
            values={
                "trajectory_gate_pass_rate_4w": trajectory_gate_pass_rate_4w,
                "trajectory_gate_pass_rate_12w": trajectory_gate_pass_rate_12w,
                "trajectory_gate_pass_rate_24w": trajectory_gate_pass_rate_24w,
                "trajectory_partial_progress_rate": trajectory_partial_progress_rate,
                "trajectory_median_time_to_gate_pass_days": trajectory_median_time_to_gate_pass_days,
            },
        )
    )

    our_row = benchmark_df[benchmark_df["method"] == "our"].iloc[0] if "method" in benchmark_df.columns and (benchmark_df["method"] == "our").any() else benchmark_df.iloc[0]
    mon_row = monitoring_df.iloc[0]
    fair_row = fairness_df.iloc[0]

    last_k_validity = _safe_float(our_row, "last_k_validity")
    last_k_safe_rate = _safe_float(our_row, "last_k_safe_rate")
    last_k_margin = _safe_float(our_row, "last_k_avg_risk_margin")
    fairness_gap = _safe_float(fair_row, "approval_gap")
    high_stress_gap = fairness_gap
    if (
        not fairness_stress_df.empty
        and "high_stress" in fairness_stress_df.columns
        and "approval_gap" in fairness_stress_df.columns
    ):
        high_rows = fairness_stress_df[fairness_stress_df["high_stress"] == 1]
        if not high_rows.empty:
            high_stress_gap = float(high_rows["approval_gap"].max())
    approval_rate = _safe_float(mon_row, "approval_rate")
    max_psi = _safe_float(mon_row, "max_psi")
    avg_reliability = _safe_float(mon_row, "avg_reliability")

    telemetry_status = str(telemetry_payload.get("status", "missing"))
    telemetry_enabled = bool(telemetry_payload.get("enabled", False))
    telemetry_exported = bool(telemetry_payload.get("exported", False))
    telemetry_success_rate = _safe_float_map(telemetry_payload, "send_success_rate", 1.0 if telemetry_exported else 0.0)
    telemetry_ingest_lag_s = _safe_float_map(telemetry_payload, "ingest_lag_s_p95", 0.0)
    if args.require_telemetry_enabled:
        telemetry_ok = (
            telemetry_enabled
            and telemetry_exported
            and telemetry_status == "success"
            and (telemetry_success_rate >= float(args.min_telemetry_success_rate))
            and (telemetry_ingest_lag_s <= float(args.max_telemetry_ingest_lag_s))
        )
    else:
        telemetry_ok = telemetry_status in {"success", "disabled"}

    rows.extend(
        [
            _gate_row(
                "G1_MODEL_BACKTEST",
                checks={
                    "last_k_validity": last_k_validity >= float(args.min_last_k_validity),
                    "last_k_safe_rate": last_k_safe_rate >= float(args.min_last_k_safe_rate),
                    "last_k_avg_risk_margin": last_k_margin >= float(args.min_last_k_avg_risk_margin),
                },
                values={
                    "last_k_validity": last_k_validity,
                    "last_k_safe_rate": last_k_safe_rate,
                    "last_k_avg_risk_margin": last_k_margin,
                },
            ),
            _gate_row(
                "G2_FAIRNESS",
                checks={
                    "fairness_gap": fairness_gap <= float(args.max_fairness_gap),
                    "high_stress_fairness_gap": high_stress_gap <= float(args.max_high_stress_fairness_gap),
                    "recourse_success_gap": recourse_success_gap <= float(args.max_recourse_success_gap),
                    "recourse_cost_gap": recourse_cost_gap <= float(args.max_recourse_cost_gap),
                },
                values={
                    "fairness_gap": fairness_gap,
                    "high_stress_fairness_gap": high_stress_gap,
                    "recourse_success_gap": recourse_success_gap,
                    "recourse_cost_gap": recourse_cost_gap,
                },
            ),
            _gate_row(
                "G3_ROBUSTNESS",
                checks={
                    "avg_reliability": avg_reliability >= float(args.min_avg_reliability),
                },
                values={
                    "avg_reliability": avg_reliability,
                },
            ),
            _gate_row(
                "G4_MONITORING_TELEMETRY",
                checks={
                    "approval_rate": approval_rate >= float(args.min_approval_rate),
                    "max_psi": max_psi <= float(args.max_psi),
                    "telemetry": telemetry_ok,
                },
                values={
                    "approval_rate": approval_rate,
                    "max_psi": max_psi,
                    "telemetry_enabled": telemetry_enabled,
                    "telemetry_exported": telemetry_exported,
                    "telemetry_status": telemetry_status,
                    "telemetry_success_rate": telemetry_success_rate,
                    "telemetry_ingest_lag_s": telemetry_ingest_lag_s,
                },
            ),
            _gate_row(
                "G5_SECURITY_AUDIT",
                checks={
                    "audit_chain_ok": bool(audit_ok),
                },
                values={
                    "audit_chain_ok": bool(audit_ok),
                    "audit_issue_count": int(audit_issue_count),
                },
            ),
        ]
    )
    return rows


def _kpi_snapshot_from_rows(
    *,
    gate_rows: list[dict[str, Any]],
    args: argparse.Namespace,
    run_id: str,
    overall_status: str,
) -> dict[str, Any]:
    details: dict[str, Any] = {}
    for row in gate_rows:
        payload = row.get("details_json", "{}")
        try:
            parsed = json.loads(payload)
        except Exception:
            parsed = {}
        if isinstance(parsed, dict):
            details.update(parsed)
    metrics = {
        "denied_to_approved_lift": details.get("denied_to_approved_lift"),
        "denied_high_risk_lift": details.get("denied_high_risk_lift"),
        "denied_gate_pass_rate": details.get("denied_gate_pass_rate"),
        "denied_reliability_violation_rate": details.get("denied_reliability_violation_rate"),
        "approval_gap_delta": details.get("approval_gap_delta"),
        "equalized_odds_gap_delta": details.get("equalized_odds_gap_delta"),
        "latency_p95_ms": details.get("latency_p95_ms"),
        "latency_p99_ms": details.get("latency_p99_ms"),
        "error_rate": details.get("error_rate"),
        "last_k_validity": details.get("last_k_validity"),
        "last_k_safe_rate": details.get("last_k_safe_rate"),
        "last_k_avg_risk_margin": details.get("last_k_avg_risk_margin"),
        "fairness_gap_after": details.get("fairness_gap"),
        "high_stress_fairness_gap_after": details.get("high_stress_fairness_gap"),
        "recourse_success_gap": details.get("recourse_success_gap"),
        "recourse_cost_gap": details.get("recourse_cost_gap"),
        "trajectory_gate_pass_rate_4w": details.get("trajectory_gate_pass_rate_4w"),
        "trajectory_gate_pass_rate_12w": details.get("trajectory_gate_pass_rate_12w"),
        "trajectory_gate_pass_rate_24w": details.get("trajectory_gate_pass_rate_24w"),
        "trajectory_partial_progress_rate": details.get("trajectory_partial_progress_rate"),
        "trajectory_median_time_to_gate_pass_days": details.get("trajectory_median_time_to_gate_pass_days"),
        "approval_rate": details.get("approval_rate"),
        "max_psi": details.get("max_psi"),
        "avg_reliability": details.get("avg_reliability"),
        "telemetry_success_rate": details.get("telemetry_success_rate"),
        "telemetry_ingest_lag_s": details.get("telemetry_ingest_lag_s"),
    }
    return build_kpi_snapshot(
        metrics,
        extract_kpi_thresholds(args),
        threshold_keys=ALL_KPI_THRESHOLD_KEYS,
        run_id=run_id,
        overall_status=overall_status,
    )


def _load_previous_kpi_snapshot(current_run_id: str) -> dict[str, Any]:
    candidates = sorted(Path("artifacts/runs").glob("*/tables/kpi_snapshot.json"))
    for cand in reversed(candidates):
        run_id = cand.parent.parent.name
        if run_id == current_run_id:
            continue
        try:
            payload = json.loads(cand.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload.setdefault("run_id", run_id)
                return payload
        except Exception:
            continue
    return {}


def _build_kpi_trend(
    *,
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    prev_kpis = previous.get("kpis", {}) if isinstance(previous.get("kpis", {}), dict) else {}
    cur_kpis = current.get("kpis", {}) if isinstance(current.get("kpis", {}), dict) else {}
    trend_rows: list[dict[str, Any]] = []
    for metric, cur_payload in sorted(cur_kpis.items()):
        if not isinstance(cur_payload, dict):
            continue
        cur_value = cur_payload.get("value")
        prev_value = None
        if metric in prev_kpis and isinstance(prev_kpis.get(metric), dict):
            prev_value = prev_kpis[metric].get("value")
        try:
            cur_f = float(cur_value)
            prev_f = float(prev_value) if prev_value is not None else None
        except Exception:
            cur_f, prev_f = None, None
        delta = (cur_f - prev_f) if (cur_f is not None and prev_f is not None) else None
        trend_rows.append(
            {
                "metric": metric,
                "current_value": cur_f,
                "previous_value": prev_f,
                "delta": delta,
            }
        )
    return {
        "previous_run_id": previous.get("run_id"),
        "metrics": trend_rows,
    }


def build_smoke_release_summary(
    *,
    batch_summary: dict[str, Any],
    batch_fairness_change_df: pd.DataFrame,
    thresholds: dict[str, float | bool],
    phase_scale_aggregate: dict[str, Any] | None = None,
    milestone_acceptance_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(milestone_acceptance_summary, dict) and str(milestone_acceptance_summary.get("release_decision", "")).strip():
        decision = str(milestone_acceptance_summary.get("release_decision", "NO_GO"))
        acceptance_eligible = bool(milestone_acceptance_summary.get("acceptance_eligible", False))
        broad_rollout_allowed = bool(milestone_acceptance_summary.get("broad_rollout_allowed", decision == "GO"))
        if not acceptance_eligible:
            broad_rollout_allowed = False
        return {
            "release_decision": decision,
            "decision_reason": str(milestone_acceptance_summary.get("decision_reason", "")),
            "smoke_pass": bool(milestone_acceptance_summary.get("smoke_pass", decision == "GO")),
            "pilot_eligible": bool(milestone_acceptance_summary.get("pilot_eligible", decision == "LIMITED_GO")),
            "broad_rollout_allowed": broad_rollout_allowed,
            "evidence_level": str(milestone_acceptance_summary.get("evidence_level", "seeded_suite")),
            "evidence_status": str(milestone_acceptance_summary.get("evidence_status", "complete")),
            "acceptance_eligible": acceptance_eligible,
            "degraded_reason": str(milestone_acceptance_summary.get("degraded_reason", "")),
            "missing_artifacts": list(milestone_acceptance_summary.get("missing_artifacts", [])),
            "fallback_source": "",
            "lift_pass": bool(milestone_acceptance_summary.get("lift_pass", False)),
            "reliability_pass": bool(milestone_acceptance_summary.get("reliability_pass", False)),
            "fairness_seed_pass_count": int(milestone_acceptance_summary.get("fairness_seed_pass_count", 0)),
            "fairness_seed_total": int(milestone_acceptance_summary.get("seed_count", 0)),
            "primary_fairness_metric": str(milestone_acceptance_summary.get("primary_fairness_metric", "")),
            "worst_fairness_gap": float(milestone_acceptance_summary.get("worst_primary_fairness_gap", 0.0)),
            "dominant_fail_segment_key": str(milestone_acceptance_summary.get("dominant_fail_segment_key", "")),
            "dominant_fail_candidate_source": str(milestone_acceptance_summary.get("dominant_fail_candidate_source", "")),
            "model_version": str(milestone_acceptance_summary.get("model_version", "")),
            "model_freeze_mode": str(milestone_acceptance_summary.get("model_freeze_mode", "")),
        }

    if isinstance(phase_scale_aggregate, dict) and int(phase_scale_aggregate.get("fairness_seed_total", 0)) > 0:
        metrics = dict(phase_scale_aggregate)
        release_payload = evaluate_release_decision(metrics, thresholds)
        acceptance_eligible = bool(str(metrics.get("model_freeze_mode", "")).strip() != "implicit_latest")
        evidence_status = "complete" if acceptance_eligible else "degraded"
        degraded_reason = "" if acceptance_eligible else "implicit_latest_model_freeze"
        broad_rollout_allowed = bool(release_payload.get("broad_rollout_allowed", False))
        if not acceptance_eligible:
            broad_rollout_allowed = False
        return {
            "release_decision": str(release_payload["decision"]),
            "decision_reason": str(release_payload.get("decision_reason", "")),
            "smoke_pass": bool(release_payload["smoke_pass"]),
            "pilot_eligible": bool(release_payload["pilot_eligible"]),
            "broad_rollout_allowed": broad_rollout_allowed,
            "evidence_level": "seeded_suite",
            "evidence_status": evidence_status,
            "acceptance_eligible": acceptance_eligible,
            "degraded_reason": degraded_reason,
            "missing_artifacts": [],
            "fallback_source": "",
            **metrics,
        }
    else:
        fair_row = batch_fairness_change_df.iloc[0].to_dict() if not batch_fairness_change_df.empty else {}
        snapshot = evaluate_seed_kpi_contract(batch_summary, fair_row, thresholds)
        metrics = aggregate_release_metrics([snapshot], thresholds=thresholds)
        release_payload = evaluate_release_decision(metrics, thresholds)
        return {
            "release_decision": str(release_payload["decision"]),
            "decision_reason": str(release_payload.get("decision_reason", "")),
            "smoke_pass": bool(release_payload["smoke_pass"]),
            "pilot_eligible": bool(release_payload["pilot_eligible"]),
            "broad_rollout_allowed": False,
            "evidence_level": "single_run_fallback",
            "evidence_status": "degraded",
            "acceptance_eligible": False,
            "degraded_reason": "missing_repeated_seeded_evidence",
            "missing_artifacts": ["milestone_acceptance_summary.json", "phase_scale_aggregate.json"],
            "fallback_source": "batch_summary_json",
            **metrics,
        }


def main() -> None:
    args = parse_args()
    contract_thresholds = load_kpi_thresholds(args.kpi_contract)
    args = apply_kpi_thresholds_to_args(args, contract_thresholds)
    resolved_thresholds = extract_kpi_thresholds(args)

    batch_summary_path = _resolve_path(
        args.batch_summary_json,
        pattern="*/tables/batch_summary.json",
        hint="batch recourse summary",
    )
    batch_fairness_change_path = _resolve_path(
        args.batch_fairness_change_csv,
        pattern="*/tables/batch_fairness_change.csv",
        hint="batch fairness delta",
    )
    benchmark_path = _resolve_path(
        args.benchmark_summary_csv,
        pattern="*/tables/benchmark_lastk_summary.csv",
        hint="benchmark rolling window report",
    )
    monitoring_path = _resolve_path(
        args.monitoring_summary_csv,
        pattern="*/tables/monitoring_summary.csv",
        hint="monitoring summary",
    )
    fairness_path = _resolve_path(
        args.fairness_csv,
        pattern="*/tables/fairness_report.csv",
        hint="fairness report",
    )
    fairness_stress_path = _resolve_path(
        args.fairness_stress_csv,
        pattern="*/tables/fairness_stress_matrix.csv",
        hint="fairness stress matrix",
    )
    telemetry_path = _resolve_path(
        args.telemetry_json,
        pattern="*/tables/telemetry_export.json",
        hint="telemetry export report",
    )
    phase_scale_aggregate_path = _resolve_optional_path(args.phase_scale_aggregate_json)
    milestone_acceptance_path = _resolve_optional_path(args.milestone_acceptance_json)

    batch_summary = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    batch_fairness_change_df = pd.read_csv(batch_fairness_change_path)
    benchmark_df = pd.read_csv(benchmark_path)
    monitoring_df = pd.read_csv(monitoring_path)
    fairness_df = pd.read_csv(fairness_path)
    fairness_stress_df = pd.read_csv(fairness_stress_path)
    telemetry_payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
    phase_scale_aggregate = (
        json.loads(phase_scale_aggregate_path.read_text(encoding="utf-8"))
        if phase_scale_aggregate_path is not None
        else {}
    )
    milestone_acceptance_summary = (
        json.loads(milestone_acceptance_path.read_text(encoding="utf-8"))
        if milestone_acceptance_path is not None
        else {}
    )
    audit_ok, audit_issues = verify_audit_chain()

    run_ctx = create_run_context(
        {
            "kpi_contract": str(args.kpi_contract),
            "batch_summary_json": str(batch_summary_path),
            "batch_fairness_change_csv": str(batch_fairness_change_path),
            "benchmark_summary_csv": str(benchmark_path),
            "monitoring_summary_csv": str(monitoring_path),
            "fairness_csv": str(fairness_path),
            "fairness_stress_csv": str(fairness_stress_path),
            "telemetry_json": str(telemetry_path),
            "milestone_acceptance_json": str(milestone_acceptance_path) if milestone_acceptance_path is not None else "",
            "thresholds": resolved_thresholds,
        },
        base_artifact_dir="artifacts/runs",
    )

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change_df,
        benchmark_df=benchmark_df,
        monitoring_df=monitoring_df,
        fairness_df=fairness_df,
        fairness_stress_df=fairness_stress_df,
        telemetry_payload=telemetry_payload,
        audit_ok=audit_ok,
        audit_issue_count=len(audit_issues),
        args=args,
    )
    gate_df = pd.DataFrame(rows)
    out_csv = run_ctx.tables_dir / "production_smoke_report.csv"
    out_json = run_ctx.tables_dir / "production_smoke_report.json"
    out_kpi_snapshot = run_ctx.tables_dir / "kpi_snapshot.json"
    out_contract_snapshot = run_ctx.tables_dir / "kpi_contract_snapshot.json"
    gate_df.to_csv(out_csv, index=False)
    release_summary = build_smoke_release_summary(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change_df,
        thresholds=resolved_thresholds,
        phase_scale_aggregate=phase_scale_aggregate,
        milestone_acceptance_summary=milestone_acceptance_summary,
    )
    overall_status = str(release_summary["release_decision"])
    kpi_snapshot = _kpi_snapshot_from_rows(
        gate_rows=rows,
        args=args,
        run_id=run_ctx.run_id,
        overall_status=overall_status,
    )
    previous_snapshot = _load_previous_kpi_snapshot(run_ctx.run_id)
    trend_payload = _build_kpi_trend(
        current=kpi_snapshot,
        previous=previous_snapshot,
    )
    supporting_artifacts = {
        "production_smoke_report_csv": "tables/production_smoke_report.csv",
        "kpi_snapshot_json": "tables/kpi_snapshot.json",
        "batch_summary_json": str(batch_summary_path),
        "batch_fairness_change_csv": str(batch_fairness_change_path),
    }
    if phase_scale_aggregate_path is not None:
        supporting_artifacts["phase_scale_aggregate_json"] = str(phase_scale_aggregate_path)
    if milestone_acceptance_path is not None:
        supporting_artifacts["milestone_acceptance_summary_json"] = str(milestone_acceptance_path)

    contract_snapshot = build_kpi_contract_snapshot(
        runner_type="smoke",
        release_payload={
            "decision": str(release_summary["release_decision"]),
            "decision_reason": str(release_summary.get("decision_reason", "")),
            "smoke_pass": bool(release_summary.get("smoke_pass", False)),
            "pilot_eligible": bool(release_summary.get("pilot_eligible", False)),
            "broad_rollout_allowed": bool(release_summary.get("broad_rollout_allowed", False)),
        },
        aggregate_metrics=release_summary,
        evidence_level=str(release_summary.get("evidence_level", "single_run_fallback")),
        acceptance_eligible=bool(release_summary.get("acceptance_eligible", False)),
        supporting_artifacts=supporting_artifacts,
        model_version=str(release_summary.get("model_version", batch_summary.get("model_version", ""))),
        model_freeze_mode=str(release_summary.get("model_freeze_mode", batch_summary.get("model_freeze_mode", ""))),
        evidence_status=str(release_summary.get("evidence_status", "degraded")),
        degraded_reason=str(release_summary.get("degraded_reason", "")),
        missing_artifacts=release_summary.get("missing_artifacts", []),
        fallback_source=str(release_summary.get("fallback_source", "")),
        metadata={"run_id": run_ctx.run_id},
    )
    out_kpi_snapshot.write_text(json.dumps(kpi_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    out_contract_snapshot.write_text(json.dumps(contract_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    out_json.write_text(
        json.dumps(
            {
                "run_id": run_ctx.run_id,
                "overall_status": overall_status,
                "release_decision": release_summary,
                "thresholds": resolved_thresholds,
                "gates": gate_df.to_dict(orient="records"),
                "kpi_trend_vs_previous": trend_payload,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    run_ctx.save_metrics(
        {
            "overall_status": overall_status,
            "smoke_pass": bool(release_summary["smoke_pass"]),
            "pilot_eligible": bool(release_summary["pilot_eligible"]),
            "acceptance_eligible": bool(release_summary.get("acceptance_eligible", False)),
            "evidence_level": str(release_summary.get("evidence_level", "single_run_fallback")),
            "gate_pass_count": int((gate_df["status"] == "PASS").sum()),
            "gate_fail_count": int((gate_df["status"] != "PASS").sum()),
            "audit_issue_count": int(len(audit_issues)),
            "kpi_contract_path": str(args.kpi_contract),
            **resolved_thresholds,
        }
    )
    logger.info("Production smoke complete. status=%s", overall_status)
    logger.info("Outputs: %s %s %s %s", out_csv, out_json, out_kpi_snapshot, out_contract_snapshot)


if __name__ == "__main__":
    main()
