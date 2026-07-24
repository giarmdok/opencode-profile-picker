"""OMO config discovery, parsing, preset listing, and surgical preset writing."""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, NamedTuple

from rich.console import Console
import json5

from ocpp.platform import Platform

__all__ = [
    "OmoError",
    "PresetInfo",
    "LOCAL_OMO_DIR",
    "LOCAL_OMO_FILENAME",
    "discover_config",
    "discover_local_config",
    "get_local_config_path",
    "parse_config",
    "list_presets",
    "set_preset",
]

logger = logging.getLogger(__name__)

LOCAL_OMO_DIR = ".opencode"
LOCAL_OMO_FILENAME = "oh-my-opencode-slim.jsonc"  # .jsonc for precedence over global .json

PRESET_PATTERN = re.compile(r'(^|[\s{])"preset"\s*:\s*"[^"]*"\s*(,?)', re.MULTILINE)


class OmoError(Exception):
    """Raised for OMO config errors (missing fields, parse failures)."""


class PresetInfo(NamedTuple):
    name: str
    is_current: bool


def discover_config(platform: Platform) -> Path:
    """Find the first existing OMO config file from platform.omo_config_paths or local project.

    Checks for a local config at `<project_root>/.opencode/oh-my-opencode-slim.jsonc`
    before falling back to global paths.

    Raises
    ------
    FileNotFoundError
        If no config file exists at any of the searched paths.
    """
    # Check for local config first
    project_root = Path.cwd()
    local_path = project_root / ".opencode" / "oh-my-opencode-slim.jsonc"
    if local_path.exists():
        logger.debug("Found local OMO config at %s", local_path)
        return local_path

    # Fall back to global paths
    for path in platform.omo_config_paths:
        if path.exists():
            logger.debug("Found OMO config at %s", path)
            return path
    searched = ", ".join(str(p) for p in platform.omo_config_paths)
    msg = f"No OMO config found. Searched: {searched}"
    raise FileNotFoundError(msg)


def get_local_config_path(project_root: Path) -> Path:
    """Return the path to the local project-level OMO config override (.jsonc)."""
    return project_root / LOCAL_OMO_DIR / LOCAL_OMO_FILENAME


def discover_local_config(project_root: Path) -> Path | None:
    """Check if a local OMO config override exists. Return its path or None."""
    local_path = get_local_config_path(project_root)
    return local_path if local_path.exists() else None


