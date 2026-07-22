## ADDED Requirements

### Requirement: Venv discovery
The venv module SHALL locate a Python virtual environment in the project root by searching for platform-specific directory names first, then falling back to the generic `.venv` name. The search SHALL use the `Platform` abstraction (change #1) to determine the platform-specific venv directory name and bin subdirectory name.

#### Scenario: platform-specific venv exists
- **WHEN** the project root contains a directory matching the platform-specific venv name (e.g., `.venv_win` on Windows)
- **THEN** the module SHALL return the path to that directory

#### Scenario: platform-specific venv absent, generic .venv exists
- **WHEN** the project root does NOT contain the platform-specific venv directory but DOES contain a `.venv` directory
- **THEN** the module SHALL return the path to `.venv`

#### Scenario: no venv directory exists
- **WHEN** the project root contains neither the platform-specific venv directory nor `.venv`
- **THEN** the module SHALL return `None`

#### Scenario: platform-specific venv takes priority over .venv
- **WHEN** the project root contains both the platform-specific venv directory (e.g., `.venv_win`) and `.venv`
- **THEN** the module SHALL return the platform-specific venv directory

### Requirement: Venv validation
The venv module SHALL validate a discovered venv by checking that the interpreter executable exists in the venv's bin subdirectory. The interpreter name SHALL be `python.exe` on Windows and `python` on POSIX (Linux/Unix).

#### Scenario: valid venv with interpreter
- **WHEN** the venv directory contains `<bin_subdir>/python.exe` (Windows) or `<bin_subdir>/python` (POSIX)
- **THEN** the module SHALL consider the venv valid

#### Scenario: invalid venv without interpreter
- **WHEN** the venv directory exists but does NOT contain the interpreter executable in the bin subdirectory
- **THEN** the module SHALL treat the venv as invalid, emit a warning via `logging.warning`, and return `None`

### Requirement: Env delta computation
The venv module SHALL compute an activation environment delta as a `dict[str, str | None]` containing: `PATH` with the venv bin directory prepended, `VIRTUAL_ENV` set to the venv root path, and `PYTHONHOME` set to `None` (meaning "unset") if present in the current environment.

#### Scenario: PATH is prepended with bin directory
- **WHEN** the current `PATH` is `/usr/bin:/usr/local/bin` and the venv bin directory is `/project/.venv_lin/bin`
- **THEN** the delta SHALL contain `"PATH": "/project/.venv_lin/bin:/usr/bin:/usr/local/bin"`

#### Scenario: VIRTUAL_ENV is set to venv root
- **WHEN** a valid venv is found at `/project/.venv_lin`
- **THEN** the delta SHALL contain `"VIRTUAL_ENV": "/project/.venv_lin"`

#### Scenario: PYTHONHOME is unset when present
- **WHEN** `PYTHONHOME` is set in the current environment
- **THEN** the delta SHALL contain `"PYTHONHOME": None`

#### Scenario: PYTHONHOME is absent from delta when not set
- **WHEN** `PYTHONHOME` is NOT set in the current environment
- **THEN** the delta SHALL NOT contain a `"PYTHONHOME"` key

#### Scenario: env delta is empty when no venv found
- **WHEN** no valid venv is found
- **THEN** the module SHALL return `None` (not a dict)

### Requirement: No venv found returns None
The venv module SHALL return `None` when no valid venv is found in the project root. This SHALL NOT be treated as an error — the caller decides how to handle the absence of a venv.

#### Scenario: no venv returns None
- **WHEN** the project root has no venv directory
- **THEN** the module SHALL return `None`

#### Scenario: invalid venv returns None
- **WHEN** a venv directory exists but the interpreter is missing
- **THEN** the module SHALL return `None` (after logging a warning)

### Requirement: Invalid venv handling
The venv module SHALL emit a warning via `logging.warning` when a venv directory is found but validation fails (interpreter executable missing). The warning message SHALL include the venv path.

#### Scenario: warning logged for invalid venv
- **WHEN** a venv directory exists at `/project/.venv_lin` but the interpreter is missing
- **THEN** a warning SHALL be logged containing the path `/project/.venv_lin`
