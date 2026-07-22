# AGENTS.md

## Project

Python CLI/TUI tool that sets up the correct environment keys (API credentials) and applies oh-my-opencode-slim (OMO) presets to a user's OpenCode configuration on the local machine.

## Build & Run

```bash
# Create venv and install (first time)
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -e ".[dev]"

# Run during development
python -m opencode_profile_picker

# Lint & type-check before committing
ruff check .
ruff format --check .
mypy src/
```

## Packaging

Single-file executable via PyInstaller or Nuitka. The executable must bundle all dependencies and work without a Python runtime on the target machine.

## Architecture

- **TUI framework**: Use Textual or Rich for the terminal interface. Do not use curses directly.
- **Environment keys**: Help the user add/edit API keys (Anthropic, OpenAI, etc.) into OpenCode config or environment. Never log or print secret values. Detect the active shell before writing env vars.
- **OMO presets**: Apply predefined oh-my-opencode-slim preset bundles (agents, models, prompts, skills, MCPs) to a user's OpenCode config.
- **Discovery**: Scan known filesystem paths for OpenCode/OMO config. Do not shell out to `opencode` CLI for discovery — read config files directly.
- **Config mutation**: Write changes back to the discovered config files. Never delete or reformat config the user didn't touch.
- **Environment variables**: Set via the current shell session or by writing to shell profile files (`.bashrc`, `.zshrc`, PowerShell profile, etc.). Detect the active shell before writing.

## Key Paths (platform-aware)

| What | Windows | macOS/Linux |
|------|---------|-------------|
| OpenCode user config | `%APPDATA%\opencode\` or `~\.config\opencode\` | `~/.config/opencode/` |
| OpenCode project config | `<project>\.opencode\` or `<project>\opencode.jsonc` | `<project>/.opencode/` or `<project>/opencode.jsonc` |
| OMO config | `%APPDATA%\opencode\` (same tree) | `~/.config/opencode/` (same tree) |
| Shell profiles | PowerShell `$PROFILE`, cmd via registry | `~/.bashrc`, `~/.zshrc`, `~/.profile` |

## Conventions

- Python 3.11+ (match the latest stable available).
- `src/` layout: source under `src/opencode_profile_picker/`, tests under `tests/`.
- Use `pathlib.Path`, not `os.path`.
- Platform-specific logic behind a clean abstraction — never scatter `if sys.platform` through business logic.
- Config files are JSON/JSONC. Use a JSONC-tolerant parser (e.g., `json5`) for reading; preserve formatting on write when possible.
- No destructive operations without explicit user confirmation.