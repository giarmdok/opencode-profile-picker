"""Venv detection, validation, and activation env delta computation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import NamedTuple

from ocpp.platform import GENERIC_VENV_DIR, Platform, PlatformFamily

__all__ = [
    "VenvResult",
    "find_venv",
    "validate_venv",
    "compute_venv_env_delta",
    "detect_venv",
]

logger = logging.getLogger(__name__)


class VenvResult(NamedTuple):
    """Result of a successful venv detection."""

    path: Path
    env_delta: dict[str, str | None]


def find_venv(platform: Platform) -> Path | None:
    """Search project root for venv: platform-specific name first, then .venv fallback.

    Returns the Path if a directory exists, None otherwise.
    """
    # 1. Platform-specific venv
    candidate = platform.project_root / platform.venv_dir_name
    if candidate.is_dir():
        return candidate

    # 2. Generic .venv fallback
    candidate = platform.project_root / GENERIC_VENV_DIR
    if candidate.is_dir():
        return candidate

    return None


def validate_venv(venv_path: Path, platform: Platform) -> bool:
    """Check interpreter executable exists in venv bin subdir.

    Returns True if valid, False otherwise.
    If venv dir exists but validation fails, log a warning.
    """
    interpreter_name = "python.exe" if platform.family is PlatformFamily.WINDOWS else "python"
    interpreter = venv_path / platform.venv_bin_subdir / interpreter_name

    if not interpreter.exists():
        logger.warning("Venv directory exists but interpreter not found: %s", venv_path)
        return False

    return True


def compute_venv_env_delta(venv_path: Path, platform: Platform) -> dict[str, str | None]:
    """Build activation env delta.

    * PATH: prepend venv bin dir to current PATH
    * VIRTUAL_ENV: set to venv root path
    * PYTHONHOME: set to None (unset) if currently set, omitted if not set
    """
    bin_dir = venv_path / platform.venv_bin_subdir

    delta: dict[str, str | None] = {
        "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
        "VIRTUAL_ENV": str(venv_path),
    }

    if "PYTHONHOME" in os.environ:
        delta["PYTHONHOME"] = None

    return delta


def detect_venv(platform: Platform) -> VenvResult | None:
    """Full detection flow: find_venv → validate_venv → compute_venv_env_delta.

    Returns VenvResult if valid venv found, None otherwise.
    If venv dir exists but is invalid, logs warning and returns None.
    """
    venv_path = find_venv(platform)
    if venv_path is None:
        return None

    if not validate_venv(venv_path, platform):
        return None

    env_delta = compute_venv_env_delta(venv_path, platform)
    return VenvResult(path=venv_path, env_delta=env_delta)
