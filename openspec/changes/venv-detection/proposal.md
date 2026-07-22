## Why

The `ocpp` tool must find and "activate" a Python virtual environment so that `opencode` (and any processes it spawns) use the project's Python environment — including the correct interpreter, installed packages, and environment isolation. Without venv detection, `ocpp` cannot guarantee that `opencode` runs with the right dependencies. Venv detection must be platform-aware because venv directory names and binary subdirectories differ between Windows (`.venv_win`, `Scripts\`) and POSIX systems (`.venv_lin`/`.venv_unx`, `bin/`).

## What Changes

A new `src/ocpp/venv.py` module that:

- Locates a platform-specific venv directory in the project root (`.venv_win` / `.venv_lin` / `.venv_unx`, with `.venv` as a generic fallback)
- Validates the venv by checking that the interpreter executable exists in the bin subdirectory
- Computes an activation environment delta: prepend the bin directory to `PATH`, set `VIRTUAL_ENV` to the venv root, and unset `PYTHONHOME` if present
- Returns `None` if no valid venv is found (not an error — the caller decides how to handle it)

## Capabilities

### New Capabilities

- `venv-detection`: Locate, validate, and compute the activation environment delta for platform-specific Python virtual environments in the project root

### Modified Capabilities

<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/venv.py` — venv discovery, validation, and env delta computation
- **No existing code is modified** — this is pure addition
- **Depends on**: change #1 (platform-abstraction) for venv directory names and bin subdirectory names
- **No new external dependencies** — uses only stdlib (`pathlib`, `os`, `shutil`)
