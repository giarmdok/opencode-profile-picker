"""Tests for the OMO config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from ocpp.omo import (
    LOCAL_OMO_DIR,
    LOCAL_OMO_FILENAME,
    OmoError,
    PresetInfo,
    discover_config,
    discover_local_config,
    get_local_config_path,
    list_presets,
    parse_config,
    set_preset,
)
from ocpp.platform import Platform, PlatformFamily

SAMPLE_CONFIG = """{
  // OMO config
  "preset": "openrouter",
  "presets": {
    "openrouter": {"orchestrator": {"model": "openrouter/glm-5.2"}},
    "anthropic": {"orchestrator": {"model": "anthropic/claude"}}
  }
}"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_config(tmp_path: Path, content: str, filename: str = "oh-my-opencode-slim.json") -> Path:
    """Write a config file and return its path."""
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _platform(tmp_path: Path, filename: str = "oh-my-opencode-slim.json") -> Platform:
    """Build a Platform whose omo_config_paths points into tmp_path."""
    return Platform(
        family=PlatformFamily.LINUX,
        venv_dir_name=".venv_lin",
        venv_bin_subdir="bin",
        omo_config_paths=[tmp_path / filename],
        project_root=tmp_path,
    )


def _local_config_path(project_root: Path) -> Path:
    """Return the expected local override path for a given project root."""
    return project_root / LOCAL_OMO_DIR / LOCAL_OMO_FILENAME


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


