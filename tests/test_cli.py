"""
Integration tests for src/ocpp/__main__.py (CLI).
"""
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from rich.console import Console

from ocpp.__main__ import main


# Mock run_bootstrap to avoid interactive prompts
@pytest.fixture(autouse=True)
def mock_bootstrap():
    with patch("ocpp.__main__.run_bootstrap", return_value=True):
        yield


@pytest.fixture
def temp_env_file(tmp_path):
    """Fixture to create a temporary .env file and clean up afterward."""
    env_content = """
    # Test .env file
    OPENAI_API_KEY=test-openai-key
    ANTHROPIC_API_KEY=test-anthropic-key
    """
    env_path = tmp_path / ".env"
    env_path.write_text(env_content)
    yield env_path


def test_main_loads_env_file(temp_env_file, capsys) -> None:
    """Test that load_env_file() is called at the start of main()."""
    # Set up existing environment variables
    os.environ["OPENAI_API_KEY"] = "old-openai-key"
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
    os.environ["UNRELATED_KEY"] = "unchanged"

    # Mock sys.argv to include --no-launch and --init to skip .project checks
    with patch("sys.argv", ["ocpp", "--no-launch", "--init"]):
        # Change working directory to the temp_env_file's parent
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_env_file.parent)
            # Call main()
            main()
        finally:
            os.chdir(original_cwd)

    # Capture stdout/stderr
    captured = capsys.readouterr()
    assert "old-openai-key" not in captured.out
    assert "test-openai-key" in captured.out
    assert "unchanged" in os.environ["UNRELATED_KEY"]