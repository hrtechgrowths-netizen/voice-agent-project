import secrets

import bcrypt

from utils.password_utils import _prepare_password_for_bcrypt, check_password, hash_password


def test_hash_and_check_short_password():
    password = "short_password_123"
    hashed = hash_password(password)

    assert hashed.startswith((b"$2a$", b"$2b$", b"$2y$"))
    assert check_password(password, hashed) is True


def test_hash_and_check_long_password():
    password = secrets.token_urlsafe(128)
    assert len(password.encode("utf-8")) > 72

    hashed = hash_password(password)

    assert hashed.startswith((b"$2a$", b"$2b$", b"$2y$"))
    assert check_password(password, hashed) is True


def test_hash_output_is_valid_for_bcrypt():
    password = "another_password_123"
    hashed = hash_password(password)

    prepared_password = _prepare_password_for_bcrypt(password)
    assert bcrypt.checkpw(prepared_password, hashed) is True
