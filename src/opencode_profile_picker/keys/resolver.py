"""Key resolution — resolve API keys from store, environment, or user prompt."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING

from opencode_profile_picker.config.discover import DiscoveryResult

if TYPE_CHECKING:
    from opencode_profile_picker.profiles.models import KeySet


def resolve_keys(
    key_set: KeySet,
    required_keys: set[str],
    current_env: dict[str, str] | None = None,
) -> dict[str, str | None]:
    """Resolve all required API keys for a key set.

    For each required key:
    1. Check if stored in the key set (encrypted, now decrypted in memory)
    2. Check the current environment
    3. Return None if not found (caller should prompt user)

    Returns {env_var: value_or_None}.
    """
    if current_env is None:
        current_env = dict(os.environ)

    resolved: dict[str, str | None] = {}
    for env_var in required_keys:
        if env_var.startswith("UNKNOWN:"):
            # Unknown provider — can't resolve
            resolved[env_var] = None
            continue

        entry = key_set.keys.get(env_var)
        if entry is not None and entry.value is not None:
            resolved[env_var] = entry.value
        elif env_var in current_env and current_env[env_var]:
            resolved[env_var] = current_env[env_var]
        else:
            resolved[env_var] = None
    return resolved


def get_required_keys(preset_name: str, discovery: DiscoveryResult) -> set[str]:
    """Get the set of required env var names for a given preset."""
    return discovery.presets.get(preset_name, set())


def build_launch_env(
    resolved_keys: Mapping[str, str | None],
    current_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build the environment dict for launching OpenCode.

    Merges resolved keys with the current environment.
    None values (unresolved keys) are excluded.
    Existing env vars are preserved unless overridden by resolved keys.
    """
    if current_env is None:
        current_env = dict(os.environ)

    env = dict(current_env)
    for key, value in resolved_keys.items():
        if value is not None and not key.startswith("UNKNOWN:"):
            env[key] = value
    return env


def get_missing_keys(resolved_keys: Mapping[str, str | None]) -> list[str]:
    """Return list of env var names that could not be resolved."""
    return [
        key
        for key, value in resolved_keys.items()
        if value is None and not key.startswith("UNKNOWN:")
    ]
