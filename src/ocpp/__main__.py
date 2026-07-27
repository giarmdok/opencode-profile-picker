"""Entry point for the ocpp CLI — orchestrates the full setup flow."""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from ocpp.env import load_env_file
from ocpp.launch import launch_opencode
from ocpp.omo import OmoError, discover_config, list_presets
from ocpp.omo import set_preset as omo_set_preset
from ocpp.platform import Platform, PlatformFamily
from ocpp.venv import detect_venv

console = Console()
err_console = Console(stderr=True)


def _mask_sensitive_value(key: str, value: str | None) -> str:
    """Mask sensitive values for logging."""
    if value is None:
        return "None"
    sensitive_keys = ["key", "token", "secret"]
    if any(k in key.lower() for k in sensitive_keys):
        if len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        return "..."
    return value


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
    return parser


def _emit_env_commands(
    platform: Platform,
    final_env: dict[str, str | None],
    venv_delta: dict[str, str | None] | None,
) -> None:
    """Print shell-specific environment commands to stdout."""
    # Combine project/env and venv environments
    # venv_delta takes precedence
    env = final_env.copy()
    if venv_delta:
        for key, value in venv_delta.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value

    if platform.family is PlatformFamily.WINDOWS:
        # PowerShell syntax
        for key, value in env.items():
            if value:
                print(f'$Env:{key}="{value}"')
            else:
                print(f"Remove-Item Env:\\{key}")
    else:
        # POSIX sh/bash/zsh syntax
        for key, value in env.items():
            if value:
                escaped_value = value.replace("'", "'\\''")
                print(f"export {key}='{escaped_value}'")
            else:
                print(f"unset {key}")


def main() -> int:
    """Run the full ocpp CLI flow."""
    parser = _build_parser()
    parsed, opencode_args = parser.parse_known_args()

    project_root = Path.cwd().resolve()

    platform = Platform.detect()
    platform = dataclasses.replace(platform, project_root=project_root)

    # Load .env overrides first. If this file exists, it takes precedence.
    env_overrides = load_env_file(project_root)
    if env_overrides:
        err_console.print(
            f"[bold green]Found .env file:[/bold green] [yellow]{project_root / '.env'}[/yellow]."
        )
    else:
        err_console.print("[dim]No .env file found in project root. Skipping environment overrides.[/dim]")

    # Detect venv
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

    # OMO preset selection
    global_config_path: Path | None = None
    try:
        global_config_path = discover_config(platform)
    except FileNotFoundError:
        err_console.print(
            "[yellow]Warning:[/yellow] OMO config not found, skipping preset selection"
        )

    if global_config_path is not None:
        _current_preset, preset_infos = list_presets(global_config_path)
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

        selected_preset: str | None = None
        if parsed.preset is not None:
            preset_names = {info.name for info in preset_infos}
            if parsed.preset not in preset_names:
                err_console.print(
                    f"[red]Error:[/red] Preset '{parsed.preset}' not found.\n"
                    f"  Available presets: {', '.join(sorted(preset_names))}"
                )
                return 1
            selected_preset = parsed.preset
        else:
            current_preset_index = next(
                (idx for idx, info in enumerate(preset_infos) if info.is_current), None
            )
            try:
                answer = Prompt.ask(
                    "Select preset number (or leave empty to use current preset, q to quit)",
                    default=str(current_preset_index + 1)
                    if current_preset_index is not None
                    else "",
                    show_default=False,
                )
            except EOFError:
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
    _emit_env_commands(platform, env_overrides, venv_delta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
