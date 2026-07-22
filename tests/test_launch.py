"""Tests for the launch module."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ocpp.launch import LaunchError, build_merged_env, launch_opencode, resolve_opencode
from ocpp.platform import Platform, PlatformFamily

# ---------------------------------------------------------------------------
# build_merged_env
# ---------------------------------------------------------------------------


class TestBuildMergedEnv:
    """Tests for build_merged_env."""

    def test_env_merge_project_overrides_override_osenviron(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Project overrides should override os.environ values."""
        monkeypatch.setenv("MY_VAR", "original")
        merged = build_merged_env(project_overrides={"MY_VAR": "overridden"})
        assert merged["MY_VAR"] == "overridden"

    def test_project_overrides_take_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Project overrides take priority over os.environ."""
        monkeypatch.setenv("MY_VAR", "original")
        merged = build_merged_env(project_overrides={"MY_VAR": "overridden"})
        assert merged["MY_VAR"] == "overridden"

    def test_venv_delta_path_overrides_project_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Venv delta PATH is applied after project overrides, so it wins."""
        monkeypatch.setenv("PATH", "/original/path")
        merged = build_merged_env(
            project_overrides={"PATH": "/project/path"},
            venv_delta={"PATH": "/venv/bin"},
        )
        assert merged["PATH"] == "/venv/bin"

    def test_venv_delta_sets_virtual_env(self) -> None:
        """VIRTUAL_ENV should be set in merged env from venv delta."""
        merged = build_merged_env(venv_delta={"VIRTUAL_ENV": "/project/.venv"})
        assert merged["VIRTUAL_ENV"] == "/project/.venv"

    def test_venv_delta_unsets_pythonhome(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Venv delta with PYTHONHOME=None should remove it."""
        monkeypatch.setenv("PYTHONHOME", "/some/path")
        merged = build_merged_env(venv_delta={"PYTHONHOME": None})
        assert "PYTHONHOME" not in merged

    def test_venv_delta_omits_pythonhome_when_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When PYTHONHOME not in venv delta and not in os.environ, it should not appear."""
        monkeypatch.delenv("PYTHONHOME", raising=False)
        merged = build_merged_env()
        assert "PYTHONHOME" not in merged

    def test_no_venv_delta(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without venv delta, merged env should be os.environ + project_overrides."""
        monkeypatch.setenv("EXISTING_KEY", "existing_val")
        merged = build_merged_env(project_overrides={"PROJ_KEY": "proj_val"})
        assert merged["EXISTING_KEY"] == "existing_val"
        assert merged["PROJ_KEY"] == "proj_val"

    def test_no_project_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without project overrides, merged env should be os.environ + venv delta."""
        monkeypatch.setenv("EXISTING_KEY", "existing_val")
        merged = build_merged_env(venv_delta={"VENV_KEY": "venv_val"})
        assert merged["EXISTING_KEY"] == "existing_val"
        assert merged["VENV_KEY"] == "venv_val"

    def test_both_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With neither project overrides nor venv delta, merged env = os.environ."""
        monkeypatch.setenv("EXISTING_KEY", "existing_val")
        merged = build_merged_env()
        assert merged["EXISTING_KEY"] == "existing_val"
        assert len(merged) >= 1

    def test_venv_delta_none_value_on_missing_key(self) -> None:
        """Deleting a key that doesn't exist should not error."""
        merged = build_merged_env(venv_delta={"SOME_MISSING_KEY": None})
        assert "SOME_MISSING_KEY" not in merged


# ---------------------------------------------------------------------------
# resolve_opencode
# ---------------------------------------------------------------------------


class TestResolveOpencode:
    """Tests for resolve_opencode."""

    def test_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When shutil.which returns a path, resolve_opencode should return it."""
        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        merged = {"PATH": "/usr/bin"}
        result = resolve_opencode(merged)
        assert result == "/usr/bin/opencode"

    def test_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When shutil.which returns None, resolve_opencode should raise LaunchError."""
        monkeypatch.setattr("shutil.which", lambda cmd, path=None: None)
        merged = {"PATH": "/usr/bin"}
        with pytest.raises(LaunchError, match="opencode not found in PATH"):
            resolve_opencode(merged)

    def test_uses_merged_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """shutil.which should be called with path from merged_env."""
        captured_paths: list[str | None] = []

        def fake_which(cmd: str, path: str | None = None) -> str | None:
            captured_paths.append(path)
            return "/usr/bin/opencode"

        monkeypatch.setattr("shutil.which", fake_which)
        merged = {"PATH": "/custom/path"}
        resolve_opencode(merged)
        assert captured_paths == ["/custom/path"]


# ---------------------------------------------------------------------------
# launch_opencode
# ---------------------------------------------------------------------------


class TestLaunchOpencode:
    """Tests for launch_opencode."""

    def test_argv_passthrough_extra_args_forwarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extra args should be forwarded to the launch command."""
        captured_args: list[list[str]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
            captured_args.append(args)
            return subprocess.CompletedProcess(args, 0)  # type: ignore[arg-type]

        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        monkeypatch.setattr("subprocess.run", fake_run)

        platform = Platform(
            family=PlatformFamily.WINDOWS,
            venv_dir_name=".venv_win",
            venv_bin_subdir="Scripts",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        launch_opencode(extra_args=["--model", "claude"], platform=platform)
        assert len(captured_args) == 1
        assert captured_args[0] == ["/usr/bin/opencode", "--model", "claude"]

    def test_argv_passthrough_no_extra_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without extra args, the args list should be just [opencode_path]."""
        captured_args: list[list[str]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
            captured_args.append(args)
            return subprocess.CompletedProcess(args, 0)  # type: ignore[arg-type]

        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        monkeypatch.setattr("subprocess.run", fake_run)

        platform = Platform(
            family=PlatformFamily.WINDOWS,
            venv_dir_name=".venv_win",
            venv_bin_subdir="Scripts",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        launch_opencode(platform=platform)
        assert len(captured_args) == 1
        assert captured_args[0] == ["/usr/bin/opencode"]

    def test_windows_launch_subprocess_run_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """On Windows, subprocess.run should be called with correct args and env."""
        captured_args: list[list[str]] = []
        captured_kwargs: list[dict[str, object]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
            captured_args.append(args)
            captured_kwargs.append(kwargs)
            return subprocess.CompletedProcess(args, 42)  # type: ignore[arg-type]

        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        monkeypatch.setattr("subprocess.run", fake_run)

        platform = Platform(
            family=PlatformFamily.WINDOWS,
            venv_dir_name=".venv_win",
            venv_bin_subdir="Scripts",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        result = launch_opencode(
            project_overrides={"PROJ_KEY": "proj_val"},
            venv_delta={"VENV_KEY": "venv_val"},
            extra_args=["--verbose"],
            platform=platform,
        )

        assert result == 42
        assert len(captured_args) == 1
        assert captured_args[0] == ["/usr/bin/opencode", "--verbose"]

        kwargs = captured_kwargs[0]
        assert kwargs.get("shell") is False
        env = kwargs.get("env")
        assert isinstance(env, dict)
        assert env["PROJ_KEY"] == "proj_val"
        assert env["VENV_KEY"] == "venv_val"

    def test_windows_launch_shell_true_not_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """On Windows, subprocess.run should never use shell=True."""
        captured_kwargs: list[dict[str, object]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
            captured_kwargs.append(kwargs)
            return subprocess.CompletedProcess(args, 0)  # type: ignore[arg-type]

        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        monkeypatch.setattr("subprocess.run", fake_run)

        platform = Platform(
            family=PlatformFamily.WINDOWS,
            venv_dir_name=".venv_win",
            venv_bin_subdir="Scripts",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        launch_opencode(platform=platform)
        assert len(captured_kwargs) == 1
        # shell=False is the default; we just verify shell=True is not set
        assert captured_kwargs[0].get("shell") is not True

    def test_posix_launch_execvpe_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """On POSIX, os.execvpe should be called with correct args and env."""
        captured_calls: list[tuple[str, list[str], dict[str, str]]] = []

        def fake_execvpe(file: str, args: list[str], env: dict[str, str]) -> None:
            captured_calls.append((file, args, env))

        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")
        monkeypatch.setattr("os.execvpe", fake_execvpe)

        platform = Platform(
            family=PlatformFamily.LINUX,
            venv_dir_name=".venv_lin",
            venv_bin_subdir="bin",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        launch_opencode(
            project_overrides={"PROJ_KEY": "proj_val"},
            venv_delta={"VENV_KEY": "venv_val"},
            extra_args=["--verbose"],
            platform=platform,
        )

        assert len(captured_calls) == 1
        file, args, env = captured_calls[0]
        assert file == "/usr/bin/opencode"
        assert args == ["/usr/bin/opencode", "--verbose"]
        assert env["PROJ_KEY"] == "proj_val"
        assert env["VENV_KEY"] == "venv_val"

    def test_missing_binary_error_prints_to_stderr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When resolve_opencode raises LaunchError, it should be printed to stderr and return 1."""
        monkeypatch.setattr(
            "ocpp.launch.resolve_opencode",
            lambda env: (_ for _ in ()).throw(
                LaunchError("opencode not found in PATH. Is opencode installed?")
            ),
        )

        platform = Platform(
            family=PlatformFamily.WINDOWS,
            venv_dir_name=".venv_win",
            venv_bin_subdir="Scripts",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        import io

        stderr_capture = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        result = launch_opencode(platform=platform)
        assert result == 1
        assert "opencode not found in PATH" in stderr_capture.getvalue()


# ===========================================================================
# Test: platform=None defaults to Platform.detect() (line 82)
# ===========================================================================


class TestLaunchOpencodePlatformNone:
    """platform=None should use Platform.detect()."""

    def test_platform_none_uses_detect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When platform is None, Platform.detect() is called."""
        captured_platforms: list[Platform] = []

        def fake_detect(**kw: object) -> Platform:
            p = Platform(
                family=PlatformFamily.WINDOWS,
                venv_dir_name=".venv_win",
                venv_bin_subdir="Scripts",
                omo_config_paths=[Path("dummy")],
                project_root=Path("."),
            )
            captured_platforms.append(p)
            return p

        monkeypatch.setattr("ocpp.launch.Platform.detect", fake_detect)
        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")

        captured_args: list[list[str]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
            captured_args.append(args)
            return subprocess.CompletedProcess(args, 0)  # type: ignore[arg-type]

        monkeypatch.setattr("subprocess.run", fake_run)

        launch_opencode(platform=None)
        assert len(captured_platforms) == 1
        assert len(captured_args) == 1
        assert captured_args[0] == ["/usr/bin/opencode"]


# ===========================================================================
# Test: OSError from os.execvpe (lines 100-101)
# ===========================================================================


class TestLaunchOpencodeExecvpeOSError:
    """OSError from os.execvpe should be caught and wrapped as LaunchError."""

    def test_oserror_wrapped_in_launch_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("shutil.which", lambda cmd, path=None: "/usr/bin/opencode")

        def failing_execvpe(file: str, args: list[str], env: dict[str, str]) -> None:
            raise OSError("Exec format error")

        monkeypatch.setattr("os.execvpe", failing_execvpe)

        import io

        stderr_capture = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        platform = Platform(
            family=PlatformFamily.LINUX,
            venv_dir_name=".venv_lin",
            venv_bin_subdir="bin",
            omo_config_paths=[Path("dummy")],
            project_root=Path("."),
        )

        result = launch_opencode(platform=platform)
        assert result == 1
        assert "Failed to launch opencode:" in stderr_capture.getvalue()
        assert "Exec format error" in stderr_capture.getvalue()
