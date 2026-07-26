# Design Document: `env-override`

## 1. Overview
This document provides a detailed design for the `env-override` change, which adds support for parsing `.env` files in the project root and force-setting environment variables. The feature is **always enabled** and skips OMO preset logic and OpenCode launch if `.env` is processed.

For context, see the [proposal.md](./proposal.md).

---

## 2. Detailed Design

### A. `.env` Parsing
- **Library**: Use [`python-dotenv`](https://saurabh-kumar.com/python-dotenv/) for parsing.
- **File Location**: `.env` in the project root.
- **Behavior**:
  - Force-set keys in `os.environ` (override existing values).
  - Skip invalid lines (log a warning).
  - Return a dict of overridden keys for logging.
- **Example**:
  ```python
  # .env file
  OPENAI_API_KEY=sk-proj-...
  ANTHROPIC_API_KEY=sk-ant-...
  
  # Parsed and force-set in os.environ
  os.environ["OPENAI_API_KEY"] = "sk-proj-..."
  os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
  ```

### B. Logging
- **Overridden Keys**: Log a diff of old vs. new values (mask sensitive values).
  - Example: `OPENAI_API_KEY: sk-old-**** → sk-new-****`.
- **Missing `.env`**: Log a notice:
  `"No .env file found in project root. Skipping environment overrides."`
- **Invalid Lines**: Log a warning for skipped lines.
- **Empty `.env`**: Log a message:
  `"Empty .env file. No overrides applied."`

### C. CLI Integration
- **Entry Point**: Call `load_env_file()` at the start of `main()` in `src/ocpp/__main__.py`.
- **Behavior**:
  - Skip OMO preset logic and OpenCode launch if `.env` is processed.
  - Always enabled (no opt-in flag).
- **Example**:
  ```python
  def main():
      overridden_keys = load_env_file()
      if overridden_keys:
          console.print("[yellow]Overridden environment variables:[/yellow]")
          for key, old_value in overridden_keys.items():
              masked_old = f"{old_value[:5]}****" if old_value else "None"
              masked_new = f"{os.environ[key][:5]}****"
              console.print(f"  - {key}: {masked_old} → {masked_new}")
      else:
          console.print("[green]No .env file found or no overrides applied.[/green]")
  ```

### D. Error Handling
- **Missing `.env`**: Skip parsing, log a notice.
- **Malformed `.env`**: Skip invalid lines, log a warning.
- **Permission Issues**: Log an error and continue.

---

## 3. Implementation Details

### A. New Files
- **`src/ocpp/env.py`**:
  - `load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]`
    - Parses `.env` using `python-dotenv`.
    - Force-sets keys in `os.environ`.
    - Returns overridden keys for logging.

### B. Modified Files
- **`src/ocpp/__main__.py`**:
  - Call `load_env_file()` at the start of `main()`.
  - Add logging for overridden keys.
  - Skip OMO preset logic and OpenCode launch if `.env` is processed.

### C. Dependencies
- Add `python-dotenv = "^1.0.0"` to `pyproject.toml`.

---

## 4. Testing Strategy

### A. Unit Tests
- **`.env` Parsing**:
  - Test valid `.env` files (e.g., `KEY=value`).
  - Test invalid lines (e.g., `KEY=`, `KEY`).
  - Test comments (e.g., `# comment`).
- **Environment Overrides**:
  - Test that `.env` keys override existing `os.environ` values.
  - Test that keys not in `.env` are unchanged.

### B. Integration Tests
- **CLI Integration**:
  - Test that `load_env_file()` is called at the start of `main()`.
  - Test logging for overridden keys.
  - Test skipping OMO preset logic and OpenCode launch.

### C. Edge Cases
- **Missing `.env`**: Verify notice is logged.
- **Empty `.env`**: Verify message is logged.
- **Malformed `.env`**: Verify warnings are logged for invalid lines.

---

## 5. Open Questions
- None (resolved in [proposal.md](./proposal.md)).

---

## 6. References
- [`python-dotenv` documentation](https://saurabh-kumar.com/python-dotenv/)
- [`.env` file format](https://hexdocs.pm/dotenvy/dotenv-file-format.html)