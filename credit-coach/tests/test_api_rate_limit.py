from __future__ import annotations

import yaml

from credit_coach.api.auth import FixedWindowRateLimiter, check_rate_limit, reset_rate_limiters


class _Clock:
    def __init__(self, ts: float) -> None:
        self.ts = ts

    def now(self) -> float:
        return self.ts


def test_fixed_window_rate_limiter_blocks_and_resets():
    clock = _Clock(0.0)
    limiter = FixedWindowRateLimiter(limit=2, window_seconds=10, clock_fn=clock.now)

    assert limiter.allow("token-a") == (True, None)
    assert limiter.allow("token-a") == (True, None)

    allowed, retry_after = limiter.allow("token-a")
    assert allowed is False
    assert retry_after == 10

    clock.ts = 11.0
    assert limiter.allow("token-a") == (True, None)


def test_check_rate_limit_uses_endpoint_override(tmp_path, monkeypatch):
    cfg = {
        "rate_limit": {
            "enabled": True,
            "default_limit": 3,
            "default_window_seconds": 60,
            "endpoints": {
                "/score/demo": {"enabled": True, "limit": 1, "window_seconds": 60}
            },
        }
    }
    cfg_path = tmp_path / "security.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    monkeypatch.setenv("CREDIT_COACH_SECURITY_CONFIG", str(cfg_path))
    reset_rate_limiters()

    assert check_rate_limit("tok", "/score/demo", now_ts=100.0) == (True, None)
    allowed, retry_after = check_rate_limit("tok", "/score/demo", now_ts=100.0)
    assert allowed is False
    assert retry_after is not None and retry_after > 0

    # Default endpoint limit should still allow 3 requests in the same window.
    assert check_rate_limit("tok", "/health", now_ts=100.0) == (True, None)
    assert check_rate_limit("tok", "/health", now_ts=100.0) == (True, None)
    assert check_rate_limit("tok", "/health", now_ts=100.0) == (True, None)
    assert check_rate_limit("tok", "/health", now_ts=100.0)[0] is False

