"""
Integration tests for src/ocpp/__main__.py (CLI).
"""
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from ocpp.__main__ import main


@pytest.fixture
def mock_project_and_env(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture to create a temporary .project and .env file."""
    # Create .project
    project_content = "OCPP_PROJECT_NAME=test-project\n"
    project_content += "OPENAI_API_KEY=test-openai-key-from-project\n"
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


def test_main_loads_env_file_and_overrides_project(
    mock_project_and_env: Path, capsys
) -> None:
    """
    Test that when a .env file is present, its values are loaded and emitted,
    and OMO preset selection is skipped.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project_and_env)

        # Mock sys.argv to run without any special flags
        with patch.object(sys, "argv", ["ocpp"]):
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0

    finally:
        os.chdir(original_cwd)

    # Capture stdout/stderr
    captured = capsys.readouterr()

    # Check stderr for the warning about skipping OMO presets
    assert "Found .env file" in captured.err
    assert "OMO preset selection will be skipped" in captured.err

    # Check stdout for the correct shell commands
    # This test runs on a single platform, so we check for either syntax.
    if sys.platform == "win32":
        assert '$Env:OPENAI_API_KEY="test-openai-key-from-env"' in captured.out
        assert '$Env:ANTHROPIC_API_KEY="test-anthropic-key-from-env"' in captured.out
        assert '$Env:OCPP_PROJECT_NAME="test-project"' in captured.out
    else:
        assert "export OPENAI_API_KEY='test-openai-key-from-env'" in captured.out
        assert "export ANTHROPIC_API_KEY='test-anthropic-key-from-env'" in captured.out
        assert "export OCPP_PROJECT_NAME='test-project'" in captured.out


def test_main_logs_overridden_keys(mock_project_and_env: Path, capsys) -> None:
    """
    Test that when a .env file overrides a .project file, the overridden keys are logged.
    """
    # Change working directory to the temp directory
    original_cwd = Path.cwd()
    try:
        os.chdir(mock_project_and_env)

        # Mock sys.argv to run without any special flags
        with patch.object(sys, "argv", ["ocpp"]):
            # Call main() and expect it to succeed (exit code 0)
            exit_code = main()
            assert exit_code == 0

    finally:
        os.chdir(original_cwd)

    # Capture stdout/stderr
    captured = capsys.readouterr()

    # Check stderr for the warning about overridden keys
    assert "Overriding" in captured.err
    assert "OPENAI_API_KEY" in captured.err
    assert "test...ject" in captured.err
    assert "test...-env" in captured.err
