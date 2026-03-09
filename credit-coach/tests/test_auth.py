from __future__ import annotations

from credit_coach.api.auth import extract_bearer_token, verify_token


def test_extract_bearer_token():
    assert extract_bearer_token("Bearer abc123") == "abc123"
    assert extract_bearer_token("bearer xyz") == "xyz"
    assert extract_bearer_token("Token abc") is None
    assert extract_bearer_token(None) is None


def test_verify_token_with_configured_token(monkeypatch):
    monkeypatch.delenv("CREDIT_COACH_ALLOW_INSECURE_API", raising=False)
    monkeypatch.setenv("CREDIT_COACH_API_TOKEN", "secret-token")
    assert verify_token("secret-token") is True
    assert verify_token("wrong") is False
    assert verify_token(None) is False


def test_verify_token_insecure_mode(monkeypatch):
    monkeypatch.delenv("CREDIT_COACH_API_TOKEN", raising=False)
    monkeypatch.delenv("CREDIT_COACH_API_TOKENS", raising=False)
    monkeypatch.setenv("CREDIT_COACH_ALLOW_INSECURE_API", "1")
    assert verify_token(None) is True
