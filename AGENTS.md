# AGENTS.md

## Project

Python CLI tool that sets up the correct environment keys (API credentials) and applies oh-my-opencode-slim (OMO) presets to a user's OpenCode configuration on the local machine, then launches opencode with the right environment and venv.

## Build & Run

```bash
# Create venv and install (first time)
python -m venv .venv_win   # Windows
python -m venv .venv_lin   # Linux
python -m venv .venv_unx   # macOS/Unix
.venv_win\Scripts\Activate.ps1   # Windows
pip install -e ".[dev]"

# Run during development
# NOTE: Use --no-launch when testing to avoid recursion
python -m ocpp --no-launch

# Lint & type-check before committing
ruff check .
ruff format --check .
mypy src/
```

## Testing `ocpp`

### **⚠️ IMPORTANT: Use `--no-launch` when running inside OpenCode.**

When testing `ocpp` or running it inside OpenCode, **always** use the `--no-launch` flag to prevent recursion:

```bash
python -m ocpp --no-launch
```

This ensures `ocpp` does not attempt to launch OpenCode while running inside OpenCode.

### **Enforcement**
- The `ocpp` CLI **launches OpenCode by default** unless `--no-launch` is specified.
- **`--no-launch` is required** when testing or running inside OpenCode to prevent recursion.
- **Never run `ocpp` without `--no-launch`** unless you are explicitly testing the launch behavior.
- **You are responsible for using `--no-launch`** when running inside OpenCode.

## Packaging

Single-file executable via PyInstaller or Nuitka. The executable must bundle all dependencies and work without a Python runtime on the target machine.

## Architecture

- **Launcher model**: ocpp builds a merged environment (current env + `.project` overrides + venv delta) and launches `opencode` as a subprocess with that environment. It does **not** modify the parent shell's environment variables. If shell persistence is needed in the future, an `eval`-compatible output mode can be added.
- **CLI framework**: stdlib `argparse` with `rich` for listing/prompts. No full TUI for v1.
- **Environment keys**: Read/write API keys (Anthropic, OpenAI, OpenRouter, Google/Gemini, xAI, Mistral) in a `.project` file in the project root. Never log or print secret values.
- **OMO presets**: Read the global `oh-my-opencode-slim.json`, list available presets for the user to choose, and update the `"preset"` field via surgical text edit (not full re-serialization) to preserve comments and formatting.
- **Discovery**: Scan known filesystem paths for OpenCode/OMO config. Do not shell out to `opencode` CLI for discovery — read config files directly.
- **Config mutation**: Write changes back to the discovered config files. Never delete or reformat config the user didn't touch.
- **Venv detection**: Find platform-specific venv (`.venv_win`/`.venv_lin`/`.venv_unx` or generic `.venv`) in the project root. "Activation" = env manipulation (prepend bin dir to `PATH`, set `VIRTUAL_ENV`, unset `PYTHONHOME`), not sourcing activate scripts.

## Key Paths (platform-aware)

| What | Windows | macOS/Linux |
|------|---------|-------------|
| OpenCode user config | `%APPDATA%\opencode\` or `~\.config\opencode\` | `~/.config/opencode/` |
| OpenCode project config | `<project>\.opencode\` or `<project>\opencode.jsonc` | `<project>/.opencode/` or `<project>/opencode.jsonc` |
| OMO config | `~\.config\opencode\oh-my-opencode-slim.json` (fallback: `%APPDATA%\opencode\`) | `~/.config/opencode/oh-my-opencode-slim.json` |
| Python venv | `<project>\.venv_win\` (or `.venv\`) | `<project>/.venv_lin/` (Linux), `<project>/.venv_unx/` (macOS/Unix), or `.venv/` |
| Venv bin subdir | `Scripts\` | `bin/` |
| Project file | `<project>\.project` | `<project>/.project` |

## Conventions

- Python 3.11+ (match the latest stable available).
- `src/` layout: source under `src/ocpp/`, tests under `tests/`.
- Use `pathlib.Path`, not `os.path`.
- Platform-specific logic behind a clean abstraction — never scatter `if sys.platform` through business logic.
- Config files are JSON/JSONC. Use a JSONC-tolerant parser (e.g., `json5`) for reading; preserve formatting on write via surgical text edits, not full re-serialization.
- `.project` files are dotenv-style `KEY=value` with `#` comments. Reserved key: `OCPP_PROJECT_NAME`.
- No destructive operations without explicit user confirmation.
- Never log or print secret values. Mask API keys in all output.
