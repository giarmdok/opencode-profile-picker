"""Discovery of oh-my-opencode-slim configuration and presets."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from opencode_profile_picker.config.parser import read_jsonc
from opencode_profile_picker.config.paths import (
    get_omo_config_paths,
    get_project_local_omo_path,
)

# Mapping of model provider prefixes to their standard environment variable names.
PROVIDER_KEY_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "xai": "XAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "github-copilot": "GITHUB_TOKEN",
    "deepseek": "DEEPSEEK_API_KEY",
    "kimi-for-coding": "KIMI_API_KEY",
    "zai-coding-plan": "ZAI_API_KEY",
    "omniroute": "OMNIROUTE_API_KEY",
    "opencode-go": "OPENCODE_GO_API_KEY",
}


@dataclass
class DiscoveryResult:
    """Result of scanning for OMO configuration."""

    config_path: Path | None = None
    config: dict[str, Any] | None = None
    presets: dict[str, set[str]] = field(default_factory=dict)
    active_preset: str | None = None
    project_local_override: str | None = None
    error: str | None = None


def discover_omo_config() -> DiscoveryResult:
    """Discover the oh-my-opencode-slim configuration.

    Scans known paths for the config file, parses it, and extracts
    preset information including required API keys per preset.
    """
    result = DiscoveryResult()

    # Find the config file
    for path in get_omo_config_paths():
        if path.exists():
            result.config_path = path
            break

    if result.config_path is None:
        result.error = "No oh-my-opencode-slim config file found"
        return result

    # Parse it
    config = read_jsonc(result.config_path)
    if config is None:
        result.error = f"Failed to parse config file: {result.config_path}"
        return result

    result.config = config
    result.active_preset = config.get("preset")
    result.presets = map_presets_to_keys(config)

    # Check for project-local override
    local_path = get_project_local_omo_path()
    if local_path is not None:
        local_config = read_jsonc(local_path)
        if local_config and "preset" in local_config:
            result.project_local_override = local_config["preset"]

    return result


def extract_presets(config: dict[str, Any]) -> list[str]:
    """Extract preset names from an OMO config dict."""
    presets = config.get("presets")
    if not isinstance(presets, dict):
        return []
    return list(presets.keys())


def extract_providers_from_preset(config: dict[str, Any], preset_name: str) -> set[str]:
    """Extract all model provider prefixes used by a specific preset.

    Walks agent configs and council configs to collect provider prefixes.
    """
    providers: set[str] = set()
    presets = config.get("presets")
    if not isinstance(presets, dict):
        return providers

    preset = presets.get(preset_name)
    if not isinstance(preset, dict):
        return providers

    # Walk agent configs
    for _agent_name, agent_config in preset.items():
        if not isinstance(agent_config, dict):
            continue
        model = agent_config.get("model")
        providers.update(_extract_providers_from_model(model))

    # Walk council configs
    council = config.get("council")
    if isinstance(council, dict):
        council_presets = council.get("presets")
        if isinstance(council_presets, dict):
            for _cp_name, cp_config in council_presets.items():
                if not isinstance(cp_config, dict):
                    continue
                for _councillor_name, councillor in cp_config.items():
                    if not isinstance(councillor, dict):
                        continue
                    model = councillor.get("model")
                    providers.update(_extract_providers_from_model(model))

    return providers


def _extract_providers_from_model(model: object) -> set[str]:
    """Extract provider prefixes from a model field (string or list)."""
    providers: set[str] = set()
    if isinstance(model, str):
        prefix = model.split("/")[0] if "/" in model else model
        providers.add(prefix)
    elif isinstance(model, list):
        for item in model:
            if isinstance(item, str):
                prefix = item.split("/")[0] if "/" in item else item
                providers.add(prefix)
            elif isinstance(item, dict):
                m = item.get("model") or item.get("id")
                if isinstance(m, str):
                    prefix = m.split("/")[0] if "/" in m else m
                    providers.add(prefix)
    return providers


def map_presets_to_keys(config: dict[str, Any]) -> dict[str, set[str]]:
    """Map each preset to the set of environment variables it requires.

    Returns {preset_name: {ENV_VAR, ...}}.
    """
    result: dict[str, set[str]] = {}
    for preset_name in extract_presets(config):
        providers = extract_providers_from_preset(config, preset_name)
        env_vars: set[str] = set()
        for provider in providers:
            env_var = PROVIDER_KEY_MAP.get(provider)
            if env_var:
                env_vars.add(env_var)
            else:
                # Unknown provider — include the raw provider name for display
                env_vars.add(f"UNKNOWN:{provider}")
        result[preset_name] = env_vars
    return result


def detect_project_local_override(cwd: Path | None = None) -> str | None:
    """Check for a project-local OMO config with a preset override.

    Returns the preset name if found, or None.
    """
    local_path = get_project_local_omo_path(cwd)
    if local_path is None:
        return None
    config = read_jsonc(local_path)
    if config is None:
        return None
    preset = config.get("preset")
    if isinstance(preset, str):
        return preset
    return None


def scan_env_for_keys() -> dict[str, str]:
    """Scan the current environment for known API key variables.

    Checks all env vars listed in PROVIDER_KEY_MAP and returns
    a dict of {provider: env_var_name} for any that are set.

    Does NOT capture the actual key values — only notes which
    providers have keys available in the environment.
    """
    found: dict[str, str] = {}
    for provider, env_var in PROVIDER_KEY_MAP.items():
        if os.environ.get(env_var):
            found[provider] = env_var
    return found
