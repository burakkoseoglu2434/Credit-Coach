from __future__ import annotations

import json

import yaml

from credit_coach.api.auth import has_required_scope, verify_token


def test_has_required_scope_passes_with_matching_scope(tmp_path, monkeypatch):
    cfg = {
        "auth": {
            "allow_insecure_local_demo": False,
            "endpoint_scopes": {"/score/demo": ["score:read"]},
        }
    }
    cfg_path = tmp_path / "security.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setenv("CREDIT_COACH_SECURITY_CONFIG", str(cfg_path))
    monkeypatch.setenv(
        "CREDIT_COACH_API_KEYS_JSON",
        json.dumps(
            [
                {
                    "token": "scoped-token",
                    "status": "active",
                    "scopes": ["score:read"],
                }
            ]
        ),
    )

    assert verify_token("scoped-token") is True
    assert has_required_scope("scoped-token", "/score/demo") is True


def test_has_required_scope_fails_without_scope(tmp_path, monkeypatch):
    cfg = {
        "auth": {
            "allow_insecure_local_demo": False,
            "endpoint_scopes": {"/score/demo": ["score:read"]},
        }
    }
    cfg_path = tmp_path / "security.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setenv("CREDIT_COACH_SECURITY_CONFIG", str(cfg_path))
    monkeypatch.setenv(
        "CREDIT_COACH_API_KEYS_JSON",
        json.dumps(
            [
                {
                    "token": "unscoped-token",
                    "status": "active",
                    "scopes": ["monitor:read"],
                }
            ]
        ),
    )

    assert verify_token("unscoped-token") is True
    assert has_required_scope("unscoped-token", "/score/demo") is False
