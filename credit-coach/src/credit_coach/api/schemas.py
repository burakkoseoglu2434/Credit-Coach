from __future__ import annotations

from pydantic import BaseModel


class ScoreRequest(BaseModel):
    features: dict[str, float]


class ScoreResponse(BaseModel):
    pd: float
    approve: bool
