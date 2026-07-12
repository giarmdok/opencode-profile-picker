"""Tests for platform path resolution."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from opencode_profile_picker.config.paths import (
    get_omo_config_paths,
    get_oopps_data_dir,
    get_opencode_config_dir,
    get_opencode_executable,
    get_project_local_omo_path,
)


class TestGetOpencodeConfigDir:
    def test_returns_path_with_opencode_suffix(self) -> None:
        result = get_opencode_config_dir()
        assert result.name == "opencode"

    def test_respects_xdg_config_home(self) -> None:
        with (
            patch.object(sys, "platform", "linux"),
            patch.dict("os.environ", {"XDG_CONFIG_HOME": "/custom/config"}, clear=True),
        ):
            result = get_opencode_config_dir()
            assert result.as_posix() == "/custom/config/opencode"

    def test_windows_uses_appdata(self) -> None:
        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("os.environ", {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}, clear=True),
        ):
            result = get_opencode_config_dir()
            assert str(result) == "C:\\Users\\test\\AppData\\Roaming\\opencode"


class TestGetOoppsDataDir:
    def test_returns_path_with_oopps_suffix(self) -> None:
        result = get_oopps_data_dir()
        assert result.name == "oopps"


class TestGetOpencodeExecutable:
    def test_returns_none_when_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            result = get_opencode_executable()
            assert result is None

    def test_returns_path_when_found(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/opencode"):
            result = get_opencode_executable()
            assert result == "/usr/bin/opencode"


class TestGetOmoConfigPaths:
    def test_returns_jsonc_first(self) -> None:
        paths = get_omo_config_paths()
        assert len(paths) == 2
        assert paths[0].suffix == ".jsonc"
        assert paths[1].suffix == ".json"

    def test_paths_are_in_config_dir(self) -> None:
        paths = get_omo_config_paths()
        config_dir = get_opencode_config_dir()
        for p in paths:
            assert p.parent == config_dir


class TestGetProjectLocalOmoPath:
    def test_returns_none_when_no_opencode_dir(self, tmp_path: Path) -> None:
        result = get_project_local_omo_path(cwd=tmp_path)
        assert result is None

    def test_returns_none_when_dir_exists_but_no_config(self, tmp_path: Path) -> None:
        (tmp_path / ".opencode").mkdir()
        result = get_project_local_omo_path(cwd=tmp_path)
        assert result is None

    def test_returns_jsonc_when_exists(self, tmp_path: Path) -> None:
        (tmp_path / ".opencode").mkdir()
        jsonc = tmp_path / ".opencode" / "oh-my-opencode-slim.jsonc"
        jsonc.write_text('{"preset": "test"}')
        result = get_project_local_omo_path(cwd=tmp_path)
        assert result == jsonc

    def test_returns_json_when_jsonc_missing(self, tmp_path: Path) -> None:
        (tmp_path / ".opencode").mkdir()
        json_path = tmp_path / ".opencode" / "oh-my-opencode-slim.json"
        json_path.write_text('{"preset": "test"}')
        result = get_project_local_omo_path(cwd=tmp_path)
        assert result == json_path

    def test_prefers_jsonc_over_json(self, tmp_path: Path) -> None:
        (tmp_path / ".opencode").mkdir()
        jsonc = tmp_path / ".opencode" / "oh-my-opencode-slim.jsonc"
        jsonc.write_text('{"preset": "jsonc"}')
        json_path = tmp_path / ".opencode" / "oh-my-opencode-slim.json"
        json_path.write_text('{"preset": "json"}')
        result = get_project_local_omo_path(cwd=tmp_path)
        assert result == jsonc
