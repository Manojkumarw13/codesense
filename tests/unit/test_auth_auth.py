from backend.app.auth.auth import (
    AuthError,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = hash_password("s3cr3t")
    assert hashed != "s3cr3t"
    assert verify_password("s3cr3t", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_round_trip_and_expiry():
    token = create_access_token({"sub": "user-1", "team_id": "team-alpha"})
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["team_id"] == "team-alpha"


def test_decode_expired_token_raises():
    import datetime

    token = create_access_token(
        {"sub": "user-1"}, expires_delta=datetime.timedelta(seconds=-1)
    )
    try:
        decode_token(token)
        raise AssertionError("expected AuthError")
    except AuthError:
        pass
