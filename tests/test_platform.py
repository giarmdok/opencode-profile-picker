"""Tests for the platform abstraction module."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from ocpp.platform import GENERIC_VENV_DIR, Platform, PlatformFamily


class TestPlatformClassification:
    """Mapping of sys.platform strings to PlatformFamily."""

    def test_win32_is_windows(self) -> None:
        p = Platform.detect(platform_string="win32")
        assert p.family is PlatformFamily.WINDOWS

    def test_linux_is_linux(self) -> None:
        p = Platform.detect(platform_string="linux")
        assert p.family is PlatformFamily.LINUX

    def test_linux2_is_linux(self) -> None:
        p = Platform.detect(platform_string="linux2")
        assert p.family is PlatformFamily.LINUX

    def test_darwin_is_unix(self) -> None:
        p = Platform.detect(platform_string="darwin")
        assert p.family is PlatformFamily.UNIX

    def test_freebsd_is_unix(self) -> None:
        p = Platform.detect(platform_string="freebsd")
        assert p.family is PlatformFamily.UNIX

    def test_unknown_is_unix(self) -> None:
        p = Platform.detect(platform_string="cygwin")
        assert p.family is PlatformFamily.UNIX


class TestVenvDirName:
    """Platform-specific venv directory names."""

    def test_windows_venv_dir(self) -> None:
        p = Platform.detect(platform_string="win32")
        assert p.venv_dir_name == ".venv_win"

    def test_linux_venv_dir(self) -> None:
        p = Platform.detect(platform_string="linux")
        assert p.venv_dir_name == ".venv_lin"

    def test_unix_venv_dir(self) -> None:
        p = Platform.detect(platform_string="darwin")
        assert p.venv_dir_name == ".venv_unx"

    def test_generic_venv_dir_constant(self) -> None:
        assert GENERIC_VENV_DIR == ".venv"


class TestVenvBinSubdir:
    """Platform-specific venv bin subdirectory."""

    def test_windows_bin_subdir(self) -> None:
        p = Platform.detect(platform_string="win32")
        assert p.venv_bin_subdir == "Scripts"

    def test_linux_bin_subdir(self) -> None:
        p = Platform.detect(platform_string="linux")
        assert p.venv_bin_subdir == "bin"

    def test_unix_bin_subdir(self) -> None:
        p = Platform.detect(platform_string="darwin")
        assert p.venv_bin_subdir == "bin"


class TestOmoConfigPaths:
    """OMO config file search-order paths."""

    def test_unix_has_two_paths(self) -> None:
        p = Platform.detect(platform_string="darwin", home_dir=Path("/home/user"))
        assert len(p.omo_config_paths) == 2

    def test_unix_json_before_jsonc(self) -> None:
        p = Platform.detect(platform_string="darwin", home_dir=Path("/home/user"))
        assert p.omo_config_paths[0] == (
            Path("/home/user/.config/opencode/oh-my-opencode-slim.json")
        )
        assert p.omo_config_paths[1] == (
            Path("/home/user/.config/opencode/oh-my-opencode-slim.jsonc")
        )

    def test_linux_has_two_paths(self) -> None:
        p = Platform.detect(platform_string="linux", home_dir=Path("/home/user"))
        assert len(p.omo_config_paths) == 2

    def test_windows_with_appdata_has_four_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APPDATA", "C:\\Users\\test\\AppData\\Roaming")
        p = Platform.detect(
            platform_string="win32",
            home_dir=Path("C:\\Users\\test"),
        )
        assert len(p.omo_config_paths) == 4
        assert p.omo_config_paths[0] == (
            Path("C:\\Users\\test/.config/opencode/oh-my-opencode-slim.json")
        )
        assert p.omo_config_paths[1] == (
            Path("C:\\Users\\test/.config/opencode/oh-my-opencode-slim.jsonc")
        )
        assert p.omo_config_paths[2] == (
            Path("C:\\Users\\test\\AppData\\Roaming/opencode/oh-my-opencode-slim.json")
        )
        assert p.omo_config_paths[3] == (
            Path("C:\\Users\\test\\AppData\\Roaming/opencode/oh-my-opencode-slim.jsonc")
        )

    def test_windows_without_appdata_has_two_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("APPDATA", raising=False)
        p = Platform.detect(
            platform_string="win32",
            home_dir=Path("C:\\Users\\test"),
        )
        assert len(p.omo_config_paths) == 2
        assert p.omo_config_paths[0] == (
            Path("C:\\Users\\test/.config/opencode/oh-my-opencode-slim.json")
        )
        assert p.omo_config_paths[1] == (
            Path("C:\\Users\\test/.config/opencode/oh-my-opencode-slim.jsonc")
        )


class TestInjectablePlatform:
    """Override platform_string and home_dir for testing."""

    def test_override_platform_string(self) -> None:
        p = Platform.detect(platform_string="win32", home_dir=Path("/linux/home"))
        assert p.family is PlatformFamily.WINDOWS
        assert p.venv_dir_name == ".venv_win"
        assert p.venv_bin_subdir == "Scripts"

    def test_override_home_dir(self) -> None:
        p = Platform.detect(
            platform_string="darwin",
            home_dir=Path("/fake/home"),
        )
        assert p.omo_config_paths[0] == (
            Path("/fake/home/.config/opencode/oh-my-opencode-slim.json")
        )
        assert p.omo_config_paths[1] == (
            Path("/fake/home/.config/opencode/oh-my-opencode-slim.jsonc")
        )


class TestDirectConstruction:
    """Construct Platform directly with explicit fields."""

    def test_direct_construction(self) -> None:
        p = Platform(
            family=PlatformFamily.LINUX,
            venv_dir_name=".venv_custom",
            venv_bin_subdir="custom_bin",
            omo_config_paths=[Path("/a/b.json")],
            project_root=Path("/project"),
        )
        assert p.family is PlatformFamily.LINUX
        assert p.venv_dir_name == ".venv_custom"
        assert p.venv_bin_subdir == "custom_bin"
        assert p.omo_config_paths == [Path("/a/b.json")]
        assert p.project_root == Path("/project")


class TestFrozenDataclass:
    """Verify that Platform instances are immutable."""

    def test_cannot_mutate_family(self) -> None:
        p = Platform.detect(platform_string="linux")
        with pytest.raises(FrozenInstanceError):
            p.family = PlatformFamily.WINDOWS  # type: ignore[misc]

    def test_cannot_mutate_venv_dir_name(self) -> None:
        p = Platform.detect(platform_string="linux")
        with pytest.raises(FrozenInstanceError):
            p.venv_dir_name = ".venv_other"  # type: ignore[misc]

    def test_cannot_mutate_omo_config_paths(self) -> None:
        p = Platform.detect(platform_string="linux")
        with pytest.raises(FrozenInstanceError):
            p.omo_config_paths = []  # type: ignore[misc]
