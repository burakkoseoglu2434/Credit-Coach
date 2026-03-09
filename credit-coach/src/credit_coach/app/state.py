from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardState:
    model_version: str
    status: str
    last_run: str
