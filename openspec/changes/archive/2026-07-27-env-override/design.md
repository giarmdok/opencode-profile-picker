# Design Document: `env-override`

## 1. Overview
This document provides a detailed design for the `env-override` change, which adds support for parsing `.env` files in the project root and merging their variables into the environment dictionary emitted to stdout. The feature is **always enabled** and skips OMO preset logic if `.env` is processed.

For context, see the [proposal.md](./proposal.md).

---

## 2. Detailed Design

### A. `.env` Parsing
- **Library**: Use [`python-dotenv`](https://saurabh-kumar.com/python-dotenv/) for parsing.
- **File Location**: `.env` in the project root.
- **Behavior**:
  - Parse the `.env` file and return a dictionary of key-value pairs.
  - Skip invalid lines (log a warning).
- **Example**:
  ```python
  # .env file
  OPENAI_API_KEY=sk-proj-...
  ANTHROPIC_API_KEY=sk-ant-...
  
  # Parsed and returned as dict
  return {
      "OPENAI_API_KEY": "sk-proj-...",
      "ANTHROPIC_API_KEY": "sk-ant-..."
  }
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
- **Entry Point**: Call `load_env_file()` in `main()` in `src/ocpp/__main__.py`.
- **Behavior**:
  - Merge the returned dictionary into the `project_kv` dictionary.
  - Skip OMO preset logic if `.env` is processed.
  - Always enabled (no opt-in flag).
- **Example**:
  ```python
  def main():
      # ... load project_kv ...
      
      env_vars = load_env_file(project_root / ".env")
      if env_vars:
          console.print("[yellow]Overridden environment variables:[/yellow]")
          for key, new_value in env_vars.items():
              old_value = project_kv.get(key)
              masked_old = f"{old_value[:5]}****" if old_value else "None"
              masked_new = f"{new_value[:5]}****"
              console.print(f"  - {key}: {masked_old} → {masked_new}")
              project_kv[key] = new_value
      else:
          console.print("[green]No .env file found or no overrides applied.[/green]")
          
      # ... skip OMO preset logic if env_vars is not empty ...
  ```

### D. Error Handling
- **Missing `.env`**: Skip parsing, log a notice.
- **Malformed `.env`**: Skip invalid lines, log a warning.
- **Permission Issues**: Log an error and continue.

---

## 3. Implementation Details

### A. Modified Files
- **`src/ocpp/env.py`**:
  - `load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]`
    - Parses `.env` using `python-dotenv`.
    - Returns a dictionary of parsed key-value pairs instead of modifying `os.environ`.

- **`src/ocpp/__main__.py`**:
  - Call `load_env_file()` in `main()`.
  - Merge the returned dictionary into `project_kv`.
  - Add logging for overridden keys.
  - Skip OMO preset logic if `.env` is processed.

### B. Dependencies
- `python-dotenv = "^1.0.0"` is already in `pyproject.toml`.

---

## 4. Testing Strategy

### A. Unit Tests
- **`.env` Parsing**:
  - Test valid `.env` files (e.g., `KEY=value`).
  - Test invalid lines (e.g., `KEY=`, `KEY`).
  - Test comments (e.g., `# comment`).
- **Environment Overrides**:
  - Test that `load_env_file` returns the correct dictionary.

### B. Integration Tests
- **CLI Integration**:
  - Test that `load_env_file()` is called in `main()`.
  - Test logging for overridden keys.
  - Test skipping OMO preset logic.
  - Assert against captured stdout (checking for `export KEY=...` or `$Env:KEY=...`) rather than checking `os.environ`.

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
