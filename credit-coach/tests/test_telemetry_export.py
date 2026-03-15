from __future__ import annotations

import json

from credit_coach.ops.telemetry import (
    build_telemetry_metrics,
    export_monitoring_telemetry,
    render_prometheus_text,
)


def test_render_prometheus_text_contains_metrics():
    metrics = {
        "approval_rate": 0.8,
        "avg_risk_margin": 0.05,
        "max_psi": 0.01,
    }
    text = render_prometheus_text(metrics, namespace="credit_coach", labels={"env": "test"})
    assert "credit_coach_approval_rate" in text
    assert 'env="test"' in text
    assert "# TYPE credit_coach_max_psi gauge" in text


def test_export_monitoring_telemetry_disabled():
    summary = {
        "approval_rate": 0.9,
        "avg_risk_margin": 0.1,
        "avg_reliability": 1.0,
        "fairness_gap": 0.03,
        "high_stress_fairness_gap": 0.04,
        "max_psi": 0.01,
    }
    result = export_monitoring_telemetry(
        summary,
        alert_count=0,
        high_alert_count=0,
        exporter_cfg={"enabled": False},
    )
    assert result["enabled"] is False
    assert result["exported"] is False
    assert result["status"] == "disabled"
    assert result["telemetry_status"] == "disabled"
    assert result["telemetry_failure_reason"] == "disabled_exporter"


def test_export_monitoring_telemetry_prometheus_http(monkeypatch):
    captured: dict = {}

    class _Resp:
        status = 202

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout=3.0):  # noqa: ARG001
        captured["url"] = req.full_url
        captured["content_type"] = req.get_header("Content-type")
        captured["body"] = req.data.decode("utf-8")
        return _Resp()

    monkeypatch.setattr("credit_coach.ops.telemetry.request.urlopen", _fake_urlopen)

    result = export_monitoring_telemetry(
        {"approval_rate": 0.7, "avg_risk_margin": 0.01, "avg_reliability": 0.8, "fairness_gap": 0.1, "high_stress_fairness_gap": 0.12, "max_psi": 0.2},
        alert_count=2,
        high_alert_count=1,
        exporter_cfg={
            "enabled": True,
            "mode": "prometheus",
            "endpoint_url": "http://example.test/metrics/job/credit_coach",
            "namespace": "credit_coach",
            "labels": {"env": "test"},
        },
    )
    assert result["exported"] is True
    assert result["status"] == "http_202"
    assert captured["url"] == "http://example.test/metrics/job/credit_coach"
    assert "credit_coach_alert_count" in captured["body"]
    assert captured["content_type"].startswith("text/plain")


def test_export_monitoring_telemetry_otlp_http(monkeypatch):
    captured: dict = {}

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout=3.0):  # noqa: ARG001
        captured["url"] = req.full_url
        captured["body"] = req.data.decode("utf-8")
        captured["content_type"] = req.get_header("Content-type")
        return _Resp()

    monkeypatch.setattr("credit_coach.ops.telemetry.request.urlopen", _fake_urlopen)

    result = export_monitoring_telemetry(
        {"approval_rate": 0.7, "avg_risk_margin": 0.01, "avg_reliability": 0.8, "fairness_gap": 0.1, "high_stress_fairness_gap": 0.12, "max_psi": 0.2},
        alert_count=2,
        high_alert_count=1,
        exporter_cfg={
            "enabled": True,
            "mode": "otlp",
            "endpoint_url": "http://example.test/v1/metrics",
            "service_name": "credit-coach-test",
            "namespace": "credit_coach",
        },
    )
    assert result["exported"] is True
    assert result["status"] == "http_200"
    assert captured["url"] == "http://example.test/v1/metrics"
    assert captured["content_type"].startswith("application/json")
    payload = json.loads(captured["body"])
    assert "resourceMetrics" in payload


def test_export_monitoring_telemetry_file_prometheus(tmp_path):
    out_path = tmp_path / "telemetry" / "monitoring.prom"
    result = export_monitoring_telemetry(
        {"approval_rate": 0.7, "avg_risk_margin": 0.01, "avg_reliability": 0.8, "fairness_gap": 0.1, "high_stress_fairness_gap": 0.12, "max_psi": 0.2},
        alert_count=2,
        high_alert_count=1,
        exporter_cfg={
            "enabled": True,
            "mode": "file",
            "output_path": str(out_path),
            "namespace": "credit_coach",
        },
    )
    assert result["exported"] is True
    assert result["status"] == "success"
    assert out_path.exists()
    payload = out_path.read_text(encoding="utf-8")
    assert "credit_coach_alert_count" in payload
    assert result["telemetry_status"] == "success"
    assert result["telemetry_failure_reason"] == ""


def test_export_monitoring_telemetry_missing_endpoint_sets_export_failure():
    result = export_monitoring_telemetry(
        {"approval_rate": 0.7, "avg_risk_margin": 0.01, "avg_reliability": 0.8, "fairness_gap": 0.1, "high_stress_fairness_gap": 0.12, "max_psi": 0.2},
        alert_count=2,
        high_alert_count=1,
        exporter_cfg={
            "enabled": True,
            "mode": "prometheus",
        },
    )
    assert result["exported"] is False
    assert result["telemetry_status"] == "export_failed"
    assert result["telemetry_failure_reason"] == "export_failed"


def test_build_telemetry_metrics_alert_fields():
    m = build_telemetry_metrics(
        {"approval_rate": 1.0, "avg_risk_margin": 0.2, "avg_reliability": 1.0, "fairness_gap": 0.01, "high_stress_fairness_gap": 0.02, "max_psi": 0.01},
        alert_count=3,
        high_alert_count=2,
    )
    assert m["alert_count"] == 3.0
    assert m["high_alert_count"] == 2.0
