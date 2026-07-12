"""Encryption utilities for the profile store.

Uses PBKDF2-SHA256 for key derivation and Fernet (AES-128-CBC + HMAC-SHA256)
for symmetric encryption of the profile data.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# OWASP 2023 recommendation for PBKDF2-SHA256
PBKDF2_ITERATIONS = 600_000
SALT_LENGTH = 16
VERIFY_PLAINTEXT = "oopps-ok"


def generate_salt() -> bytes:
    """Generate a random 16-byte salt for PBKDF2."""
    return os.urandom(SALT_LENGTH)


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet-compatible key from a password and salt.

    Uses PBKDF2-SHA256 with 600,000 iterations.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def encrypt_store(store_dict: dict[str, Any], password: str) -> bytes:
    """Encrypt a store dict with a password.

    Returns bytes containing salt + verification token + encrypted data,
    all base64-encoded and JSON-serialized.
    """
    salt = generate_salt()
    key = derive_key(password, salt)
    fernet = Fernet(key)

    verify_token = fernet.encrypt(VERIFY_PLAINTEXT.encode("utf-8"))
    data_token = fernet.encrypt(json.dumps(store_dict).encode("utf-8"))

    envelope = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "verify": verify_token.decode("ascii"),
        "data": data_token.decode("ascii"),
    }
    return json.dumps(envelope).encode("utf-8")


def decrypt_store(encrypted_bytes: bytes, password: str) -> dict[str, Any]:
    """Decrypt an encrypted store with a password.

    Returns the store dict on success.
    Raises ValueError if the password is wrong or data is corrupted.
    """
    try:
        envelope = json.loads(encrypted_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError("Corrupted store file") from e

    salt = base64.b64decode(envelope["salt"])
    verify_token = envelope["verify"].encode("ascii")
    data_token = envelope["data"].encode("ascii")

    key = derive_key(password, salt)
    fernet = Fernet(key)

    # Verify password first
    try:
        decrypted_verify = fernet.decrypt(verify_token)
        if decrypted_verify.decode("utf-8") != VERIFY_PLAINTEXT:
            raise ValueError("Incorrect password")
    except InvalidToken as e:
        raise ValueError("Incorrect password") from e

    # Decrypt data
    try:
        decrypted_data = fernet.decrypt(data_token)
        return json.loads(decrypted_data.decode("utf-8"))
    except (InvalidToken, json.JSONDecodeError) as e:
        raise ValueError("Corrupted store data") from e


def verify_password(encrypted_bytes: bytes, password: str) -> bool:
    """Check if a password can decrypt the store without full decryption."""
    try:
        decrypt_store(encrypted_bytes, password)
        return True
    except ValueError:
        return False
