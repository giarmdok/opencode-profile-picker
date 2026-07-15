"""CRUD operations for profiles and key sets on a ProfileStore."""

from __future__ import annotations

from dataclasses import dataclass

from opencode_profile_picker.config.discover import PROVIDER_KEY_MAP
from opencode_profile_picker.profiles.models import KeyEntry, KeySet, Profile, ProfileStore


@dataclass
class MergePreview:
    """Structured preview of what would change when importing keys from environment."""

    new: list[KeyEntry]  # env vars set, not in key set
    overlap: list[KeyEntry]  # env vars set, already in key set (info only)
    orphan_stored: list[KeyEntry]  # in key set, not in env, value is not None
    orphan_env_fallback: list[KeyEntry]  # in key set, not in env, value is None


def compute_merge(
    key_set: KeySet,
    env: dict[str, str] | None = None,
) -> MergePreview:
    """Compare a key set against environment variables and return a structured preview.

    Args:
        key_set: The key set to diff against.
        env: Optional environment dict. Defaults to os.environ.

    Returns:
        MergePreview with four categorized lists.
    """
    import os as _os

    if env is None:
        env = dict(_os.environ)

    # Find which known env vars are set
    env_entries: list[tuple[str, str]] = []  # (provider, env_var)
    for provider, env_var in PROVIDER_KEY_MAP.items():
        if env.get(env_var):
            env_entries.append((provider, env_var))

    env_var_set = {ev for _, ev in env_entries}

    new: list[KeyEntry] = []
    overlap: list[KeyEntry] = []

    for provider, env_var in env_entries:
        if env_var in key_set.keys:
            overlap.append(key_set.keys[env_var])
        else:
            new.append(KeyEntry(provider=provider, env_var=env_var, value=None))

    orphan_stored: list[KeyEntry] = []
    orphan_env_fallback: list[KeyEntry] = []

    for entry in key_set.keys.values():
        if entry.env_var not in env_var_set:
            if entry.value is not None:
                orphan_stored.append(entry)
            else:
                orphan_env_fallback.append(entry)

    return MergePreview(
        new=new,
        overlap=overlap,
        orphan_stored=orphan_stored,
        orphan_env_fallback=orphan_env_fallback,
    )


# ── Profile Operations ──────────────────────────────────────────────


def add_profile(store: ProfileStore, name: str, preset: str, key_set: str = "") -> Profile:
    """Add a new profile to the store.

    Raises ValueError if a profile with the same name already exists.
    """
    if name in store.profiles:
        raise ValueError(f"Profile '{name}' already exists")
    profile = Profile(name=name, preset=preset, key_set=key_set)
    store.profiles[name] = profile
    return profile


def get_profile(store: ProfileStore, name: str) -> Profile | None:
    """Get a profile by name, or None if not found."""
    return store.profiles.get(name)


def list_profiles(store: ProfileStore) -> list[Profile]:
    """Return all profiles in the store."""
    return list(store.profiles.values())


def update_profile(
    store: ProfileStore, name: str, preset: str | None = None, key_set: str | None = None
) -> Profile:
    """Update an existing profile's preset and/or key set.

    Raises KeyError if the profile doesn't exist.
    """
    profile = store.profiles[name]
    if preset is not None:
        profile.preset = preset
    if key_set is not None:
        profile.key_set = key_set
    return profile


def delete_profile(store: ProfileStore, name: str) -> None:
    """Delete a profile from the store. Does not delete the referenced key set.

    Raises KeyError if the profile doesn't exist.
    """
    del store.profiles[name]


def validate_profiles(store: ProfileStore) -> list[str]:
    """Check all profiles reference existing key sets.

    Returns a list of profile names that reference missing key sets.
    """
    orphaned: list[str] = []
    for profile in store.profiles.values():
        if profile.key_set not in store.key_sets:
            orphaned.append(profile.name)
    return orphaned


# ── Key Set Operations ──────────────────────────────────────────────


def add_key_set(store: ProfileStore, name: str) -> KeySet:
    """Add a new empty key set to the store.

    Raises ValueError if a key set with the same name already exists.
    """
    if name in store.key_sets:
        raise ValueError(f"Key set '{name}' already exists")
    ks = KeySet(name=name)
    store.key_sets[name] = ks
    return ks


def get_key_set(store: ProfileStore, name: str) -> KeySet | None:
    """Get a key set by name, or None if not found."""
    return store.key_sets.get(name)


def list_key_sets(store: ProfileStore) -> list[tuple[str, int]]:
    """Return all key sets with their key counts.

    Returns list of (name, key_count) tuples.
    """
    return [(name, len(ks.keys)) for name, ks in store.key_sets.items()]


def delete_key_set(store: ProfileStore, name: str) -> list[str]:
    """Delete a key set from the store.

    Returns a list of profile names that now reference a missing key set.

    Raises KeyError if the key set doesn't exist.
    """
    del store.key_sets[name]
    return validate_profiles(store)


def add_key(key_set: KeySet, provider: str, env_var: str, value: str | None = None) -> KeyEntry:
    """Add a key entry to a key set.

    Raises ValueError if a key with the same env_var already exists.
    """
    if env_var in key_set.keys:
        raise ValueError(f"Key '{env_var}' already exists in key set '{key_set.name}'")
    entry = KeyEntry(provider=provider, env_var=env_var, value=value)
    key_set.keys[env_var] = entry
    return entry


def remove_key(key_set: KeySet, env_var: str) -> None:
    """Remove a key entry from a key set.

    Raises KeyError if the key doesn't exist.
    """
    del key_set.keys[env_var]


def update_key_value(key_set: KeySet, env_var: str, new_value: str | None) -> KeyEntry:
    """Update the value of an existing key entry.

    Raises KeyError if the key doesn't exist.
    """
    entry = key_set.keys[env_var]
    entry.value = new_value
    return entry
