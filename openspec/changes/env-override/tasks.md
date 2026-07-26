# Tasks: `env-override`

## 1. Overview
This document breaks down the implementation of the `env-override` change into small, actionable tasks. For context, see:
- [proposal.md](./proposal.md)
- [design.md](./design.md)

---

## 2. Tasks

### A. Dependency Setup
| Task ID | Description | Owner | Dependencies | Effort | Status |
|---------|-------------|-------|--------------|--------|--------|
| T1 | Add `python-dotenv = "^1.0.0"` to `pyproject.toml` under `[project.dependencies]` | `pyproject.toml` | None | Small | pending |
| T2 | Run `pip install -e ".[dev]"` to install the new dependency | `project root` | T1 | Small | pending |

---

### B. `.env` Parser
| Task ID | Description | Owner | Dependencies | Effort | Status |
|---------|-------------|-------|--------------|--------|--------|
| T3 | Create `src/ocpp/env.py` with `load_env_file()` function | `src/ocpp/env.py` | T1, T2 | Medium | pending |
| T4 | Implement `.env` file discovery (default: project root) | `src/ocpp/env.py` | T3 | Small | pending |
| T5 | Use `python-dotenv.load_dotenv()` to parse `.env` and force-set keys in `os.environ` | `src/ocpp/env.py` | T3, T4 | Small | pending |
| T6 | Return a dict of overridden keys (old value → new value) for logging | `src/ocpp/env.py` | T3, T5 | Small | pending |
| T7 | Handle edge cases: missing `.env`, empty `.env`, malformed lines | `src/ocpp/env.py` | T3-T6 | Medium | pending |

---

### C. CLI Integration
| Task ID | Description | Owner | Dependencies | Effort | Status |
|---------|-------------|-------|--------------|--------|--------|
| T8 | Import `load_env_file` in `src/ocpp/__main__.py` | `src/ocpp/__main__.py` | T3 | Small | pending |
| T9 | Call `load_env_file()` at the start of `main()` | `src/ocpp/__main__.py` | T7 | Small | pending |
| T10 | Skip OMO preset logic and OpenCode launch if `.env` is processed (i.e., if `overridden_keys` is non-empty) | `src/ocpp/__main__.py` | T9 | Small | pending |

---

### D. Logging
| Task ID | Description | Owner | Dependencies | Effort | Status |
|---------|-------------|-------|--------------|--------|--------|
| T11 | Log overridden keys with masked values (e.g., `OPENAI_API_KEY: sk-old-**** → sk-new-****`) | `src/ocpp/__main__.py` | T6, T9 | Small | pending |
| T12 | Log a notice if `.env` is missing: `"No .env file found in project root. Skipping environment overrides."` | `src/ocpp/__main__.py` | T7, T9 | Small | pending |
| T13 | Log a warning for malformed lines in `.env` | `src/ocpp/env.py` | T7 | Small | pending |
| T14 | Log a message if `.env` is empty: `"Empty .env file. No overrides applied."` | `src/ocpp/__main__.py` | T7, T9 | Small | pending |

---

### E. Testing
| Task ID | Description | Owner | Dependencies | Effort | Status |
|---------|-------------|-------|--------------|--------|--------|
| T15 | Write unit tests for `.env` parsing (valid/invalid lines, comments) | `tests/test_env.py` | T3-T7 | Medium | pending |
| T16 | Write unit tests for environment overrides (existing keys, new keys) | `tests/test_env.py` | T15 | Small | pending |
| T17 | Write integration tests for CLI integration (e.g., `load_env_file()` called in `main()`) | `tests/test_cli.py` | T8-T10 | Medium | pending |
| T18 | Write integration tests for logging (overridden keys, missing `.env`, empty `.env`) | `tests/test_cli.py` | T11-T14 | Medium | pending |
| T19 | Test edge cases: missing `.env`, empty `.env`, malformed lines | `tests/test_env.py` | T15-T18 | Small | pending |

---

## 3. Implementation Workflow

### Phase 1: Dependency Setup and `.env` Parser
1. **T1**: Add `python-dotenv` to `pyproject.toml`.
2. **T2**: Install the dependency.
3. **T3-T7**: Implement `load_env_file()` in `src/ocpp/env.py`.

### Phase 2: CLI Integration and Logging
4. **T8-T10**: Integrate `.env` parsing into `src/ocpp/__main__.py`.
5. **T11-T14**: Add logging for overridden keys and edge cases.

### Phase 3: Testing and Validation
6. **T15-T19**: Write and run unit/integration tests.

---

## 4. Open Questions
- None (resolved in [proposal.md](./proposal.md) and [design.md](./design.md)).

---

## 5. References
- [proposal.md](./proposal.md)
- [design.md](./design.md)