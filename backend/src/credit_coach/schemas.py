"""Pydantic schemas: single source of truth for the API contract."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
