"""
Integration tests for the full CLI flow.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from ocpp.__main__ import main


@pytest.fixture
def mock_env(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture to create a temporary .env file."""
    # Create .env
    env_content = """
    # Test .env file
    OPENAI_API_KEY=test-openai-key-from-env
    ANTHROPIC_API_KEY=test-anthropic-key-from-env
    """
    env_path = tmp_path / ".env"
    env_path.write_text(env_content)

    # Mock OMO config discovery to prevent errors when it's not found
    with patch("ocpp.__main__.discover_config", return_value=None):
        yield tmp_path


@pytest.fixture
def mock_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture to create a temporary .project file."""
    # Mock OMO config discovery to prevent errors when it's not found
    with patch("ocpp.__main__.discover_config", return_value=None):
        yield tmp_path


def test_full_flow(mock_env: Path, capsys) -> None:
    """
    Test the full simplified flow.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_env)

        # Mock sys.argv to run without any special flags
        with patch.object(sys, "argv", ["ocpp"]), patch(
            "rich.prompt.Prompt.ask", return_value=""
        ):
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0

    finally:
        os.chdir(original_cwd)


def test_preset_flag_valid(mock_project: Path, capsys) -> None:
    """
    Test --preset flag: non-interactive preset selection, valid name.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project)

        # Mock sys.argv to run with --preset
        with patch.object(
            sys, "argv", ["ocpp", "--preset", "openrouter"]
        ), patch(
            "ocpp.__main__.discover_config", return_value=Path("dummy_config.json")
        ), patch(
            "ocpp.__main__.list_presets",
            return_value=(
                "default",
                [
                    type("PresetInfo", (), {"name": "openrouter", "is_current": False})(),
                ],
            ),
        ), patch(
            "ocpp.__main__.omo_set_preset"
        ) as mock_set_preset:
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_set_preset.assert_called_once_with(
                Path("dummy_config.json"), "openrouter", mock_project, confirm=True
            )

    finally:
        os.chdir(original_cwd)


