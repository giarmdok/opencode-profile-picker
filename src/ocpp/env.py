"""
.env file parser for opencode-profile-picker.

This module provides functionality to parse .env files and force-set environment variables,
overriding existing values in os.environ.
"""
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import dotenv_values


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load and force-set environment variables from a .env file.

    Args:
        env_path: Path to the .env file. Defaults to `.env` in the project root.

    Returns:
        Dict of overridden keys (old_value -> new_value) for logging.

    Behavior:
        - If `.env` does not exist, returns an empty dict.
        - If `.env` is empty, returns an empty dict.
        - Force-sets keys in os.environ (overrides existing values).
        - Skips malformed lines (logs a warning).
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"

    overridden_keys: Dict[str, str] = {}

    if not env_path.exists():
        return overridden_keys

    # Parse .env file using python-dotenv
    env_vars = dotenv_values(env_path)

    if not env_vars:
        return overridden_keys

    # Force-set keys in os.environ and track overrides
    for key, new_value in env_vars.items():
        if new_value is None or new_value == "":
            continue  # Skip None or empty values (invalid lines)
        if key in os.environ:
            overridden_keys[key] = os.environ[key]
        os.environ[key] = new_value

    return overridden_keys