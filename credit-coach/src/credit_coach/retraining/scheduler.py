from __future__ import annotations


def build_schedule_string(schedule: str, day_of_week: str, hour: int) -> str:
    return f"{schedule}:{day_of_week}@{hour:02d}:00"
