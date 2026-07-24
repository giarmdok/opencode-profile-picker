"""Launch opencode with merged environment, binary resolution, and process execution."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from ocpp.platform import Platform, PlatformFamily

__all__ = [
    "LaunchError",
    "build_merged_env",
    "resolve_opencode",
    "launch_opencode",
]


class LaunchError(Exception):
    """Raised when opencode cannot be launched."""


def build_merged_env(
    project_overrides: dict[str, str] | None = None,
    venv_delta: dict[str, str | None] | None = None,
) -> dict[str, str]:
    """Build the final merged environment.

    Order:
    1. Start with copy of os.environ
    2. Overlay project_overrides (str values set the key)
    3. Apply venv_delta LAST:
       - str value → set the key
       - None value → delete the key from merged env
    4. Return the merged dict
    """
    merged: dict[str, str] = dict(os.environ)

    if project_overrides:
        for key, val in project_overrides.items():
            merged[key] = val

    if venv_delta:
        for key, v in venv_delta.items():
            if v is None:
                merged.pop(key, None)
            else:
                merged[key] = v

    return merged


def resolve_opencode(merged_env: dict[str, str]) -> str:
    """Resolve opencode binary via shutil.which using merged PATH.

    Raises LaunchError if not found.
    """
    path = shutil.which("opencode", path=merged_env.get("PATH"))
    if path is None:
        raise LaunchError("opencode not found in PATH. Is opencode installed?")
    return path


def launch_opencode(
    project_overrides: dict[str, str] | None = None,
    venv_delta: dict[str, str | None] | None = None,
    extra_args: list[str] | None = None,
    platform: Platform | None = None,
) -> int:
    """Full launch flow.

    1. Build merged env
    2. Resolve opencode binary
    3. Build args list: [opencode_path, *extra_args]
    4. Launch:
       - POSIX (platform.family is not WINDOWS): os.execvpe (replaces process)
       - Windows: subprocess.run + return exit code
    5. Catch LaunchError, print to stderr, return exit code 1
    """
    if platform is None:
        platform = Platform.detect()

    if extra_args is None:
        extra_args = []

    try:
        # Display venv info if detected
        if venv_delta:
            from rich.console import Console

            console = Console()
            venv_path = venv_delta.get("VIRTUAL_ENV", "Unknown")
            console.print(
                f"[bold green]Detected virtual environment:[/bold green] [bold yellow]{venv_path}[/bold yellow]"
            )
            console.print("[bold green]Activating virtual environment...[/bold green]")
            import time

            time.sleep(5)  # Pause for 5 seconds to allow reading

        merged_env = build_merged_env(
            project_overrides=project_overrides,
            venv_delta=venv_delta,
        )
        opencode_path = resolve_opencode(merged_env)

        args = [opencode_path, *extra_args]

        if platform.family is not PlatformFamily.WINDOWS:
            # POSIX: replace the current process (execvpe never returns on success)
            try:
                os.execvpe(opencode_path, args, merged_env)
            except OSError as exc:
                raise LaunchError(f"Failed to launch opencode: {exc}") from exc
        else:
            # Windows: subprocess + explicit handle redirection + graceful exit
            subprocess.Popen(
                args,
                env=merged_env,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.DETACHED_PROCESS,
            )
            sys.exit(0)
    except LaunchError as error:
        print(str(error), file=sys.stderr)
        return 1
