from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from credit_coach.ops.kpi_contract import (
    ALL_KPI_THRESHOLD_KEYS,
    apply_kpi_thresholds_to_args,
    build_kpi_contract_snapshot,
    build_kpi_snapshot,
    build_release_evidence_pack,
    derive_acceptance_status,
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run production smoke gates from latest artifacts")
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--batch_summary_json", type=str, default="")
    p.add_argument("--batch_fairness_change_csv", type=str, default="")
    p.add_argument("--benchmark_summary_csv", type=str, default="")
    p.add_argument("--monitoring_summary_csv", type=str, default="")
    p.add_argument("--fairness_csv", type=str, default="")
    p.add_argument("--fairness_stress_csv", type=str, default="")
    p.add_argument("--telemetry_json", type=str, default="")
    p.add_argument("--release_evidence_pack_json", type=str, default="")
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
    p.add_argument("--artifact_root", type=str, default="artifacts/runs")
    return p.parse_args(argv)


def _latest_or_fail(pattern: str, *, hint: str) -> Path:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"Missing artifact for {hint}. Run corresponding pipeline first.")
    return candidates[-1]


def _latest_or_none(pattern: str) -> Path | None:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        return None
    return candidates[-1]


def _resolve_path(raw: str, *, pattern: str, hint: str) -> Path:
    return Path(raw) if raw else _latest_or_fail(pattern, hint=hint)


def _resolve_optional_path(raw: str) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    return path if path.exists() else None


def _resolve_optional_artifact_path(raw: str, *, pattern: str) -> Path | None:
    if raw:
        path = Path(raw)
        return path if path.exists() else None
    return _latest_or_none(pattern)


