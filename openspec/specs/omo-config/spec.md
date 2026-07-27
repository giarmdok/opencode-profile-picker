## ADDED Requirements

### Requirement: OMO config discovery
The omo module SHALL discover the global OMO config file by iterating the candidate paths returned by the platform-abstraction module and returning the first path that exists on disk. Both `.json` and `.jsonc` variants SHALL be checked per the platform-abstraction path order.

#### Scenario: OMO config found at primary path
- **WHEN** `~/.config/opencode/oh-my-opencode-slim.json` exists
- **THEN** the discovered path SHALL be `~/.config/opencode/oh-my-opencode-slim.json`

#### Scenario: OMO config found at jsonc variant
- **WHEN** `~/.config/opencode/oh-my-opencode-slim.json` does not exist but `~/.config/opencode/oh-my-opencode-slim.jsonc` exists
- **THEN** the discovered path SHALL be `~/.config/opencode/oh-my-opencode-slim.jsonc`

#### Scenario: OMO config found at Windows fallback
- **WHEN** no `.config` path exists and `%APPDATA%\opencode\oh-my-opencode-slim.json` exists
- **THEN** the discovered path SHALL be the `%APPDATA%` fallback path

#### Scenario: OMO config not found
- **WHEN** none of the candidate paths exist
- **THEN** the omo module SHALL raise an error indicating the config was not found and listing the searched paths

### Requirement: Config parsing and validation
The omo module SHALL parse the discovered OMO config file using `json5` and validate that the top-level object contains a `"preset"` string field and a `"presets"` object field.

#### Scenario: valid config parsed successfully
- **WHEN** the OMO config file is valid JSONC with `"preset"` and `"presets"` fields
- **THEN** the parsed data SHALL contain the `"preset"` string value and the `"presets"` object

#### Scenario: malformed config file
- **WHEN** the OMO config file contains invalid JSONC syntax
- **THEN** the omo module SHALL raise a parse error with the file path and the line/column of the syntax error

#### Scenario: missing preset field
- **WHEN** the parsed config has no top-level `"preset"` field
- **THEN** the omo module SHALL raise a validation error indicating the `"preset"` field is missing

#### Scenario: missing presets field
- **WHEN** the parsed config has no top-level `"presets"` field
- **THEN** the omo module SHALL raise a validation error indicating the `"presets"` field is missing

#### Scenario: preset field is not a string
- **WHEN** the `"preset"` field exists but is not a string
- **THEN** the omo module SHALL raise a validation error indicating the `"preset"` field must be a string

#### Scenario: presets field is not an object
- **WHEN** the `"presets"` field exists but is not an object
- **THEN** the omo module SHALL raise a validation error indicating the `"presets"` field must be an object

### Requirement: Preset listing
The omo module SHALL list the available preset names from the `"presets"` object and indicate which one is currently active (the `"preset"` value). Each preset SHALL include a summary of its contained agents.

#### Scenario: list presets with current marked
- **WHEN** the config has `"preset": "openrouter"` and `"presets"` contains `openrouter`, `anthropic`, `google`
- **THEN** the returned list SHALL contain three entries with `openrouter` marked as the current preset

#### Scenario: preset name not in presets object
- **WHEN** the `"preset"` value is `"custom"` but `"presets"` does not contain `"custom"`
- **THEN** the current preset SHALL be reported as `"custom"` and SHALL be noted as missing from the `"presets"` object

#### Scenario: empty presets object
- **WHEN** the `"presets"` object is empty
- **THEN** the returned list SHALL be empty and the current preset value SHALL still be reported

### Requirement: Preset selection and write
The omo module SHALL update the active preset by performing a surgical text edit on the raw file content. The edit SHALL replace only the top-level `"preset"` field value, preserving all comments, whitespace, and formatting. The regex pattern SHALL match the top-level `"preset"` key by anchoring to line start or the opening `{` character.

#### Scenario: surgical write replaces preset field
- **WHEN** the user selects preset `"anthropic"` and the current value is `"openrouter"`
- **THEN** the raw file content SHALL have `"preset": "openrouter"` changed to `"preset": "anthropic"` and all other content SHALL be unchanged

#### Scenario: surgical write preserves comments
- **WHEN** the config file contains comments before and after the `"preset"` field
- **THEN** after the write, all comments SHALL be preserved exactly as they were

#### Scenario: surgical write preserves formatting
- **WHEN** the config file has custom indentation (e.g., tabs, 2-space, 4-space)
- **THEN** after the write, the indentation and whitespace SHALL be preserved exactly

#### Scenario: regex pattern not found fallback
- **WHEN** the top-level `"preset"` field cannot be matched by the regex pattern
- **THEN** the omo module SHALL fall back to a full re-serialize using `json5.dumps()`, SHALL warn the user about potential formatting loss, and SHALL require explicit confirmation

### Requirement: Write safety
The omo module SHALL write changes via a temp file in the same directory as the target file, followed by an atomic rename (`os.replace()`). A `.bak` backup SHALL be created before any write operation. The user SHALL be prompted for confirmation before writing.

#### Scenario: temp file and atomic rename
- **WHEN** performing a write
- **THEN** the content SHALL be written to a temporary file in the same directory, then atomically renamed to the target path via `os.replace()`

#### Scenario: backup file created before write
- **WHEN** performing a write
- **THEN** a `.bak` copy of the original file SHALL be created in the same directory before any modification

#### Scenario: existing backup is overwritten
- **WHEN** a `.bak` file already exists from a previous write
- **THEN** the new backup SHALL overwrite the existing `.bak` file

#### Scenario: user confirmation required
- **WHEN** the user is about to change the preset from `"openrouter"` to `"anthropic"`
- **THEN** the module SHALL prompt: `"Update active preset from 'openrouter' to 'anthropic'? [y/N]"` and SHALL only proceed on affirmative input

#### Scenario: user declines confirmation
- **WHEN** the user responds `n` or `N` to the confirmation prompt
- **THEN** the write SHALL be aborted and no changes SHALL be made to the config file

### Requirement: Missing config handling
The omo module SHALL handle a missing OMO config file gracefully by reporting a clear error message and not crashing. It SHALL list the candidate paths that were searched so the user can diagnose the issue.

#### Scenario: missing config file error message
- **WHEN** the OMO config file does not exist at any candidate path
- **THEN** the omo module SHALL raise a `FileNotFoundError` (or custom exception) with a message listing all paths that were searched

#### Scenario: missing config does not crash
- **WHEN** the OMO config file is missing
- **THEN** the omo module SHALL NOT crash with an unhandled exception; the error SHALL be propagated to the caller as a typed exception