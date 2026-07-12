"""Encrypted profile store persistence.

Manages reading, writing, creating, and resetting the encrypted profiles.json.enc file.
"""

from __future__ import annotations

from pathlib import Path

from opencode_profile_picker.config.paths import get_oopps_data_dir
from opencode_profile_picker.profiles.crypto import decrypt_store, encrypt_store
from opencode_profile_picker.profiles.models import ProfileStore

STORE_FILENAME = "profiles.json.enc"


class ProfileStoreManager:
    """Manages the encrypted profile store on disk.

    Holds the decrypted store in memory and the encryption password
    for the session lifetime.
    """

    def __init__(self, store: ProfileStore, password: str, store_path: Path) -> None:
        self._store = store
        self._password = password
        self._store_path = store_path

    @property
    def store(self) -> ProfileStore:
        """Return the in-memory profile store."""
        return self._store

    @classmethod
    def load(cls, password: str) -> ProfileStoreManager:
        """Load and decrypt an existing profile store.

        Raises ValueError if the password is wrong or the file is corrupted.
        Raises FileNotFoundError if the store file doesn't exist.
        """
        store_path = cls._get_store_path()
        if not store_path.exists():
            raise FileNotFoundError(f"Store file not found: {store_path}")

        encrypted = store_path.read_bytes()
        data = decrypt_store(encrypted, password)
        store = ProfileStore.from_dict(data)
        return cls(store, password, store_path)

    @classmethod
    def create(cls, password: str) -> ProfileStoreManager:
        """Create a new empty profile store with the given password.

        The store is immediately encrypted and written to disk.
        """
        store_path = cls._get_store_path()
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store = ProfileStore()
        manager = cls(store, password, store_path)
        manager.save()
        return manager

    def save(self) -> None:
        """Encrypt and write the current store to disk."""
        data = self._store.to_dict()
        encrypted = encrypt_store(data, self._password)
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_bytes(encrypted)

    def reset(self) -> None:
        """Delete the encrypted store file from disk."""
        if self._store_path.exists():
            self._store_path.unlink()

    @staticmethod
    def store_exists() -> bool:
        """Check if an encrypted profile store exists on disk."""
        return ProfileStoreManager._get_store_path().exists()

    @staticmethod
    def _get_store_path() -> Path:
        """Return the path to the encrypted store file."""
        return get_oopps_data_dir() / STORE_FILENAME
