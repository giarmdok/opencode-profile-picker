## Context

The platform-abstraction module (change #1) provides `Platform` with venv directory names (`.venv_win` / `.venv_lin` / `.venv_unx`), the generic `.venv` fallback, and venv bin subdirectory names (`Scripts` on Windows, `bin` on POSIX). No venv detection, validation, or activation logic exists yet in the codebase. The `src/ocpp/` package currently contains only a CLI entry point and the platform module.

## Goals / Non-Goals

**Goals:**

- Locate a platform-specific venv directory in the project root, searching platform-specific name first (`.venv_win` / `.venv_lin` / `.venv_unx`), then `.venv` as a generic fallback
- Validate the venv by checking that the interpreter executable exists in the bin subdirectory (`python.exe` on Windows, `python` on POSIX)
- Compute an activation environment delta as a `dict[str, str | None]`:
  - `PATH`: prepend the bin directory to the current `PATH` value
  - `VIRTUAL_ENV`: set to the venv root directory
  - `PYTHONHOME`: set to `None` (meaning "unset") if present in the current environment
- Return `None` if no valid venv is found — not an error
- Warn the user (via `logging.warning`) if a venv directory exists but is invalid (e.g., missing interpreter)

**Non-Goals:**

- Creating virtual environments — out of scope for v1
- Installing packages into the venv — out of scope for v1
- Venv activation via shell scripts (sourcing `activate` / `Activate.ps1`) — activation is done via env manipulation only, per AGENTS.md
- Shell persistence or `eval`-compatible output modes
- Searching for venvs outside the project root

## Decisions

### 1. Search order: platform-specific first, then `.venv` fallback

The search order is:
1. Platform-specific name: `.venv_win` / `.venv_lin` / `.venv_unx` (from `Platform.venv_dir_name`)
2. Generic fallback: `.venv`

This matches the AGENTS.md convention and the platform-abstraction design. The platform-specific name takes priority because it is unambiguous about which platform it targets. The generic `.venv` is checked second for legacy setups that predate the platform-specific naming convention.

### 2. Validation: interpreter executable exists in bin dir

Validation checks that the interpreter executable exists at `<venv_root>/<bin_subdir>/<interpreter_name>`. The interpreter name is `python.exe` on Windows and `python` on POSIX (Linux/Unix). This is the simplest reliable check — if the interpreter binary is missing, the venv is unusable. No additional checks (e.g., `pyvenv.cfg` parsing, site-packages existence) are performed in v1.

### 3. Env delta as `dict[str, str | None]`

The activation environment delta is a dictionary where:
- Keys are environment variable names
- Values are either `str` (set the variable to this value) or `None` (unset/remove the variable from the environment)

This representation is chosen because:
- It composes cleanly with the launcher's environment merging logic (change #6)
- `None` explicitly signals "remove this variable" vs. "leave it unchanged" (key absent)
- It is serializable and testable without side effects

### 4. PATH prepend only, never replace

The `PATH` value in the delta is constructed by prepending the venv bin directory to the current `PATH`, separated by `os.pathsep`. The original `PATH` is preserved as the tail. This ensures that the venv's binaries take priority without losing access to system-wide tools.

### 5. No venv found = return `None`, not an error

If no venv directory exists, or if the directory exists but is invalid (missing interpreter), the function returns `None`. It does not raise an exception or exit. The caller (the launcher in change #6) decides how to handle the absence of a venv — for example, by proceeding without venv activation or by prompting the user.

### 6. Invalid venv triggers a warning

If a venv directory is found (the directory exists) but validation fails (interpreter missing), a `logging.warning` is emitted. This alerts the user to a potentially corrupted or incomplete venv without aborting the workflow. The function still returns `None`.

## Risks / Trade-offs

- **Venv may be corrupted (missing interpreter)**: A venv directory might exist but be incomplete or corrupted (e.g., interrupted `python -m venv`, manual deletion of the interpreter). **Mitigation**: The validation step checks for the interpreter executable. If missing, a warning is logged and `None` is returned. The caller can then decide whether to proceed without venv activation.
- **Multiple venv directories present**: A project could have both `.venv_win` and `.venv` (or `.venv_lin` and `.venv`). **Mitigation**: The search order is deterministic — platform-specific takes priority, then `.venv`. Only one venv is ever returned.
- **PATH prepend may shadow system Python**: Prepend semantics mean the venv's `python` is found first. This is the desired behavior for activation. **Mitigation**: This is intentional — it is the standard venv activation behavior.
- **No pyvenv.cfg validation**: The current validation only checks for the interpreter binary. A `pyvenv.cfg` file could be missing or malformed while the interpreter exists. **Mitigation**: This is an acceptable trade-off for v1. If the interpreter exists, the venv is functional enough for `opencode` to run. Additional validation can be added in a future change.
