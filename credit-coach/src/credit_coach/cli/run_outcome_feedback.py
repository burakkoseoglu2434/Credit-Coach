from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from credit_coach.data.schema import DecisionOutcomeRecord
from credit_coach.storage.db import init_db
from credit_coach.storage.repository import (
    compute_policy_outcome_deltas,
    save_decision_outcome,
    summarize_decision_outcomes,
)
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_outcome_feedback")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest delayed decision outcomes and publish policy delta report")
    p.add_argument("--outcomes_csv", type=str, default="", help="Optional CSV to upsert outcomes")
    p.add_argument("--window_days", type=int, default=90)
    return p.parse_args()


def _ingest_csv(path: Path) -> int:
    df = pd.read_csv(path)
    required = {"decision_id", "run_id", "customer_id"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    inserted = 0
    for _, row in df.iterrows():
        rec = DecisionOutcomeRecord(
            decision_id=str(row["decision_id"]),
            run_id=str(row["run_id"]),
            customer_id=str(row["customer_id"]),
            policy_arm=str(row.get("policy_arm", "control")),
            decision_status=str(row.get("decision_status", "UNKNOWN")),
            approved=bool(int(row.get("approved", 0))),
            predicted_pd=(float(row["predicted_pd"]) if "predicted_pd" in row and pd.notna(row["predicted_pd"]) else None),
            observed_default_30d=(int(row["observed_default_30d"]) if "observed_default_30d" in row and pd.notna(row["observed_default_30d"]) else None),
            observed_default_60d=(int(row["observed_default_60d"]) if "observed_default_60d" in row and pd.notna(row["observed_default_60d"]) else None),
            observed_default_90d=(int(row["observed_default_90d"]) if "observed_default_90d" in row and pd.notna(row["observed_default_90d"]) else None),
            observed_margin_90d=(float(row["observed_margin_90d"]) if "observed_margin_90d" in row and pd.notna(row["observed_margin_90d"]) else None),
        )
        save_decision_outcome(rec)
        inserted += 1
    return inserted


def main() -> None:
    args = parse_args()
    init_db()
    run_ctx = create_run_context(
        {"window_days": int(args.window_days), "outcomes_csv": str(args.outcomes_csv)},
        base_artifact_dir="artifacts/runs",
    )

    ingested = 0
    if args.outcomes_csv:
        ingested = _ingest_csv(Path(args.outcomes_csv))

    summary_df = summarize_decision_outcomes(window_days=int(args.window_days))
    deltas = compute_policy_outcome_deltas(window_days=int(args.window_days))

    summary_out = run_ctx.tables_dir / "outcome_policy_summary.csv"
    deltas_out = run_ctx.tables_dir / "outcome_policy_deltas.json"
    summary_df.to_csv(summary_out, index=False)
    deltas_out.write_text(json.dumps(deltas, indent=2, ensure_ascii=False), encoding="utf-8")
    run_ctx.save_metrics(
        {
            "window_days": int(args.window_days),
            "ingested_records": int(ingested),
            "policy_arm_count": int(summary_df["policy_arm"].nunique()) if not summary_df.empty else 0,
            "approval_rate_delta": float(deltas.get("approval_rate_delta", 0.0)),
            "default_rate_90d_delta": float(deltas.get("default_rate_90d_delta", 0.0)),
            "avg_margin_90d_delta": float(deltas.get("avg_margin_90d_delta", 0.0)),
        }
    )
    logger.info("Outcome feedback summary: %s", summary_out)
    logger.info("Outcome policy deltas: %s", deltas_out)


if __name__ == "__main__":
    main()
