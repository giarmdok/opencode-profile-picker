# Config Discovery

## Purpose

Discover and parse the oh-my-opencode-slim configuration file, extract available presets, map presets to required API keys (including council models), and detect project-local config overrides.

## Requirements

### Requirement: Discover OMO configuration file
The system SHALL locate the oh-my-opencode-slim configuration file by scanning platform-appropriate paths. On all platforms, `~/.config/opencode/oh-my-opencode-slim.jsonc` SHALL be preferred over `oh-my-opencode-slim.json`. On Windows, `%APPDATA%\opencode\` SHALL also be checked.

#### Scenario: Config file found at primary location
- **WHEN** `~/.config/opencode/oh-my-opencode-slim.jsonc` exists
- **THEN** the system parses that file and returns its contents

#### Scenario: JSONC preferred over JSON
- **WHEN** both `oh-my-opencode-slim.jsonc` and `oh-my-opencode-slim.json` exist in the same directory
- **THEN** the system parses the `.jsonc` file and ignores the `.json` file

#### Scenario: No config file exists
- **WHEN** no `oh-my-opencode-slim.json` or `.jsonc` is found at any known path
- **THEN** the system returns an empty discovery result with no presets and no error

### Requirement: Extract available preset names
The system SHALL parse the discovered OMO configuration and extract all preset names from the `presets` top-level key.

#### Scenario: Multiple presets defined
- **WHEN** the config contains `"presets": {"go": {...}, "or": {...}, "gm": {...}}`
- **THEN** the system returns `["go", "or", "gm"]` as available presets

#### Scenario: No presets defined
- **WHEN** the config has no `presets` key or an empty `presets` object
- **THEN** the system returns an empty preset list

#### Scenario: Malformed config file
- **WHEN** the config file contains invalid JSON/JSONC that cannot be parsed
- **THEN** the system returns an empty discovery result and logs a warning

### Requirement: Map presets to required API keys
The system SHALL analyze each preset's agent configurations to determine which API providers are used, and map those providers to their required environment variable names using a built-in provider-to-key mapping table.

#### Scenario: Single-provider preset
- **WHEN** a preset's agents all use models prefixed with `openrouter/`
- **THEN** the system returns `{"OPENROUTER_API_KEY"}` as the required keys for that preset

#### Scenario: Multi-provider preset
- **WHEN** a preset uses `google/gemini-3.5-flash` for orchestrator and `mistral/mistral-small` for fixer
- **THEN** the system returns `{"GOOGLE_API_KEY", "MISTRAL_API_KEY"}` as required keys

#### Scenario: Unknown provider prefix
- **WHEN** a preset references a model with a provider prefix not in the mapping table (e.g., `custom-provider/model`)
- **THEN** the system includes the raw model string in the result as an unrecognized provider and does not map it to an env var

### Requirement: Include council model requirements
The system SHALL also analyze the `council.presets` configuration to identify additional API keys needed for council councillor models.

#### Scenario: Council uses different providers than agents
- **WHEN** a preset uses only Google models but the council uses OpenAI and Anthropic councillors
- **THEN** the system returns the union of preset agent keys and council keys: `{"GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}`

#### Scenario: No council configured
- **WHEN** the config has no `council` key or no `council.presets`
- **THEN** the system returns only the preset agent keys

### Requirement: Detect project-local config override
The system SHALL check for a project-local `.opencode/oh-my-opencode-slim.json` or `.jsonc` in the current working directory and report whether it contains a `preset` field that would override the global setting.

#### Scenario: Project-local config with preset override
- **WHEN** `.opencode/oh-my-opencode-slim.json` exists in the current directory and contains `"preset": "custom"`
- **THEN** the system reports that a project-local preset override is active with value `"custom"`

#### Scenario: No project-local config
- **WHEN** no `.opencode/` directory or no OMO config exists in the current directory
- **THEN** the system reports no project-local override
