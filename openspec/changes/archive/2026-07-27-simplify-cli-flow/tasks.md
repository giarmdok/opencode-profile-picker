## 1. Code Removal

- [x] 1.1 In `src/ocpp/__main__.py`, remove all code related to `.project` files, including the `parse_project` import and all related logic.
- [x] 1.2 In `src/ocpp/__main__.py`, remove the `--no-launch`, `--project-dir`, `--dry-run`, and `--init` flags from the `ArgumentParser`.
- [x] 1.3 Delete the `src/ocpp/bootstrap.py` and `src/ocpp/project.py` files.
- [x] 1.4 Delete the `tests/test_bootstrap.py` and `tests/test_project.py` files.

## 2. CLI Simplification

- [x] 2.1 In `src/ocpp/__main__.py`, update the `main` function to implement the simplified flow:
    1.  Load API keys from `.env`.
    2.  Select OMO preset.
    3.  Activate Python venv.
- [x] 2.2 Ensure the `--preset` flag still works for non-interactive preset selection.

## 3. Test Updates

- [x] 3.1 In `tests/test_cli_flow.py`, update the tests to reflect the simplified CLI functionality.
- [x] 3.2 Remove any tests that are no longer relevant.
- [x] 3.3 Run all tests and ensure they pass.