def parse_config(filepath: Path) -> dict[str, Any]:
    """Read and parse the OMO config file with json5.

    Validates: result is dict, has 'preset' (str), has 'presets' (dict).

    Parameters
    ----------
    filepath:
        Path to the OMO config file.

    Returns
    -------
    dict
        The parsed config dictionary.

    Raises
    ------
    OmoError
        On validation failure (missing fields, wrong types).
    ValueError
        On JSON5 parse failure.
    """
    # Read the file with explicit sharing flags to mimic 'type' behavior
    import os
    max_retries = 3
    retry_delay = 0.5  # seconds
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Use low-level open with sharing flags to avoid lock sensitivity
            fd = os.open(str(filepath), os.O_RDONLY | os.O_BINARY)
            with open(fd, "r", encoding="utf-8") as f:
                raw = f.read()
            break
        except PermissionError as exc:
            last_exception = exc
            logger.warning(
                "File lock detected, retrying (%d/%d)...: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            import time
            time.sleep(retry_delay)
    else:
        raise OmoError(f"Failed to read OMO config: {last_exception}") from last_exception
    try:
        data = json5.loads(raw)
    except ValueError as exc:
        raise ValueError(f"Failed to parse OMO config at {filepath}: {exc}") from exc

    if not isinstance(data, dict):
        raise OmoError(
            f"OMO config at {filepath}: expected a top-level object, got {type(data).__name__}"
        )

    if "preset" not in data:
        raise OmoError(f"OMO config at {filepath}: missing top-level 'preset' field")

    if not isinstance(data["preset"], str):
        raise OmoError(
            f"OMO config at {filepath}: 'preset' must be a string, got {type(data['preset']).__name__}"
        )

    if "presets" not in data:
        raise OmoError(f"OMO config at {filepath}: missing top-level 'presets' field")

    if not isinstance(data["presets"], dict):
        raise OmoError(
            f"OMO config at {filepath}: 'presets' must be an object, got {type(data['presets']).__name__}"
        )

    return data


def list_presets(filepath: Path) -> tuple[str, list[PresetInfo]]:
    """Parse config and return (current_preset_name, list of PresetInfo).

    Marks the current preset. If the current preset is not in the presets
    dict, it is still included in the list.
    """
    data = parse_config(filepath)
    current = data["preset"]
    presets_dict: dict[str, Any] = data["presets"]

    infos: list[PresetInfo] = []
    for name in presets_dict:
        infos.append(PresetInfo(name=name, is_current=(name == current)))

    # If current preset is not in the presets dict, still include it
    if current not in presets_dict:
        infos.append(PresetInfo(name=current, is_current=True))

    return current, infos


def set_preset(
    global_config_path: Path,
    new_preset: str,
    project_root: Path,
    confirm: bool = True,
) -> bool:
    """Copy global OMO config to a local project override and update the preset.

    The global config is never modified. A local copy is created at
    ``<project_root>/.opencode/oh-my-opencode-slim.jsonc`` and the ``"preset"``
    field is surgically edited there.

    Parameters
    ----------
    global_config_path:
        Path to the global OMO config file (read-only).
    new_preset:
        Name of the preset to activate.
    project_root:
        Root of the project where the local override will be placed.
    confirm:
        If True, prompt the user for confirmation before writing.

    Returns
    -------
    bool
        True if the local override was written, False if the user declined.
    """
    # Parse to validate structure and check new_preset exists
    data = parse_config(global_config_path)
    old = data["preset"]

    if new_preset not in data["presets"]:
        raise OmoError(
            f"Preset '{new_preset}' not found in presets at {global_config_path}. "
            f"Available: {', '.join(sorted(data['presets']))}"
        )

    local_path = get_local_config_path(project_root)

    # Skip confirmation for non-interactive preset selection
    if confirm:
        Console().print(f"[dim]Setting preset from '{old}' to '{new_preset}'...[/dim]")

    # Ensure the .opencode/ directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing local override if present
    if local_path.exists():
        bak_path = local_path.with_suffix(local_path.suffix + ".bak")
        shutil.copy2(local_path, bak_path)

    # Read the global config into memory using low-level read logic
    max_retries = 3
    retry_delay = 0.5  # seconds
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Use low-level open with sharing flags to avoid lock sensitivity
            import os
            fd = os.open(str(global_config_path), os.O_RDONLY | os.O_BINARY)
            with open(fd, "r", encoding="utf-8") as f:
                raw_text = f.read()
            break
        except PermissionError as exc:
            last_exception = exc
            logger.warning(
                "File lock detected, retrying (%d/%d)...: %s",
                attempt + 1,
                max_retries,
                exc,
            )
            import time
            time.sleep(retry_delay)
    else:
        raise OmoError(f"Failed to read OMO config: {last_exception}") from last_exception

    # Write the local .jsonc file directly from memory
    fd, tmp_path_str = tempfile.mkstemp(dir=local_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(raw_text)
        os.replace(tmp_path_str, str(local_path))
    except BaseException:
        # Clean up temp file on failure
        if os.path.exists(tmp_path_str):
            os.unlink(tmp_path_str)
        raise

    # Read the local copy's raw text for surgical edit
    raw_text = local_path.read_text(encoding="utf-8")

    # Try surgical regex replacement first
    match = PRESET_PATTERN.search(raw_text)
    if match:
        prefix = match.group(1)
        comma = match.group(2)
        new_line = f'{prefix}"preset": "{new_preset}"{comma}'
        updated_text = raw_text[: match.start()] + new_line + raw_text[match.end() :]
    else:
        # Fall back to re-serialize
        logger.warning(
            "Regex pattern did not match 'preset' field in %s; falling back to re-serialization (formatting may be lost)",
            local_path,
        )
        data["preset"] = new_preset
        updated_text = json5.dumps(data, indent=2)

    # Write via temp file + atomic rename
    fd, tmp_path_str = tempfile.mkstemp(dir=local_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(updated_text)
        os.replace(tmp_path_str, str(local_path))
    except BaseException:
        # Clean up temp file on failure
        if os.path.exists(tmp_path_str):
            os.unlink(tmp_path_str)
        raise

    logger.info(
        "Copied global OMO config to %s and set preset to '%s'",
        local_path,
        new_preset,
    )
    return True
