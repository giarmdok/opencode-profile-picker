"""Tests for the bootstrap module."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest

from ocpp.bootstrap import (
    API_KEY_ALLOWLIST,
    check_gitignore,
    derive_project_name,
    harvest_api_keys,
    offer_gitignore_append,
    run_bootstrap,
)
from ocpp.platform import Platform


def make_platform(tmp_path: Path) -> Platform:
    """Build a minimal Platform for testing, rooted at *tmp_path*."""
    p = Platform.detect(platform_string="linux", home_dir=tmp_path)
    return dataclasses.replace(p, project_root=tmp_path)


# ---------------------------------------------------------------------------
# derive_project_name
# ---------------------------------------------------------------------------


class TestDeriveProjectName:
    """Project name derivation from directory names."""

    def test_simple_name(self, tmp_path: Path) -> None:
        d = tmp_path / "myproject"
        d.mkdir()
        assert derive_project_name(d) == "myproject"

    def test_name_with_special_chars(self, tmp_path: Path) -> None:
        d = tmp_path / "my project!"
        d.mkdir()
        assert derive_project_name(d) == "my-project"

    def test_multiple_special_chars(self, tmp_path: Path) -> None:
        d = tmp_path / "hello   world!!! test"
        d.mkdir()
        assert derive_project_name(d) == "hello-world-test"

    def test_whitespace_handling(self, tmp_path: Path) -> None:
        d = tmp_path / "  spaced  "
        d.mkdir()
        assert derive_project_name(d) == "spaced"

    def test_allows_dots_and_hyphens(self, tmp_path: Path) -> None:
        d = tmp_path / "foo_bar.baz"
        d.mkdir()
        assert derive_project_name(d) == "foo_bar.baz"

    def test_hyphen_preserved(self, tmp_path: Path) -> None:
        d = tmp_path / "my-cool-project"
        d.mkdir()
        assert derive_project_name(d) == "my-cool-project"

    def test_leading_trailing_whitespace(self, tmp_path: Path) -> None:
        d = tmp_path / "  my-proj  "
        d.mkdir()
        assert derive_project_name(d) == "my-proj"


# ---------------------------------------------------------------------------
# harvest_api_keys
# ---------------------------------------------------------------------------


class TestHarvestApiKeys:
    """Environment variable harvesting."""

    def test_all_keys_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in API_KEY_ALLOWLIST:
            monkeypatch.setenv(key, f"sk-{key.lower()}-val")
        result = harvest_api_keys()
        for key in API_KEY_ALLOWLIST:
            assert result[key] == f"sk-{key.lower()}-val"
        assert len(result) == len(API_KEY_ALLOWLIST)

    def test_some_keys_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        # Leave the rest unset
        for key in API_KEY_ALLOWLIST:
            if key not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
                monkeypatch.delenv(key, raising=False)
        result = harvest_api_keys()
        assert result == {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-openai-test",
        }

    def test_all_keys_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in API_KEY_ALLOWLIST:
            monkeypatch.delenv(key, raising=False)
        result = harvest_api_keys()
        assert result == {}

    def test_whitespace_only_values_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in API_KEY_ALLOWLIST:
            monkeypatch.setenv(key, "   ")
        result = harvest_api_keys()
        assert result == {}


# ---------------------------------------------------------------------------
# check_gitignore
# ---------------------------------------------------------------------------


class TestCheckGitignore:
    """Gitignore detection."""

    def test_not_a_git_repo(self, tmp_path: Path) -> None:
        """No .git dir -> return True."""
        assert check_gitignore(tmp_path) is True

    def test_gitignore_missing(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        assert check_gitignore(tmp_path) is False

    def test_gitignore_contains_project(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n.project\n__pycache__/\n", encoding="utf-8")
        assert check_gitignore(tmp_path) is True

    def test_gitignore_does_not_contain_project(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n__pycache__/\n", encoding="utf-8")
        assert check_gitignore(tmp_path) is False

    def test_gitignore_with_comment_line(self, tmp_path: Path) -> None:
        """Comment lines should be ignored during matching."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text(
            "# .project should be ignored\n*.pyc\n", encoding="utf-8"
        )
        assert check_gitignore(tmp_path) is False


# ---------------------------------------------------------------------------
# offer_gitignore_append
# ---------------------------------------------------------------------------


class TestOfferGitignoreAppend:
    """Gitignore append flow."""

    def test_user_accepts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / ".git").mkdir()
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n", encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")
        offer_gitignore_append(tmp_path)
        content = gitignore.read_text(encoding="utf-8")
        assert ".project" in content

    def test_user_declines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / ".git").mkdir()
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n", encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "n")
        offer_gitignore_append(tmp_path)
        content = gitignore.read_text(encoding="utf-8")
        assert ".project" not in content

    def test_already_gitignored(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / ".git").mkdir()
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".project\n", encoding="utf-8")
        # Should not prompt at all — if it did, input would fail
        offer_gitignore_append(tmp_path)
        content = gitignore.read_text(encoding="utf-8")
        assert content == ".project\n"

    def test_not_a_git_repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """No .git dir should skip the prompt entirely."""
        monkeypatch.setattr(
            "builtins.input",
            lambda _: (_ for _ in ()).throw(AssertionError("should not be called")),
        )
        offer_gitignore_append(tmp_path)


