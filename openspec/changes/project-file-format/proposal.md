## Why

The `ocpp` tool needs to read and write environment variable overrides — primarily API keys for various LLM providers (Anthropic, OpenAI, OpenRouter, Google/Gemini, xAI, Mistral) — from a `.project` file in the project root. This file serves as the single source of truth for per-project environment configuration, enabling the bootstrap (change #3) and launch (change #6) workflows to apply the correct credentials without modifying the user's shell profile or global environment. A defined format with a reusable parser and serializer is required before those dependent changes can be implemented.

## What Changes

A new `src/ocpp/project.py` module implementing:

- **`.project` file format spec**: dotenv-style (`KEY=value`), one entry per line, `#` line comments, split on first `=`, no interpolation or command substitution, UTF-8 encoding
- **Parser**: reads `.project` from the project root, returns an ordered dictionary of key→value pairs, tracks comment lines for preservation on rewrite
- **Serializer**: writes `.project` back to disk preserving all comments, blank lines, and unknown non-key-value lines
- **Value masking**: utility to mask secret values (e.g., `KEY=***`) in all diagnostic output — never prints actual secret values
- **Validation**: rejects invalid variable names (non-`[A-Za-z_][A-Za-z0-9_]*`) and embedded newlines in values
- **Reserved key**: `OCPP_PROJECT_NAME` is recognized and reserved for project naming

## Capabilities

### New Capabilities

- `project-file`: Dotenv-style `.project` file parsing, serialization, validation, and value masking for diagnostics

### Modified Capabilities

<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/project.py` — parser, serializer, value masking, validation logic
- **No existing code is modified** — this is pure addition
- **No new external dependencies** — uses only stdlib (`pathlib`, `re` for validation)
- **Dependent changes**: change #3 (project-bootstrap) and change #6 (launch-opencode) will depend on this module