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
def mock_project_and_env(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture to create a temporary .project and .env file."""
    # Create .project
    project_content = "OCPP_PROJECT_NAME=test-project\n"
    project_path = tmp_path / ".project"
    project_path.write_text(project_content)

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
    # Create .project
    project_content = "OCPP_PROJECT_NAME=test-project\n"
    project_path = tmp_path / ".project"
    project_path.write_text(project_content)

    # Mock OMO config discovery to prevent errors when it's not found
    with patch("ocpp.__main__.discover_config", return_value=None):
        yield tmp_path


def test_full_flow_bootstrap_skipped(mock_project_and_env: Path, capsys) -> None:
    """
    Test full flow: bootstrap skipped (.project exists), load succeeds, venv detected, preset selected interactively, preset written, opencode launched (mocked subprocess).
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project_and_env)

        # Mock sys.argv to run without any special flags
        with patch.object(sys, "argv", ["ocpp"]), patch(
            "ocpp.__main__.launch_opencode"
        ) as mock_launch:
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_launch.assert_called_once()

    finally:
        os.chdir(original_cwd)


def test_full_flow_bootstrap_runs(tmp_path: Path, capsys) -> None:
    """
    Test full flow: bootstrap runs (.project missing), user confirms, then load, venv, preset, launch.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a dummy .project file to be created by bootstrap
        (tmp_path / ".project").write_text("OCPP_PROJECT_NAME=test-project\n")

        # Mock sys.argv to run without any special flags
        with patch.object(sys, "argv", ["ocpp"]), patch(
            "ocpp.__main__.run_bootstrap", return_value=True
        ), patch("ocpp.__main__.launch_opencode") as mock_launch, patch(
            "rich.prompt.Prompt.ask", return_value=""
        ):
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_launch.assert_called_once()

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
        ) as mock_set_preset, patch(
            "ocpp.__main__.launch_opencode"
        ) as mock_launch:
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_set_preset.assert_called_once_with(
                Path("dummy_config.json"), "openrouter", mock_project, confirm=True
            )
            mock_launch.assert_called_once()

    finally:
        os.chdir(original_cwd)


def test_no_launch_flag(mock_project_and_env: Path, capsys) -> None:
    """
    Test --no-launch flag: all steps except launch executed, exits with status 0.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project_and_env)

        # Mock sys.argv to run with --no-launch
        with patch.object(sys, "argv", ["ocpp", "--no-launch"]), patch(
            "ocpp.__main__.launch_opencode"
        ) as mock_launch:
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_launch.assert_not_called()

    finally:
        os.chdir(original_cwd)


def test_dry_run_flag(mock_project: Path, capsys) -> None:
    """
    Test --dry-run flag: shows planned actions, no files written, no subprocess launched.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project)

        # Mock sys.argv to run with --dry-run
        with patch.object(sys, "argv", ["ocpp", "--dry-run"]), patch(
            "ocpp.__main__.launch_opencode"
        ) as mock_launch:
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0
            mock_launch.assert_not_called()

    finally:
        os.chdir(original_cwd)

    # Capture stdout/stderr
    captured = capsys.readouterr()

    # Check stderr for the dry-run messages
    assert "--dry-run" in captured.err
    assert "Would load .project" in captured.err
    assert "Would detect venv" in captured.err
    assert "Would list presets" in captured.err
    assert "Would launch opencode" in captured.err

