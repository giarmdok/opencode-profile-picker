"""Tests for config discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from opencode_profile_picker.config.discover import (
    PROVIDER_KEY_MAP,
    detect_project_local_override,
    discover_omo_config,
    extract_presets,
    extract_providers_from_preset,
    map_presets_to_keys,
)
from opencode_profile_picker.config.parser import read_jsonc, write_json


class TestReadJsonc:
    def test_reads_valid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        path.write_text('{"key": "value"}')
        result = read_jsonc(path)
        assert result == {"key": "value"}

    def test_reads_jsonc_with_comments(self, tmp_path: Path) -> None:
        path = tmp_path / "test.jsonc"
        path.write_text('{\n  // comment\n  "key": "value"\n}')
        result = read_jsonc(path)
        assert result == {"key": "value"}

    def test_reads_jsonc_with_trailing_commas(self, tmp_path: Path) -> None:
        path = tmp_path / "test.jsonc"
        path.write_text('{"a": 1, "b": 2,}')
        result = read_jsonc(path)
        assert result == {"a": 1, "b": 2}

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        result = read_jsonc(tmp_path / "nonexistent.json")
        assert result is None

    def test_returns_none_for_malformed_json(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        result = read_jsonc(path)
        assert result is None


class TestWriteJson:
    def test_writes_valid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "out.json"
        result = write_json(path, {"key": "value"})
        assert result is True
        assert path.exists()
        assert json.loads(path.read_text()) == {"key": "value"}

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / "out.json"
        result = write_json(path, {"a": 1})
        assert result is True
        assert path.exists()


class TestExtractPresets:
    def test_extracts_preset_names(self, sample_omo_config: dict[str, Any]) -> None:
        presets = extract_presets(sample_omo_config)
        assert set(presets) == {"or", "go", "gm"}

    def test_returns_empty_for_no_presets(self) -> None:
        assert extract_presets({}) == []
        assert extract_presets({"presets": None}) == []  # type: ignore[dict-item]


class TestExtractProvidersFromPreset:
    def test_single_provider_preset(self, sample_omo_config: dict[str, Any]) -> None:
        providers = extract_providers_from_preset(sample_omo_config, "go")
        # "go" uses google, plus global council uses openai + anthropic
        assert "google" in providers
        assert "openai" in providers
        assert "anthropic" in providers

    def test_multi_provider_preset(self, sample_omo_config: dict[str, Any]) -> None:
        providers = extract_providers_from_preset(sample_omo_config, "gm")
        # "gm" uses google + mistral, plus global council uses openai + anthropic
        assert "google" in providers
        assert "mistral" in providers
        assert "openai" in providers
        assert "anthropic" in providers

    def test_includes_council_providers(self, sample_omo_config: dict[str, Any]) -> None:
        providers = extract_providers_from_preset(sample_omo_config, "or")
        assert "openrouter" in providers
        assert "openai" in providers
        assert "anthropic" in providers

    def test_unknown_preset_returns_empty(self, sample_omo_config: dict[str, Any]) -> None:
        providers = extract_providers_from_preset(sample_omo_config, "nonexistent")
        assert providers == set()


class TestMapPresetsToKeys:
    def test_maps_presets_to_env_vars(self, sample_omo_config: dict[str, Any]) -> None:
        result = map_presets_to_keys(sample_omo_config)
        assert "or" in result
        assert "OPENROUTER_API_KEY" in result["or"]
        assert "OPENAI_API_KEY" in result["or"]
        assert "ANTHROPIC_API_KEY" in result["or"]
        assert "go" in result
        assert "GOOGLE_API_KEY" in result["go"]
        # Council providers (openai, anthropic) are global and apply to all presets
        assert "OPENAI_API_KEY" in result["go"]
        assert "ANTHROPIC_API_KEY" in result["go"]
        assert "gm" in result
        assert "GOOGLE_API_KEY" in result["gm"]
        assert "MISTRAL_API_KEY" in result["gm"]


class TestProviderKeyMap:
    def test_has_expected_entries(self) -> None:
        assert PROVIDER_KEY_MAP["openai"] == "OPENAI_API_KEY"
        assert PROVIDER_KEY_MAP["anthropic"] == "ANTHROPIC_API_KEY"
        assert PROVIDER_KEY_MAP["google"] == "GOOGLE_API_KEY"
        assert PROVIDER_KEY_MAP["openrouter"] == "OPENROUTER_API_KEY"


class TestDiscoverOmoConfig:
    def test_discovers_valid_config(
        self, tmp_path: Path, sample_omo_config: dict[str, Any]
    ) -> None:
        config_path = tmp_path / "oh-my-opencode-slim.json"
        config_path.write_text(json.dumps(sample_omo_config))

        with (
            patch(
                "opencode_profile_picker.config.discover.get_omo_config_paths",
                return_value=[config_path],
            ),
            patch(
                "opencode_profile_picker.config.discover.get_project_local_omo_path",
                return_value=None,
            ),
        ):
            result = discover_omo_config()
            assert result.config_path == config_path
            assert result.active_preset == "or"
            assert "or" in result.presets
            assert result.error is None

    def test_handles_missing_config(self) -> None:
        with patch(
            "opencode_profile_picker.config.discover.get_omo_config_paths",
            return_value=[Path("/nonexistent/path.json")],
        ):
            result = discover_omo_config()
            assert result.config_path is None
            assert result.error is not None

    def test_handles_malformed_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "oh-my-opencode-slim.json"
        config_path.write_text("{invalid json!!!")

        with patch(
            "opencode_profile_picker.config.discover.get_omo_config_paths",
            return_value=[config_path],
        ):
            result = discover_omo_config()
            assert result.error is not None


class TestDetectProjectLocalOverride:
    def test_returns_none_when_no_override(self, tmp_path: Path) -> None:
        result = detect_project_local_override(cwd=tmp_path)
        assert result is None

    def test_detects_override(self, tmp_path: Path) -> None:
        (tmp_path / ".opencode").mkdir()
        (tmp_path / ".opencode" / "oh-my-opencode-slim.json").write_text('{"preset": "custom"}')
        result = detect_project_local_override(cwd=tmp_path)
        assert result == "custom"
