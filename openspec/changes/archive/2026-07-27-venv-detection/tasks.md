## 1. Create venv module

- [ ] 1.1 Create `src/ocpp/venv.py` with `__all__` exporting `find_venv`, `validate_venv`, `compute_venv_env_delta`, `VenvResult` (a `NamedTuple` or dataclass with `path: Path` and `env_delta: dict[str, str | None]`)
- [ ] 1.2 Add module docstring describing the venv detection, validation, and env delta computation contract

## 2. Implement venv discovery

- [ ] 2.1 Implement `find_venv(platform: Platform) -> Path | None` that searches the project root for the platform-specific venv directory name first, then `.venv` as a fallback
- [ ] 2.2 Return the `Path` to the venv directory if found, or `None` if no matching directory exists

## 3. Implement venv validation

- [ ] 3.1 Implement `validate_venv(venv_path: Path, platform: Platform) -> bool` that checks for the interpreter executable in the venv's bin subdirectory
- [ ] 3.2 Use `python.exe` as the interpreter name on Windows, `python` on POSIX (Linux/Unix)
- [ ] 3.3 Return `True` if the interpreter exists, `False` otherwise
- [ ] 3.4 If the venv directory exists but validation fails, emit a `logging.warning` with the venv path

## 4. Implement env delta computation

- [ ] 4.1 Implement `compute_venv_env_delta(venv_path: Path, platform: Platform) -> dict[str, str | None]` that builds the activation environment delta
- [ ] 4.2 Prepend the venv bin directory to the current `PATH` using `os.pathsep`
- [ ] 4.3 Set `VIRTUAL_ENV` to the venv root path (as a string)
- [ ] 4.4 If `PYTHONHOME` is set in `os.environ`, include `"PYTHONHOME": None` in the delta (meaning "unset")
- [ ] 4.5 If `PYTHONHOME` is not set, omit the key from the delta

## 5. Write unit tests

- [ ] 5.1 Test finding `.venv_win` on Windows platform (using a temporary directory with the venv dir)
- [ ] 5.2 Test finding `.venv_lin` on Linux platform
- [ ] 5.3 Test finding `.venv_unx` on Unix platform
- [ ] 5.4 Test `.venv` fallback when platform-specific venv does not exist
- [ ] 5.5 Test platform-specific venv takes priority when both platform-specific and `.venv` exist
- [ ] 5.6 Test no venv returns `None`
- [ ] 5.7 Test invalid venv (directory exists but interpreter missing) returns `None` with warning
- [ ] 5.8 Test valid venv returns the correct path
- [ ] 5.9 Test env delta contains correct `PATH` prepend
- [ ] 5.10 Test env delta contains `VIRTUAL_ENV` set to venv root
- [ ] 5.11 Test env delta unsets `PYTHONHOME` when it was set
- [ ] 5.12 Test env delta omits `PYTHONHOME` when it was not set
- [ ] 5.13 Test env delta is `None` when no venv found

## 6. Verify linting and type checking

- [ ] 6.1 Run `ruff check .` and fix any violations
- [ ] 6.2 Run `mypy src/` and fix any type errors
- [ ] 6.3 Run `pytest tests/` and confirm all venv detection tests pass
