from __future__ import annotations

import argparse
import json
import logging

from credit_coach.storage.db import init_db
from credit_coach.storage.repository import get_audit_events, verify_audit_chain

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_audit_verify")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify immutable audit hash chain")
    p.add_argument("--print_events", action="store_true", help="Print all audit events as JSON")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    init_db()

    ok, issues = verify_audit_chain()
    events = get_audit_events()

    if args.print_events:
        logger.info("Audit events:\n%s", json.dumps(events, indent=2, ensure_ascii=False))

    if ok:
        logger.info("Audit chain verification PASSED. events=%d", len(events))
        return

    logger.error("Audit chain verification FAILED. issue_count=%d", len(issues))
    for issue in issues:
        logger.error("Issue: %s", json.dumps(issue, ensure_ascii=False))
    raise SystemExit(1)


if __name__ == "__main__":
    main()

