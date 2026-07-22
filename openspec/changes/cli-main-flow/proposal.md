## Why

All six individual components of the `ocpp` tool are now implemented: platform abstraction (change #1), project file format parser (change #2), project bootstrap (change #3), venv detection (change #4), OMO config presets (change #5), and the opencode launcher (change #6). However, they are not wired together — there is no user-facing CLI that orchestrates the full flow from bootstrap to launch. The current `__main__.py` is a placeholder that prints "Not yet implemented" and exits. Without a wired CLI, the tool is unusable. This change delivers the final integration layer that makes `ocpp` a functional end-to-end tool.

## What Changes

Rewrite `src/ocpp/__main__.py` to implement `main()` with `argparse` that orchestrates the full six-step flow:

1. Bootstrap (if `.project` missing or `--init` flag)
2. Load `.project` via the project-file parser
3. Detect venv via venv-detection module
4. List/select preset via omo-config-presets module (with `rich` for listing)
5. Write selected preset via omo-config-presets surgical write
6. Launch opencode via launch-opencode module with merged environment + venv

Add the following CLI flags to `argparse`:
- `--preset NAME` — non-interactive preset selection (skip the rich prompt)
- `--no-launch` — do everything except launch opencode
- `--project-dir PATH` — override project root directory (default: cwd)
- `--dry-run` — show what actions would be taken, do not write to disk or launch
- `--init` — force bootstrap even if `.project` already exists
- `--` separator — passthrough remaining arguments to opencode

Use `rich` for preset listing (numbered list or table) and confirmation prompts. Provide clear error messages for each failure mode (missing OMO config, invalid `.project`, missing opencode binary, etc.).

## Capabilities

### New Capabilities
- `cli-flow`: Full `argparse`-based CLI that orchestrates bootstrap → project load → venv detection → preset selection → preset write → opencode launch, with flags for non-interactive mode (`--preset`), dry-run (`--dry-run`), force-init (`--init`), project directory override (`--project-dir`), no-launch (`--no-launch`), and argument passthrough (`--`)

### Modified Capabilities
- `src/ocpp/__main__.py`: placeholder skeleton rewritten to full orchestration CLI

## Impact

- **Modified file**: `src/ocpp/__main__.py` — the only file changed
- **New dependencies**: `rich` (already available in the project)
- **Depends on**: all previous 6 changes — `platform.py` (change #1), `project.py` (change #2), `bootstrap.py` (change #3), `venv.py` (change #4), `omo.py` (change #5), `launch.py` (change #6)
- **No new source modules** — this change only wires existing modules together in the CLI entry point