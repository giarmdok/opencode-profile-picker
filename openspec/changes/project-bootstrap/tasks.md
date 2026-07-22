## 1. Create bootstrap module

- [ ] 1.1 Create `src/ocpp/bootstrap.py` with a `run_bootstrap()` entry function that orchestrates the full bootstrap workflow
- [ ] 1.2 Define `API_KEY_ALLOWLIST` as a module-level constant with the six allowlisted variable names
- [ ] 1.3 Ensure `__all__` exports `run_bootstrap` and `API_KEY_ALLOWLIST`

## 2. Implement project name derivation

- [ ] 2.1 Implement `derive_project_name(project_root: Path) -> str` that returns the sanitized last component of `project_root`
- [ ] 2.2 Implement sanitization: strip whitespace, replace sequences of non-alphanumeric characters (excluding `-`, `_`, `.`) with a single `-`
- [ ] 2.3 Write the derived name as `OCPP_PROJECT_NAME=<value>` in the `.project` content

## 3. Implement API key harvesting from environment

- [ ] 3.1 Implement `harvest_api_keys() -> dict[str, str]` that iterates `API_KEY_ALLOWLIST` and collects non-empty values from `os.environ`
- [ ] 3.2 Skip variables with empty, whitespace-only, or unset values
- [ ] 3.3 Return the harvested keys as a dictionary for inclusion in the `.project` file

## 4. Implement confirmation prompt with masked values

- [ ] 4.1 Implement `confirm_bootstrap(project_name: str, api_keys: dict[str, str], file_path: Path) -> bool` that displays a summary with masked values
- [ ] 4.2 Use the mask utility from the project-file module (change #2) to mask API key values in the prompt
- [ ] 4.3 Prompt the user with `[y/N]` (default: no) and return `True` only if the user explicitly confirms
- [ ] 4.4 If the user declines, print a message and exit without writing

## 5. Implement gitignore check and offer to append

- [ ] 5.1 Implement `check_gitignore(project_root: Path) -> bool` that returns `True` if `.project` is already gitignored
- [ ] 5.2 Detect git repository by checking for `.git` directory in `project_root`
- [ ] 5.3 Check if `.project` appears in the project-level `.gitignore` or global gitignore
- [ ] 5.4 If not gitignored, display a warning and offer to append `.project` to `.gitignore` with confirmation
- [ ] 5.5 Append `.project` to `.gitignore` if the user accepts; skip if the user declines

## 6. Implement file permission setting

- [ ] 6.1 After writing the `.project` file, call `Path.chmod(0o600)` to set restrictive permissions
- [ ] 6.2 Handle permission errors gracefully on platforms where `chmod` is not fully supported (e.g., Windows)
- [ ] 6.3 Write the file atomically (write to temp file, then rename) to avoid partial writes

## 7. Write unit tests

- [ ] 7.1 Test that bootstrap creates `.project` when the file does not exist
- [ ] 7.2 Test that bootstrap skips (does not modify) when `.project` already exists
- [ ] 7.3 Test project name derivation: simple names, names with special characters, whitespace handling
- [ ] 7.4 Test API key harvesting: all keys present, some keys empty, all keys empty, whitespace-only values
- [ ] 7.5 Test confirmation flow: user confirms, user declines, default behavior (Enter)
- [ ] 7.6 Test that values are masked in the confirmation prompt output
- [ ] 7.7 Test gitignore warning: git repo without `.project` in gitignore, git repo with `.project` already gitignored, not a git repo
- [ ] 7.8 Test gitignore append: user accepts, user declines
- [ ] 7.9 Test file permissions: 0o600 on POSIX, graceful fallback on Windows
- [ ] 7.10 Test that the full integration flow works end-to-end with mocked `os.environ` and `Path` operations

## 8. Verify linting and type checking

- [ ] 8.1 Run `ruff check .` and fix any violations
- [ ] 8.2 Run `mypy src/` and fix any type errors
- [ ] 8.3 Run `pytest tests/` and confirm all bootstrap tests pass