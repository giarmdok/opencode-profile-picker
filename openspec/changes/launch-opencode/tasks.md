## 1. Create launch module

- [ ] 1.1 Create `src/ocpp/launch.py` with `__all__` exporting `launch_opencode`, `build_merged_env`, `resolve_opencode`, `LaunchError` (a custom exception class)
- [ ] 1.2 Add module docstring describing the launch contract, env merge order, and platform-specific behavior

## 2. Implement env merge (os.environ + .project + venv delta)

- [ ] 2.1 Implement `build_merged_env(project_overrides: dict[str, str] | None, venv_delta: dict[str, str | None] | None) -> dict[str, str]` that returns a new dict with the merged environment
- [ ] 2.2 Start with a copy of `os.environ`
- [ ] 2.3 Overlay `.project` key-value pairs on top of the `os.environ` copy
- [ ] 2.4 Apply venv delta last: for each key, if value is `str`, set it; if value is `None`, delete the key from the merged env
- [ ] 2.5 Handle Windows case-insensitive environment variable names (normalize keys to uppercase before overlay)

## 3. Implement opencode resolution via shutil.which

- [ ] 3.1 Implement `resolve_opencode(merged_env: dict[str, str]) -> str` that calls `shutil.which("opencode", path=merged_env.get("PATH"))` and returns the resolved full path
- [ ] 3.2 Raise `LaunchError` if `shutil.which` returns `None`

## 4. Implement POSIX launch (os.execvpe)

- [ ] 4.1 Implement `_launch_posix(opencode_path: str, args: list[str], merged_env: dict[str, str]) -> int` that calls `os.execvpe(opencode_path, args, merged_env)`
- [ ] 4.2 Catch `OSError` from `os.execvpe` and raise `LaunchError` with a descriptive message
- [ ] 4.3 This function does not return on success (the process is replaced)

## 5. Implement Windows launch (subprocess.run + sys.exit)

- [ ] 5.1 Implement `_launch_windows(opencode_path: str, args: list[str], merged_env: dict[str, str]) -> int` that calls `subprocess.run(args, env=merged_env)` and returns the return code
- [ ] 5.2 Never use `shell=True` — pass args as a list

## 6. Implement argv passthrough

- [ ] 6.1 Implement argument parsing that separates `ocpp` flags from `opencode` arguments (those after `--`)
- [ ] 6.2 Use `argparse.REMAINDER` or parse known flags and forward the rest to `opencode`
- [ ] 6.3 Build the full argument list: `[opencode_path, *extra_args]`

## 7. Implement missing binary error handling

- [ ] 7.1 In `resolve_opencode`, when `opencode` is not found, raise `LaunchError` with a message like `"opencode not found in PATH. Is opencode installed?"`
- [ ] 7.2 In the top-level `launch_opencode` function, catch `LaunchError` and call `sys.exit(1)` after printing the error to stderr
- [ ] 7.3 Use `print(message, file=sys.stderr)` for error output

## 8. Write unit tests

- [ ] 8.1 Test env merge: `os.environ` + `.project` overrides produces correct merged dict
- [ ] 8.2 Test env merge: `.project` overrides take priority over `os.environ`
- [ ] 8.3 Test env merge: venv delta PATH prepend is applied last (overrides `.project` PATH)
- [ ] 8.4 Test env merge: venv delta sets `VIRTUAL_ENV` and unsets `PYTHONHOME`
- [ ] 8.5 Test env merge: no venv delta — merged env is `os.environ` + `.project` only
- [ ] 8.6 Test resolve opencode: found in merged PATH returns resolved path
- [ ] 8.7 Test resolve opencode: not found raises `LaunchError`
- [ ] 8.8 Test resolve opencode: found in venv PATH when venv is active
- [ ] 8.9 Test argv passthrough: extra args forwarded correctly
- [ ] 8.10 Test argv passthrough: no extra args — only `opencode` path in list
- [ ] 8.11 Test Windows launch: `subprocess.run` called with correct args and env
- [ ] 8.12 Test POSIX launch: `os.execvpe` called with correct args and env
- [ ] 8.13 Test missing binary error: prints to stderr and exits with code 1
- [ ] 8.14 Test `shell=True` is never used (assert `shell` is not in the `subprocess.run` call or is `False`)

## 9. Verify linting and type checking

- [ ] 9.1 Run `ruff check .` and fix any violations
- [ ] 9.2 Run `mypy src/` and fix any type errors
- [ ] 9.3 Run `pytest tests/` and confirm all launch tests pass