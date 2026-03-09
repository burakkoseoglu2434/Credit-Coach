from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from credit_coach.coaching.loop import run_weekly_coaching_loop
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_coaching")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Weekly coaching loop")
    p.add_argument("--weeks", type=int, default=4)
    p.add_argument("--coaching_config", type=str, default="configs/coaching.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--plans_csv", type=str, default="")
    return p.parse_args()


def _latest_plans_csv() -> Path:
    candidates = sorted(Path("artifacts/runs").glob("*/tables/plans.csv"))
    if not candidates:
        raise FileNotFoundError("No plans.csv found. Run run_recourse first.")
    return candidates[-1]


def _status_rank(status: str) -> int:
    st = str(status or "").upper()
    if st == "APPROVED":
        return 0
    if st == "NEEDS_REVIEW":
        return 1
    if st == "REJECTED":
        return 2
    return 3


def _select_best_plan_row(plans_df: pd.DataFrame) -> pd.Series:
    if plans_df.empty:
        raise ValueError("Plans CSV is empty")
    df = plans_df.copy()
    df["status_rank"] = df["status"].map(_status_rank) if "status" in df.columns else 3

    sort_cols = ["status_rank"]
    ascending = [True]
    if "robust_score" in df.columns:
        sort_cols.append("robust_score")
        ascending.append(False)
    if "score" in df.columns:
        sort_cols.append("score")
        ascending.append(False)
    if "predicted_pd" in df.columns:
        sort_cols.append("predicted_pd")
        ascending.append(True)

    return df.sort_values(sort_cols, ascending=ascending).iloc[0]


def _parse_macro_shock_schedule(raw_schedule) -> dict[int, dict]:
    out: dict[int, dict] = {}
    if not isinstance(raw_schedule, list):
        return out
    for item in raw_schedule:
        if not isinstance(item, dict):
            continue
        week = item.get("week")
        if week is None:
            continue
        try:
            week_i = int(week)
        except Exception:
            continue
        out[week_i] = {"changes": item.get("changes", {}) if isinstance(item.get("changes", {}), dict) else {}}
    return out


def main() -> None:
    args = parse_args()
    c_cfg = load_config(args.coaching_config)
    m_cfg = load_config(args.model_config)

    run_ctx = create_run_context({"coaching": c_cfg, "model": m_cfg}, base_artifact_dir="artifacts/runs")

    plans_path = Path(args.plans_csv) if args.plans_csv else _latest_plans_csv()
    plans_df = pd.read_csv(plans_path)
    best = _select_best_plan_row(plans_df)

    base_pd = float(best.get("predicted_pd", 0.5))
    tau = float(m_cfg.get("decision", {}).get("tau_0", 0.35))

    progress_cfg = c_cfg.get("progress", {})
    trigger_cfg = c_cfg.get("replan_triggers", {})
    demo_cfg = c_cfg.get("demo", {})
    seq_cfg = c_cfg.get("sequential", {})
    robust_gate_cfg = c_cfg.get("robust_gates", {})

    schedule = _parse_macro_shock_schedule(seq_cfg.get("macro_shock_schedule", []))
    plan_actions = int(best.get("action_count", seq_cfg.get("default_plan_action_count", 6)))
    target_pd = float(
        min(
            tau - float(seq_cfg.get("target_pd_margin_under_tau", 0.01)),
            best.get("robust_anchor_pd", best.get("predicted_pd", tau - 0.01)),
        )
    )

    weekly_df = run_weekly_coaching_loop(
        base_pd=base_pd,
        tau=tau,
        weeks=args.weeks,
        macro_shock_week=int(demo_cfg.get("macro_shock_week", 3)),
        improving_threshold=float(progress_cfg.get("improving_threshold", -0.02)),
        stagnant_threshold=float(progress_cfg.get("stagnant_threshold", 0.02)),
        plan_action_count=plan_actions,
        target_pd=target_pd,
        action_dropout_prob=float(seq_cfg.get("action_dropout_prob", 0.15)),
        execution_noise_std=float(seq_cfg.get("execution_noise_std", 0.003)),
        action_effect_per_step=float(seq_cfg.get("action_effect_per_step", 0.005)),
        ci_buffer=float(seq_cfg.get("ci_buffer", 0.02)),
        random_state=int(seq_cfg.get("random_state", 42)),
        max_missed_actions=int(trigger_cfg.get("missed_actions", 2)),
        status_deteriorating=bool(trigger_cfg.get("status_deteriorating", True)),
        ci_exceed_tau=bool(trigger_cfg.get("ci_exceed_tau", True)),
        missed_actions_enabled=bool(int(trigger_cfg.get("missed_actions", 2)) > 0),
        max_weekly_actions=int(seq_cfg.get("max_weekly_actions", 3)),
        macro_shock_schedule=schedule,
        min_robust_margin=(
            float(robust_gate_cfg.get("min_robust_margin"))
            if robust_gate_cfg.get("min_robust_margin") is not None
            else None
        ),
    )

    out = run_ctx.tables_dir / "weekly_coaching.csv"
    weekly_df.to_csv(out, index=False)

    final_pd = float(weekly_df.iloc[-1]["predicted_pd"])
    achieved_target = bool(final_pd <= target_pd)
    run_ctx.save_metrics(
        {
            "weeks": int(args.weeks),
            "replan_count": int(weekly_df["replan"].sum()),
            "final_pd": final_pd,
            "target_pd": float(target_pd),
            "achieved_target": achieved_target,
            "avg_execution_rate": float(weekly_df["execution_rate"].mean()),
            "missed_action_weeks": int(weekly_df["missed_action"].sum()),
            "selected_plan_id": str(best.get("plan_id", "")),
        }
    )
    logger.info("Weekly coaching output: %s", out)


if __name__ == "__main__":
    main()

