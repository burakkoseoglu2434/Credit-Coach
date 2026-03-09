from __future__ import annotations

import hmac
import json
import math
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml


def extract_bearer_token(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    parts = authorization_header.strip().split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts
    if scheme.lower() != "bearer":
        return None
    token = token.strip()
    return token or None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utc_now(now_utc: datetime | None = None) -> datetime:
    if now_utc is None:
        return datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=timezone.utc)
    return now_utc.astimezone(timezone.utc)


@dataclass(frozen=True)
class TokenPolicyEntry:
    token: str
    status: str = "active"  # active | next | retired
    expires_at: datetime | None = None
    grace_until: datetime | None = None
    key_id: str | None = None
    scopes: tuple[str, ...] = ()

    def is_valid_at(self, now_utc: datetime) -> bool:
        status = self.status.lower()
        if status in {"active", "next"}:
            if self.expires_at is None:
                return True
            if now_utc <= self.expires_at:
                return True
            return self.grace_until is not None and now_utc <= self.grace_until
        if status == "retired":
            return self.grace_until is not None and now_utc <= self.grace_until
        return False

    def has_scope(self, scope: str) -> bool:
        if not self.scopes:
            return True
        return scope in self.scopes


def _security_config_path() -> Path:
    return Path(os.getenv("CREDIT_COACH_SECURITY_CONFIG", "configs/security.yaml"))


def _load_security_config() -> dict[str, Any]:
    path = _security_config_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        return {}
    if not isinstance(cfg, dict):
        return {}
    return cfg


def _entry_from_mapping(item: dict[str, Any]) -> TokenPolicyEntry | None:
    token = item.get("token")
    if not isinstance(token, str) or not token.strip():
        return None
    status = str(item.get("status", "active")).strip().lower() or "active"
    raw_scopes = item.get("scopes", [])
    scopes: tuple[str, ...] = ()
    if isinstance(raw_scopes, str):
        scopes = tuple(s.strip() for s in raw_scopes.split(",") if s and s.strip())
    elif isinstance(raw_scopes, list):
        scopes = tuple(str(s).strip() for s in raw_scopes if str(s).strip())
    return TokenPolicyEntry(
        token=token.strip(),
        status=status,
        expires_at=_parse_iso_datetime(item.get("expires_at")),
        grace_until=_parse_iso_datetime(item.get("grace_until")),
        key_id=str(item.get("key_id")).strip() if item.get("key_id") is not None else None,
        scopes=scopes,
    )


def _entries_from_list(raw_items: Any) -> list[TokenPolicyEntry]:
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        return []
    out: list[TokenPolicyEntry] = []
    for item in raw_items:
        if isinstance(item, dict):
            entry = _entry_from_mapping(item)
            if entry is not None:
                out.append(entry)
    return out


def _configured_token_entries() -> list[TokenPolicyEntry]:
    # New format (priority): JSON policy entries from env.
    raw_json = os.getenv("CREDIT_COACH_API_KEYS_JSON", "").strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            parsed = []
        entries = _entries_from_list(parsed)
        if entries:
            return entries

    # Backward-compatible env settings.
    tokens_env = os.getenv("CREDIT_COACH_API_TOKENS", "").strip()
    if tokens_env:
        return [TokenPolicyEntry(token=t.strip()) for t in tokens_env.split(",") if t.strip()]

    single = os.getenv("CREDIT_COACH_API_TOKEN", "").strip()
    if single:
        return [TokenPolicyEntry(token=single)]

    # YAML policy entries.
    cfg = _load_security_config()
    auth_cfg = cfg.get("auth", {}) if isinstance(cfg.get("auth", {}), dict) else {}
    yaml_entries = _entries_from_list(auth_cfg.get("keys", []))
    if yaml_entries:
        return yaml_entries

    # YAML simple tokens (optional backward compatibility).
    yaml_tokens = auth_cfg.get("tokens", [])
    if isinstance(yaml_tokens, list):
        return [TokenPolicyEntry(token=str(v).strip()) for v in yaml_tokens if str(v).strip()]
    return []


def _allow_insecure_api() -> bool:
    env_flag = os.getenv("CREDIT_COACH_ALLOW_INSECURE_API", "").strip()
    if env_flag:
        return env_flag == "1"
    cfg = _load_security_config()
    auth_cfg = cfg.get("auth", {}) if isinstance(cfg.get("auth", {}), dict) else {}
    return bool(auth_cfg.get("allow_insecure_local_demo", False))


def verify_token(token: str | None, now_utc: datetime | None = None) -> bool:
    return resolve_token_policy(token, now_utc=now_utc) is not None


