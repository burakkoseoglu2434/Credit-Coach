from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from credit_coach.pilot.contracts import (
    DecisionExplanationDriver,
    DecisionExplanationPack,
    DecisionExplanationReason,
)
from credit_coach.utils.time import utc_now


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _summary(roadmap: Mapping[str, Any]) -> dict[str, Any]:
    payload = roadmap.get("summary", {})
    return dict(payload) if isinstance(payload, Mapping) else {}


def _as_packet(packet: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(packet, "model_dump"):
        payload = packet.model_dump(mode="json")
        return dict(payload) if isinstance(payload, dict) else {}
    if isinstance(packet, Mapping):
        return dict(packet)
    return {}


def _require_external_decision(decision_status: Any) -> str:
    status = _safe_text(decision_status, "CONDITIONAL")
    if status == "NEEDS_REVIEW":
        raise ValueError("Explanation pack cannot expose NEEDS_REVIEW")
    if status not in {"APPROVED", "CONDITIONAL", "REJECTED"}:
        return "CONDITIONAL"
    return status


def _build_driver_rows(summary: Mapping[str, Any]) -> list[DecisionExplanationDriver]:
    out: list[DecisionExplanationDriver] = []
    for raw_driver in summary.get("decision_reason_drivers", []):
        if not isinstance(raw_driver, Mapping):
            continue
        current_value = raw_driver.get("current_value")
        target_value = raw_driver.get("target_value")
        if current_value is None or target_value is None:
            continue
        out.append(
            DecisionExplanationDriver(
                driver_key=_safe_text(raw_driver.get("driver_key"), "driver"),
                current_value=_safe_float(current_value, 0.0),
                target_value=_safe_float(target_value, 0.0),
                unit=_safe_text(raw_driver.get("unit")),
                source_field=_safe_text(raw_driver.get("source_field")) or None,
                comparison=_safe_text(raw_driver.get("comparison")) or None,
            )
        )
        if len(out) >= 3:
            break
    return out


def _reason_title(code: str) -> str:
    return code.replace("_", " ").strip().title() or "Risk factor"


def _build_reason_rows(codes: Sequence[Any]) -> list[DecisionExplanationReason]:
    out: list[DecisionExplanationReason] = []
    seen: set[str] = set()
    for raw_code in codes:
        code = _safe_text(raw_code).lower()
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(
            DecisionExplanationReason(
                reason_code=code,
                title=_reason_title(code),
                description=f"{_reason_title(code)} remains above the current institution-safe threshold.",
                remediation_hint="Follow the recommended improvement path and re-evaluate the file.",
            )
        )
        if len(out) >= 4:
            break
    return out


def _extract_reason_codes(summary: Mapping[str, Any], metrics_summary: Mapping[str, Any] | None) -> list[Any]:
    if metrics_summary is not None and isinstance(metrics_summary.get("adverse_action_reasons"), list):
        return list(metrics_summary.get("adverse_action_reasons", []))
    if isinstance(summary.get("adverse_action_reasons"), list):
        return list(summary.get("adverse_action_reasons", []))
    return []


def _assert_packet_drift_guard(
    *,
    pack: DecisionExplanationPack,
    operator_packet: Mapping[str, Any],
) -> None:
    packet = _as_packet(operator_packet)
    short_view = packet.get("short_view", {})
    if not isinstance(short_view, Mapping):
        short_view = {}
    packet_decision_id = _safe_text(packet.get("decision_id"))
    packet_policy_version = _safe_text(packet.get("decision_policy_version"))
    packet_status = _safe_text(short_view.get("decision_status"))
    packet_summary = _safe_text(short_view.get("decision_reason_summary"))
    packet_readiness = _safe_text(short_view.get("expected_readiness"))
    packet_upgrade = _safe_text(short_view.get("upgrade_condition"))

    if packet_decision_id and packet_decision_id != pack.decision_id:
        raise ValueError("Explanation pack drift: decision_id mismatch")
    if packet_policy_version and packet_policy_version != pack.policy_version:
        raise ValueError("Explanation pack drift: decision_policy_version mismatch")
    if packet_status and packet_status != pack.decision_outcome:
        raise ValueError("Explanation pack drift: decision outcome mismatch")
    if packet_summary and packet_summary != pack.one_line_decision_reason:
        raise ValueError("Explanation pack drift: decision summary mismatch")
    if packet_readiness and packet_readiness != pack.expected_readiness:
        raise ValueError("Explanation pack drift: expected readiness mismatch")
    if packet_upgrade and packet_upgrade != _safe_text(pack.upgrade_condition):
        raise ValueError("Explanation pack drift: upgrade condition mismatch")


def build_decision_explanation_pack(
    roadmap: Mapping[str, Any],
    *,
    metrics_summary: Mapping[str, Any] | None = None,
    operator_packet: Mapping[str, Any] | Any | None = None,
    qa_status: str = "PASS",
    qa_stamp: str = "",
    policy_effective_at: datetime | None = None,
    artifact_generated_at: datetime | None = None,
    human_review_required: bool = False,
) -> DecisionExplanationPack:
    summary = _summary(roadmap)
    customer_id = _safe_text(roadmap.get("customer_id"), _safe_text(summary.get("customer_id"), "customer"))
    decision_id = _safe_text(summary.get("decision_id"), f"{customer_id}_decision")
    policy_version = _safe_text(summary.get("decision_policy_version"), "")
    pack = DecisionExplanationPack(
        decision_id=decision_id,
        customer_id=customer_id,
        decision_outcome=_require_external_decision(summary.get("decision_status")),
        one_line_decision_reason=_safe_text(summary.get("decision_reason_summary"), "Decision explanation unavailable."),
        structured_numeric_drivers=_build_driver_rows(summary),
        upgrade_condition=_safe_text(summary.get("upgrade_condition")) or None,
        expected_readiness=_safe_text(summary.get("expected_readiness"), "unknown_review"),
        adverse_action_friendly_reasons=_build_reason_rows(_extract_reason_codes(summary, metrics_summary)),
        policy_version=policy_version,
        policy_effective_at=policy_effective_at,
        artifact_generated_at=artifact_generated_at or utc_now(),
        qa_status=_safe_text(qa_status, "PASS"),
        qa_stamp=_safe_text(qa_stamp),
        human_review_required=bool(human_review_required),
    )
    if operator_packet is not None:
        _assert_packet_drift_guard(pack=pack, operator_packet=operator_packet)
    return pack


def render_decision_explanation_pack_markdown(pack: DecisionExplanationPack) -> str:
    lines = [
        f"# Decision Explanation Pack — {pack.customer_id}",
        "",
        "## Decision Summary",
        f"- Decision ID: {pack.decision_id}",
        f"- Decision: {pack.decision_outcome}",
        f"- Policy version: {pack.policy_version or 'n/a'}",
        f"- Reason: {pack.one_line_decision_reason}",
        "",
        "## Improvement Path",
        f"- Upgrade condition: {pack.upgrade_condition or 'n/a'}",
        f"- Expected readiness: {pack.expected_readiness}",
        "",
        "## Numeric Drivers",
    ]
    if pack.structured_numeric_drivers:
        for driver in pack.structured_numeric_drivers:
            unit = f" {driver.unit}" if driver.unit else ""
            lines.append(
                f"- {driver.driver_key}: {driver.current_value:g}{unit} -> {driver.target_value:g}{unit}"
            )
    else:
        lines.append("- n/a")
    lines.extend(["", "## Adverse-Action-Compatible Reasons"])
    if pack.adverse_action_friendly_reasons:
        for reason in pack.adverse_action_friendly_reasons:
            lines.append(f"- {reason.title}: {reason.description}")
    else:
        lines.append("- n/a")
    lines.extend(["", "## Governance"])
    lines.append(f"- QA status: {pack.qa_status}")
    lines.append(f"- QA stamp: {pack.qa_stamp or 'n/a'}")
    lines.append(f"- Human review required: {'yes' if pack.human_review_required else 'no'}")
    lines.extend(["", "## Boundaries"])
    for item in pack.disclaimer:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_decision_explanation_pack(
    pack: DecisionExplanationPack,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "decision_explanation_pack.json"
    md_path = output_dir / "decision_explanation_pack.md"
    json_path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_decision_explanation_pack_markdown(pack), encoding="utf-8")
    return {
        "decision_explanation_pack_json": json_path,
        "decision_explanation_pack_md": md_path,
    }
