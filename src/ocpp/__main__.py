"""Entry point for the ocpp CLI — orchestrates the full 6-step setup flow."""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from ocpp.bootstrap import run_bootstrap
from ocpp.env import load_env_file

from ocpp.omo import OmoError, PresetInfo, discover_config, list_presets
from ocpp.omo import set_preset as omo_set_preset
from ocpp.platform import Platform, PlatformFamily
from ocpp.project import OCPP_PROJECT_NAME, parse_project
from ocpp.venv import detect_venv

console = Console()
err_console = Console(stderr=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocpp",
        description="Opencode Profile Picker — set up API keys, apply OMO presets, and export environment variables.",
    )
    parser.add_argument(
        "--preset",
        metavar="NAME",
        default=None,
        help="Non-interactive preset selection (skip the prompt).",
    )
    parser.add_argument(
        "--project-dir",
        metavar="PATH",
        type=Path,
        default=None,
        help="Override project root (default: current working directory).",
    )
    return parser


def _emit_env_commands(
    platform: Platform,
    project_kv: dict[str, str],
    venv_delta: dict[str, str | None] | None,
) -> None:
    """Print shell-specific environment commands to stdout."""
    # Combine project and venv environments
    # venv_delta takes precedence
    env = project_kv.copy()
    if venv_delta:
        for key, value in venv_delta.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value

    if platform.family is PlatformFamily.WINDOWS:
        # PowerShell syntax
        for key, value in env.items():
            # In PowerShell, variables with null/empty value are removed
            if value:
                print(f'$Env:{key}="{value}"')
            else:
                print(f"Remove-Item Env:\\{key}")
    else:
        # POSIX sh/bash/zsh syntax
        for key, value in env.items():
            if value:
                # Basic shell escaping for values
                escaped_value = value.replace("'", "'\\''")
                print(f"export {key}='{escaped_value}'")
            else:
                print(f"unset {key}")


def main() -> int:
    """Run the full ocpp CLI flow.


    """
    parser = _build_parser()

    # Step 1: Parse args
    parsed = parser.parse_args()

    # Step 2: Validate --project-dir
    project_root: Path
    if parsed.project_dir is not None:
        resolved = parsed.project_dir.resolve()
        if not resolved.is_dir():
            err_console.print(f"[red]Error:[/red] --project-dir path does not exist: {resolved}")
            return 1
        project_root = resolved
    else:
        project_root = Path.cwd().resolve()

    # Step 3: Detect platform
    platform = Platform.detect()
    platform = dataclasses.replace(platform, project_root=project_root)

    # Step 5: Load .project
    project_file = project_root / ".project"
    project_kv: dict[str, str] = {}
    try:
        project_kv, _project_lines = parse_project(project_file)
    except (ValueError, OSError) as exc:
        err_console.print(
            f"[red]Error:[/red] Failed to parse .project at {project_file}: {exc}\n"
            f"  Run with --init to recreate it."
        )
        return 1

    if not project_kv:
        err_console.print(
            f"[red]Error:[/red] .project file at {project_file} is empty or missing entries.\n"
            f"  Run with --init to recreate it."
        )
        return 1

    # Step 6: Detect venv
    venv_delta: dict[str, str | None] | None = None
    venv_result = detect_venv(platform)
    if venv_result is None:
        err_console.print(
            "[yellow]Warning:[/yellow] No venv found, continuing without venv activation"
        )
    else:
        err_console.print(
            f"[bold green]Activating venv:[/bold green] [yellow]{venv_result.path}[/yellow]"
        )
        venv_delta = venv_result.env_delta

    # Step 7: List presets — discover config
    global_config_path: Path | None = None
    preset_infos: list[PresetInfo] = []
    try:
        global_config_path = discover_config(platform)
    except FileNotFoundError:
        err_console.print(
            "[yellow]Warning:[/yellow] OMO config not found, skipping preset selection"
        )

    selected_preset: str | None = None
    if global_config_path is not None:
        _current_preset, preset_infos = list_presets(global_config_path)

        # Display presets with rich table
        current_preset_name = next(
            (info.name for info in preset_infos if info.is_current), None
        )
        table_title = "Available OMO Presets"
        if current_preset_name:
            table_title += f" (Current: {current_preset_name})"
        table = Table(title=table_title)
        table.add_column("#", style="dim", width=4)
        table.add_column("Preset Name", style="cyan")
        table.add_column("Status", justify="center")
        for idx, info in enumerate(preset_infos, start=1):
            status = "[bold green]*[/bold green]" if info.is_current else ""
            table.add_row(str(idx), info.name, status)
        err_console.print(table)

        # Step 8: Select preset
        if parsed.preset is not None:
            # Validate --preset
            preset_names = {info.name for info in preset_infos}
            if parsed.preset not in preset_names:
                err_console.print(
                    f"[red]Error:[/red] Preset '{parsed.preset}' not found.\n"
                    f"  Available presets: {', '.join(sorted(preset_names))}"
                )
                return 1
            selected_preset = parsed.preset
        else:
            # Find the index of the current preset
            current_preset_index = next(
                (idx for idx, info in enumerate(preset_infos) if info.is_current), None
            )
            # Interactive selection via rich prompt (default to current preset)
            try:
                answer = Prompt.ask(
                    "Select preset number (or leave empty to use current preset, q to quit)",
                    default=str(current_preset_index + 1)
                    if current_preset_index is not None
                    else "",
                    show_default=False,
                )
            except EOFError:
                # Non-interactive environment (e.g., tests, CI)
                answer = ""
                err_console.print("[dim]Non-interactive mode: Using current preset.[/dim]")

            if answer.strip().lower() == "q":
                err_console.print("[dim]Preset selection cancelled.[/dim]")
                return 0
            elif answer.strip() == "":
                selected_preset = None
            else:
                try:
                    idx = int(answer.strip())
                    if 1 <= idx <= len(preset_infos):
                        selected_preset = preset_infos[idx - 1].name
                    else:
                        err_console.print(
                            f"[red]Error:[/red] Invalid selection. Choose a number between 1 and {len(preset_infos)}."
                        )
                        return 1
                except ValueError:
                    err_console.print(
                        "[red]Error:[/red] Invalid input. Enter a number, leave empty, or press q to quit."
                    )
                    return 1
        # Step 9: Write preset
        if selected_preset is not None:
            try:
                omo_set_preset(
                    global_config_path,
                    selected_preset,
                    project_root,
                    confirm=True,
                )
            except OmoError as exc:
                err_console.print(f"[red]Error:[/red] {exc}")
                return 1

    # Final Step: Emit all environment commands to stdout
    _emit_env_commands(platform, project_kv, venv_delta)
    return 0







if __name__ == "__main__":
    # Guard against running inside OpenCode (e.g., recursive launch)

    sys.exit(main())