def resolve_token_policy(token: str | None, now_utc: datetime | None = None) -> TokenPolicyEntry | None:
    configured = _configured_token_entries()
    if not configured:
        # Explicitly opt-in only for local demos.
        return TokenPolicyEntry(token="__insecure__", status="active") if _allow_insecure_api() else None
    if not token:
        return None

    now = _utc_now(now_utc)
    for entry in configured:
        if not entry.is_valid_at(now):
            continue
        if hmac.compare_digest(token, entry.token):
            return entry
    return None


def endpoint_required_scopes(endpoint: str) -> tuple[str, ...]:
    cfg = _load_security_config()
    auth_cfg = cfg.get("auth", {}) if isinstance(cfg.get("auth", {}), dict) else {}
    scopes_map = auth_cfg.get("endpoint_scopes", {}) if isinstance(auth_cfg.get("endpoint_scopes", {}), dict) else {}
    raw = scopes_map.get(endpoint, [])
    if isinstance(raw, str):
        return tuple(s.strip() for s in raw.split(",") if s and s.strip())
    if isinstance(raw, list):
        return tuple(str(s).strip() for s in raw if str(s).strip())
    return ()


def has_required_scope(token: str | None, endpoint: str, now_utc: datetime | None = None) -> bool:
    required = endpoint_required_scopes(endpoint)
    if not required:
        return True
    entry = resolve_token_policy(token, now_utc=now_utc)
    if entry is None:
        return False
    return all(entry.has_scope(scope) for scope in required)


class FixedWindowRateLimiter:
    """
    Thread-safe fixed-window limiter.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        clock_fn: Callable[[], float] | None = None,
    ) -> None:
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._clock_fn = clock_fn or time.time
        self._state: dict[str, tuple[int, int]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now_ts: float | None = None) -> tuple[bool, int | None]:
        now = float(self._clock_fn() if now_ts is None else now_ts)
        current_window = int(now // self.window_seconds)

        with self._lock:
            prev_window, count = self._state.get(key, (current_window, 0))
            if prev_window != current_window:
                prev_window, count = current_window, 0

            if count >= self.limit:
                retry_after = max(
                    1,
                    int(math.ceil(((current_window + 1) * self.window_seconds) - now)),
                )
                self._state[key] = (prev_window, count)
                return False, retry_after

            self._state[key] = (prev_window, count + 1)
            return True, None


_RATE_LIMITERS: dict[tuple[str, int, int], FixedWindowRateLimiter] = {}
_RATE_LIMITERS_LOCK = threading.Lock()


def reset_rate_limiters() -> None:
    with _RATE_LIMITERS_LOCK:
        _RATE_LIMITERS.clear()


def _rate_limit_settings(endpoint: str) -> dict[str, int | bool]:
    cfg = _load_security_config()
    rl_cfg = cfg.get("rate_limit", {}) if isinstance(cfg.get("rate_limit", {}), dict) else {}
    endpoints = rl_cfg.get("endpoints", {}) if isinstance(rl_cfg.get("endpoints", {}), dict) else {}
    endpoint_cfg = endpoints.get(endpoint, {}) if isinstance(endpoints.get(endpoint, {}), dict) else {}

    enabled = bool(rl_cfg.get("enabled", True))
    enabled = bool(endpoint_cfg.get("enabled", enabled))

    default_limit = int(rl_cfg.get("default_limit", 60))
    default_window = int(rl_cfg.get("default_window_seconds", 60))
    limit = int(endpoint_cfg.get("limit", default_limit))
    window_seconds = int(endpoint_cfg.get("window_seconds", default_window))

    return {
        "enabled": enabled and limit > 0 and window_seconds > 0,
        "limit": max(1, limit),
        "window_seconds": max(1, window_seconds),
    }


def _get_rate_limiter(endpoint: str, limit: int, window_seconds: int) -> FixedWindowRateLimiter:
    key = (endpoint, limit, window_seconds)
    with _RATE_LIMITERS_LOCK:
        limiter = _RATE_LIMITERS.get(key)
        if limiter is None:
            limiter = FixedWindowRateLimiter(limit=limit, window_seconds=window_seconds)
            _RATE_LIMITERS[key] = limiter
        return limiter


def check_rate_limit(
    token: str | None,
    endpoint: str,
    now_ts: float | None = None,
) -> tuple[bool, int | None]:
    settings = _rate_limit_settings(endpoint=endpoint)
    if not bool(settings["enabled"]):
        return True, None

    limit = int(settings["limit"])
    window_seconds = int(settings["window_seconds"])
    limiter = _get_rate_limiter(endpoint=endpoint, limit=limit, window_seconds=window_seconds)

    identity = token.strip() if isinstance(token, str) and token.strip() else "__anonymous__"
    return limiter.allow(key=f"{endpoint}:{identity}", now_ts=now_ts)
