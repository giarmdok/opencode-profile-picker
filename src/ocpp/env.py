"""
.env file parser for opencode-profile-picker.

This module provides functionality to parse a .env file and return its contents
as a dictionary.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values


def load_dotenv_file(env_path: Path) -> dict[str, str | None]:
    """
    Parse a .env file and return its contents as a dictionary.

    Args:
        env_path: The path to the .env file.

    Returns:
        A dictionary of key-value pairs from the .env file.
        Returns an empty dictionary if the file does not exist or is empty.
    """
    if not env_path.is_file():
        return {}

    # Parse .env file using python-dotenv
    # It gracefully handles non-existent files, but we check above for clarity.
    # It returns an OrderedDict, but we can treat it as a Dict.
    # Values can be None if a key is present without a value.
    return dotenv_values(env_path)


def load_env_file(
    project_root: Path,
) -> dict[str, str | None]:
    """
    Load environment variables from a .env file in the project root.

    Args:
        project_root: The root directory of the project.

    Returns:
        A dictionary of key-value pairs from the .env file.
        Returns an empty dictionary if the file does not exist or is empty.
    """
    env_path = project_root / ".env"
    return load_dotenv_file(env_path)
