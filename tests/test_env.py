"""
Unit tests for src/ocpp/env.py.
"""
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import pytest

from ocpp.env import load_env_file


@pytest.fixture(autouse=True)
def clear_env():
    """Fixture to clear os.environ before each test."""
    original_env = os.environ.copy()
    os.environ.clear()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_env_file():
    """Fixture to create a temporary .env file and clean up afterward."""
    env_content = """
    # Test .env file
    OPENAI_API_KEY=test-openai-key
    ANTHROPIC_API_KEY=test-anthropic-key
    INVALID_LINE=
    # Comment
    EMPTY_VALUE=
    """
    with NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        f.flush()
        env_path = Path(f.name)
    yield env_path
    env_path.unlink(missing_ok=True)


def test_load_env_file_valid(temp_env_file: Path) -> None:
    """Test parsing a valid .env file."""
    # Set up existing environment variables
    os.environ["OPENAI_API_KEY"] = "old-openai-key"
    os.environ["UNRELATED_KEY"] = "unchanged"

    # Call load_env_file
    overridden_keys = load_env_file(temp_env_file)

    # Assert overrides
    assert overridden_keys == {"OPENAI_API_KEY": "old-openai-key"}
    assert os.environ["OPENAI_API_KEY"] == "test-openai-key"
    assert os.environ["ANTHROPIC_API_KEY"] == "test-anthropic-key"
    assert os.environ["UNRELATED_KEY"] == "unchanged"
    assert "INVALID_LINE" not in os.environ  # Skipped because value is empty
    assert "EMPTY_VALUE" not in os.environ  # Skipped because value is empty


def test_load_env_file_missing() -> None:
    """Test behavior when .env file is missing."""
    overridden_keys = load_env_file(Path("nonexistent.env"))
    assert overridden_keys == {}


def test_load_env_file_empty() -> None:
    """Test behavior when .env file is empty."""
    with NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.flush()
        env_path = Path(f.name)
    
    overridden_keys = load_env_file(env_path)
    assert overridden_keys == {}
    env_path.unlink()


def test_load_env_file_empty_values() -> None:
    """Test behavior when .env file contains empty values."""
    env_content = """
    KEY_WITH_EMPTY=
    """
    with NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        f.flush()
        env_path = Path(f.name)
    
    overridden_keys = load_env_file(env_path)
    assert overridden_keys == {}
    assert "KEY_WITH_EMPTY" not in os.environ  # Skipped because value is empty
    env_path.unlink()