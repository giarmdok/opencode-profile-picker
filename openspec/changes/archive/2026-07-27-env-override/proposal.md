# OpenSpec Proposal: `env-override`

## 1. Proposal Metadata
- **Change Name**: `env-override`
- **Description**: Parse `.env` files in the project root and merge the keys into the environment dictionary emitted to stdout, overriding existing values. The feature is always enabled and skips OMO preset logic if `.env` is processed.
- **Status**: `proposed`
- **Author**: orchestrator
- **Date**: 2026-07-26

---

## 2. Goals and Non-Goals

### Goals
- Parse `.env` files in the project root and merge the keys into the environment dictionary emitted to stdout, overriding existing values.
- Use `python-dotenv` for robust parsing (supports comments, quotes, etc.).
- Log overridden keys (mask sensitive values, e.g., `OPENAI_API_KEY=sk-proj-****`).
- Skip OMO preset logic if `.env` is processed.
- **Always enable** the feature (no opt-in flag required).

### Non-Goals
- Do **not** create a `.env` file if it doesn’t exist.
- Do **not** override keys that are **not** in `.env`.
- Do **not** modify OMO preset logic unless `.env` is processed.
- Do **not** support full `.env` semantics (e.g., `export`, multiline values, variable interpolation).

---

## 3. Motivation
- Users often rely on `.env` files for API keys and configuration.
- The current tool doesn’t parse `.env` files, forcing users to manually set environment variables.
- This change simplifies environment setup and ensures consistency by emitting these variables for the parent shell to evaluate.

---

## 4. Design

### Workflow
1. Check for `.env` in the project root.
2. If `.env` exists, parse it using `python-dotenv` and return the key-value pairs.
3. Merge these pairs into the main environment dictionary that gets passed to `_emit_env_commands`.
4. Log overridden keys (mask sensitive values).
5. Skip OMO preset logic if `.env` is processed.
6. If `.env` is not found, log a **notice**: `"No .env file found in project root. Skipping environment overrides."`
7. **Always enabled**: No opt-in flag required.

### Key Components
- **`.env` Parser**: `src/ocpp/env.py`.
  - Uses `python-dotenv` to parse `.env` files.
  - Returns a dictionary of parsed key-value pairs.
- **CLI Integration**: `src/ocpp/__main__.py`.
  - Calls `load_env_file()` in `main()`.
  - Merges the returned dictionary into the `project_kv` dictionary.
  - Logs overridden keys using `rich.console`.
  - Skips OMO preset logic if `.env` is processed.

### Edge Cases
| Scenario | Behavior |
|----------|----------|
| `.env` not found | Skip parsing, log a **notice**: `"No .env file found in project root. Skipping environment overrides."` |
| Malformed `.env` | `python-dotenv` skips invalid lines. |
| Empty `.env` | No overrides, log a message. |
| Conflicts with `.project` | `.env` keys override `.project` keys. |
| Sensitive keys in logs | Mask values (e.g., `OPENAI_API_KEY=sk-proj-****`). |

---

## 5. Tasks
1. Modify `src/ocpp/env.py:load_env_file()` to return a dict of parsed key-value pairs instead of modifying `os.environ`.
2. Update `src/ocpp/__main__.py:main()` to call `load_env_file()` and merge the results into the environment dictionary.
3. Add logging for overridden keys.
4. Implement logic to skip OMO preset selection when a `.env` file is processed.
5. Fix integration tests in `tests/test_cli.py` to assert against captured stdout, not `os.environ`.

---

## 6. Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| `.env` keys override critical system variables | Document the override behavior clearly. |
| Malformed `.env` causes crashes | Use `python-dotenv` for robust parsing. |
| Sensitive keys leaked in logs | Mask values in logs. |

---

## 7. Alternatives Considered
- **Custom Parser**: Reuse `.project` file logic, but `python-dotenv` is more robust.
- **No Overrides**: Require users to manually set environment variables, but this reduces usability.
