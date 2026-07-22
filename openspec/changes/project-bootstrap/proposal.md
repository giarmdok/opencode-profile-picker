## Why

When a user runs `ocpp` in a new project, there is no `.project` file in the project root. The tool should bootstrap one automatically — deriving a project name from the current working directory and harvesting existing API keys from the user's environment — so the user does not have to create or populate the file manually. Without this change, every new project would require the user to write a `.project` file by hand before `ocpp` can launch `opencode` with the correct configuration.

## What Changes

A new bootstrap module/function in `src/ocpp/bootstrap.py` that:

- Checks for the existence of a `.project` file in the project root
- If absent, derives `OCPP_PROJECT_NAME` from the current working directory name (sanitized)
- Harvests non-empty values from the environment for a fixed allowlist of API key variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `MISTRAL_API_KEY`
- Presents the user with a summary of what will be written (with values masked) and requests confirmation
- On confirmation, writes the `.project` file using the project-file serializer from change #2
- Detects whether the project is a git repository; if so, checks whether `.project` is already in `.gitignore`; if not, warns the user and offers to append it
- Sets restrictive file permissions (0o600 or equivalent) on the `.project` file where the platform supports it

## Capabilities

### New Capabilities
- `project-bootstrap`: Auto-create a `.project` file when one does not exist, deriving the project name from the cwd directory name and harvesting non-empty API keys from the current environment, with user confirmation, gitignore warnings, and restrictive file permissions

### Modified Capabilities
<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/bootstrap.py` — bootstrap orchestration logic
- **Depends on**: change #1 (platform-abstraction) for platform-aware path resolution and file permissions; change #2 (project-file-format) for `.project` parsing, serialization, and value masking
- **No existing code is modified** — this is pure addition
- **No new external dependencies** — uses only stdlib (`pathlib`, `os`, `getpass`)