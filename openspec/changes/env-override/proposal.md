# OpenSpec Proposal: `env-override`

## 1. Proposal Metadata
- **Change Name**: `env-override`
- **Description**: Parse `.env` files in the project root and force-set the keys in the environment, overriding existing values. The feature is always enabled and skips OMO preset logic and OpenCode launch if `.env` is processed.
- **Status**: `proposed`
- **Author**: orchestrator
- **Date**: 2026-07-26

---

## 2. Goals and Non-Goals

### Goals
- Parse `.env` files in the project root and **force-set** the keys in the environment, overriding existing values.
- Use `python-dotenv` for robust parsing (supports comments, quotes, etc.).
- Log overridden keys (mask sensitive values, e.g., `OPENAI_API_KEY=sk-proj-****`).
- Skip OMO preset logic and OpenCode launch if `.env` is processed.
- **Always enable** the feature (no opt-in flag required).

### Non-Goals
- Do **not** create a `.env` file if it doesn’t exist.
- Do **not** override keys that are **not** in `.env`.
- Do **not** modify OMO preset logic or OpenCode launch behavior unless `.env` is processed.
- Do **not** support full `.env` semantics (e.g., `export`, multiline values, variable interpolation).

---

## 3. Motivation
- Users often rely on `.env` files for API keys and configuration.
- The current tool doesn’t parse `.env` files, forcing users to manually set environment variables.
- This change simplifies environment setup and ensures consistency.

---

## 4. Design

### Workflow
1. Check for `.env` in the project root.
2. If `.env` exists, parse it using `python-dotenv` and force-set keys in `os.environ`.
3. Log overridden keys (mask sensitive values).
4. Skip OMO preset logic and OpenCode launch if `.env` is processed.
5. If `.env` is not found, log a **notice**: `"No .env file found in project root. Skipping environment overrides."`
6. **Always enabled**: No opt-in flag required.

### Key Components
- **`.env` Parser**: `src/ocpp/env.py` (new file).
  - Uses `python-dotenv` to parse `.env` files.
  - Force-sets keys in `os.environ` (overrides existing values).
  - Returns a dict of overridden keys for logging.
- **CLI Integration**: `src/ocpp/__main__.py`.
  - Calls `load_env_file()` at the start of `main()`.
  - Logs overridden keys using `rich.console`.
  - Skips OMO preset logic and OpenCode launch if `.env` is processed.

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
1. Add `python-dotenv` to `pyproject.toml`.
2. Create `src/ocpp/env.py` with `load_env_file()`.
3. Integrate `.env` parsing into `src/ocpp/__main__.py`.
4. Add logging for overridden keys.
5. Test edge cases (e.g., `.env` not found, malformed `.env`).

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