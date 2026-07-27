"""
Tests for the .env file parser.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from ocpp.env import load_dotenv_file


def test_load_dotenv_file_valid(tmp_path: Path):
    """
    Test load_dotenv_file with a valid .env file.
    """
    env_content = textwrap.dedent(
        """
        KEY1=VALUE1
        KEY2="VALUE2"
        # This is a comment
        KEY3='VALUE3'
        """
    )
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)

    result = load_dotenv_file(env_file)

    assert result == {"KEY1": "VALUE1", "KEY2": "VALUE2", "KEY3": "VALUE3"}


def test_load_dotenv_file_invalid(tmp_path: Path):
    """
    Test load_dotenv_file with an invalid .env file.
    python-dotenv is very lenient, so "invalid" means lines that are not key-value pairs.
    """
    env_content = textwrap.dedent(
        """
        INVALID_LINE
        KEY1=VALUE1
        """
    )
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)

    result = load_dotenv_file(env_file)

    assert result == {"INVALID_LINE": None, "KEY1": "VALUE1"}


def test_load_dotenv_file_not_found(tmp_path: Path):
    """
    Test load_dotenv_file when the .env file is not found.
    """
    env_file = tmp_path / ".env"

    result = load_dotenv_file(env_file)

    assert result == {}


def test_load_dotenv_file_empty(tmp_path: Path):
    """
    Test load_dotenv_file with an empty .env file.
    """
    env_file = tmp_path / ".env"
    env_file.touch()

    result = load_dotenv_file(env_file)

    assert result == {}

