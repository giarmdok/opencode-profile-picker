## Context

All six previous changes provide the building blocks:

| Change | Module | Key Exports |
|--------|--------|-------------|
| #1 platform-abstraction | `src/ocpp/platform.py` | `Platform` (frozen dataclass with `detect()`, `project_root`, `venv_dir_name`, `venv_bin_subdir`, `omo_config_paths`) |
| #2 project-file-format | `src/ocpp/project.py` | `parse_project()`, `serialize_project()`, `mask_value()`, `mask_dict()` — line-based dotenv parser with comment preservation |
| #3 project-bootstrap | `src/ocpp/bootstrap.py` | `run_bootstrap()` — interactive `.project` creation with API key harvesting, gitignore check, and confirmation prompt |
| #4 venv-detection | `src/ocpp/venv.py` | `find_venv()`, `validate_venv()`, `compute_venv_env_delta()`, `VenvResult` — venv discovery and activation env delta |
| #5 omo-config-presets | `src/ocpp/omo.py` | `discover_config()`, `parse_config()`, `list_presets()`, `set_preset()` — OMO config reading, surgical write, `OmoError` |
| #6 launch-opencode | `src/ocpp/launch.py` | `launch_opencode()` — environment merging, binary resolution, platform-specific process launch |

The current `src/ocpp/__main__.py` is a placeholder that prints "Not yet implemented" and returns 0. The `argparse` CLI framework and `rich` library are already available. No wiring code exists yet.

## Goals / Non-Goals

**Goals:**

- Wire `main()` with `argparse` to orchestrate the full six-step flow: bootstrap → load project → detect venv → list/select preset → write preset → launch opencode
- Support `--preset NAME` for non-interactive preset selection (skip the rich prompt)
- Support `--no-launch` to skip the launch step (e.g., for CI or setup-only usage)
- Support `--project-dir PATH` to override the project root directory (default: `Path.cwd()`)
- Support `--dry-run` to show what actions would be taken without writing to disk or launching
- Support `--init` to force bootstrap even if `.project` already exists
- Support `--` separator for passthrough arguments to opencode
- Use `rich` for preset listing (numbered list or table) and confirmation prompts
- Provide clear, actionable error messages for each failure mode
- Ensure each step is skippable on failure with a clear error message (e.g., OMO config missing → continue without preset change)

**Non-Goals:**

- Full TUI or interactive mode beyond simple prompts — future change
- Shell export mode (`eval`-compatible output) — future change
- Configuration file for `ocpp` itself (e.g., `~/.config/ocpp/config.toml`) — out of scope for v1
- Multiple commands or subcommands — `ocpp` is a single-command tool with flags
- Preset editing or creation — already handled by change #5
- Venv creation — out of scope for v1
- Persistent shell environment modification — parent shell is never modified

## Decisions

### 1. argparse (not click/typer) — single command with flags

`argparse` from the stdlib is chosen over `click` or `typer` to avoid additional external dependencies. The CLI is a single command (`ocpp`) with flags, not a multi-command hierarchy. `argparse` handles this pattern cleanly with a straightforward `ArgumentParser` definition. The `--` passthrough is handled via `argparse.REMAINDER` or by parsing known flags first and collecting remaining arguments.

### 2. Flow: bootstrap → load project → detect venv → list presets → select → write preset → launch

The execution order is designed to fail early and provide maximum context before requiring user input:

1. **Bootstrap** (if `.project` missing or `--init`): Creates `.project` interactively. If the user declines bootstrap, the tool exits with an error — there is no `.project` to load.
2. **Load .project**: Parse the `.project` file. If parsing fails, show a clear error with the file path and line number; offer to re-bootstrap.
3. **Detect venv**: Find and validate the venv. If no venv is found, emit a warning and continue (venv is optional for opencode).
4. **List presets**: Discover and parse the OMO config. If OMO config is missing, emit a warning and offer to skip preset selection.
5. **Select preset**: If `--preset` was given, validate the preset name exists and use it directly. Otherwise, use `rich` to display a numbered list and prompt the user. If the user cancels, skip the preset write.
6. **Write preset**: Perform the surgical write via `omo.set_preset()`. Skip if `--dry-run`.
7. **Launch opencode**: Build the merged environment (`os.environ` + `.project` values + venv delta), resolve `opencode` binary, and launch. Skip if `--no-launch` or `--dry-run`.

