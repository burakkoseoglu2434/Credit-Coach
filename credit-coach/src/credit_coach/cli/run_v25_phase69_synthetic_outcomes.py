from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 69: deterministic synthetic outcome inputs (explicitly synthetic, non-causal).")
    p.add_argument(
        "--phase69_eval_dir",
        type=str,
        required=True,
        help="Phase 69 cohort evaluation directory containing customer_level_analysis.csv",
    )
    p.add_argument(
        "--synthetic_run_id",
        type=str,
        default="phase69_synthetic",
        help="Run id written into synthetic outcome rows (schema field only).",
    )
    p.add_argument(
        "--event_at",
        type=str,
        default="2026-04-11T00:00:00Z",
        help="ISO timestamp for synthetic action events.",
    )
    return p.parse_args()


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _unit_interval(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return int(digest, 16) / float(2**64)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def main() -> None:
    args = parse_args()
    eval_dir = Path(args.phase69_eval_dir).expanduser().resolve()
    customer_level_path = eval_dir / "customer_level_analysis.csv"
    if not customer_level_path.exists():
        raise FileNotFoundError(f"Missing Phase 69 customer_level_analysis.csv: {customer_level_path}")

    df = pd.read_csv(customer_level_path)
    if df.empty:
        raise ValueError("Phase 69 customer_level_analysis.csv is empty.")
    required_cols = {"source_customer_id", "recourse_mode", "recoverable_flag", "threshold_reach_probability", "selected_plan_id"}
    missing = sorted([col for col in required_cols if col not in df.columns])
    if missing:
        raise ValueError(f"Phase 69 customer_level_analysis.csv missing required columns: {missing}")

    df = df.copy()
    df["source_customer_id"] = df["source_customer_id"].map(_safe_text)
    df["recourse_mode"] = df["recourse_mode"].map(_safe_text).str.lower()
    df["recoverable_flag"] = df["recoverable_flag"].fillna(False).astype(bool)
    df["threshold_reach_probability"] = pd.to_numeric(df["threshold_reach_probability"], errors="coerce").fillna(0.0).astype(float)
    df["movement_score"] = pd.to_numeric(df.get("movement_score", pd.Series([None] * len(df))), errors="coerce")
    df["selected_path_type"] = df.get("selected_path_type", pd.Series([""] * len(df))).map(_safe_text)
    df["selected_path_movement_strength"] = df.get("selected_path_movement_strength", pd.Series([""] * len(df))).map(_safe_text)

    synthetic_reason_codes = [
        "SYNTHETIC_SIMULATION_PHASE69",
        "NON_CAUSAL_DESCRIPTIVE_ONLY",
    ]
    now_iso = datetime.now(tz=timezone.utc).isoformat()

    outcome_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        source_customer_id = _safe_text(row.get("source_customer_id"))
        if not source_customer_id:
            continue
        decision_id = f"phase69_synth::{source_customer_id}"
        customer_id = source_customer_id
        recourse_mode = _safe_text(row.get("recourse_mode")).lower()
        recoverable_flag = bool(row.get("recoverable_flag"))
        p_reach = _clamp01(_safe_float(row.get("threshold_reach_probability"), 0.0))
        selected_plan_id = _safe_text(row.get("selected_plan_id"))
        selected_path_type = _safe_text(row.get("selected_path_type"))
        selected_path_movement_strength = _safe_text(row.get("selected_path_movement_strength")) or None

        eligible_for_actions = recourse_mode == "full" and bool(selected_plan_id)
        u_exec = _unit_interval(f"{decision_id}::exec")
        u_reach = _unit_interval(f"{decision_id}::reach")

        action_completed = bool(eligible_for_actions and u_exec < p_reach)
        threshold_reached = bool(action_completed and u_reach < p_reach)

        decision_status = "CONDITIONAL" if threshold_reached else "REJECTED"

        reason_codes = list(synthetic_reason_codes)
        reason_codes.append("SYNTHETIC_EXEC_PROXY_THRESHOLD_REACH_PROB")
        reason_codes.append("SYNTHETIC_THRESHOLD_REACH_DRAW" if threshold_reached else "SYNTHETIC_NO_THRESHOLD_REACH_DRAW")

        outcome_rows.append(
            {
                "decision_id": decision_id,
                "run_id": str(args.synthetic_run_id),
                "customer_id": customer_id,
                "policy_arm": "synthetic",
                "policy_arm_profile": json.dumps({"offer_family": "synthetic", "scoring_profile": "synthetic"}, ensure_ascii=False),
                "selected_plan_id": selected_plan_id,
                "selected_plan_status": "",
                "selected_path_id": "",
                "selected_path_type": selected_path_type,
                "selected_path_movement_strength": selected_path_movement_strength or "",
                "recourse_mode": recourse_mode,
                "recoverable_flag": int(recoverable_flag),
                "movement_score": _safe_float(row.get("movement_score"), 0.0) if pd.notna(row.get("movement_score")) else "",
                "threshold_reach_probability": p_reach,
                "reason_codes": json.dumps(reason_codes, ensure_ascii=False),
                "recommended_plan_flag": int(bool(selected_plan_id)),
                "decision_status": decision_status,
                "approved": 0,
                "action_completed": int(action_completed),
                "offer_accepted": "",
                "observed_default_90d": "",
                "observed_margin_90d": "",
                "observed_payment_ratio_90d": "",
                "observed_recovery_amount_90d": "",
                "synthetic_flag": 1,
                "synthetic_generated_at_utc": now_iso,
            }
        )

        if not eligible_for_actions:
            continue

        action_keys = []
        if "action_keys_json" in df.columns:
            raw = _safe_text(row.get("action_keys_json"))
            if raw.startswith("["):
                try:
                    action_keys = [str(item).strip() for item in json.loads(raw) if str(item).strip()]
                except Exception:
                    action_keys = []
        action_key = action_keys[0] if action_keys else "synthetic_action"
        event_type = "completed" if action_completed else "attempted"
        event_rows.append(
            {
                "decision_id": decision_id,
                "customer_id": customer_id,
                "selected_plan_id": selected_plan_id,
                "selected_path_id": "",
                "action_key": action_key,
                "event_type": event_type,
                "event_at": str(args.event_at),
                "event_source": "synthetic_simulator_phase69",
                "evidence_reference": "synthetic",
                "synthetic_flag": 1,
                "synthetic_generated_at_utc": now_iso,
            }
        )

    if not outcome_rows:
        raise ValueError("Synthetic generator produced no outcome rows (no usable source_customer_id values).")

    outcomes_path = eval_dir / "synthetic_outcomes.csv"
    events_path = eval_dir / "synthetic_action_execution_events.csv"
    pd.DataFrame(outcome_rows).to_csv(outcomes_path, index=False)
    pd.DataFrame(event_rows).to_csv(events_path, index=False)

    metadata = {
        "phase": "69-evidence-amplification",
        "synthetic": True,
        "non_causal": True,
        "input_customer_level_analysis_csv": str(customer_level_path),
        "output_synthetic_outcomes_csv": str(outcomes_path),
        "output_synthetic_action_events_csv": str(events_path),
        "synthetic_run_id": str(args.synthetic_run_id),
        "event_at": str(args.event_at),
        "generated_at_utc": now_iso,
        "row_counts": {"outcomes": int(len(outcome_rows)), "action_events": int(len(event_rows))},
    }
    (eval_dir / "synthetic_outcome_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(str(eval_dir))


if __name__ == "__main__":
    main()

