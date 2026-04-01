from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from credit_coach.coaching.messaging import (
    build_operator_downside_risk,
    build_operator_driver_line,
    build_operator_offer_state,
    build_operator_readiness_note,
    build_operator_summary_line,
)
from credit_coach.data.schema import (
    LocalizedText,
    OperatorPacketAction,
    OperatorPacketBlocker,
    OperatorPacketShortView,
    OperatorPacketTechnicalAppendix,
    OperatorReviewPacket,
)


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return bool(default)
    try:
        return bool(int(value))
    except Exception:
        text = str(value).strip().lower()
        if text in {"true", "yes", "y"}:
            return True
        if text in {"false", "no", "n", ""}:
            return False
    return bool(default)


def _lt(tr: str, en: str) -> LocalizedText:
    return LocalizedText(tr=str(tr), en=str(en))


_BLOCKER_TITLE_MAP: dict[str, tuple[str, str]] = {
    "best_action_count": ("Uygulanabilir adim yok", "No actionable step is available"),
    "expected_pd_improvement": ("Beklenen etki yetersiz", "Expected impact is still too small"),
    "realization_anchor": ("Uygulama gucu zayif", "Execution strength is still weak"),
    "decision_confidence": ("Karar guveni dusuk", "Decision confidence is not strong enough yet"),
    "expected_readiness_week": ("Hazirlik zamani daha ileri", "Readiness timing is still too far out"),
    "critical_field_null_count": ("Karar verisi eksik", "Decision data is incomplete"),
    "parity_pass": ("Artifact tutarliligi sorunlu", "Artifact consistency needs repair"),
    "rankable_offer_count": ("Kurum destegi aktif degil", "Institution support is not active yet"),
}


_PRIMARY_REASON_TITLE_MAP: dict[str, tuple[str, str]] = {
    "NO_PATH": ("Su an icin yol yok", "No viable path right now"),
    "LOW_IMPACT": ("Etki seviyesi dusuk", "Impact is too limited"),
    "LOW_EXECUTION": ("Gerceklesme gucu zayif", "Execution strength is too weak"),
    "OFFER_BLOCK": ("Kurum destegi gerekiyor", "Institution support is still needed"),
    "TIME_BLOCK": ("Biraz daha zaman gerekiyor", "More time is still required"),
    "DATA_ISSUE": ("Karar verisi tamam degil", "Decision data is not complete yet"),
}


def _localized_text_from_payload(payload: Any, *, fallback_en: str = "", fallback_tr: str = "") -> LocalizedText | None:
    if isinstance(payload, Mapping):
        tr = _safe_text(payload.get("tr"), fallback_tr)
        en = _safe_text(payload.get("en"), fallback_en)
        if tr or en:
            return _lt(tr or fallback_tr or en, en or fallback_en or tr)
        return None
    text = _safe_text(payload)
    if not text and not fallback_en and not fallback_tr:
        return None
    return _lt(fallback_tr or text, fallback_en or text)


def _selected_surface_empty_state() -> LocalizedText:
    return _lt(
        "Su an icin gecerli bir oneri yolu yok.",
        "No valid recommendation path is currently available.",
    )


