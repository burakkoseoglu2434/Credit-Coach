from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from credit_coach.api.auth import verify_token


def test_verify_token_rotation_status_and_grace(monkeypatch):
    now = datetime(2026, 3, 7, 12, 0, 0, tzinfo=timezone.utc)
    keys = [
        {
            "key_id": "k-active",
            "token": "active-token",
            "status": "active",
            "expires_at": (now + timedelta(days=1)).isoformat(),
        },
        {
            "key_id": "k-next",
            "token": "next-token",
            "status": "next",
            "expires_at": (now + timedelta(days=2)).isoformat(),
        },
        {
            "key_id": "k-retired",
            "token": "retired-token",
            "status": "retired",
            "grace_until": (now + timedelta(minutes=30)).isoformat(),
        },
    ]
    monkeypatch.setenv("CREDIT_COACH_API_KEYS_JSON", json.dumps(keys))
    monkeypatch.delenv("CREDIT_COACH_API_TOKEN", raising=False)
    monkeypatch.delenv("CREDIT_COACH_API_TOKENS", raising=False)
    monkeypatch.delenv("CREDIT_COACH_ALLOW_INSECURE_API", raising=False)

    assert verify_token("active-token", now_utc=now) is True
    assert verify_token("next-token", now_utc=now) is True
    assert verify_token("retired-token", now_utc=now) is True

    assert verify_token("retired-token", now_utc=now + timedelta(hours=1)) is False
    assert verify_token("unknown-token", now_utc=now) is False


def test_verify_token_expired_without_grace(monkeypatch):
    now = datetime(2026, 3, 7, 12, 0, 0, tzinfo=timezone.utc)
    keys = [
        {
            "token": "expired-active",
            "status": "active",
            "expires_at": (now - timedelta(minutes=1)).isoformat(),
        }
    ]
    monkeypatch.setenv("CREDIT_COACH_API_KEYS_JSON", json.dumps(keys))
    monkeypatch.delenv("CREDIT_COACH_ALLOW_INSECURE_API", raising=False)

    assert verify_token("expired-active", now_utc=now) is False

