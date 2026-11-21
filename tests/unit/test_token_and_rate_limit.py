from __future__ import annotations

import logging

import pytest
from api.routes.recommendations import _DECISION_CALLS, check_rate_limit, require_operator_token
from fastapi import HTTPException


def test_require_operator_token_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_TOKEN", "super-secret-operator-pass")

    # Correct token
    assert require_operator_token("super-secret-operator-pass") == "operator"

    # Incorrect token
    with pytest.raises(HTTPException) as exc_wrong:
        require_operator_token("wrong-pass")
    assert exc_wrong.value.status_code == 401

    # Empty token
    with pytest.raises(HTTPException) as exc_empty:
        require_operator_token("")
    assert exc_empty.value.status_code == 401


def test_require_operator_token_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPERATOR_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_operator_token("any-token")
    assert exc.value.status_code == 503
    assert "not configured" in exc.value.detail


def test_rate_limiter_blocks_excessive_calls() -> None:
    key = "test-rate-limit-actor"
    _DECISION_CALLS[key] = []

    # First 60 calls within 1 minute succeed
    for _ in range(60):
        check_rate_limit(key)

    # 61st call must be blocked with HTTP 429
    with pytest.raises(HTTPException) as exc:
        check_rate_limit(key)
    assert exc.value.status_code == 429
    assert "rate limit exceeded" in exc.value.detail.lower()


def test_operator_token_never_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "secret-token-never-to-be-logged"
    monkeypatch.setenv("OPERATOR_TOKEN", secret)

    with caplog.at_level(logging.DEBUG):
        try:
            require_operator_token(secret)
        except Exception:
            pass

    assert secret not in caplog.text
