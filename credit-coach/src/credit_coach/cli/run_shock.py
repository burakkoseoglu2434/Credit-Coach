from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from credit_coach.macro.shock_sim import run_shock_reliability
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_shock")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run macro shock reliability")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--plans_csv", type=str, default="data/processed/latest_plans.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    macro_cfg = load_config(args.macro_config)
    model_cfg = load_config(args.model_config)

    run_ctx = create_run_context({"macro": macro_cfg, "model": model_cfg}, base_artifact_dir="artifacts/runs")

    plans_path = Path(args.plans_csv)
    if not plans_path.exists():
        # fallback: locate latest plans table from recourse runs
        candidates = sorted(Path("artifacts/runs").glob("*/tables/plans.csv"))
        if not candidates:
            raise FileNotFoundError("No plans.csv found. Run run_recourse first.")
        plans_path = candidates[-1]

    plans_df = pd.read_csv(plans_path)
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    scenarios = macro_cfg.get("shock_scenarios", [])
    shift = float(macro_cfg.get("event_impact", {}).get("threshold_shift_per_msi_unit", 0.0))

    out_df = run_shock_reliability(
        plans_df,
        tau=tau,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=shift,
    )
    out_csv = run_ctx.tables_dir / "shock_reliability.csv"
    out_df.to_csv(out_csv, index=False)

    run_ctx.save_metrics(
        {
            "plan_count": int(len(out_df)),
            "avg_reliability": float(out_df["reliability"].mean()),
            "min_reliability": float(out_df["reliability"].min()),
            "avg_worst_risk_margin": float(out_df["worst_risk_margin"].mean()),
            "threshold_shift_per_msi_unit": shift,
        }
    )
    logger.info("Shock reliability saved: %s", out_csv)


if __name__ == "__main__":
    main()
