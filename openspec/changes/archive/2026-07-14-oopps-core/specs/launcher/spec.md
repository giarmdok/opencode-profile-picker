## ADDED Requirements

### Requirement: Resolve API keys for a profile
The system SHALL resolve all required API keys for a profile using the resolution chain: stored encrypted value → environment variable → prompt user. Resolution SHALL happen at launch time, not at profile selection time.

#### Scenario: Key found in encrypted store
- **WHEN** the profile's key set contains a stored value for `OPENROUTER_API_KEY`
- **THEN** the system decrypts and uses the stored value

#### Scenario: Key found in environment
- **WHEN** the profile's key set has no stored value for `OPENROUTER_API_KEY` but the environment variable `OPENROUTER_API_KEY` is set
- **THEN** the system uses the environment variable value

#### Scenario: Key not found anywhere
- **WHEN** the profile's key set has no stored value and the environment variable is not set
- **THEN** the system prompts the user to enter the key, with an option to save it to the key set

### Requirement: Build launch environment
The system SHALL construct an environment dictionary for the OpenCode child process that includes all resolved API keys merged with the current process environment. Existing environment variables SHALL be preserved unless explicitly overridden by resolved keys.

#### Scenario: Environment merge
- **WHEN** the current environment has `PATH=/usr/bin` and the resolved keys include `OPENROUTER_API_KEY=sk-abc`
- **THEN** the child process environment contains both `PATH=/usr/bin` and `OPENROUTER_API_KEY=sk-abc`

#### Scenario: Resolved key overrides existing env var
- **WHEN** the environment already has `OPENROUTER_API_KEY=sk-old` and the resolved key is `sk-new`
- **THEN** the child process receives `OPENROUTER_API_KEY=sk-new`

### Requirement: Launch OpenCode process
The system SHALL spawn OpenCode as a child process with the constructed environment. On Windows, the process SHALL be created with a new console window. On Unix, the process SHALL inherit the terminal.

#### Scenario: Successful launch on Unix
- **WHEN** the user launches a profile on Linux or macOS
- **THEN** OpenCode starts in the current terminal with the injected environment variables

#### Scenario: Successful launch on Windows
- **WHEN** the user launches a profile on Windows
- **THEN** OpenCode starts in a new console window with the injected environment variables

### Requirement: Handle OpenCode not found
The system SHALL check for the `opencode` executable on the system PATH before attempting to launch. If not found, the system SHALL display an error and not attempt to spawn a process.

#### Scenario: OpenCode not installed
- **WHEN** `opencode` is not found on the system PATH
- **THEN** the system displays "OpenCode not found on PATH" and blocks the launch

#### Scenario: OpenCode found
- **WHEN** `opencode` is found on the system PATH
- **THEN** the system proceeds with the launch

### Requirement: Handle launch failure
The system SHALL handle cases where the OpenCode process fails to start and display an appropriate error message.

#### Scenario: Process fails to spawn
- **WHEN** `subprocess.Popen` raises an exception
- **THEN** the system displays the error message and returns to the main screen without exiting

### Requirement: Exit after successful launch
The system SHALL exit after successfully spawning the OpenCode child process. The oopps process SHALL NOT remain running.

#### Scenario: Launch and exit
- **WHEN** OpenCode is successfully spawned as a child process
- **THEN** the oopps process exits with status code 0

### Requirement: Never log or display API keys
The system SHALL NOT write API key values to log files, stdout, or stderr during the launch process. Error messages SHALL reference key names (e.g., `OPENROUTER_API_KEY`) but never key values.

#### Scenario: Launch error with key reference
- **WHEN** a launch fails because `OPENROUTER_API_KEY` is missing
- **THEN** the error message states "Missing required key: OPENROUTER_API_KEY" without exposing any key values