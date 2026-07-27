## ADDED Requirements

### Requirement: Simplified CLI Flow
The CLI SHALL execute a simplified flow in the following order:
1.  Load OpenCode API keys from a `.env` file in the current directory.
2.  Select an OMO preset.
3.  Activate the Python virtual environment.

#### Scenario: All steps succeed
-   **WHEN** a `.env` file with API keys exists, an OMO config is present, and a venv is detected
-   **THEN** the CLI SHALL load the keys, prompt for a preset, activate the venv, and emit the environment variables.

### Requirement: ArgumentParser Simplification
The CLI's `ArgumentParser` SHALL only accept the `--preset` flag. All other flags SHALL be removed.

#### Scenario: Run with `--preset`
-   **WHEN** the user runs `ocpp --preset openrouter`
-   **THEN** the CLI SHALL select the `openrouter` preset without prompting the user.

#### Scenario: Run with an invalid flag
-   **WHEN** the user runs `ocpp --invalid-flag`
-   **THEN** the `ArgumentParser` SHALL raise an error.
