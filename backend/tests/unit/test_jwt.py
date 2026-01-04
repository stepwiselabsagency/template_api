from __future__ import annotations

from datetime import timedelta

import jwt
import pytest
from app.auth.jwt import create_access_token, decode_token


@pytest.mark.unit
def test_create_access_token_includes_sub_and_exp() -> None:
    token = create_access_token("user-123", expires_delta=timedelta(minutes=5))
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert isinstance(payload["exp"], int)


@pytest.mark.unit
def test_decode_token_raises_for_expired_token() -> None:
    # `decode_token` uses a small leeway; expire well beyond it.
    token = create_access_token("user-123", expires_delta=timedelta(seconds=-120))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)
