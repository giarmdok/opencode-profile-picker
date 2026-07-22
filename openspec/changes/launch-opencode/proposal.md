## Why

The `ocpp` tool's core purpose is to launch `opencode` with the correct environment (API keys, project-specific overrides) and the project's Python virtual environment activated. Without a launcher, the user must manually set environment variables, activate the venv, and run `opencode` — defeating the purpose of a profile picker. The launcher must merge environment variables in the correct order (`os.environ` → `.project` overrides → venv delta), resolve the `opencode` binary, and handle platform-specific process replacement (POSIX: `os.execvpe` to replace the process; Windows: `subprocess.run` since `execvpe` is not available). This change delivers the launch mechanism that makes `ocpp` functional as a drop-in replacement for running `opencode` directly.

## What Changes

A new `src/ocpp/launch.py` module that:

- Builds the final merged environment: copy `os.environ`, overlay `.project` values from change #2, then apply the venv activation delta from change #4 (PATH prepend applied last)
- Resolves the `opencode` binary via `shutil.which` using the merged PATH
- Launches `opencode` with the merged environment:
  - POSIX: `os.execvpe` (replace the current process so `opencode` replaces `ocpp`)
  - Windows: `subprocess.run` + `sys.exit(returncode)` (no `execvpe` equivalent on Windows)
- Handles missing `opencode` binary gracefully with a clear error message and non-zero exit code
- Passes through extra command-line arguments after `--` (e.g., `ocpp -- --model claude-3-opus` → `opencode --model claude-3-opus`)
- Never uses `shell=True`

## Capabilities

### New Capabilities

- `launch`: Build merged environment (`os.environ` + `.project` overrides + venv delta), resolve `opencode` binary via `shutil.which`, and launch with platform-specific process model (`os.execvpe` on POSIX, `subprocess.run` on Windows)

### Modified Capabilities

<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/launch.py` — environment merging, opencode resolution, platform-specific launch logic
- **No existing code is modified** — this is pure addition
- **Depends on**: change #2 (project-file-format) for `.project` parser, change #4 (venv-detection) for venv env delta
- **No new external dependencies** — uses only stdlib (`os`, `sys`, `shutil`, `subprocess`)