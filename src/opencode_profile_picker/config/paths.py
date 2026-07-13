"""Platform-aware path resolution for OpenCode and oopps config directories."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _get_config_home() -> Path:
    """Get the user config home directory, respecting XDG_CONFIG_HOME on Unix."""
    if sys.platform == "win32":
        # On Windows, prefer %APPDATA% but also check ~/.config
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def get_opencode_config_dir() -> Path:
    """Return the OpenCode user config directory.

    On Windows, checks %APPDATA%\\opencode\\ first, then ~\\.config\\opencode\\.
    On Unix, returns ~/.config/opencode/ (or $XDG_CONFIG_HOME/opencode/).
    """
    config_home = _get_config_home()
    return config_home / "opencode"


def get_oopps_data_dir() -> Path:
    """Return the oopps data directory for storing encrypted profiles.

    Returns ~/.config/oopps/ on all platforms (or platform equivalent).
    """
    config_home = _get_config_home()
    return config_home / "oopps"


def get_opencode_executable() -> str | None:
    """Locate the opencode executable on the system PATH.

    Returns the path string if found, or None if not available.
    """
    return shutil.which("opencode")


def get_omo_config_paths() -> list[Path]:
    """Return candidate paths for oh-my-opencode-slim config files.

    Returns paths in order of preference (jsonc preferred over json).
    On Windows, checks both %APPDATA%\\opencode\\ and ~\\.config\\opencode\\.
    """
    config_dir = get_opencode_config_dir()
    paths = [
        config_dir / "oh-my-opencode-slim.jsonc",
        config_dir / "oh-my-opencode-slim.json",
    ]

    # On Windows, also check ~/.config/opencode/ (many tools use this path)
    if sys.platform == "win32":
        dotconfig_dir = Path.home() / ".config" / "opencode"
        if dotconfig_dir != config_dir:
            paths.extend(
                [
                    dotconfig_dir / "oh-my-opencode-slim.jsonc",
                    dotconfig_dir / "oh-my-opencode-slim.json",
                ]
            )

    return paths


def get_project_local_omo_path(cwd: Path | None = None) -> Path | None:
    """Check for a project-local OMO config in .opencode/ directory.

    Returns the path if found (preferring .jsonc over .json), or None.
    """
    if cwd is None:
        cwd = Path.cwd()
    project_config = cwd / ".opencode"
    if not project_config.is_dir():
        return None
    jsonc = project_config / "oh-my-opencode-slim.jsonc"
    if jsonc.exists():
        return jsonc
    json_path = project_config / "oh-my-opencode-slim.json"
    if json_path.exists():
        return json_path
    return None
