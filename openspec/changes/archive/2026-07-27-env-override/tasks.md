## 1. Environment Parsing

- [x] 1.1 Modify `src/ocpp/env.py`: Create a new function `load_dotenv_file(env_path: Path) -> Dict[str, str]` that uses `python-dotenv` to parse the `.env` file and return a dictionary of key-value pairs.
- [x] 1.2 In `src/ocpp/env.py`, update `load_env_file` to call `load_dotenv_file` and merge the results, but for now, keep the `os.environ` modification for compatibility. This will be removed in a later step.

## 2. CLI Integration

- [x] 2.1 In `src/ocpp/__main__.py`, update `main()` to call `env.load_env_file()` early in the function.
- [x] 2.2 In `src/ocpp/__main__.py`, merge the dictionary returned from `load_env_file()` into the `project_kv` dictionary, overwriting existing keys.
- [x] 2.3 In `src/ocpp/__main__.py`, add logging to print overridden keys, masking sensitive values as described in the design document.
- [x] 2.4 In `src/ocpp/__main__.py`, implement the logic to skip the OMO preset selection prompt when a `.env` file is processed.
- [x] 2.5 In `src/ocpp/__main__.py`, add a notice when no `.env` file is found.

## 3. Refactoring and Cleanup

- [x] 3.1 Modify `src/ocpp/env.py`: Remove the `os.environ` modification from `load_env_file` as the CLI now handles the environment.
- [x] 3.2 Update `src/ocpp/env.py`: Ensure `load_env_file` returns the dictionary from `load_dotenv_file`.

## 4. Testing

- [x] 4.1 Create a new test file `tests/test_env.py`.
- [x] 4.2 In `tests/test_env.py`, add unit tests for `load_dotenv_file` to verify correct parsing of valid and invalid `.env` files.
- [x] 4.3 In `tests/test_cli.py`, update integration tests to assert against captured stdout instead of `os.environ`.
- [x] 4.4 In `tests/test_cli.py`, add integration tests to verify the logging of overridden keys.
- [x] 4.5 In `tests/test_cli.py`, add integration tests to verify that OMO preset logic is skipped when a `.env` file is present.
