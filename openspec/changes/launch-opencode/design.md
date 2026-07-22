## Context

Change #2 (project-file-format) provides the `.project` parser that returns an ordered dict of key-value overrides from the project root. Change #4 (venv-detection) provides the venv env delta — a `dict[str, str | None]` with `PATH` prepend, `VIRTUAL_ENV`, and optional `PYTHONHOME` unset. No launch mechanism exists yet in the codebase; `__main__.py` is a skeleton that prints a placeholder message. The `ocpp` tool must combine these two data sources with the current environment and launch `opencode` as a subprocess (or process replacement on POSIX). The environment merge order is critical: `.project` overrides must not be able to break venv resolution by shadowing the venv's PATH.

## Goals / Non-Goals

**Goals:**

- Build the final merged environment: `os.environ` → overlay `.project` overrides → apply venv delta (PATH prepend last)
- Resolve the `opencode` binary via `shutil.which` using the merged PATH
- Launch `opencode` with the merged environment:
  - POSIX: `os.execvpe` — replace the current process so `opencode` inherits the terminal and signal handling cleanly
  - Windows: `subprocess.run` + `sys.exit(returncode)` — because `execvpe` is not available on Windows
- Pass through extra command-line arguments after `--` to `opencode`
- Handle missing `opencode` binary with a clear error message and non-zero exit code
- Never use `shell=True`

**Non-Goals:**

- Shell environment export mode (e.g., `eval`-compatible output for sourcing) — deferred to a future change if needed
- Persistent shell modification (modifying the parent shell's environment) — explicitly excluded per AGENTS.md
- Launching other tools or binaries besides `opencode`
- Interactive prompt before launch — the launch is the final step after all configuration is applied
- Logging or printing the merged environment (except masked diagnostic output)

## Decisions

### 1. Env merge order: `os.environ` → `.project` overrides → venv delta (PATH prepend last)

The merge order is:

1. Start with a copy of `os.environ`
2. Overlay `.project` key-value pairs (these are user-configured overrides, e.g., API keys)
3. Apply venv delta LAST — this prepends the venv `bin`/`Scripts` directory to PATH, sets `VIRTUAL_ENV`, and unsets `PYTHONHOME`

This ordering ensures that the venv PATH entry takes highest priority. If `.project` contained a `PATH` override, it would be applied in step 2, but the venv delta's PATH prepend in step 3 would still place the venv's bin directory first. This is intentional: the venv should always take precedence for its own Python interpreter and installed tools, and `.project` PATH overrides should not be able to break venv resolution.

### 2. Resolve `opencode` via `shutil.which` in the merged PATH

`shutil.which("opencode")` is called after the merged environment is built, using the merged PATH. This ensures the resolution sees the venv's PATH entry first, so if `opencode` is installed in the venv, it is found before any system-wide installation. `shutil.which` correctly handles Windows executable extensions (`.exe`, `.cmd`) via `PATHEXT`.

### 3. POSIX: `os.execvpe` (replace process)

On POSIX systems, `os.execvpe` replaces the current process with `opencode`. This is the correct behavior for a launcher tool:

- The `opencode` process inherits the same PID, terminal, signal handlers, and process group
- No orphaned parent process is left behind
- The `ocpp` process is fully replaced — there is no way for the user to accidentally leave `ocpp` running in the background
- Exit codes and signals from `opencode` propagate directly to the shell

### 4. Windows: `subprocess.run` + `sys.exit(returncode)`

Windows does not support `os.execvpe` (no `exec` family of system calls). Instead, `subprocess.run` is used to launch `opencode` as a child process, and `sys.exit(returncode)` propagates the exit code. This is the standard approach for Windows launchers. The child process inherits the merged environment.

### 5. Never `shell=True`

`shell=True` is a security risk and is never used. The `opencode` binary path is resolved via `shutil.which` and passed as a list to `os.execvpe` / `subprocess.run`. Arguments are passed as a list, never as a shell command string.

### 6. Pass through extra argv after `--`

The `ocpp` CLI parses its own arguments and passes all remaining arguments after `--` directly to `opencode`. This is implemented via `argparse.REMAINDER` or by consuming known flags and forwarding the rest. For example:

- `ocpp launch -- --model claude-3-opus --temperature 0.7` → `opencode` receives `["--model", "claude-3-opus", "--temperature", "0.7"]`
- `ocpp launch` (no extra args) → `opencode` receives no extra arguments

### 7. Missing `opencode`: clear error message, non-zero exit

If `shutil.which("opencode")` returns `None`, the tool prints a clear error message to stderr (e.g., "opencode not found in PATH. Is it installed?") and exits with code 1. No attempt is made to guess alternative paths or install `opencode`.

## Risks / Trade-offs

- **`opencode` on Windows is likely a `.cmd`/`.exe` npm shim**: On Windows, `opencode` may be a `.cmd` batch file or `.exe` shim installed by npm. `shutil.which` handles this correctly via `PATHEXT`, and the resolved full path is passed to `subprocess.run`. **Mitigation**: `shutil.which` returns the full path including extension, and `subprocess.run` can launch `.cmd` files directly on Windows.
- **PATH from `.project` could shadow venv**: If `.project` contains a `PATH` override, it would be applied in step 2 before the venv delta. But the venv delta's PATH prepend in step 3 places the venv bin directory first, so the `.project` PATH cannot shadow the venv's Python. **Mitigation**: Venv delta PATH prepend is applied last, ensuring venv PATH takes priority.
- **Windows environment variable names are case-insensitive**: On Windows, `PATH` and `Path` are the same variable. Overlaying `.project` values could create duplicate or conflicting entries. **Mitigation**: The venv delta computation (change #4) uses `os.environ` to get the current PATH, which on Windows returns the correct case. The `.project` parser returns keys as-is, but the launcher should handle case-insensitive overlay on Windows by normalizing keys to uppercase before merging.
- **`os.execvpe` on POSIX means no recovery after launch**: If `os.execvpe` fails (e.g., `opencode` binary was deleted between resolution and exec), the process is already replaced and cannot recover. **Mitigation**: The `shutil.which` check happens immediately before `os.execvpe`, so the race window is very small. If `os.execvpe` fails, `OSError` is caught and a clear error is printed before the process exits.
- **No venv found is not an error**: If `find_venv` returns `None` (no venv exists), the launcher proceeds without venv activation. The merged environment will still include `.project` overrides. This is intentional — the user may not need a venv for their setup.