"""Tests for profile store persistence."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from opencode_profile_picker.profiles.models import KeyEntry, KeySet, Profile
from opencode_profile_picker.profiles.store import ProfileStoreManager


class TestProfileStoreManager:
    @pytest.fixture(autouse=True)
    def _mock_store_path(self, tmp_path: Path) -> None:
        """Redirect store path to a temp directory."""
        store_file = tmp_path / "profiles.json.enc"
        with patch.object(
            ProfileStoreManager,
            "_get_store_path",
            return_value=store_file,
        ):
            yield

    def test_create_and_load(self) -> None:
        manager = ProfileStoreManager.create("password123")
        assert manager.store is not None
        assert manager.store.version == 1
        assert len(manager.store.profiles) == 0
        assert len(manager.store.key_sets) == 0

        # Reload
        loaded = ProfileStoreManager.load("password123")
        assert loaded.store.version == 1

    def test_load_wrong_password(self) -> None:
        ProfileStoreManager.create("correct")
        with pytest.raises(ValueError, match="Incorrect password"):
            ProfileStoreManager.load("wrong")

    def test_load_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            ProfileStoreManager.load("password")

    def test_save_persists_changes(self) -> None:
        manager = ProfileStoreManager.create("password")
        manager.store.key_sets["test"] = KeySet(name="test")
        manager.store.key_sets["test"].keys["OPENAI_API_KEY"] = KeyEntry(
            provider="openai", env_var="OPENAI_API_KEY", value="sk-test"
        )
        manager.save()

        loaded = ProfileStoreManager.load("password")
        assert "test" in loaded.store.key_sets
        assert "OPENAI_API_KEY" in loaded.store.key_sets["test"].keys

    def test_reset_deletes_file(self) -> None:
        manager = ProfileStoreManager.create("password")
        assert ProfileStoreManager.store_exists()
        manager.reset()
        assert not ProfileStoreManager.store_exists()

    def test_store_exists(self) -> None:
        assert not ProfileStoreManager.store_exists()
        ProfileStoreManager.create("password")
        assert ProfileStoreManager.store_exists()

    def test_full_cycle(self) -> None:
        # Create
        manager = ProfileStoreManager.create("password")

        # Add data
        ks = KeySet(name="personal")
        ks.keys["OPENROUTER_API_KEY"] = KeyEntry(
            provider="openrouter", env_var="OPENROUTER_API_KEY", value="sk-abc"
        )
        manager.store.key_sets["personal"] = ks
        manager.store.profiles["or-personal"] = Profile(
            name="or-personal", preset="or", key_set="personal"
        )
        manager.save()

        # Reload
        loaded = ProfileStoreManager.load("password")
        assert "personal" in loaded.store.key_sets
        assert "or-personal" in loaded.store.profiles
        assert loaded.store.key_sets["personal"].keys["OPENROUTER_API_KEY"].value == "sk-abc"
