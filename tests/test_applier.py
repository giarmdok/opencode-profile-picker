"""Tests for preset application."""

from __future__ import annotations

import json
from pathlib import Path

from opencode_profile_picker.presets.applier import (
    apply_preset,
    get_active_preset,
    is_preset_already_active,
)


class TestGetActivePreset:
    def test_reads_active_preset(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"preset": "or", "other": "data"}')
        assert get_active_preset(path) == "or"

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        assert get_active_preset(tmp_path / "nonexistent.json") is None

    def test_returns_none_for_malformed_file(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        assert get_active_preset(path) is None

    def test_returns_none_when_no_preset_field(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"other": "data"}')
        assert get_active_preset(path) is None


class TestApplyPreset:
    def test_changes_preset_field(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"preset": "or", "other": "data"}')
        result = apply_preset(path, "go")
        assert result.success is True
        assert result.previous_preset == "or"

        data = json.loads(path.read_text())
        assert data["preset"] == "go"
        assert data["other"] == "data"

    def test_preserves_other_fields(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        original = {
            "preset": "or",
            "presets": {"go": {"orchestrator": {"model": "google/gemini"}}},
            "council": {"enabled": True},
            "companion": {"position": "right"},
        }
        path.write_text(json.dumps(original))
        apply_preset(path, "go")

        data = json.loads(path.read_text())
        assert data["presets"] == original["presets"]
        assert data["council"] == original["council"]
        assert data["companion"] == original["companion"]

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        result = apply_preset(tmp_path / "nonexistent.json", "go")
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_handles_malformed_file(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid!!!")
        result = apply_preset(path, "go")
        assert result.success is False

    def test_noop_when_same_preset(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"preset": "or"}')
        result = apply_preset(path, "or")
        assert result.success is True
        assert result.previous_preset == "or"


class TestIsPresetAlreadyActive:
    def test_true_when_same(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"preset": "or"}')
        assert is_preset_already_active(path, "or") is True

    def test_false_when_different(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text('{"preset": "or"}')
        assert is_preset_already_active(path, "go") is False

    def test_false_when_no_file(self, tmp_path: Path) -> None:
        assert is_preset_already_active(tmp_path / "nonexistent.json", "or") is False
