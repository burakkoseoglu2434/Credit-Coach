from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_governance_report")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate governance report summary")
    p.add_argument("--source_json", type=str, default="")
    return p.parse_args()


def _latest_decision() -> Path:
    candidates = sorted(Path("artifacts/runs").glob("*/tables/governance_decision.json"))
    if not candidates:
        raise FileNotFoundError("No governance decision file found. Run run_retrain first.")
    return candidates[-1]


def main() -> None:
    args = parse_args()
    source = Path(args.source_json) if args.source_json else _latest_decision()
    decision = json.loads(source.read_text(encoding="utf-8"))

    run_ctx = create_run_context({"source": str(source)}, base_artifact_dir="artifacts/runs")

    report = pd.DataFrame(
        [
            {
                "status": decision.get("status"),
                "reason_count": len(decision.get("reasons", [])),
                "champion_auc": decision.get("champion_metrics", {}).get("auc"),
                "challenger_auc": decision.get("challenger_metrics", {}).get("auc"),
                "champion_ece": decision.get("champion_metrics", {}).get("ece"),
                "challenger_ece": decision.get("challenger_metrics", {}).get("ece"),
                "approval_compliance": decision.get("governance_workflow", {}).get("approval_compliance"),
                "release_artifact_completeness": decision.get("governance_workflow", {}).get("release_artifact_completeness"),
                "rollback_test_passed": decision.get("governance_workflow", {}).get("rollback_test_passed"),
            }
        ]
    )
    out = run_ctx.tables_dir / "governance_report.csv"
    report.to_csv(out, index=False)
    run_ctx.save_metrics({"status": decision.get("status", "UNKNOWN")})
    logger.info("Governance report: %s", out)


if __name__ == "__main__":
    main()