### 3. `--preset` skips preset prompt (non-interactive)

When `--preset NAME` is provided, the CLI skips the rich preset listing prompt and uses the given name directly. The preset name is validated against the parsed `"presets"` object. If the name is not found, the CLI prints an error listing available presets and exits with non-zero status. This enables scripted/CI usage.

### 4. `--no-launch` does everything except launch

All steps up to and including the preset write are executed. The launch step is skipped. This is useful for setup-only invocations (e.g., in CI or when setting up a new project).

### 5. `--dry-run` shows actions without writing or launching

Each step that would modify state (bootstrap write, preset write, gitignore modification) is shown as a log message but not executed. The launch step is also skipped. The dry-run output shows the full plan of what `ocpp` would do, including the selected preset name, the venv path, and the merged environment overview (without printing secret values).

### 6. `--init` forces bootstrap

Normally, bootstrap is skipped if `.project` already exists. With `--init`, the bootstrap is forced even if `.project` exists. The existing `.project` is backed up (`.project.bak`), then the bootstrap creates a new `.project`. The user is warned about the backup before proceeding.

### 7. `--project-dir` overrides cwd

When `--project-dir PATH` is provided, the platform's `project_root` is overridden to the given path. All file lookups (`.project`, venv, OMO config) are relative to this path. The default is `Path.cwd()`.

### 8. `--` separator for passthrough args

All arguments after `--` are collected and passed directly to `opencode` as-is. For example:
```
ocpp --preset openrouter --no-launch -- --model claude-3-opus --temperature 0.7
```
Results in `opencode` being launched with `--model claude-3-opus --temperature 0.7` appended.

### 9. `rich` for preset listing (numbered list)

The preset listing uses `rich` to display a numbered list of available presets with the current preset highlighted. The user enters a number to select. The `rich.console.Console` and `rich.table.Table` are used for consistent, styled output. `rich.prompt.Prompt` is used for confirmation prompts.

### 10. Each step has a clear error message on failure

Every step in the flow has a typed error handler that produces a user-facing message explaining:
- What went wrong (e.g., "OMO config file not found at: <paths>")
- What the user can do to fix it (e.g., "Run `oh-my-opencode-slim setup` to create one, or use `--skip-preset` to continue without preset changes")
- The exit code is non-zero

## Risks / Trade-offs

- **User may not have opencode installed**: The launch step calls `shutil.which("opencode")` and fails if the binary is not found. **Mitigation**: A clear error message is shown at the launch step: "opencode binary not found on PATH. Install opencode (https://github.com/opencode-ai/opencode) or use `--no-launch` to skip launching." The tool exits with non-zero status.
- **OMO config may be missing**: The user may not have `oh-my-opencode-slim` installed, meaning no OMO config file exists. **Mitigation**: The CLI detects this at the preset listing step, prints a warning: "OMO config not found. Preset selection skipped. You can run `oh-my-opencode-slim setup` to create one." The flow continues to the launch step without changing presets.
- **.project may have invalid format**: The `.project` file could be manually edited with invalid syntax. **Mitigation**: The parse error is reported with the file path and line number. The user is offered to re-bootstrap (which backs up the existing `.project` and creates a fresh one).
- **Venv not found**: A project may not have a Python venv. **Mitigation**: Emit a warning and continue. The venv is optional for opencode — it only affects the subprocess environment.
- **--preset value may not exist**: The user may provide a preset name that does not exist in the OMO config. **Mitigation**: Print an error listing all available preset names and exit with non-zero status.
- **argparse.REMAINDER behavior on Windows**: `argparse.REMAINDER` has inconsistent behavior across platforms. **Mitigation**: Use `parse_known_args()` to extract known flags, then collect unrecognized args as passthrough. This is more portable than `REMAINDER`.