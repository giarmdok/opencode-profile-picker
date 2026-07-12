"""Tests for encryption utilities."""

from __future__ import annotations

import pytest

from opencode_profile_picker.profiles.crypto import (
    decrypt_store,
    derive_key,
    encrypt_store,
    generate_salt,
    verify_password,
)


class TestGenerateSalt:
    def test_generates_correct_length(self) -> None:
        salt = generate_salt()
        assert len(salt) == 16

    def test_generates_unique_salts(self) -> None:
        salts = {generate_salt() for _ in range(10)}
        assert len(salts) == 10


class TestDeriveKey:
    def test_derives_consistent_key(self) -> None:
        salt = generate_salt()
        key1 = derive_key("password123", salt)
        key2 = derive_key("password123", salt)
        assert key1 == key2

    def test_different_passwords_produce_different_keys(self) -> None:
        salt = generate_salt()
        key1 = derive_key("password1", salt)
        key2 = derive_key("password2", salt)
        assert key1 != key2

    def test_different_salts_produce_different_keys(self) -> None:
        key1 = derive_key("password", generate_salt())
        key2 = derive_key("password", generate_salt())
        assert key1 != key2


class TestEncryptDecrypt:
    def test_roundtrip(self) -> None:
        original = {"version": 1, "profiles": {"test": {"name": "test"}}}
        encrypted = encrypt_store(original, "mypassword")
        decrypted = decrypt_store(encrypted, "mypassword")
        assert decrypted == original

    def test_wrong_password_raises(self) -> None:
        encrypted = encrypt_store({"data": "secret"}, "correct")
        with pytest.raises(ValueError, match="Incorrect password"):
            decrypt_store(encrypted, "wrong")

    def test_corrupted_data_raises(self) -> None:
        encrypted = encrypt_store({"data": "secret"}, "password")
        corrupted = encrypted[:-5] + b"xxxxx"
        with pytest.raises(ValueError):
            decrypt_store(corrupted, "password")

    def test_empty_store(self) -> None:
        encrypted = encrypt_store({}, "password")
        decrypted = decrypt_store(encrypted, "password")
        assert decrypted == {}

    def test_nested_data(self) -> None:
        original = {
            "key_sets": {
                "personal": {"keys": {"OPENAI_API_KEY": {"provider": "openai", "value": "sk-abc"}}}
            }
        }
        encrypted = encrypt_store(original, "password")
        decrypted = decrypt_store(encrypted, "password")
        assert decrypted == original


class TestVerifyPassword:
    def test_correct_password(self) -> None:
        encrypted = encrypt_store({"data": "test"}, "password")
        assert verify_password(encrypted, "password") is True

    def test_wrong_password(self) -> None:
        encrypted = encrypt_store({"data": "test"}, "password")
        assert verify_password(encrypted, "wrong") is False
