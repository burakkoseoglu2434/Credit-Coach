from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """
    Timezone-aware current UTC timestamp.
    """
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """
    Naive UTC timestamp for DB columns that are configured as timezone-naive.
    """
    return utc_now().replace(tzinfo=None)