def _narrative_steps(roadmap: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    narrative = roadmap.get("narrative", {})
    if isinstance(narrative, Mapping):
        steps = narrative.get("steps", [])
        if isinstance(steps, Sequence):
            return [step for step in steps if isinstance(step, Mapping)]
    return []


def _roadmap_summary(roadmap: Mapping[str, Any]) -> dict[str, Any]:
    summary = roadmap.get("summary", {})
    return dict(summary) if isinstance(summary, Mapping) else {}


def _driver_blocker(driver: Mapping[str, Any], *, fallback_primary: str | None = None) -> OperatorPacketBlocker:
    driver_key = _safe_text(driver.get("driver_key"))
    title_tr, title_en = _BLOCKER_TITLE_MAP.get(
        driver_key,
        _PRIMARY_REASON_TITLE_MAP.get(_safe_text(fallback_primary).upper(), ("Blokaj devam ediyor", "The blocker remains active")),
    )
    blocker_code = f"driver:{driver_key}" if driver_key else f"reason:{_safe_text(fallback_primary).upper() or 'UNKNOWN'}"
    return OperatorPacketBlocker(
        blocker_code=blocker_code,
        blocker_title=_lt(title_tr, title_en),
        blocker_detail=build_operator_driver_line(driver) if driver_key else _lt(title_tr, title_en),
        driver_key=driver_key or None,
    )


def _fallback_blocker(summary: Mapping[str, Any]) -> OperatorPacketBlocker:
    primary = _safe_text(summary.get("decision_reason_primary"), "LOW_EXECUTION").upper()
    title_tr, title_en = _PRIMARY_REASON_TITLE_MAP.get(primary, ("Blokaj devam ediyor", "The blocker remains active"))
    detail = build_operator_summary_line(summary.get("decision_reason_summary")) or title_en
    return OperatorPacketBlocker(
        blocker_code=f"reason:{primary}",
        blocker_title=_lt(title_tr, title_en),
        blocker_detail=_lt(detail, detail),
        driver_key=None,
    )


def _blockers_from_summary(summary: Mapping[str, Any]) -> list[OperatorPacketBlocker]:
    raw_drivers = summary.get("decision_reason_drivers", [])
    drivers = [driver for driver in raw_drivers if isinstance(driver, Mapping)]
    if not drivers:
        return [_fallback_blocker(summary)]
    blockers = [_driver_blocker(driver, fallback_primary=_safe_text(summary.get("decision_reason_primary"))) for driver in drivers[:3]]
    if not blockers:
        return [_fallback_blocker(summary)]
    return blockers


def _step_related_to_blocker(step: Mapping[str, Any], blocker: OperatorPacketBlocker) -> bool:
    blocker_key = _safe_text(blocker.driver_key).lower()
    if not blocker_key:
        return True
    action_key = _safe_text(step.get("action_key")).lower()
    action_summary = _safe_text((step.get("action_summary", {}) or {}).get("en")).lower() if isinstance(step.get("action_summary"), Mapping) else ""
    primary_recommendation = (
        _safe_text((step.get("primary_recommendation", {}) or {}).get("en")).lower()
        if isinstance(step.get("primary_recommendation"), Mapping)
        else ""
    )
    expected_outcome = _safe_text((step.get("expected_outcome", {}) or {}).get("en")).lower() if isinstance(step.get("expected_outcome"), Mapping) else ""
    if blocker_key in {"rankable_offer_count"}:
        return bool(step.get("offer_narrative")) or action_key in {"installment_plan", "credit_limit_adjustment", "settlement_discount"}
    if blocker_key in {"expected_readiness_week", "decision_confidence", "realization_anchor", "expected_pd_improvement"}:
        return True
    if blocker_key in {"critical_field_null_count", "parity_pass"}:
        return True
    joined = " ".join([action_key, action_summary, primary_recommendation, expected_outcome])
    heuristic_terms = {
        "best_action_count": "",
        "realization_anchor": "execution",
        "expected_pd_improvement": "target",
        "decision_confidence": "confidence",
        "expected_readiness_week": "readiness",
    }
    term = heuristic_terms.get(blocker_key, blocker_key.replace("_", " "))
    return term in joined if term else True


def _actions_from_narrative(
    summary: Mapping[str, Any],
    steps: Sequence[Mapping[str, Any]],
    blockers: Sequence[OperatorPacketBlocker],
) -> list[OperatorPacketAction]:
    selected: list[OperatorPacketAction] = []
    selected_projection_source = _safe_text(summary.get("selected_recommendation_source"))
    if selected_projection_source == "empty_state":
        return []
    selected_projection_text = _localized_text_from_payload(
        summary.get("selected_recommendation_text_localized"),
        fallback_en=_safe_text(summary.get("selected_recommendation_text")),
        fallback_tr=_safe_text(summary.get("selected_recommendation_text")),
    )
    selected_institution_condition = _localized_text_from_payload(
        summary.get("selected_institution_condition_localized"),
        fallback_en=_safe_text(summary.get("selected_institution_condition")),
        fallback_tr=_safe_text(summary.get("selected_institution_condition")),
    )
    if selected_projection_source == "selected_plan" and selected_projection_text is not None:
        first_step = steps[0] if steps else {}
        timing_hint = _localized_text_from_payload(first_step.get("action_timing_hint")) if isinstance(first_step, Mapping) else None
        blocker_codes = [blocker.blocker_code for blocker in blockers[:3]]
        selected.append(
            OperatorPacketAction(
                step_id=_safe_text((first_step or {}).get("step_id"), "selected_projection"),
                action_key=_safe_text((first_step or {}).get("action_key")) or None,
                action_summary=selected_projection_text,
                institution_condition=selected_institution_condition,
                timing_hint=timing_hint,
                blocker_codes=blocker_codes,
            )
        )
    for raw_step in steps:
        blocker_codes = [
            blocker.blocker_code
            for blocker in blockers
            if _step_related_to_blocker(raw_step, blocker)
        ]
        if not blocker_codes and blockers:
            blocker_codes = [blockers[0].blocker_code]
        action_summary = _localized_text_from_payload(raw_step.get("primary_recommendation"))
        if action_summary is None:
            action_summary = _localized_text_from_payload(raw_step.get("action_summary"))
        if action_summary is None:
            continue
        if (
            selected
            and selected[0].action_summary.en == action_summary.en
            and (selected[0].action_key or "") == (_safe_text(raw_step.get("action_key")) or "")
        ):
            continue
        institution_condition = _localized_text_from_payload(raw_step.get("institution_condition"))
        timing_hint = _localized_text_from_payload(raw_step.get("action_timing_hint"))
        selected.append(
            OperatorPacketAction(
                step_id=_safe_text(raw_step.get("step_id"), "step"),
                action_key=_safe_text(raw_step.get("action_key")) or None,
                action_summary=action_summary,
                institution_condition=institution_condition,
                timing_hint=timing_hint,
                blocker_codes=blocker_codes[:3],
            )
        )
        if len(selected) >= 3:
            break
    return selected


def build_operator_review_packet(roadmap: Mapping[str, Any]) -> OperatorReviewPacket:
    summary = _roadmap_summary(roadmap)
    steps = _narrative_steps(roadmap)
    blockers = _blockers_from_summary(summary)
    actions = _actions_from_narrative(summary, steps, blockers)
    narrative = roadmap.get("narrative", {}) if isinstance(roadmap.get("narrative", {}), Mapping) else {}
    executive_summary = narrative.get("executive_summary", {}) if isinstance(narrative, Mapping) else {}
    offer_state = None
    if isinstance(executive_summary, Mapping):
        offer_card = executive_summary.get("offer_status", {})
        if isinstance(offer_card, Mapping):
            offer_state = _localized_text_from_payload(offer_card.get("label"))
    if offer_state is None:
        offer_state = build_operator_offer_state(
            offer_maturity=summary.get("offer_maturity"),
            offer_plan=summary.get("offer_plan"),
            offer_acceptance_probability=summary.get("offer_acceptance_probability"),
        )

    downside = None
    if steps and _safe_text(summary.get("decision_status")) != "APPROVED":
        downside = _localized_text_from_payload((steps[0].get("what_happens_if_not_done", {}) if isinstance(steps[0], Mapping) else {}))
    if downside is None:
        downside = build_operator_downside_risk(
            decision_status=summary.get("decision_status"),
            conditional_type=summary.get("conditional_type"),
            rejection_type=summary.get("rejection_type"),
        )

    short_view = OperatorPacketShortView(
        decision_status=_safe_text(summary.get("selected_decision_status"), _safe_text(summary.get("decision_status"), "CONDITIONAL")),
        decision_reason_summary=build_operator_summary_line(summary.get("decision_reason_summary")),
        decision_confidence=_safe_float(summary.get("decision_confidence"), 0.0),
        top_blockers=blockers[:3],
        next_best_actions=actions[:3],
        expected_readiness=_safe_text(summary.get("expected_readiness"), "unknown_review"),
        expected_readiness_note=build_operator_readiness_note(summary.get("expected_readiness")),
        recommendation_sanity_flag=bool(_safe_int(summary.get("recommendation_sanity_flag", 0), 0)),
        recommendation_sanity_note=(
            _lt(
                "Numeric oneride manuel kontrol notu var",
                "Numeric recommendation has a manual-review note",
            )
            if bool(_safe_int(summary.get("recommendation_sanity_flag", 0), 0))
            else None
        ),
        upgrade_condition=_safe_text(summary.get("upgrade_condition")) or None,
        offer_state=offer_state,
        downside_risk=downside,
        technical_detail_available=True,
    )
    appendix = OperatorPacketTechnicalAppendix(
        decision_status_internal=_safe_text(summary.get("decision_status_internal"), "NEEDS_REVIEW"),
        decision_reason_primary=_safe_text(summary.get("decision_reason_primary")) or None,
        rejection_type=_safe_text(summary.get("rejection_type")) or None,
        conditional_type=_safe_text(summary.get("conditional_type")) or None,
        decision_reason_drivers=[dict(driver) for driver in summary.get("decision_reason_drivers", []) if isinstance(driver, Mapping)],
        recommendation_validity_codes=[str(code) for code in list(summary.get("recommendation_validity_codes", [])) if str(code)],
        recommendation_warning_action_count=_safe_int(summary.get("recommendation_warning_action_count", 0), 0),
        contract_health=dict(roadmap.get("contract_health", {}) or {}),
        decision_gate_trace=dict(summary.get("decision_gate_trace", {}) or {}),
        selection_outcome=_safe_text(summary.get("selection_outcome")) or None,
        selection_stage=_safe_text(summary.get("selection_stage")) or None,
        selected_plan_status_internal=_safe_text(summary.get("selected_plan_status_internal")) or None,
        selected_recommendation_source=_safe_text(summary.get("selected_recommendation_source")) or None,
        selected_recommendation_projection_version=(
            _safe_text(summary.get("selected_recommendation_projection_version")) or None
        ),
        selected_action_count=_safe_int(summary.get("selected_action_count", 0), 0),
    )
    return OperatorReviewPacket(
        decision_id=_safe_text(summary.get("decision_id"), f"{_safe_text(roadmap.get('customer_id'), _safe_text(summary.get('customer_id'), 'customer'))}_decision"),
        decision_policy_version=_safe_text(summary.get("decision_policy_version"), ""),
        customer_id=_safe_text(roadmap.get("customer_id"), _safe_text(summary.get("customer_id"), "customer")),
        best_plan_id=_safe_text(roadmap.get("best_plan_id"), _safe_text(summary.get("best_plan_id"))) or None,
        short_view=short_view,
        technical_appendix=appendix,
    )


def render_operator_review_packet_markdown(packet: OperatorReviewPacket) -> str:
    short = packet.short_view
    appendix = packet.technical_appendix
    lines = [
        f"# Operator Packet — {packet.customer_id}",
        "",
        "## Decision Header",
        f"- Decision ID: {packet.decision_id}",
        f"- Decision policy version: {packet.decision_policy_version or 'n/a'}",
        f"- Decision: {short.decision_status}",
        f"- Decision confidence: {short.decision_confidence:.2f}" if short.decision_confidence is not None else "- Decision confidence: n/a",
        f"- Recommendation note: {short.recommendation_sanity_note.en}" if short.recommendation_sanity_note is not None else "- Recommendation note: n/a",
        "",
        "## 1-line Summary",
        f"- {short.decision_reason_summary or 'n/a'}",
        "",
        "## Blockers",
    ]
    if short.top_blockers:
        for blocker in short.top_blockers:
            lines.append(f"- {blocker.blocker_title.en}: {blocker.blocker_detail.en}")
    else:
        lines.append("- n/a")
    lines.extend(["", "## Next Best Actions"])
    if short.next_best_actions:
        for action in short.next_best_actions:
            timing = f" ({action.timing_hint.en})" if action.timing_hint is not None else ""
            lines.append(f"- {action.action_summary.en}{timing}")
            if action.institution_condition is not None:
                lines.append(f"- Institution condition: {action.institution_condition.en}")
    elif appendix.selected_recommendation_source == "empty_state":
        lines.append(f"- {_selected_surface_empty_state().en}")
    else:
        lines.append("- n/a")
    lines.extend(
        [
            "",
            "## Upgrade Path",
            f"- {short.upgrade_condition or 'n/a'}",
            "",
            "## Readiness",
            f"- {short.expected_readiness}",
            f"- {short.expected_readiness_note.en if short.expected_readiness_note is not None else 'n/a'}",
            "",
            "## Offer State",
            f"- {short.offer_state.en if short.offer_state is not None else 'n/a'}",
            "",
            "## Downside Risk",
            f"- {short.downside_risk.en if short.downside_risk is not None else 'n/a'}",
            "",
            "## Technical Appendix",
            f"- Internal decision: {appendix.decision_status_internal}",
        ]
    )
    if appendix.conditional_type:
        lines.append(f"- Conditional type: {appendix.conditional_type}")
    if appendix.rejection_type:
        lines.append(f"- Rejection type: {appendix.rejection_type}")
    if appendix.decision_reason_primary:
        lines.append(f"- Primary reason: {appendix.decision_reason_primary}")
    lines.append(f"- Driver count: {len(appendix.decision_reason_drivers)}")
    lines.append(f"- Recommendation warning action count: {appendix.recommendation_warning_action_count}")
    lines.append(
        f"- Recommendation validity codes: {json.dumps(appendix.recommendation_validity_codes, ensure_ascii=False)}"
    )
    lines.append(f"- Selection outcome: {appendix.selection_outcome or 'n/a'}")
    lines.append(f"- Selection stage: {appendix.selection_stage or 'n/a'}")
    lines.append(f"- Selected plan status (technical): {appendix.selected_plan_status_internal or 'n/a'}")
    lines.append(f"- Selected recommendation source: {appendix.selected_recommendation_source or 'n/a'}")
    lines.append(f"- Selected recommendation projection version: {appendix.selected_recommendation_projection_version or 'n/a'}")
    lines.append(f"- Selected action count: {appendix.selected_action_count}")
    lines.append(f"- Contract health: {json.dumps(appendix.contract_health, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def operator_packet_metrics_fields(
    packet: OperatorReviewPacket,
    *,
    packet_relpath: str,
) -> dict[str, Any]:
    return {
        "operator_packet_relpath": str(packet_relpath),
        "operator_decision_id": str(packet.decision_id),
        "operator_decision_policy_version": str(packet.decision_policy_version),
        "operator_decision_summary": str(packet.short_view.decision_reason_summary),
        "operator_top_blocker_codes_json": json.dumps(
            [blocker.blocker_code for blocker in packet.short_view.top_blockers],
            ensure_ascii=False,
        ),
        "operator_next_best_action_keys_json": json.dumps(
            [action.action_key or "" for action in packet.short_view.next_best_actions],
            ensure_ascii=False,
        ),
        "operator_expected_readiness_note_en": (
            packet.short_view.expected_readiness_note.en
            if packet.short_view.expected_readiness_note is not None
            else ""
        ),
        "operator_recommendation_sanity_flag": int(bool(packet.short_view.recommendation_sanity_flag)),
        "operator_recommendation_sanity_note_en": (
            packet.short_view.recommendation_sanity_note.en
            if packet.short_view.recommendation_sanity_note is not None
            else ""
        ),
        "operator_selected_decision_status": str(packet.short_view.decision_status),
        "operator_selected_recommendation_text": (
            packet.short_view.next_best_actions[0].action_summary.en
            if packet.short_view.next_best_actions
            else ""
        ),
        "operator_selected_action_count": int(packet.technical_appendix.selected_action_count),
        "operator_offer_state_en": packet.short_view.offer_state.en if packet.short_view.offer_state is not None else "",
        "operator_downside_risk_en": packet.short_view.downside_risk.en if packet.short_view.downside_risk is not None else "",
        "operator_technical_detail_available": int(bool(packet.short_view.technical_detail_available)),
    }


def write_operator_review_packet(
    packet: OperatorReviewPacket,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "operator_packet.json"
    md_path = output_dir / "operator_packet.md"
    json_path.write_text(json.dumps(packet.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_operator_review_packet_markdown(packet), encoding="utf-8")
    return {
        "operator_packet_json": json_path,
        "operator_packet_md": md_path,
    }


def build_collection_operator_briefing(
    *,
    metrics_df: pd.DataFrame,
    operator_packets: Sequence[Mapping[str, Any]],
    funnel_summary: Mapping[str, Any],
    readiness_summary: Mapping[str, Any],
    segment_breakdown_df: pd.DataFrame,
) -> dict[str, Any]:
    work = metrics_df.copy()
    if work.empty:
        return {
            "decision_funnel": {},
            "priority_queues": [],
            "dominant_blockers": [],
            "conditional_hotspots": [],
            "offer_hotspots": [],
            "review_guidance": [],
            "health_note": "",
            "technical_appendix_refs": [],
        }
    work["decision_status"] = work.get("decision_status", pd.Series(dtype=object)).fillna("").astype(str)
    work["conditional_type"] = work.get("conditional_type", pd.Series(dtype=object)).fillna("").astype(str)
    work["expected_readiness"] = work.get("expected_readiness", pd.Series(dtype=object)).fillna("").astype(str)
    work["decision_confidence"] = pd.to_numeric(work.get("decision_confidence", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    work["offer_needed_flag"] = work.get("offer_needed_flag", pd.Series(dtype=object)).fillna("no_offer_needed").astype(str)

    approved_count = int((work["decision_status"] == "APPROVED").sum())
    conditional_count = int((work["decision_status"] == "CONDITIONAL").sum())
    rejected_count = int((work["decision_status"] == "REJECTED").sum())

    likely_queue = (
        work.loc[
            (work["decision_status"] == "CONDITIONAL")
            & (work["expected_readiness"].isin(["week_4", "week_12"]))
        ]
        .sort_values(["expected_readiness", "decision_confidence", "customer_id"], ascending=[True, False, True])
        .head(10)
    )
    priority_queues = [
        {
            "queue_key": "likely_to_upgrade_soon",
            "label": "Likely to upgrade soon",
            "count": int(len(likely_queue)),
            "customers": likely_queue.get("customer_id", pd.Series(dtype=object)).astype(str).tolist(),
        },
        {
            "queue_key": "week_4_conditionals",
            "label": "Week-4 conditionals",
            "count": int(
                (
                    (work["decision_status"] == "CONDITIONAL")
                    & (work["expected_readiness"] == "week_4")
                ).sum()
            ),
            "customers": work.loc[
                (work["decision_status"] == "CONDITIONAL") & (work["expected_readiness"] == "week_4"),
                "customer_id",
            ].astype(str).tolist()[:10],
        },
    ]

    blocker_counts: dict[str, dict[str, Any]] = {}
    for packet in operator_packets:
        short_view = packet.get("short_view", {})
        blockers = short_view.get("top_blockers", []) if isinstance(short_view, Mapping) else []
        if not isinstance(blockers, Sequence):
            continue
        for blocker in blockers:
            if not isinstance(blocker, Mapping):
                continue
            code = _safe_text(blocker.get("blocker_code"))
            title = blocker.get("blocker_title", {})
            title_en = _safe_text(title.get("en") if isinstance(title, Mapping) else title, code)
            if not code:
                continue
            blocker_counts.setdefault(code, {"blocker_code": code, "title": title_en, "count": 0})
            blocker_counts[code]["count"] += 1
    dominant_blockers = sorted(blocker_counts.values(), key=lambda item: (-int(item["count"]), str(item["title"])))[:5]

    conditional_hotspots = []
    conditional_counts = (
        work.loc[work["decision_status"] == "CONDITIONAL", "conditional_type"]
        .value_counts()
        .sort_values(ascending=False)
    )
    for conditional_type, count in conditional_counts.head(5).items():
        conditional_hotspots.append(
            {
                "conditional_type": str(conditional_type),
                "count": int(count),
            }
        )

    offer_hotspots = []
    offer_counts = (
        work.groupby(["offer_needed_flag", "decision_status"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "offer_needed_flag"], ascending=[False, True])
    )
    for row in offer_counts.head(5).to_dict(orient="records"):
        offer_hotspots.append(
            {
                "offer_needed_flag": _safe_text(row.get("offer_needed_flag")),
                "decision_status": _safe_text(row.get("decision_status")),
                "count": int(row.get("count", 0)),
            }
        )

    health_note = ""
    internal_share = _safe_float(funnel_summary.get("internal_needs_review_share"), 0.0)
    if internal_share > 0.0:
        health_note = f"Internal needs-review share is {internal_share:.4f}; treat it as a system-health note, not a customer-facing decision."

    dominant_segments = []
    if not segment_breakdown_df.empty:
        spotlight = segment_breakdown_df.sort_values(
            ["approve_plus_conditional_share", "count"],
            ascending=[False, False],
        ).head(5)
        for row in spotlight.to_dict(orient="records"):
            dominant_segments.append(
                {
                    "segment_axis": _safe_text(row.get("segment_axis")),
                    "segment_value": _safe_text(row.get("segment_value")),
                    "count": int(row.get("count", 0)),
                }
            )

    review_guidance: list[str] = []
    if priority_queues and int(priority_queues[0]["count"]) > 0:
        review_guidance.append("Review likely-to-upgrade-soon customers first.")
    if any(item.get("conditional_type") == "OFFER_GATED" for item in conditional_hotspots):
        review_guidance.append("Offer-gated cases may require institution-side follow-up.")
    if int((work["decision_status"] == "REJECTED").sum()) > 0:
        review_guidance.append("Low-impact rejected cases are usually lower priority for manual review than near-term conditionals.")

    readiness_distribution = dict(readiness_summary.get("distribution", {}))
    decision_funnel = {
        "approved_count": approved_count,
        "conditional_count": conditional_count,
        "rejected_count": rejected_count,
        "approved_share": _safe_float(funnel_summary.get("approved_share"), 0.0),
        "conditional_share": _safe_float(funnel_summary.get("conditional_share"), 0.0),
        "rejected_share": _safe_float(funnel_summary.get("rejected_share"), 0.0),
        "approve_plus_conditional_share": _safe_float(funnel_summary.get("approve_plus_conditional_share"), 0.0),
        "readiness_distribution": readiness_distribution,
        "dominant_segment_hotspots": dominant_segments,
    }

    return {
        "decision_funnel": decision_funnel,
        "priority_queues": priority_queues,
        "dominant_blockers": dominant_blockers,
        "conditional_hotspots": conditional_hotspots,
        "offer_hotspots": offer_hotspots,
        "review_guidance": review_guidance,
        "health_note": health_note,
        "technical_appendix_refs": [
            "calibration/decision_shift_matrix.csv",
            "calibration/segment_breakdown.csv",
            "calibration/policy_comparison.csv",
        ],
    }


def render_collection_operator_briefing_markdown(briefing: Mapping[str, Any]) -> str:
    funnel = dict(briefing.get("decision_funnel", {}) or {})
    lines = [
        "# Operator Review Briefing",
        "",
        "## Decision Funnel",
        f"- Approved: {int(funnel.get('approved_count', 0))}",
        f"- Conditional: {int(funnel.get('conditional_count', 0))}",
        f"- Rejected: {int(funnel.get('rejected_count', 0))}",
        f"- Approve + conditional share: {_safe_float(funnel.get('approve_plus_conditional_share'), 0.0):.4f}",
        "",
        "## Priority Queues",
    ]
    queues = briefing.get("priority_queues", [])
    if isinstance(queues, Sequence) and queues:
        for queue in queues:
            if not isinstance(queue, Mapping):
                continue
            lines.append(f"- {_safe_text(queue.get('label'))}: {int(queue.get('count', 0))}")
    else:
        lines.append("- n/a")
    lines.extend(["", "## Dominant Blockers"])
    blockers = briefing.get("dominant_blockers", [])
    if isinstance(blockers, Sequence) and blockers:
        for blocker in blockers:
            if not isinstance(blocker, Mapping):
                continue
            lines.append(f"- {_safe_text(blocker.get('title'))}: {int(blocker.get('count', 0))}")
    else:
        lines.append("- n/a")
    lines.extend(["", "## Conditional Hotspots"])
    hotspots = briefing.get("conditional_hotspots", [])
    if isinstance(hotspots, Sequence) and hotspots:
        for hotspot in hotspots:
            if not isinstance(hotspot, Mapping):
                continue
            lines.append(f"- {_safe_text(hotspot.get('conditional_type'))}: {int(hotspot.get('count', 0))}")
    else:
        lines.append("- n/a")
    lines.extend(["", "## Offer Hotspots"])
    offers = briefing.get("offer_hotspots", [])
    if isinstance(offers, Sequence) and offers:
        for item in offers:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"- {_safe_text(item.get('offer_needed_flag'))} / {_safe_text(item.get('decision_status'))}: {int(item.get('count', 0))}"
            )
    else:
        lines.append("- n/a")
    lines.extend(["", "## Review Guidance"])
    guidance = briefing.get("review_guidance", [])
    if isinstance(guidance, Sequence) and guidance:
        for item in guidance:
            lines.append(f"- {_safe_text(item)}")
    else:
        lines.append("- n/a")
    health_note = _safe_text(briefing.get("health_note"))
    if health_note:
        lines.extend(["", "## Health Note", f"- {health_note}"])
    lines.extend(["", "## Technical Appendix Refs"])
    refs = briefing.get("technical_appendix_refs", [])
    if isinstance(refs, Sequence) and refs:
        for ref in refs:
            lines.append(f"- {_safe_text(ref)}")
    else:
        lines.append("- n/a")
    return "\n".join(lines) + "\n"