def _load_release_evidence_pack(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_artifact_from_release_pack(
    *,
    pack_payload: dict[str, Any] | None,
    pack_path: Path | None,
    artifact_key: str,
) -> Path | None:
    if pack_path is None or not isinstance(pack_payload, dict):
        return None
    candidates: list[dict[str, Any]] = []
    required = pack_payload.get("required_artifacts", {})
    optional = pack_payload.get("optional_artifacts", {})
    if isinstance(required, dict):
        candidates.append(required)
    if isinstance(optional, dict):
        candidates.append(optional)
    raw_path = ""
    for catalog in candidates:
        if artifact_key in catalog:
            raw_path = str(catalog.get(artifact_key, "")).strip()
            break
    if not raw_path:
        return None
    if raw_path.startswith("tables/"):
        resolved = pack_path.parent.parent / raw_path
    else:
        resolved = Path(raw_path)
    return resolved if resolved.exists() else None


def _mirror_artifact(source: Path | None, destination: Path) -> bool:
    if source is None or not source.exists():
        return False
    destination.write_bytes(source.read_bytes())
    return True


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


def _evaluate_telemetry_gate(
    *,
    telemetry_payload: dict[str, Any] | None,
    require_telemetry_enabled: bool,
    min_telemetry_success_rate: float,
    max_telemetry_ingest_lag_s: float,
    telemetry_artifact_path: str = "",
) -> dict[str, Any]:
    payload = dict(telemetry_payload or {})
    artifact_path = str(telemetry_artifact_path or payload.get("telemetry_artifact_path", "")).strip()
    telemetry_enabled = bool(payload.get("enabled", False))
    telemetry_exported = bool(payload.get("exported", False))
    telemetry_status = str(payload.get("telemetry_status", payload.get("status", "missing")) or "missing")
    telemetry_success_rate = _safe_float_map(payload, "send_success_rate", 1.0 if telemetry_exported else 0.0)
    telemetry_ingest_lag_s = _safe_float_map(payload, "ingest_lag_s_p95", 0.0)
    telemetry_failure_reason = str(payload.get("telemetry_failure_reason", "")).strip()
    telemetry_required_for_broad_rollout = True
    telemetry_required_for_pilot = True

    if not artifact_path:
        telemetry_failure_reason = "missing_artifact"
        telemetry_status = "missing"
    elif not telemetry_enabled:
        telemetry_failure_reason = telemetry_failure_reason or "disabled_exporter"
    elif not telemetry_exported:
        telemetry_failure_reason = telemetry_failure_reason or "export_failed"
    elif telemetry_success_rate < float(min_telemetry_success_rate):
        telemetry_failure_reason = "success_rate_below_threshold"
    elif telemetry_ingest_lag_s > float(max_telemetry_ingest_lag_s):
        telemetry_failure_reason = "ingest_lag_above_threshold"

    telemetry_gate_status = "healthy" if not telemetry_failure_reason else "degraded"

    return {
        "telemetry_status": telemetry_status,
        "telemetry_gate_status": telemetry_gate_status,
        "telemetry_failure_reason": telemetry_failure_reason,
        "telemetry_success_rate": telemetry_success_rate,
        "telemetry_ingest_lag_s": telemetry_ingest_lag_s,
        "telemetry_required_for_broad_rollout": telemetry_required_for_broad_rollout,
        "telemetry_required_for_pilot": telemetry_required_for_pilot,
        "telemetry_artifact_path": artifact_path,
        "telemetry_enabled": telemetry_enabled,
        "telemetry_exported": telemetry_exported,
        "telemetry_ok": bool(telemetry_gate_status != "degraded"),
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
    telemetry_artifact_path: str = "",
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

    telemetry_gate = _evaluate_telemetry_gate(
        telemetry_payload=telemetry_payload,
        require_telemetry_enabled=bool(args.require_telemetry_enabled),
        min_telemetry_success_rate=float(args.min_telemetry_success_rate),
        max_telemetry_ingest_lag_s=float(args.max_telemetry_ingest_lag_s),
        telemetry_artifact_path=telemetry_artifact_path,
    )

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
                    "telemetry": bool(telemetry_gate["telemetry_ok"]),
                },
                values={
                    "approval_rate": approval_rate,
                    "max_psi": max_psi,
                    "telemetry_enabled": bool(telemetry_gate["telemetry_enabled"]),
                    "telemetry_exported": bool(telemetry_gate["telemetry_exported"]),
                    "telemetry_status": str(telemetry_gate["telemetry_status"]),
                    "telemetry_gate_status": str(telemetry_gate["telemetry_gate_status"]),
                    "telemetry_failure_reason": str(telemetry_gate["telemetry_failure_reason"]),
                    "telemetry_success_rate": float(telemetry_gate["telemetry_success_rate"]),
                    "telemetry_ingest_lag_s": float(telemetry_gate["telemetry_ingest_lag_s"]),
                    "telemetry_required_for_broad_rollout": bool(
                        telemetry_gate["telemetry_required_for_broad_rollout"]
                    ),
                    "telemetry_required_for_pilot": bool(telemetry_gate["telemetry_required_for_pilot"]),
                    "telemetry_artifact_path": str(telemetry_gate["telemetry_artifact_path"]),
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
    telemetry_payload: dict[str, Any] | None = None,
    telemetry_artifact_path: str = "",
    phase_scale_aggregate: dict[str, Any] | None = None,
    milestone_acceptance_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    telemetry_gate = _evaluate_telemetry_gate(
        telemetry_payload=dict(telemetry_payload or {}),
        require_telemetry_enabled=bool(thresholds.get("require_telemetry_enabled", False)),
        min_telemetry_success_rate=float(thresholds.get("min_telemetry_success_rate", 0.0)),
        max_telemetry_ingest_lag_s=float(thresholds.get("max_telemetry_ingest_lag_s", 0.0)),
        telemetry_artifact_path=telemetry_artifact_path,
    )
    if isinstance(milestone_acceptance_summary, dict) and str(milestone_acceptance_summary.get("release_decision", "")).strip():
        decision = str(milestone_acceptance_summary.get("release_decision", "NO_GO"))
        acceptance_eligible = bool(milestone_acceptance_summary.get("acceptance_eligible", False))
        broad_rollout_allowed = bool(milestone_acceptance_summary.get("broad_rollout_allowed", decision == "GO"))
        if not acceptance_eligible:
            broad_rollout_allowed = False
        summary = {
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
        if telemetry_gate["telemetry_gate_status"] == "degraded":
            summary["smoke_pass"] = False
            summary["pilot_eligible"] = False
            summary["broad_rollout_allowed"] = False
            summary["evidence_status"] = "degraded"
        summary["acceptance_status"] = derive_acceptance_status(
            summary["release_decision"],
            acceptance_eligible=bool(summary["acceptance_eligible"]),
            broad_rollout_allowed=bool(summary["broad_rollout_allowed"]),
        )
        summary.update(telemetry_gate)
        return summary

    if isinstance(phase_scale_aggregate, dict) and int(phase_scale_aggregate.get("fairness_seed_total", 0)) > 0:
        metrics = dict(phase_scale_aggregate)
        release_payload = evaluate_release_decision(metrics, thresholds)
        acceptance_eligible = bool(str(metrics.get("model_freeze_mode", "")).strip() != "implicit_latest")
        evidence_status = "complete" if acceptance_eligible else "degraded"
        degraded_reason = "" if acceptance_eligible else "implicit_latest_model_freeze"
        broad_rollout_allowed = bool(release_payload.get("broad_rollout_allowed", False))
        if not acceptance_eligible:
            broad_rollout_allowed = False
        summary = {
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
        if telemetry_gate["telemetry_gate_status"] == "degraded":
            summary["smoke_pass"] = False
            summary["pilot_eligible"] = False
            summary["broad_rollout_allowed"] = False
            summary["evidence_status"] = "degraded"
        summary["acceptance_status"] = derive_acceptance_status(
            summary["release_decision"],
            acceptance_eligible=bool(summary["acceptance_eligible"]),
            broad_rollout_allowed=bool(summary["broad_rollout_allowed"]),
        )
        summary.update(telemetry_gate)
        return summary
    else:
        fair_row = batch_fairness_change_df.iloc[0].to_dict() if not batch_fairness_change_df.empty else {}
        snapshot = evaluate_seed_kpi_contract(batch_summary, fair_row, thresholds)
        metrics = aggregate_release_metrics([snapshot], thresholds=thresholds)
        release_payload = evaluate_release_decision(metrics, thresholds)
        summary = {
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
        if telemetry_gate["telemetry_gate_status"] == "degraded":
            summary["smoke_pass"] = False
            summary["pilot_eligible"] = False
            summary["broad_rollout_allowed"] = False
        summary["acceptance_status"] = derive_acceptance_status(
            summary["release_decision"],
            acceptance_eligible=bool(summary["acceptance_eligible"]),
            broad_rollout_allowed=bool(summary["broad_rollout_allowed"]),
        )
        summary.update(telemetry_gate)
        return summary


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
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
    release_evidence_pack_path = _resolve_optional_artifact_path(
        args.release_evidence_pack_json,
        pattern="*/tables/release_evidence_pack.json",
    )
    release_evidence_pack = _load_release_evidence_pack(release_evidence_pack_path)
    telemetry_path = _resolve_optional_path(args.telemetry_json) or _resolve_artifact_from_release_pack(
        pack_payload=release_evidence_pack,
        pack_path=release_evidence_pack_path,
        artifact_key="telemetry_export_json",
    ) or _latest_or_none("*/tables/telemetry_export.json")
    phase_scale_aggregate_path = _resolve_optional_path(args.phase_scale_aggregate_json) or _resolve_artifact_from_release_pack(
        pack_payload=release_evidence_pack,
        pack_path=release_evidence_pack_path,
        artifact_key="phase_scale_aggregate_json",
    )
    milestone_acceptance_path = _resolve_optional_path(args.milestone_acceptance_json) or _resolve_artifact_from_release_pack(
        pack_payload=release_evidence_pack,
        pack_path=release_evidence_pack_path,
        artifact_key="milestone_acceptance_summary_json",
    )

    batch_summary = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    batch_fairness_change_df = pd.read_csv(batch_fairness_change_path)
    benchmark_df = pd.read_csv(benchmark_path)
    monitoring_df = pd.read_csv(monitoring_path)
    fairness_df = pd.read_csv(fairness_path)
    fairness_stress_df = pd.read_csv(fairness_stress_path)
    telemetry_payload = (
        json.loads(telemetry_path.read_text(encoding="utf-8"))
        if telemetry_path is not None and telemetry_path.exists()
        else {}
    )
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
            "telemetry_json": str(telemetry_path) if telemetry_path is not None else "",
            "release_evidence_pack_json": (
                str(release_evidence_pack_path) if release_evidence_pack_path is not None else ""
            ),
            "milestone_acceptance_json": str(milestone_acceptance_path) if milestone_acceptance_path is not None else "",
            "thresholds": resolved_thresholds,
        },
        base_artifact_dir=args.artifact_root,
    )
    mirrored_telemetry = _mirror_artifact(telemetry_path, run_ctx.tables_dir / "telemetry_export.json")
    mirrored_phase_scale = _mirror_artifact(
        phase_scale_aggregate_path,
        run_ctx.tables_dir / "phase_scale_aggregate.json",
    )
    mirrored_milestone_acceptance = _mirror_artifact(
        milestone_acceptance_path,
        run_ctx.tables_dir / "milestone_acceptance_summary.json",
    )

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change_df,
        benchmark_df=benchmark_df,
        monitoring_df=monitoring_df,
        fairness_df=fairness_df,
        fairness_stress_df=fairness_stress_df,
        telemetry_payload=telemetry_payload,
        telemetry_artifact_path=str(telemetry_path) if telemetry_path is not None else "",
        audit_ok=audit_ok,
        audit_issue_count=len(audit_issues),
        args=args,
    )
    gate_df = pd.DataFrame(rows)
    out_csv = run_ctx.tables_dir / "production_smoke_report.csv"
    out_json = run_ctx.tables_dir / "production_smoke_report.json"
    out_release_summary = run_ctx.tables_dir / "release_smoke_summary.json"
    out_kpi_snapshot = run_ctx.tables_dir / "kpi_snapshot.json"
    out_contract_snapshot = run_ctx.tables_dir / "kpi_contract_snapshot.json"
    out_release_evidence_snapshot = run_ctx.tables_dir / "release_evidence_snapshot.json"
    gate_df.to_csv(out_csv, index=False)
    release_summary = build_smoke_release_summary(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change_df,
        thresholds=resolved_thresholds,
        telemetry_payload=telemetry_payload,
        telemetry_artifact_path=str(telemetry_path) if telemetry_path is not None else "",
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
        "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
        "release_evidence_snapshot_json": "tables/release_evidence_snapshot.json",
    }
    if mirrored_telemetry:
        supporting_artifacts["telemetry_export_json"] = "tables/telemetry_export.json"
    if mirrored_phase_scale:
        supporting_artifacts["phase_scale_aggregate_json"] = "tables/phase_scale_aggregate.json"
    if mirrored_milestone_acceptance:
        supporting_artifacts["milestone_acceptance_summary_json"] = "tables/milestone_acceptance_summary.json"

    contract_snapshot = build_kpi_contract_snapshot(
        runner_type="smoke",
        release_payload={
            "decision": str(release_summary["release_decision"]),
            "decision_reason": str(release_summary.get("decision_reason", "")),
            "smoke_pass": bool(release_summary.get("smoke_pass", False)),
            "pilot_eligible": bool(release_summary.get("pilot_eligible", False)),
            "broad_rollout_allowed": bool(release_summary.get("broad_rollout_allowed", False)),
            "telemetry_status": str(release_summary.get("telemetry_status", "")),
            "telemetry_gate_status": str(release_summary.get("telemetry_gate_status", "")),
            "telemetry_failure_reason": str(release_summary.get("telemetry_failure_reason", "")),
            "telemetry_success_rate": float(release_summary.get("telemetry_success_rate", 0.0)),
            "telemetry_ingest_lag_s": float(release_summary.get("telemetry_ingest_lag_s", 0.0)),
            "telemetry_required_for_broad_rollout": bool(
                release_summary.get("telemetry_required_for_broad_rollout", False)
            ),
            "telemetry_required_for_pilot": bool(release_summary.get("telemetry_required_for_pilot", False)),
            "telemetry_artifact_path": str(release_summary.get("telemetry_artifact_path", "")),
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
    out_release_summary.write_text(
        json.dumps(
            {
                "run_id": run_ctx.run_id,
                **release_summary,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    release_evidence_snapshot = build_release_evidence_pack(
        runner_type="smoke",
        phase=str(release_summary.get("phase", "")),
        milestone=str(release_summary.get("milestone", "")),
        release_decision=str(release_summary["release_decision"]),
        acceptance_status=str(release_summary.get("acceptance_status", "")),
        evidence_level=str(release_summary.get("evidence_level", "single_run_fallback")),
        evidence_status=str(release_summary.get("evidence_status", "degraded")),
        acceptance_eligible=bool(release_summary.get("acceptance_eligible", False)),
        required_artifacts={
            "production_smoke_report_csv": "tables/production_smoke_report.csv",
            "production_smoke_report_json": "tables/production_smoke_report.json",
            "release_smoke_summary_json": "tables/release_smoke_summary.json",
            "kpi_snapshot_json": "tables/kpi_snapshot.json",
            "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
        },
        optional_artifacts={
            **({"telemetry_export_json": "tables/telemetry_export.json"} if mirrored_telemetry else {}),
            **(
                {"phase_scale_aggregate_json": "tables/phase_scale_aggregate.json"}
                if mirrored_phase_scale
                else {}
            ),
            **(
                {"milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json"}
                if mirrored_milestone_acceptance
                else {}
            ),
        },
        existing_artifacts=[
            "tables/production_smoke_report.csv",
            "tables/production_smoke_report.json",
            "tables/release_smoke_summary.json",
            "tables/kpi_snapshot.json",
            "tables/kpi_contract_snapshot.json",
            *(
                ["tables/telemetry_export.json"]
                if mirrored_telemetry
                else []
            ),
            *(
                ["tables/phase_scale_aggregate.json"]
                if mirrored_phase_scale
                else []
            ),
            *(
                ["tables/milestone_acceptance_summary.json"]
                if mirrored_milestone_acceptance
                else []
            ),
        ],
        metadata={
            "source_release_evidence_pack_found": bool(release_evidence_pack_path is not None),
        },
    )
    out_release_evidence_snapshot.write_text(
        json.dumps(release_evidence_snapshot, indent=2, ensure_ascii=False),
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
    return run_ctx
    logger.info("Outputs: %s %s %s %s", out_csv, out_json, out_kpi_snapshot, out_contract_snapshot)


if __name__ == "__main__":
    main()
