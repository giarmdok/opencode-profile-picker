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
from ocpp.platform import Platform
from ocpp.project import OCPP_PROJECT_NAME, parse_project
from ocpp.venv import detect_venv

console = Console()
err_console = Console(stderr=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocpp",
        description="Opencode Profile Picker — set up API keys, apply OMO presets, and launch opencode.",
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without writing or launching.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Force bootstrap even if .project already exists.",
    )
    return parser


def main() -> int:
    """Run the full ocpp CLI flow.


    """
    parser = _build_parser()


    # Step 0: Parse .env and force-set environment variables
    overridden_keys = load_env_file()
    if overridden_keys:
        console.print("[yellow]Overridden environment variables:[/yellow]")
        for key, old_value in overridden_keys.items():
            masked_old = f"{old_value[:5]}****" if old_value else "None"
            masked_new = f"{os.environ[key][:5]}****"
            console.print(f"  - {key}: {masked_old} → {masked_new}")
    else:
        console.print("[green]No .env file found or no overrides applied.[/green]")

    # Step 1: Parse args with parse_known_args for passthrough
    parsed, passthrough_args = parser.parse_known_args()

    # Step 2: Detect if running inside OpenCode


    # Strip the leading '--' separator if present
    if passthrough_args and passthrough_args[0] == "--":
        passthrough_args = passthrough_args[1:]

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

    # Step 4: Bootstrap
    project_file = project_root / ".project"
    should_bootstrap = not project_file.is_file() or parsed.init

    if should_bootstrap:
        if parsed.init and project_file.is_file():
            # Back up existing .project
            bak_path = project_file.with_suffix(".project.bak")
            err_console.print(
                f"[yellow]Warning:[/yellow] --init specified, backing up existing .project to {bak_path}"
            )
            try:
                project_file.rename(bak_path)
            except OSError as exc:
                err_console.print(f"[red]Error:[/red] Failed to back up .project: {exc}")
                return 1

        if parsed.dry_run:
            console.print(f"[dim]Would bootstrap .project at {project_file}[/dim]")
        else:
            ok = run_bootstrap(platform, confirm=not parsed.dry_run)
            if not ok:
                err_console.print("[red]Error:[/red] Bootstrap declined by user.")
                return 1

    # Step 5: Load .project
    project_kv: dict[str, str] = {}
    if parsed.dry_run:
        console.print(f"[dim]Would load .project from {project_file}[/dim]")
    else:
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
    venv_result = detect_venv(platform)
    if parsed.dry_run:
        if venv_result is not None:
            console.print(f"[dim]Would detect venv at {venv_result.path}[/dim]")
        else:
            console.print("[dim]No venv would be found[/dim]")
    else:
        if venv_result is None:
            err_console.print(
                "[yellow]Warning:[/yellow] No venv found, continuing without venv activation"
            )

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

        if parsed.dry_run:
            console.print(f"[dim]Would list presets from {global_config_path}[/dim]")
        else:
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
            console.print(table)

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
                console.print("[dim]Non-interactive mode: Using current preset.[/dim]")

            if answer.strip().lower() == "q":
                console.print("[dim]Preset selection cancelled.[/dim]")
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
            if parsed.dry_run:
                local_omo_path = project_root / ".opencode" / "oh-my-opencode-slim.jsonc"
                console.print(
                    f"[dim]Would copy global OMO config to {local_omo_path} and set preset to '{selected_preset}'[/dim]"
                )
            else:
                try:
                    omo_set_preset(
                        global_config_path,
                        selected_preset,
                        project_root,
                        confirm=not parsed.dry_run,
                    )
                except OmoError as exc:
                    err_console.print(f"[red]Error:[/red] {exc}")
                    return 1

    # Step 10: Launch opencode (default behavior)







if __name__ == "__main__":
    # Guard against running inside OpenCode (e.g., recursive launch)

    sys.exit(main())