# ---------------------------------------------------------------------------
# run_bootstrap
# ---------------------------------------------------------------------------


class TestRunBootstrap:
    """Full bootstrap workflow."""

    def test_creates_project_file_when_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        platform = make_platform(tmp_path)
        # Set some env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        # No confirm prompt
        result = run_bootstrap(platform, confirm=False)
        assert result is True
        project_file = tmp_path / ".project"
        assert project_file.is_file()
        content = project_file.read_text(encoding="utf-8")
        assert "# ocpp project file" in content
        assert "OCPP_PROJECT_NAME=" in content
        assert "ANTHROPIC_API_KEY=sk-ant-test" in content
        assert "OPENAI_API_KEY=sk-openai-test" in content

    def test_skips_when_project_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        platform = make_platform(tmp_path)
        project_file = tmp_path / ".project"
        project_file.write_text("EXISTING=keep\n", encoding="utf-8")
        result = run_bootstrap(platform, confirm=False)
        assert result is True
        # File should remain unchanged
        content = project_file.read_text(encoding="utf-8")
        assert content == "EXISTING=keep\n"

    def test_user_confirms(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        platform = make_platform(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setattr("builtins.input", lambda _: "y")
        result = run_bootstrap(platform, confirm=True)
        assert result is True
        assert (tmp_path / ".project").is_file()

    def test_user_declines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        platform = make_platform(tmp_path)
        monkeypatch.setattr("builtins.input", lambda _: "n")
        result = run_bootstrap(platform, confirm=True)
        assert result is False
        assert not (tmp_path / ".project").is_file()

    def test_values_masked_in_confirmation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        platform = make_platform(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-value")
        monkeypatch.setattr("builtins.input", lambda _: "y")
        run_bootstrap(platform, confirm=True)
        captured = capsys.readouterr()
        # API key should be masked
        assert "ANTHROPIC_API_KEY=***" in captured.out
        # Secret value should NOT appear in output
        assert "sk-secret-value" not in captured.out

    def test_bootstrap_with_some_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Partial key set in environment."""
        platform = make_platform(tmp_path)
        # Clear all API keys first, then set only those we want
        for key in API_KEY_ALLOWLIST:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-1")
        monkeypatch.setenv("XAI_API_KEY", "sk-xai-2")
        # OCPP_PROJECT_NAME should be derived from dir name
        result = run_bootstrap(platform, confirm=False)
        assert result is True
        content = (tmp_path / ".project").read_text(encoding="utf-8")
        assert "ANTHROPIC_API_KEY=sk-ant-1" in content
        assert "XAI_API_KEY=sk-xai-2" in content
        # Keys not in env should not appear
        assert "OPENAI_API_KEY=" not in content
        # Project name should be the directory name
        assert f"OCPP_PROJECT_NAME={tmp_path.name}" in content


class TestBootstrapGitignoreInteraction:
    """Bootstrap interaction with gitignore."""

    def test_gitignore_offered_and_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
        platform = make_platform(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        # Answer "y" to confirmation, "y" to gitignore append
        monkeypatch.setattr("builtins.input", lambda _: "y")
        result = run_bootstrap(platform, confirm=True)
        assert result is True
        gitignore_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".project" in gitignore_content

    def test_gitignore_offered_and_declined(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
        platform = make_platform(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        # First input "y" for confirmation, then "n" for gitignore
        inputs = iter(["y", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        result = run_bootstrap(platform, confirm=True)
        assert result is True
        gitignore_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".project" not in gitignore_content


class TestBootstrapFilePermissions:
    """File permissions on created .project file."""

    def test_permissions_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        platform = make_platform(tmp_path)
        monkeypatch.setattr("builtins.input", lambda _: "y")
        result = run_bootstrap(platform, confirm=True)
        assert result is True
        project_file = tmp_path / ".project"
        # chmod may not work on Windows; on POSIX we check it
        # On all platforms, verify the file exists and is readable
        assert project_file.is_file()
        # Permissions check only on POSIX
        if os.name != "nt":
            mode = project_file.stat().st_mode & 0o777
            assert mode == 0o600


class TestBootstrapFullIntegration:
    """Full integration test with mocked environment."""

    def test_full_integration(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate a real bootstrap scenario."""
        # Set up a git repo with gitignore
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")

        platform = make_platform(tmp_path)
        # Clear all API keys first, then set only what we need
        for key in API_KEY_ALLOWLIST:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-real")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-real")

        # Confirm and gitignore both accepted
        inputs = iter(["y", "y"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        result = run_bootstrap(platform, confirm=True)
        assert result is True

        # Verify .project content
        project_file = tmp_path / ".project"
        content = project_file.read_text(encoding="utf-8")
        assert "# ocpp project file" in content
        assert "OCPP_PROJECT_NAME=" in content
        assert "ANTHROPIC_API_KEY=sk-ant-real" in content
        assert "OPENAI_API_KEY=sk-openai-real" in content
        assert "OPENROUTER_API_KEY=sk-or-real" in content
        # These should NOT appear
        assert "GEMINI_API_KEY=" not in content
        assert "XAI_API_KEY=" not in content
        assert "MISTRAL_API_KEY=" not in content

        # Verify .gitignore was updated
        gitignore_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".project" in gitignore_content
