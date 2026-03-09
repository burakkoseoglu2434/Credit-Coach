from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib import request


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def build_telemetry_metrics(
    summary: dict[str, Any],
    *,
    alert_count: int,
    high_alert_count: int,
) -> dict[str, float]:
    metrics = {
        "approval_rate": _safe_float(summary.get("approval_rate")),
        "avg_risk_margin": _safe_float(summary.get("avg_risk_margin")),
        "avg_reliability": _safe_float(summary.get("avg_reliability")),
        "fairness_gap": _safe_float(summary.get("fairness_gap")),
        "high_stress_fairness_gap": _safe_float(summary.get("high_stress_fairness_gap")),
        "max_psi": _safe_float(summary.get("max_psi")),
        "denied_to_approved_lift": _safe_float(summary.get("denied_to_approved_lift")),
        "latency_p95_ms": _safe_float(summary.get("latency_p95_ms")),
        "latency_p99_ms": _safe_float(summary.get("latency_p99_ms")),
        "error_rate": _safe_float(summary.get("error_rate")),
        "alert_count": float(int(alert_count)),
        "high_alert_count": float(int(high_alert_count)),
    }
    # Optional recourse and model KPIs used by smoke/release gates.
    for key in (
        "denied_high_risk_lift",
        "denied_reliability_violation_rate",
        "denied_ci_violation_rate",
        "denied_worst_margin_violation_rate",
        "denied_internal_gate_pass_share",
        "denied_dice_gate_pass_share",
        "denied_internal_vs_dice_gate_pass_share",
        "last_k_validity",
        "last_k_safe_rate",
        "last_k_avg_risk_margin",
    ):
        if key in summary:
            metrics[key] = _safe_float(summary.get(key))
    # Optional latency bucket gauges (counts) for SLO trend monitoring.
    for key in (
        "latency_bucket_le_500_count",
        "latency_bucket_le_1000_count",
        "latency_bucket_le_2000_count",
        "latency_bucket_gt_2000_count",
    ):
        if key in summary:
            metrics[key] = _safe_float(summary.get(key))
    return metrics


def render_prometheus_text(
    metrics: dict[str, float],
    *,
    namespace: str = "credit_coach",
    labels: dict[str, str] | None = None,
) -> str:
    labels = labels or {}
    label_str = ""
    if labels:
        encoded = ",".join(f'{k}="{str(v)}"' for k, v in sorted(labels.items()))
        label_str = "{" + encoded + "}"

    lines: list[str] = []
    for name, value in sorted(metrics.items()):
        full_name = f"{namespace}_{name}"
        lines.append(f"# TYPE {full_name} gauge")
        lines.append(f"{full_name}{label_str} {value}")
    lines.append("")
    return "\n".join(lines)


def _post_bytes(url: str, body: bytes, *, content_type: str, timeout_seconds: float = 3.0) -> tuple[bool, str]:
    req = request.Request(
        url=url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:  # nosec B310
            status = int(getattr(resp, "status", 200))
        if 200 <= status < 300:
            return True, f"http_{status}"
        return False, f"http_{status}"
    except Exception as exc:
        return False, f"error:{exc.__class__.__name__}"


def _write_payload(path_like: str, payload: str) -> tuple[bool, str]:
    try:
        out_path = Path(path_like).expanduser()
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        return True, "success"
    except Exception as exc:
        return False, f"error:{exc.__class__.__name__}"


def export_prometheus_text(
    metrics: dict[str, float],
    *,
    endpoint_url: str,
    namespace: str = "credit_coach",
    labels: dict[str, str] | None = None,
    timeout_seconds: float = 3.0,
) -> tuple[bool, str, str]:
    payload = render_prometheus_text(metrics, namespace=namespace, labels=labels)
    ok, status = _post_bytes(
        endpoint_url,
        payload.encode("utf-8"),
        content_type="text/plain; version=0.0.4",
        timeout_seconds=timeout_seconds,
    )
    return ok, status, payload


def _render_otlp_like_json(
    metrics: dict[str, float],
    *,
    service_name: str,
    namespace: str = "credit_coach",
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    labels = labels or {}
    now_ns = int(time.time() * 1_000_000_000)
    metrics_list: list[dict[str, Any]] = []
    for name, value in sorted(metrics.items()):
        attrs = [{"key": k, "value": {"stringValue": str(v)}} for k, v in sorted(labels.items())]
        metric_entry = {
            "name": f"{namespace}.{name}",
            "unit": "1",
            "gauge": {
                "dataPoints": [
                    {
                        "asDouble": float(value),
                        "timeUnixNano": str(now_ns),
                        "attributes": attrs,
                    }
                ]
            },
        }
        metrics_list.append(metric_entry)

    return {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": [{"key": "service.name", "value": {"stringValue": service_name}}],
                },
                "scopeMetrics": [
                    {
                        "scope": {"name": "credit_coach.ops.monitoring"},
                        "metrics": metrics_list,
                    }
                ],
            }
        ]
    }


