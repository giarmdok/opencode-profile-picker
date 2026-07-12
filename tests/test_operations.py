"""Tests for profile and key set CRUD operations."""

from __future__ import annotations

import pytest

from opencode_profile_picker.profiles.models import KeyEntry, KeySet, ProfileStore
from opencode_profile_picker.profiles.operations import (
    add_key,
    add_key_set,
    add_profile,
    delete_key_set,
    delete_profile,
    get_key_set,
    get_profile,
    list_key_sets,
    list_profiles,
    remove_key,
    update_key_value,
    update_profile,
    validate_profiles,
)


@pytest.fixture
def store() -> ProfileStore:
    """Create a store with some test data."""
    s = ProfileStore()
    ks = KeySet(name="personal")
    ks.keys["OPENAI_API_KEY"] = KeyEntry(
        provider="openai", env_var="OPENAI_API_KEY", value="sk-test"
    )
    s.key_sets["personal"] = ks
    s.key_sets["work"] = KeySet(name="work")
    return s


class TestProfileOperations:
    def test_add_profile(self, store: ProfileStore) -> None:
        profile = add_profile(store, "test", "or", "personal")
        assert profile.name == "test"
        assert profile.preset == "or"
        assert profile.key_set == "personal"
        assert "test" in store.profiles

    def test_add_duplicate_raises(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        with pytest.raises(ValueError, match="already exists"):
            add_profile(store, "test", "go", "work")

    def test_get_profile(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        p = get_profile(store, "test")
        assert p is not None
        assert p.preset == "or"

    def test_get_profile_missing(self, store: ProfileStore) -> None:
        assert get_profile(store, "nonexistent") is None

    def test_list_profiles(self, store: ProfileStore) -> None:
        add_profile(store, "a", "or", "personal")
        add_profile(store, "b", "go", "work")
        profiles = list_profiles(store)
        assert len(profiles) == 2

    def test_update_profile(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        update_profile(store, "test", preset="go")
        assert store.profiles["test"].preset == "go"
        assert store.profiles["test"].key_set == "personal"

    def test_update_profile_key_set(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        update_profile(store, "test", key_set="work")
        assert store.profiles["test"].key_set == "work"

    def test_delete_profile(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        delete_profile(store, "test")
        assert "test" not in store.profiles

    def test_delete_profile_preserves_key_set(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        delete_profile(store, "test")
        assert "personal" in store.key_sets

    def test_validate_profiles_clean(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        assert validate_profiles(store) == []

    def test_validate_profiles_orphaned(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        del store.key_sets["personal"]
        orphaned = validate_profiles(store)
        assert "test" in orphaned


class TestKeySetOperations:
    def test_add_key_set(self, store: ProfileStore) -> None:
        ks = add_key_set(store, "experiment")
        assert ks.name == "experiment"
        assert "experiment" in store.key_sets

    def test_add_duplicate_key_set_raises(self, store: ProfileStore) -> None:
        with pytest.raises(ValueError, match="already exists"):
            add_key_set(store, "personal")

    def test_get_key_set(self, store: ProfileStore) -> None:
        ks = get_key_set(store, "personal")
        assert ks is not None
        assert ks.name == "personal"

    def test_get_key_set_missing(self, store: ProfileStore) -> None:
        assert get_key_set(store, "nonexistent") is None

    def test_list_key_sets(self, store: ProfileStore) -> None:
        result = list_key_sets(store)
        assert len(result) == 2
        names_and_counts = dict(result)
        assert names_and_counts["personal"] == 1
        assert names_and_counts["work"] == 0

    def test_delete_key_set(self, store: ProfileStore) -> None:
        delete_key_set(store, "work")
        assert "work" not in store.key_sets

    def test_delete_key_set_reports_orphaned(self, store: ProfileStore) -> None:
        add_profile(store, "test", "or", "personal")
        orphaned = delete_key_set(store, "personal")
        assert "test" in orphaned

    def test_add_key(self, store: ProfileStore) -> None:
        ks = store.key_sets["work"]
        entry = add_key(ks, "openrouter", "OPENROUTER_API_KEY", "sk-abc")
        assert entry.provider == "openrouter"
        assert entry.value == "sk-abc"
        assert "OPENROUTER_API_KEY" in ks.keys

    def test_add_key_duplicate_raises(self, store: ProfileStore) -> None:
        ks = store.key_sets["personal"]
        with pytest.raises(ValueError, match="already exists"):
            add_key(ks, "openai", "OPENAI_API_KEY", "sk-xyz")

    def test_add_key_null_value(self, store: ProfileStore) -> None:
        ks = store.key_sets["work"]
        entry = add_key(ks, "openrouter", "OPENROUTER_API_KEY", None)
        assert entry.value is None

    def test_remove_key(self, store: ProfileStore) -> None:
        ks = store.key_sets["personal"]
        remove_key(ks, "OPENAI_API_KEY")
        assert "OPENAI_API_KEY" not in ks.keys

    def test_update_key_value(self, store: ProfileStore) -> None:
        ks = store.key_sets["personal"]
        update_key_value(ks, "OPENAI_API_KEY", "sk-new")
        assert ks.keys["OPENAI_API_KEY"].value == "sk-new"

    def test_update_key_value_to_none(self, store: ProfileStore) -> None:
        ks = store.key_sets["personal"]
        update_key_value(ks, "OPENAI_API_KEY", None)
        assert ks.keys["OPENAI_API_KEY"].value is None
