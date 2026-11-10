"""Canonical serialization (ADR-005): one object -> exactly one byte string.

Rules: UTF-8, keys sorted, no whitespace, ASCII-escaped non-ASCII, floats via Python's
shortest round-trip repr (deterministic across platforms), -0.0 normalised to 0.0,
NaN/Infinity rejected. Records store these bytes as TEXT (never JSONB, which reorders and
reformats), so hashing and replay compare identical bytes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel


class NonCanonicalValue(ValueError):
    """A value that has no single canonical form (NaN, Infinity, unsupported type)."""


def _normalise(obj: Any) -> Any:
    if isinstance(obj, bool) or obj is None or isinstance(obj, int | str):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise NonCanonicalValue(f"non-finite float: {obj!r}")
        return 0.0 if obj == 0.0 else obj  # -0.0 -> 0.0
    if isinstance(obj, dict):
        if not all(isinstance(k, str) for k in obj):
            raise NonCanonicalValue("object keys must be strings")
        return {k: _normalise(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_normalise(v) for v in obj]
    raise NonCanonicalValue(f"unsupported type: {type(obj).__name__}")


def canonical_text(obj: Any) -> str:
    return json.dumps(
        _normalise(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_bytes(obj: Any) -> bytes:
    return canonical_text(obj).encode("utf-8")


def model_canonical_text(model: BaseModel) -> str:
    return canonical_text(model.model_dump(mode="json"))


def sha256_hex(data: str | bytes) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()