class TestDiscoverConfig:
    def test_json_file_found(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        platform = _platform(tmp_path)
        result = discover_config(platform)
        assert result == config_path

    def test_jsonc_file_found(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG, filename="oh-my-opencode-slim.jsonc")
        platform = _platform(tmp_path, filename="oh-my-opencode-slim.jsonc")
        result = discover_config(platform)
        assert result == config_path

    def test_no_config_found(self, tmp_path: Path) -> None:
        platform = _platform(tmp_path)
        with pytest.raises(FileNotFoundError) as excinfo:
            discover_config(platform)
        assert str(tmp_path / "oh-my-opencode-slim.json") in str(excinfo.value)

    def test_error_message_lists_searched_paths(self, tmp_path: Path) -> None:
        platform = Platform(
            family=PlatformFamily.LINUX,
            venv_dir_name=".venv_lin",
            venv_bin_subdir="bin",
            omo_config_paths=[tmp_path / "a.json", tmp_path / "b.jsonc"],
            project_root=tmp_path,
        )
        with pytest.raises(FileNotFoundError) as excinfo:
            discover_config(platform)
        msg = str(excinfo.value)
        assert str(tmp_path / "a.json") in msg
        assert str(tmp_path / "b.jsonc") in msg


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class TestParseConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        data = parse_config(config_path)
        assert data["preset"] == "openrouter"
        assert "openrouter" in data["presets"]
        assert "anthropic" in data["presets"]

    def test_malformed_jsonc_raises_value_error(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, "{invalid: jsonc,}")
        with pytest.raises(ValueError, match="Failed to parse OMO config"):
            parse_config(config_path)

    def test_missing_preset_field(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '{"presets": {}}')
        with pytest.raises(OmoError, match="missing top-level 'preset' field"):
            parse_config(config_path)

    def test_missing_presets_field(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '{"preset": "openrouter"}')
        with pytest.raises(OmoError, match="missing top-level 'presets' field"):
            parse_config(config_path)

    def test_preset_wrong_type(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '{"preset": 42, "presets": {}}')
        with pytest.raises(OmoError, match="'preset' must be a string"):
            parse_config(config_path)

    def test_presets_wrong_type(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '{"preset": "a", "presets": []}')
        with pytest.raises(OmoError, match="'presets' must be an object"):
            parse_config(config_path)

    def test_top_level_not_dict(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '"just a string"')
        with pytest.raises(OmoError, match="expected a top-level object"):
            parse_config(config_path)

    def test_malformed_config_error_includes_file_path(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, "{broken")
        with pytest.raises(ValueError) as excinfo:
            parse_config(config_path)
        assert str(config_path) in str(excinfo.value)


# ---------------------------------------------------------------------------
# Preset listing
# ---------------------------------------------------------------------------


class TestListPresets:
    def test_multiple_presets_listed(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        current, infos = list_presets(config_path)
        assert current == "openrouter"
        assert len(infos) == 2
        names = {i.name for i in infos}
        assert names == {"openrouter", "anthropic"}

    def test_current_preset_marked(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        _, infos = list_presets(config_path)
        for info in infos:
            if info.name == "openrouter":
                assert info.is_current is True
            else:
                assert info.is_current is False

    def test_current_preset_not_in_presets_dict(self, tmp_path: Path) -> None:
        config = """{
          "preset": "missing-preset",
          "presets": {
            "openrouter": {}
          }
        }"""
        config_path = _write_config(tmp_path, config)
        current, infos = list_presets(config_path)
        assert current == "missing-preset"
        names = {i.name for i in infos}
        assert names == {"openrouter", "missing-preset"}
        for info in infos:
            if info.name == "missing-preset":
                assert info.is_current is True

    def test_empty_presets_dict(self, tmp_path: Path) -> None:
        config = '{"preset": "none", "presets": {}}'
        config_path = _write_config(tmp_path, config)
        current, infos = list_presets(config_path)
        assert current == "none"
        assert len(infos) == 1
        assert infos[0] == PresetInfo(name="none", is_current=True)


# ---------------------------------------------------------------------------
# Local config path helpers
# ---------------------------------------------------------------------------


class TestGetLocalConfigPath:
    def test_local_config_path_correct(self, tmp_path: Path) -> None:
        expected = tmp_path / ".opencode" / "oh-my-opencode-slim.jsonc"
        result = get_local_config_path(tmp_path)
        assert result == expected


class TestDiscoverLocalConfig:
    def test_discover_local_config_none(self, tmp_path: Path) -> None:
        assert discover_local_config(tmp_path) is None

    def test_discover_local_config_exists(self, tmp_path: Path) -> None:
        local_path = _local_config_path(tmp_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(SAMPLE_CONFIG, encoding="utf-8")
        result = discover_local_config(tmp_path)
        assert result == local_path


# ---------------------------------------------------------------------------
# Surgical write
# ---------------------------------------------------------------------------


class TestSetPresetSurgical:
    def test_preset_value_changed(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        result = set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        assert result is True
        # Local file should have the new preset
        local_path = _local_config_path(tmp_path)
        assert local_path.exists()
        updated = local_path.read_text(encoding="utf-8")
        assert '"preset": "anthropic"' in updated
        # Comments preserved in local copy
        assert "// OMO config" in updated
        # Global config unchanged
        global_content = config_path.read_text(encoding="utf-8")
        assert '"preset": "openrouter"' in global_content

    def test_comments_preserved(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        local_path = _local_config_path(tmp_path)
        updated = local_path.read_text(encoding="utf-8")
        assert "// OMO config" in updated

    def test_formatting_preserved(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        original = config_path.read_text(encoding="utf-8")
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        local_path = _local_config_path(tmp_path)
        updated = local_path.read_text(encoding="utf-8")
        # The only change should be the preset value line
        original_lines = original.splitlines()
        updated_lines = updated.splitlines()
        assert len(original_lines) == len(updated_lines)
        for o_line, u_line in zip(original_lines, updated_lines, strict=True):
            if '"preset":' in o_line and '"presets"' not in o_line:
                assert '"preset": "anthropic"' in u_line
            else:
                assert o_line == u_line

    def test_trailing_comma_preserved(self, tmp_path: Path) -> None:
        config = """{
          "preset": "openrouter",
          "presets": {
            "openrouter": {},
            "anthropic": {},
          },
        }"""
        config_path = _write_config(tmp_path, config)
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        local_path = _local_config_path(tmp_path)
        updated = local_path.read_text(encoding="utf-8")
        assert '"preset": "anthropic"' in updated
        # Trailing commas should still be there
        assert '"anthropic": {},' in updated or '"anthropic": {},\n' in updated

    def test_bak_backup_created(self, tmp_path: Path) -> None:
        """When a local override already exists, a .bak backup is created."""
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        local_path = _local_config_path(tmp_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        # Write an existing local override with a different preset
        local_config = SAMPLE_CONFIG.replace('"preset": "openrouter"', '"preset": "anthropic"')
        local_path.write_text(local_config, encoding="utf-8")
        # Now call set_preset with a third preset
        set_preset(config_path, "openrouter", project_root=tmp_path, confirm=False)
        # Verify .bak was created from the pre-existing local override
        bak_path = local_path.with_suffix(local_path.suffix + ".bak")
        assert bak_path.exists()
        bak_content = bak_path.read_text(encoding="utf-8")
        assert '"preset": "anthropic"' in bak_content
        # Local file should now have the new preset
        assert '"preset": "openrouter"' in local_path.read_text(encoding="utf-8")

    def test_no_bak_when_no_local_exists(self, tmp_path: Path) -> None:
        """When no local override exists, no .bak is created."""
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        local_path = _local_config_path(tmp_path)
        bak_path = local_path.with_suffix(local_path.suffix + ".bak")
        assert not bak_path.exists()

    def test_atomic_write(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        local_path = _local_config_path(tmp_path)
        # Verify final content is correct
        data = parse_config(local_path)
        assert data["preset"] == "anthropic"

    def test_global_config_unchanged(self, tmp_path: Path) -> None:
        """Verify the global config file is not modified after set_preset."""
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        original_content = config_path.read_text(encoding="utf-8")
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        # Global config should be byte-for-byte identical
        assert config_path.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# Regex fallback
# ---------------------------------------------------------------------------


class TestSetPresetFallback:
    def test_fallback_re_serialize(self, tmp_path: Path) -> None:
        """When regex doesn't match, fall back to json5.dumps()."""
        # Unusual formatting: preset on same line as opening brace, no quotes
        config = '{preset:"openrouter",presets:{openrouter:{},anthropic:{}}}'
        config_path = _write_config(tmp_path, config)
        result = set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        assert result is True
        local_path = _local_config_path(tmp_path)
        updated = local_path.read_text(encoding="utf-8")
        # After re-serialization, comments are lost but preset should be updated
        assert "anthropic" in updated
        # Global config should still have the original preset
        assert config_path.read_text(encoding="utf-8") == config


# ---------------------------------------------------------------------------
# User confirmation
# ---------------------------------------------------------------------------


class TestSetPresetConfirmation:
    def test_affirmative_proceeds(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "y")
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        result = set_preset(config_path, "anthropic", project_root=tmp_path, confirm=True)
        assert result is True
        local_path = _local_config_path(tmp_path)
        assert local_path.exists()
        data = parse_config(local_path)
        assert data["preset"] == "anthropic"
        # Global config unchanged
        assert parse_config(config_path)["preset"] == "openrouter"

    def test_negative_aborts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "n")
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        result = set_preset(config_path, "anthropic", project_root=tmp_path, confirm=True)
        assert result is False
        # No local file should be created
        local_path = _local_config_path(tmp_path)
        assert not local_path.exists()
        # Global config unchanged
        assert parse_config(config_path)["preset"] == "openrouter"

    def test_yes_also_works(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        result = set_preset(config_path, "anthropic", project_root=tmp_path, confirm=True)
        assert result is True
        local_path = _local_config_path(tmp_path)
        assert local_path.exists()
        data = parse_config(local_path)
        assert data["preset"] == "anthropic"
        # Global config unchanged
        assert parse_config(config_path)["preset"] == "openrouter"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestSetPresetErrors:
    def test_preset_not_in_presets(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        with pytest.raises(OmoError, match="not found in presets"):
            set_preset(config_path, "nonexistent", project_root=tmp_path, confirm=False)

    def test_missing_config_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------


class TestOpenCodeDirCreated:
    def test_opencode_dir_created(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        local_path = _local_config_path(tmp_path)
        assert not local_path.parent.exists()  # .opencode/ dir does not exist yet
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        assert local_path.parent.exists()
        assert local_path.parent.is_dir()


# ---------------------------------------------------------------------------
# Global config safety
# ---------------------------------------------------------------------------


class TestGlobalConfigSafety:
    def test_global_config_unchanged(self, tmp_path: Path) -> None:
        """Verify global config file content is identical before and after set_preset."""
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        original_content = config_path.read_text(encoding="utf-8")
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        assert config_path.read_text(encoding="utf-8") == original_content

    def test_no_global_bak(self, tmp_path: Path) -> None:
        """Verify no .bak file is created for the global config."""
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        set_preset(config_path, "anthropic", project_root=tmp_path, confirm=False)
        # Check there's no .bak next to the global config
        global_bak = config_path.with_suffix(config_path.suffix + ".bak")
        assert not global_bak.exists()
