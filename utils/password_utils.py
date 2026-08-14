import hashlib
import bcrypt

"""
Helpers to safely use bcrypt with passwords of any length.

bcrypt only accepts up to 72 bytes. This module:
- pre-hashes the input with SHA-256 when it's longer than 72 bytes (recommended),
  so you don't lose entropy.
- provides hash_password() and check_password() wrappers you can call from your code.

If you absolutely want truncation instead, replace the _prepare_password_for_bcrypt
implementation to return password_bytes[:72].
"""


def _prepare_password_for_bcrypt(password: str | bytes) -> bytes:
    # Normalize to bytes
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password

    # bcrypt has a 72-byte input limit
    if len(password_bytes) > 72:
        # Pre-hash with SHA-256 to get a fixed-length, high-entropy input
        # This is better than truncation because it preserves entropy.
        return hashlib.sha256(password_bytes).digest()

    return password_bytes


def hash_password(password: str | bytes) -> bytes:
    """
    Return a bcrypt hash suitable for storage.
    """
    pw = _prepare_password_for_bcrypt(password)
    return bcrypt.hashpw(pw, bcrypt.gensalt())


def check_password(password: str | bytes, hashed: bytes) -> bool:
    """
    Verify a password against a stored bcrypt hash.
    """
    pw = _prepare_password_for_bcrypt(password)
    return bcrypt.checkpw(pw, hashed)
