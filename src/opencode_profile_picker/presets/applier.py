"""Preset application — read and write the active preset in OMO config files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from opencode_profile_picker.config.parser import read_jsonc, write_json


@dataclass
class ApplyResult:
    """Result of applying a preset to an OMO config file."""

    success: bool
    message: str
    previous_preset: str | None = None


def get_active_preset(config_path: Path) -> str | None:
    """Read the currently active preset from an OMO config file.

    Returns the preset name, or None if the file doesn't exist or is malformed.
    """
    config = read_jsonc(config_path)
    if config is None:
        return None
    preset = config.get("preset")
    if isinstance(preset, str):
        return preset
    return None


def apply_preset(config_path: Path, preset_name: str) -> ApplyResult:
    """Write a new preset name to the OMO config file.

    Only modifies the top-level 'preset' field. All other fields are preserved.
    Preserves the file extension (.json or .jsonc).

    Returns an ApplyResult describing the outcome.
    """
    if not config_path.exists():
        return ApplyResult(
            success=False,
            message=f"Config file not found: {config_path}",
        )

    config = read_jsonc(config_path)
    if config is None:
        return ApplyResult(
            success=False,
            message=f"Failed to parse config file: {config_path}",
        )

    previous = config.get("preset")
    config["preset"] = preset_name

    if not write_json(config_path, config):
        return ApplyResult(
            success=False,
            message=f"Failed to write config file: {config_path}",
        )

    return ApplyResult(
        success=True,
        message=f"Preset changed to '{preset_name}'",
        previous_preset=previous if isinstance(previous, str) else None,
    )


def is_preset_already_active(config_path: Path, preset_name: str) -> bool:
    """Check if the given preset is already the active one."""
    current = get_active_preset(config_path)
    return current == preset_name
