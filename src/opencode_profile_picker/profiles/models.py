"""Data models for profiles, key sets, and the profile store."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeyEntry:
    """A single API key entry within a key set."""

    provider: str
    env_var: str
    value: str | None = None  # None = use environment variable fallback


@dataclass
class KeySet:
    """A named collection of API keys."""

    name: str
    keys: dict[str, KeyEntry] = field(default_factory=dict)


@dataclass
class Profile:
    """A named combination of an OMO preset and a key set."""

    name: str
    preset: str
    key_set: str  # References a KeySet.name


@dataclass
class ProfileStore:
    """Top-level container for all profiles and key sets."""

    version: int = 1
    key_sets: dict[str, KeySet] = field(default_factory=dict)
    profiles: dict[str, Profile] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the store to a plain dict for JSON encoding."""
        return {
            "version": self.version,
            "key_sets": {
                name: {
                    "name": ks.name,
                    "keys": {
                        env_var: {
                            "provider": ke.provider,
                            "env_var": ke.env_var,
                            "value": ke.value,
                        }
                        for env_var, ke in ks.keys.items()
                    },
                }
                for name, ks in self.key_sets.items()
            },
            "profiles": {
                name: {
                    "name": p.name,
                    "preset": p.preset,
                    "key_set": p.key_set,
                }
                for name, p in self.profiles.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProfileStore:
        """Deserialize a plain dict into a ProfileStore."""
        store = cls(version=data.get("version", 1))

        key_sets_data = data.get("key_sets", {})
        for name, ks_data in key_sets_data.items():
            ks = KeySet(name=ks_data.get("name", name))
            keys_data = ks_data.get("keys", {})
            for env_var, ke_data in keys_data.items():
                ks.keys[env_var] = KeyEntry(
                    provider=ke_data.get("provider", ""),
                    env_var=ke_data.get("env_var", env_var),
                    value=ke_data.get("value"),
                )
            store.key_sets[name] = ks

        profiles_data = data.get("profiles", {})
        for name, p_data in profiles_data.items():
            store.profiles[name] = Profile(
                name=p_data.get("name", name),
                preset=p_data.get("preset", ""),
                key_set=p_data.get("key_set", ""),
            )

        return store
