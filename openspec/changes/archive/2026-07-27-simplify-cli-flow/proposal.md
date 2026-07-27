## Why

The current CLI has grown complex, including functionality related to `.project` files, bootstrapping, and multiple flags that are no longer needed. This change simplifies the tool to its core purpose: loading API keys from a `.env` file, selecting an OMO preset, and activating a Python virtual environment.

## What Changes

- Remove all code and tests related to `.project` files and the `--init` flag.
- Remove the `--no-launch`, `--project-dir`, and `--dry-run` flags. The only retained flag will be `--preset`.
- The CLI will now perform these steps in order:
  1. Look for a `.env` file in the current directory and load OpenCode API keys if present.
  2. Discover and present OMO presets for selection (unless `--preset` is used).
  3. Detect and activate the appropriate Python virtual environment.
- The core logic will be consolidated into `src/ocpp/__main__.py`.
- The `bootstrap.py` and `project.py` modules will be deleted.

## Capabilities

### New Capabilities
- `simplified-cli-flow`: A streamlined CLI that focuses exclusively on loading a `.env` file, selecting an OMO preset, and activating a Python venv.

### Modified Capabilities
- `cli-flow`: The existing CLI flow is being replaced with a much simpler one.

## Impact

- **Deleted files**: `src/ocpp/bootstrap.py`, `src/ocpp/project.py`, `tests/test_bootstrap.py`, `tests/test_project.py`.
- **Modified files**: `src/ocpp/__main__.py`, `pyproject.toml` (to remove unused dependencies if any), and tests will be updated to reflect the new, simpler functionality.
- **Breaking Changes**: The `--init`, `--no-launch`, `--project-dir`, and `--dry-run` flags will be removed. All functionality related to `.project` files is removed.
