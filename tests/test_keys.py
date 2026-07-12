"""Tests for key resolution and launching."""

from __future__ import annotations

from unittest.mock import patch

from opencode_profile_picker.config.discover import DiscoveryResult
from opencode_profile_picker.keys.launcher import check_opencode_available, launch_opencode
from opencode_profile_picker.keys.resolver import (
    build_launch_env,
    get_missing_keys,
    get_required_keys,
    resolve_keys,
)
from opencode_profile_picker.profiles.models import KeyEntry, KeySet


class TestResolveKeys:
    def test_resolves_from_store(self) -> None:
        ks = KeySet(name="test")
        ks.keys["OPENAI_API_KEY"] = KeyEntry(
            provider="openai", env_var="OPENAI_API_KEY", value="sk-stored"
        )
        result = resolve_keys(ks, {"OPENAI_API_KEY"}, current_env={})
        assert result["OPENAI_API_KEY"] == "sk-stored"

    def test_falls_back_to_env(self) -> None:
        ks = KeySet(name="test")
        ks.keys["OPENAI_API_KEY"] = KeyEntry(
            provider="openai", env_var="OPENAI_API_KEY", value=None
        )
        result = resolve_keys(ks, {"OPENAI_API_KEY"}, current_env={"OPENAI_API_KEY": "sk-env"})
        assert result["OPENAI_API_KEY"] == "sk-env"

    def test_returns_none_when_not_found(self) -> None:
        ks = KeySet(name="test")
        result = resolve_keys(ks, {"OPENAI_API_KEY"}, current_env={})
        assert result["OPENAI_API_KEY"] is None

    def test_stored_value_takes_precedence_over_env(self) -> None:
        ks = KeySet(name="test")
        ks.keys["OPENAI_API_KEY"] = KeyEntry(
            provider="openai", env_var="OPENAI_API_KEY", value="sk-stored"
        )
        result = resolve_keys(ks, {"OPENAI_API_KEY"}, current_env={"OPENAI_API_KEY": "sk-env"})
        assert result["OPENAI_API_KEY"] == "sk-stored"

    def test_handles_unknown_provider(self) -> None:
        ks = KeySet(name="test")
        result = resolve_keys(ks, {"UNKNOWN:custom"}, current_env={})
        assert result["UNKNOWN:custom"] is None


class TestGetRequiredKeys:
    def test_returns_keys_for_preset(self) -> None:
        discovery = DiscoveryResult(presets={"or": {"OPENROUTER_API_KEY", "OPENAI_API_KEY"}})
        result = get_required_keys("or", discovery)
        assert result == {"OPENROUTER_API_KEY", "OPENAI_API_KEY"}

    def test_returns_empty_for_unknown_preset(self) -> None:
        discovery = DiscoveryResult(presets={})
        result = get_required_keys("nonexistent", discovery)
        assert result == set()


class TestBuildLaunchEnv:
    def test_merges_resolved_keys(self) -> None:
        resolved = {"OPENAI_API_KEY": "sk-abc"}
        env = build_launch_env(resolved, current_env={"PATH": "/usr/bin"})
        assert env["OPENAI_API_KEY"] == "sk-abc"
        assert env["PATH"] == "/usr/bin"

    def test_excludes_none_values(self) -> None:
        resolved = {"OPENAI_API_KEY": None, "ANTHROPIC_API_KEY": "sk-xyz"}
        env = build_launch_env(resolved, current_env={})
        assert "OPENAI_API_KEY" not in env
        assert env["ANTHROPIC_API_KEY"] == "sk-xyz"

    def test_excludes_unknown_providers(self) -> None:
        resolved = {"UNKNOWN:custom": None, "OPENAI_API_KEY": "sk-abc"}
        env = build_launch_env(resolved, current_env={})
        assert "UNKNOWN:custom" not in env
        assert env["OPENAI_API_KEY"] == "sk-abc"

    def test_resolved_overrides_existing(self) -> None:
        resolved = {"OPENAI_API_KEY": "sk-new"}
        env = build_launch_env(resolved, current_env={"OPENAI_API_KEY": "sk-old"})
        assert env["OPENAI_API_KEY"] == "sk-new"


class TestGetMissingKeys:
    def test_returns_unresolved_keys(self) -> None:
        resolved = {"KEY_A": "value", "KEY_B": None, "KEY_C": "value2"}
        missing = get_missing_keys(resolved)
        assert missing == ["KEY_B"]

    def test_excludes_unknown_providers(self) -> None:
        resolved = {"KEY_A": None, "UNKNOWN:custom": None}
        missing = get_missing_keys(resolved)
        assert missing == ["KEY_A"]

    def test_empty_when_all_resolved(self) -> None:
        resolved = {"KEY_A": "value", "KEY_B": "value2"}
        missing = get_missing_keys(resolved)
        assert missing == []


class TestCheckOpencodeAvailable:
    def test_returns_true_when_found(self) -> None:
        with patch(
            "opencode_profile_picker.keys.launcher.get_opencode_executable",
            return_value="/usr/bin/opencode",
        ):
            assert check_opencode_available() is True

    def test_returns_false_when_not_found(self) -> None:
        with patch(
            "opencode_profile_picker.keys.launcher.get_opencode_executable",
            return_value=None,
        ):
            assert check_opencode_available() is False


class TestLaunchOpencode:
    def test_returns_error_when_not_found(self) -> None:
        with patch(
            "opencode_profile_picker.keys.launcher.get_opencode_executable",
            return_value=None,
        ):
            result = launch_opencode({})
            assert result.success is False
            assert "not found" in result.message.lower()

    def test_launches_on_unix(self) -> None:
        with (
            patch(
                "opencode_profile_picker.keys.launcher.get_opencode_executable",
                return_value="/usr/bin/opencode",
            ),
            patch("subprocess.Popen") as mock_popen,
            patch("sys.platform", "linux"),
        ):
            result = launch_opencode({"KEY": "val"})
            assert result.success is True
            mock_popen.assert_called_once_with(["/usr/bin/opencode"], env={"KEY": "val"})

    def test_launches_on_windows(self) -> None:
        with (
            patch(
                "opencode_profile_picker.keys.launcher.get_opencode_executable",
                return_value="C:\\opencode.exe",
            ),
            patch("subprocess.Popen") as mock_popen,
            patch("sys.platform", "win32"),
        ):
            result = launch_opencode({"KEY": "val"})
            assert result.success is True
            call_kwargs = mock_popen.call_args.kwargs
            assert call_kwargs["env"] == {"KEY": "val"}

    def test_handles_os_error(self) -> None:
        with (
            patch(
                "opencode_profile_picker.keys.launcher.get_opencode_executable",
                return_value="/usr/bin/opencode",
            ),
            patch("subprocess.Popen", side_effect=OSError("spawn failed")),
        ):
            result = launch_opencode({})
            assert result.success is False
            assert "spawn failed" in result.message
