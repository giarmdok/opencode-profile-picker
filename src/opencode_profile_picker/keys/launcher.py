"""OpenCode process launcher."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass

from opencode_profile_picker.config.paths import get_opencode_executable


@dataclass
class LaunchResult:
    """Result of attempting to launch OpenCode."""

    success: bool
    message: str


def check_opencode_available() -> bool:
    """Check if opencode is available on the system PATH."""
    return get_opencode_executable() is not None


def launch_opencode(env: dict[str, str]) -> LaunchResult:
    """Launch OpenCode as a child process with the given environment.

    On Windows, creates a new console window.
    On Unix, inherits the current terminal.
    """
    executable = get_opencode_executable()
    if executable is None:
        return LaunchResult(
            success=False,
            message="OpenCode not found on PATH. Is it installed?",
        )

    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                [executable],
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                start_new_session=True,
            )
        else:
            process = subprocess.Popen(
                [executable],
                env=env,
            )

        # Don't wait — let OpenCode run independently.
        # The oopps process will exit after spawning.
        _ = process  # Acknowledge we created it but don't manage it

        return LaunchResult(success=True, message="OpenCode launched")

    except OSError as e:
        return LaunchResult(
            success=False,
            message=f"Failed to launch OpenCode: {e}",
        )
