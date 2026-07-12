"""Shared test fixtures and configuration."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_omo_config() -> dict[str, Any]:
    """Return a sample oh-my-opencode-slim config dict."""
    return {
        "preset": "or",
        "presets": {
            "or": {
                "orchestrator": {
                    "model": "openrouter/deepseek/deepseek-v4-pro",
                    "variant": "medium",
                    "skills": ["*"],
                    "mcps": ["*"],
                },
                "oracle": {
                    "model": "openrouter/deepseek/deepseek-v4-pro",
                    "variant": "high",
                },
                "librarian": {
                    "model": "openrouter/qwen/qwen3.6-35b-a3b",
                    "mcps": ["websearch", "context7"],
                },
            },
            "go": {
                "orchestrator": {
                    "model": "google/gemini-3.5-flash",
                    "variant": "low",
                    "skills": ["*"],
                    "mcps": ["*"],
                },
                "oracle": {
                    "model": "google/gemini-2.5-pro",
                    "variant": "high",
                },
            },
            "gm": {
                "orchestrator": {
                    "model": "google/gemini-3.5-flash",
                    "variant": "low",
                },
                "fixer": {
                    "model": "mistral/mistral-small-latest",
                    "variant": "low",
                },
            },
        },
        "council": {
            "presets": {
                "diverse": {
                    "openai_rep": {"model": "openai/gpt-5.6-sol"},
                    "anthropic_rep": {"model": "anthropic/claude-opus-4-8"},
                }
            }
        },
    }


@pytest.fixture
def sample_omo_config_path(temp_dir: Path, sample_omo_config: dict[str, Any]) -> Path:
    """Write sample OMO config to a temp file and return the path."""
    path = temp_dir / "oh-my-opencode-slim.json"
    path.write_text(json.dumps(sample_omo_config, indent=2))
    return path
