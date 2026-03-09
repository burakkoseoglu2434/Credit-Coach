from __future__ import annotations

from credit_coach.data.schema import MacroSnapshot
from credit_coach.utils.time import utc_now


def load_macro_snapshot_mock() -> MacroSnapshot:
    return MacroSnapshot(
        snapshot_date=utc_now(),
        interest_rate=35.0,
        unemployment_rate=9.0,
        gdp_growth=3.0,
        inflation_rate=42.0,
        credit_spread=5.0,
        source="mock",
    )
