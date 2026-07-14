## ADDED Requirements

### Requirement: Write preset to OMO configuration
The system SHALL write the selected preset name to the `preset` field of the global `oh-my-opencode-slim.json` (or `.jsonc`) file. No other fields SHALL be modified.

#### Scenario: Change active preset
- **WHEN** the user launches profile "go-work" which uses preset "go", and the current active preset is "or"
- **THEN** the system writes `"preset": "go"` to the config file, replacing the previous value

#### Scenario: Preset unchanged
- **WHEN** the user launches a profile whose preset matches the currently active preset
- **THEN** the system skips the write operation (no-op)

### Requirement: Preserve file extension
The system SHALL write to the same file extension that was discovered. If the config was loaded from a `.jsonc` file, the system SHALL write back to the `.jsonc` file.

#### Scenario: Write to JSONC file
- **WHEN** the config was loaded from `oh-my-opencode-slim.jsonc`
- **THEN** the system writes the updated config to `oh-my-opencode-slim.jsonc`

#### Scenario: Write to JSON file
- **WHEN** the config was loaded from `oh-my-opencode-slim.json`
- **THEN** the system writes the updated config to `oh-my-opencode-slim.json`

### Requirement: Handle missing config file
The system SHALL gracefully handle the case where no OMO config file exists by skipping the preset write and notifying the user.

#### Scenario: No config file to write
- **WHEN** the user launches a profile but no `oh-my-opencode-slim.json` or `.jsonc` exists
- **THEN** the system displays a warning that the preset could not be applied, and proceeds with key injection and launch

### Requirement: Handle malformed config file
The system SHALL gracefully handle a malformed OMO config file by skipping the preset write and notifying the user.

#### Scenario: Unparseable config
- **WHEN** the OMO config file exists but contains invalid JSON that cannot be parsed
- **THEN** the system displays a warning that the preset could not be applied due to a malformed config file, and proceeds with key injection and launch

### Requirement: Detect project-local preset override
The system SHALL detect when a project-local `.opencode/oh-my-opencode-slim.json` contains its own `preset` field and inform the user that the global preset change may not take effect in that project.

#### Scenario: Project-local override exists
- **WHEN** the current working directory contains `.opencode/oh-my-opencode-slim.json` with `"preset": "custom"`
- **THEN** the system displays an informational note: "Project-local config overrides preset to 'custom'. Global preset set to '<selected>'."

### Requirement: Never modify other configuration
The system SHALL NOT modify any field in the OMO config file other than the top-level `preset` field. Agent configurations, council settings, companion settings, and all other fields SHALL be preserved exactly as found.

#### Scenario: Config with many fields
- **WHEN** the OMO config contains `preset`, `presets`, `council`, `companion`, `backgroundJobs`, and `disabled_agents` fields
- **THEN** after writing a new preset value, all other fields remain identical to their pre-write state