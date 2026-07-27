"""
This module provides functionality to launch the opencode CLI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from ocpp.platform import Platform, PlatformFamily


def launch_opencode(
    platform: Platform,
    project_kv: dict[str, str],
    venv_delta: dict[str, str | None] | None,
    opencode_args: list[str],
) -> None:
    """
    Launch the opencode CLI with the merged environment.
    """
    # Build the merged environment
    env = os.environ.copy()
    env.update(project_kv)
    if venv_delta:
        for key, value in venv_delta.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value

    # Resolve opencode binary
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        print(
            "Error: opencode binary not found. Install opencode (https://github.com/opencode-ai/opencode) or use --no-launch to skip launching.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Launch opencode
    if platform.family is PlatformFamily.WINDOWS:
        subprocess.run([opencode_bin, *opencode_args], env=env, check=False)
    else:
        os.execve(opencode_bin, [opencode_bin, *opencode_args], env)
