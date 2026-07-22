## Why

The `ocpp` tool must run on Windows, Linux, and macOS/Unix (BSD, etc.) to support users across different development environments. Currently, the codebase has no platform abstraction — any `sys.platform` checks would be scattered across business logic modules, making the code fragile, hard to test, and difficult to maintain as the project grows. This change introduces a single source of truth for all platform-specific knowledge so that every subsequent change can rely on clean, platform-agnostic APIs.

## What Changes

A new `src/ocpp/platform.py` module is created containing a `Platform` facade (a frozen dataclass or protocol) that exposes:

- **OS family classification**: `win32` → `Windows`, `linux` → `Linux`, everything else (including `darwin`, `freebsd`, etc.) → `Unix`
- **Venv directory name**: `.venv_win` / `.venv_lin` / `.venv_unx` per platform, with `.venv` as a generic fallback
- **Venv bin subdirectory**: `Scripts` on Windows, `bin` on POSIX
- **OMO config path search order**: `~/.config/opencode/oh-my-opencode-slim.json` first on all platforms, then `%APPDATA%\opencode\` as a Windows fallback; both `.json` and `.jsonc` variants are checked
- **Project root resolution**: defaults to the current working directory

The `Platform` instance is injectable — callers can override `home_dir` and the platform string for testing. No other module in the codebase will contain `import sys` or `sys.platform` checks.

## Capabilities

### New Capabilities
- `platform-paths`: Platform-aware path resolution for venv directory names, venv bin subdirectories, OMO config file search paths, and project root directory

### Modified Capabilities
<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/platform.py` — the only file introduced
- **No existing code is modified** — this is pure addition
- **No new external dependencies** — uses only stdlib (`pathlib`, `sys`, `dataclasses`, `os`)
- **All future changes** will depend on this module for platform decisions