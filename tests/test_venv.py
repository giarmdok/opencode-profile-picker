"""Tests for the venv detection module."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest

from ocpp.platform import GENERIC_VENV_DIR, Platform, PlatformFamily
from ocpp.venv import (
    VenvResult,
    compute_venv_env_delta,
    detect_venv,
    find_venv,
    validate_venv,
)


def make_platform(
    tmp_path: Path,
    family: PlatformFamily = PlatformFamily.WINDOWS,
) -> Platform:
    """Build a Platform with project_root pointing at tmp_path."""
    p = Platform.detect(
        platform_string={
            PlatformFamily.WINDOWS: "win32",
            PlatformFamily.LINUX: "linux",
            PlatformFamily.UNIX: "darwin",
        }[family],
        home_dir=tmp_path,
    )
    return dataclasses.replace(p, project_root=tmp_path)


def _create_venv(
    root: Path,
    dir_name: str,
    bin_subdir: str,
    family: PlatformFamily = PlatformFamily.WINDOWS,
) -> Path:
    """Create a fake venv directory with a dummy interpreter."""
    venv_dir = root / dir_name
    bin_dir = venv_dir / bin_subdir
    bin_dir.mkdir(parents=True)
    interpreter = "python.exe" if family is PlatformFamily.WINDOWS else "python"
    (bin_dir / interpreter).touch()
    return venv_dir


class TestFindVenv:
    """Search order and existence checks."""

    def test_find_venv_win(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        result = find_venv(platform)
        assert result == tmp_path / ".venv_win"

    def test_find_venv_lin(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.LINUX)
        _create_venv(tmp_path, ".venv_lin", "bin", PlatformFamily.LINUX)
        result = find_venv(platform)
        assert result == tmp_path / ".venv_lin"

    def test_find_venv_unx(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.UNIX)
        _create_venv(tmp_path, ".venv_unx", "bin", PlatformFamily.UNIX)
        result = find_venv(platform)
        assert result == tmp_path / ".venv_unx"

    def test_fallback_to_generic_venv(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        _create_venv(tmp_path, GENERIC_VENV_DIR, "Scripts", PlatformFamily.WINDOWS)
        result = find_venv(platform)
        assert result == tmp_path / GENERIC_VENV_DIR

    def test_platform_specific_takes_priority(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        _create_venv(tmp_path, GENERIC_VENV_DIR, "Scripts", PlatformFamily.WINDOWS)
        result = find_venv(platform)
        assert result == tmp_path / ".venv_win"

    def test_no_venv_returns_none(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        result = find_venv(platform)
        assert result is None


class TestValidateVenv:
    """Interpreter existence checks."""

    def test_valid_venv_returns_true(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_path = _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        assert validate_venv(venv_path, platform) is True

    def test_invalid_venv_returns_false_with_warning(
        self,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_dir = tmp_path / ".venv_win"
        venv_dir.mkdir()  # no bin subdir, no interpreter
        result = validate_venv(venv_dir, platform)
        assert result is False
        assert "Venv directory exists but interpreter not found" in caplog.text
        assert str(venv_dir) in caplog.text


class TestComputeVenvEnvDelta:
    """Environment delta computation."""

    def test_path_prepend(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_path = _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        delta = compute_venv_env_delta(venv_path, platform)
        bin_dir = venv_path / "Scripts"
        expected_path = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
        assert delta["PATH"] == expected_path

    def test_virtual_env_set(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_path = _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        delta = compute_venv_env_delta(venv_path, platform)
        assert delta["VIRTUAL_ENV"] == str(venv_path)

    def test_pythonhome_unset_when_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("PYTHONHOME", "/usr")
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_path = _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        delta = compute_venv_env_delta(venv_path, platform)
        assert delta["PYTHONHOME"] is None

    def test_pythonhome_omitted_when_not_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHONHOME", raising=False)
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        venv_path = _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        delta = compute_venv_env_delta(venv_path, platform)
        assert "PYTHONHOME" not in delta


class TestDetectVenv:
    """Full detection flow."""

    def test_detect_returns_none_when_no_venv(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        result = detect_venv(platform)
        assert result is None

    def test_detect_returns_venv_result_when_valid(self, tmp_path: Path) -> None:
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        _create_venv(tmp_path, ".venv_win", "Scripts", PlatformFamily.WINDOWS)
        result = detect_venv(platform)
        assert result is not None
        assert isinstance(result, VenvResult)
        assert result.path == tmp_path / ".venv_win"
        assert "PATH" in result.env_delta
        assert "VIRTUAL_ENV" in result.env_delta
        assert result.env_delta["VIRTUAL_ENV"] == str(tmp_path / ".venv_win")

    def test_detect_returns_none_when_venv_invalid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """detect_venv returns None when venv dir exists but has no interpreter (line 95)."""
        platform = make_platform(tmp_path, PlatformFamily.WINDOWS)
        # Create venv dir without interpreter
        venv_dir = tmp_path / ".venv_win"
        venv_dir.mkdir()
        # validate_venv returns False, so detect_venv should return None
        result = detect_venv(platform)
        assert result is None
