"""Runtime switches. The decision log is OFF by default and needs no database."""

from __future__ import annotations

import os

DECISION_LOG_ENV = "CREDIT_COACH_DECISION_LOG"


def decision_log_enabled() -> bool:
    return os.environ.get(DECISION_LOG_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


class DecisionLogNotAvailable(RuntimeError):
    pass


def require_decision_log_off() -> None:
    """Demo v0 has no database writes. The existing `record_decision` covers the decision layer
    only (not the support check or recourse), so enabling the log here is refused explicitly
    instead of silently logging an incomplete record."""
    if decision_log_enabled():
        raise DecisionLogNotAvailable(
            f"{DECISION_LOG_ENV} is set, but the decision log is not part of demo v0 "
            "(no database writes; ADR-004 record_decision does not cover support/recourse)."
        )
