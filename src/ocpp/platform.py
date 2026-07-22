"""Platform abstraction — confine all sys.platform checks to this module."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

__all__ = [
    "GENERIC_VENV_DIR",
    "Platform",
    "PlatformFamily",
]

GENERIC_VENV_DIR = ".venv"


class PlatformFamily(Enum):
    """Operating-system family classification."""

    WINDOWS = "windows"
    LINUX = "linux"
    UNIX = "unix"


@dataclass(frozen=True)
class Platform:
    """Immutable platform descriptor with pre-resolved paths and names."""

    family: PlatformFamily
    venv_dir_name: str
    venv_bin_subdir: str
    omo_config_paths: list[Path]
    project_root: Path

    @classmethod
    def detect(
        cls,
        platform_string: str | None = None,
        home_dir: Path | None = None,
    ) -> Platform:
        """Detect the current platform and build a Platform descriptor.

        Parameters
        ----------
        platform_string:
            Override for ``sys.platform`` (used for testing).
        home_dir:
            Override for ``Path.home()`` (used for testing).
        """
        if platform_string is None:
            platform_string = sys.platform
        if home_dir is None:
            home_dir = Path.home()

        # --- family ---
        if platform_string == "win32":
            family = PlatformFamily.WINDOWS
        elif platform_string.startswith("linux"):
            family = PlatformFamily.LINUX
        else:
            family = PlatformFamily.UNIX

        # --- venv names ---
        venv_dir_name: str
        venv_bin_subdir: str
        if family is PlatformFamily.WINDOWS:
            venv_dir_name = ".venv_win"
            venv_bin_subdir = "Scripts"
        elif family is PlatformFamily.LINUX:
            venv_dir_name = ".venv_lin"
            venv_bin_subdir = "bin"
        else:  # UNIX
            venv_dir_name = ".venv_unx"
            venv_bin_subdir = "bin"

        # --- OMO config paths ---
        omo_config_paths: list[Path] = [
            home_dir / ".config" / "opencode" / "oh-my-opencode-slim.json",
            home_dir / ".config" / "opencode" / "oh-my-opencode-slim.jsonc",
        ]

        if family is PlatformFamily.WINDOWS:
            appdata = os.environ.get("APPDATA")
            if appdata:
                appdata_dir = Path(appdata)
                omo_config_paths.append(appdata_dir / "opencode" / "oh-my-opencode-slim.json")
                omo_config_paths.append(appdata_dir / "opencode" / "oh-my-opencode-slim.jsonc")
            # If APPDATA is not set, fall back to the .config paths already added.
            # Duplicates are harmless, so we keep the list as-is.

        return cls(
            family=family,
            venv_dir_name=venv_dir_name,
            venv_bin_subdir=venv_bin_subdir,
            omo_config_paths=omo_config_paths,
            project_root=Path.cwd(),
        )