def export_otlp_http_json(
    metrics: dict[str, float],
    *,
    endpoint_url: str,
    service_name: str = "credit-coach",
    namespace: str = "credit_coach",
    labels: dict[str, str] | None = None,
    timeout_seconds: float = 3.0,
) -> tuple[bool, str, str]:
    payload_obj = _render_otlp_like_json(
        metrics,
        service_name=service_name,
        namespace=namespace,
        labels=labels,
    )
    payload = json.dumps(payload_obj, ensure_ascii=False)
    ok, status = _post_bytes(
        endpoint_url,
        payload.encode("utf-8"),
        content_type="application/json",
        timeout_seconds=timeout_seconds,
    )
    return ok, status, payload


def export_monitoring_telemetry(
    summary: dict[str, Any],
    *,
    alert_count: int,
    high_alert_count: int,
    exporter_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = exporter_cfg or {}
    enabled = bool(cfg.get("enabled", False))
    mode = str(cfg.get("mode", "prometheus")).strip().lower()
    endpoint_url = str(cfg.get("endpoint_url", "")).strip()
    timeout_seconds = float(cfg.get("timeout_seconds", 3.0))
    namespace = str(cfg.get("namespace", "credit_coach")).strip() or "credit_coach"
    service_name = str(cfg.get("service_name", "credit-coach")).strip() or "credit-coach"
    labels = cfg.get("labels", {}) if isinstance(cfg.get("labels", {}), dict) else {}

    metrics = build_telemetry_metrics(summary, alert_count=alert_count, high_alert_count=high_alert_count)
    text_payload = render_prometheus_text(metrics, namespace=namespace, labels=labels)

    if not enabled:
        return {
            "enabled": False,
            "mode": mode,
            "status": "disabled",
            "exported": False,
            "metrics_count": len(metrics),
            "payload_preview": text_payload,
        }
    if mode == "file":
        output_path = str(cfg.get("output_path", endpoint_url)).strip()
        if not output_path:
            return {
                "enabled": True,
                "mode": mode,
                "status": "missing_output_path",
                "exported": False,
                "metrics_count": len(metrics),
                "payload_preview": text_payload,
            }

        file_format = str(cfg.get("file_format", "prometheus")).strip().lower()
        if file_format == "otlp":
            payload = json.dumps(
                _render_otlp_like_json(
                    metrics,
                    service_name=service_name,
                    namespace=namespace,
                    labels=labels,
                ),
                ensure_ascii=False,
            )
        else:
            payload = text_payload
        ok, status = _write_payload(output_path, payload)
        return {
            "enabled": True,
            "mode": mode,
            "status": status,
            "exported": bool(ok),
            "metrics_count": len(metrics),
            "payload_preview": payload,
        }
    if not endpoint_url:
        return {
            "enabled": True,
            "mode": mode,
            "status": "missing_endpoint_url",
            "exported": False,
            "metrics_count": len(metrics),
            "payload_preview": text_payload,
        }

    if mode == "otlp":
        ok, status, payload = export_otlp_http_json(
            metrics,
            endpoint_url=endpoint_url,
            service_name=service_name,
            namespace=namespace,
            labels=labels,
            timeout_seconds=timeout_seconds,
        )
    else:
        ok, status, payload = export_prometheus_text(
            metrics,
            endpoint_url=endpoint_url,
            namespace=namespace,
            labels=labels,
            timeout_seconds=timeout_seconds,
        )

    return {
        "enabled": True,
        "mode": mode,
        "status": status,
        "exported": bool(ok),
        "metrics_count": len(metrics),
        "payload_preview": payload,
    }
