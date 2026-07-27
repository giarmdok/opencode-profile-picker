## ADDED Requirements

### Requirement: Platform classification
The platform module SHALL classify the current OS into one of three families: `Windows`, `Linux`, or `Unix`. The classification SHALL be based on `sys.platform`: `'win32'` maps to `Windows`, values starting with `'linux'` map to `Linux`, and all other values (including `'darwin'`, `'freebsd'`, `'netbsd'`, `'openbsd'`) map to `Unix`.

#### Scenario: win32 detected as Windows
- **WHEN** `sys.platform` is `'win32'`
- **THEN** the platform family SHALL be `Windows`

#### Scenario: linux detected as Linux
- **WHEN** `sys.platform` is `'linux'`
- **THEN** the platform family SHALL be `Linux`

#### Scenario: darwin detected as Unix
- **WHEN** `sys.platform` is `'darwin'`
- **THEN** the platform family SHALL be `Unix`

#### Scenario: freebsd detected as Unix
- **WHEN** `sys.platform` is `'freebsd'`
- **THEN** the platform family SHALL be `Unix`

#### Scenario: unknown platform detected as Unix
- **WHEN** `sys.platform` is an unrecognized value (e.g., `'cygwin'`)
- **THEN** the platform family SHALL be `Unix`

### Requirement: Venv directory name resolution
The platform module SHALL resolve the platform-specific venv directory name: `.venv_win` for Windows, `.venv_lin` for Linux, `.venv_unx` for Unix. It SHALL also provide the generic `.venv` as a fallback name.

#### Scenario: Windows venv directory name
- **WHEN** the platform family is `Windows`
- **THEN** the platform-specific venv directory name SHALL be `.venv_win`

#### Scenario: Linux venv directory name
- **WHEN** the platform family is `Linux`
- **THEN** the platform-specific venv directory name SHALL be `.venv_lin`

#### Scenario: Unix venv directory name
- **WHEN** the platform family is `Unix`
- **THEN** the platform-specific venv directory name SHALL be `.venv_unx`

#### Scenario: generic venv fallback name
- **WHEN** the generic venv name is requested
- **THEN** it SHALL be `.venv`

### Requirement: Venv bin subdirectory resolution
The platform module SHALL resolve the venv bin subdirectory name: `Scripts` for Windows, `bin` for POSIX (Linux and Unix).

#### Scenario: Windows bin subdirectory
- **WHEN** the platform family is `Windows`
- **THEN** the venv bin subdirectory name SHALL be `Scripts`

#### Scenario: Linux bin subdirectory
- **WHEN** the platform family is `Linux`
- **THEN** the venv bin subdirectory name SHALL be `bin`

#### Scenario: Unix bin subdirectory
- **WHEN** the platform family is `Unix`
- **THEN** the venv bin subdirectory name SHALL be `bin`

### Requirement: OMO config path discovery
The platform module SHALL provide an ordered list of candidate OMO config file paths. The search order SHALL be: (1) `~/.config/opencode/oh-my-opencode-slim.json`, (2) `~/.config/opencode/oh-my-opencode-slim.jsonc`, (3) `%APPDATA%\opencode\oh-my-opencode-slim.json` (Windows only), (4) `%APPDATA%\opencode\oh-my-opencode-slim.jsonc` (Windows only). The list SHALL be returned in priority order (first match wins).

#### Scenario: Unix OMO config search paths
- **WHEN** the platform family is `Unix`
- **THEN** the candidate OMO paths SHALL be `[~/.config/opencode/oh-my-opencode-slim.json, ~/.config/opencode/oh-my-opencode-slim.jsonc]` in that order

#### Scenario: Linux OMO config search paths
- **WHEN** the platform family is `Linux`
- **THEN** the candidate OMO paths SHALL be `[~/.config/opencode/oh-my-opencode-slim.json, ~/.config/opencode/oh-my-opencode-slim.jsonc]` in that order

#### Scenario: Windows OMO config search paths with APPDATA
- **WHEN** the platform family is `Windows` and `%APPDATA%` is set
- **THEN** the candidate OMO paths SHALL be `[~/.config/opencode/oh-my-opencode-slim.json, ~/.config/opencode/oh-my-opencode-slim.jsonc, %APPDATA%\opencode\oh-my-opencode-slim.json, %APPDATA%\opencode\oh-my-opencode-slim.jsonc]` in that order

#### Scenario: Windows OMO config search paths without APPDATA
- **WHEN** the platform family is `Windows` and `%APPDATA%` is not set
- **THEN** the candidate OMO paths SHALL be `[~/.config/opencode/oh-my-opencode-slim.json, ~/.config/opencode/oh-my-opencode-slim.jsonc, ~\.config\opencode\oh-my-opencode-slim.json, ~\.config\opencode\oh-my-opencode-slim.jsonc]` in that order

### Requirement: Project root resolution
The platform module SHALL resolve the project root directory to the current working directory.

#### Scenario: default project root
- **WHEN** `Platform.detect()` is called
- **THEN** the project root SHALL equal `Path.cwd()`

### Requirement: Injectable platform for testing
The platform module SHALL allow callers to override the platform string and home directory for testing purposes. The factory function SHALL accept optional `platform_string` and `home_dir` parameters.

#### Scenario: override platform string to Windows
- **WHEN** `Platform.detect(platform_string='win32')` is called on a Linux machine
- **THEN** the platform family SHALL be `Windows`

#### Scenario: override home directory
- **WHEN** `Platform.detect(home_dir=Path('/fake/home'))` is called
- **THEN** the OMO config paths SHALL be rooted at `/fake/home/.config/opencode/` instead of the real home directory

#### Scenario: direct construction
- **WHEN** a `Platform` instance is constructed directly with explicit field values
- **THEN** all fields SHALL be set to the provided values, bypassing platform detection entirely