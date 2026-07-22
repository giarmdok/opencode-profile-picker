## ADDED Requirements

### Requirement: Environment merging

The launcher SHALL build the final merged environment by combining three sources in the following order: start with `os.environ`, overlay `.project` key-value overrides, then apply the venv activation delta last. The venv delta's PATH prepend SHALL be applied after all other sources to ensure the venv bin directory takes highest priority.

#### Scenario: Merge order is os.environ → .project → venv delta
- **WHEN** `os.environ` contains `MY_VAR=original`, `.project` defines `MY_VAR=override`, and the venv delta defines `PATH=/venv/bin:<original_path>`
- **THEN** the merged environment MUST contain `MY_VAR=override` (`.project` wins over `os.environ`) and `PATH` MUST start with `/venv/bin` (venv delta PATH prepend wins over `.project`)

#### Scenario: .project overlay overrides os.environ
- **WHEN** `os.environ` contains `ANTHROPIC_API_KEY=sk-env-999` and `.project` contains `ANTHROPIC_API_KEY=sk-project-123`
- **THEN** the merged environment MUST contain `ANTHROPIC_API_KEY=sk-project-123`

#### Scenario: venv PATH prepend is applied last
- **WHEN** `.project` contains `PATH=/custom/bin` and the venv delta prepends `/venv/bin` to the current PATH
- **THEN** the merged PATH MUST start with `/venv/bin`, followed by `/custom/bin`, followed by the original PATH entries

#### Scenario: No venv found — proceed without venv delta
- **WHEN** no venv is found (venv delta is `None`)
- **THEN** the merged environment MUST be `os.environ` + `.project` overrides only, with no venv activation

### Requirement: Opencode binary resolution

The launcher SHALL resolve the `opencode` binary using `shutil.which` with the merged PATH. The resolution SHALL happen after the merged environment is built.

#### Scenario: Opencode found in merged PATH
- **WHEN** `shutil.which("opencode")` returns a path in the merged PATH
- **THEN** the launcher MUST use the resolved full path for the launch

#### Scenario: Opencode found in venv bin directory
- **WHEN** `opencode` is installed in the venv bin directory and the venv PATH prepend is applied
- **THEN** `shutil.which("opencode")` MUST resolve to the venv's `opencode` binary

#### Scenario: Opencode not found
- **WHEN** `shutil.which("opencode")` returns `None`
- **THEN** the launcher MUST print a clear error message to stderr and exit with code 1

### Requirement: Process launch

The launcher SHALL launch `opencode` using a platform-specific mechanism. On POSIX systems, it SHALL use `os.execvpe` to replace the current process. On Windows, it SHALL use `subprocess.run` followed by `sys.exit(returncode)`.

#### Scenario: POSIX launch uses os.execvpe
- **WHEN** the platform is POSIX and `opencode` is found
- **THEN** the launcher MUST call `os.execvpe("opencode", args, merged_env)` to replace the current process

#### Scenario: Windows launch uses subprocess.run
- **WHEN** the platform is Windows and `opencode` is found
- **THEN** the launcher MUST call `subprocess.run(args, env=merged_env)` and then `sys.exit(returncode)`

#### Scenario: os.execvpe failure on POSIX
- **WHEN** `os.execvpe` raises `OSError` (e.g., binary deleted between resolution and exec)
- **THEN** the launcher MUST catch the exception, print a clear error to stderr, and exit with code 1

### Requirement: Argument passthrough

The launcher SHALL pass through extra command-line arguments after `--` to the `opencode` process. Each argument SHALL be passed as a separate element in the argument list. No shell quoting or escaping SHALL be applied.

#### Scenario: Extra arguments forwarded
- **WHEN** `ocpp launch -- --model claude-3-opus --temperature 0.7` is invoked
- **THEN** `opencode` MUST be launched with arguments `["opencode", "--model", "claude-3-opus", "--temperature", "0.7"]`

#### Scenario: No extra arguments — empty passthrough
- **WHEN** `ocpp launch` is invoked without any arguments after `--`
- **THEN** `opencode` MUST be launched with no extra arguments beyond the binary name

#### Scenario: Single extra argument
- **WHEN** `ocpp launch -- --version` is invoked
- **THEN** `opencode` MUST be launched with arguments `["opencode", "--version"]`

### Requirement: No shell=True

The launcher SHALL NEVER use `shell=True` in any subprocess or exec call. All process launches SHALL use the list form of arguments.

#### Scenario: Arguments passed as list, not string
- **WHEN** `opencode` is launched on Windows
- **THEN** `subprocess.run` MUST be called with a list of arguments (not a string), and `shell` MUST be `False` (the default)

#### Scenario: POSIX exec also uses list form
- **WHEN** `opencode` is launched on POSIX
- **THEN** `os.execvpe` MUST be called with a list of arguments (not a string)

### Requirement: Missing opencode error handling

The launcher SHALL handle the case where the `opencode` binary is not found with a clear, user-friendly error message and a non-zero exit code. The error message SHALL be written to stderr.

#### Scenario: Missing opencode prints error to stderr
- **WHEN** `shutil.which("opencode")` returns `None`
- **THEN** the launcher MUST print `"opencode not found in PATH. Is opencode installed?"` (or equivalent) to stderr

#### Scenario: Missing opencode exits with code 1
- **WHEN** `shutil.which("opencode")` returns `None`
- **THEN** the launcher MUST exit with return code 1