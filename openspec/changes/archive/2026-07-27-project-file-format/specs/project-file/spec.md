## ADDED Requirements

### Requirement: .project file format

The `.project` file SHALL use a constrained dotenv-style format with the following grammar:
- Each line SHALL be one of: key-value pair, comment, blank, or unknown line
- Key-value pairs SHALL match `^[A-Za-z_][A-Za-z0-9_]*=.*` — split on the first `=`
- Comment lines SHALL start with `#` (optional leading whitespace)
- Blank lines SHALL contain only whitespace
- All other lines SHALL be treated as unknown lines and preserved verbatim
- No `export` prefix, no quoting, no escape sequences, no variable interpolation, no command substitution SHALL be supported
- File encoding SHALL be UTF-8

#### Scenario: Basic key-value pair
- **WHEN** the `.project` file contains `ANTHROPIC_API_KEY=sk-ant-123`
- **THEN** the parser MUST return `{"ANTHROPIC_API_KEY": "sk-ant-123"}`

#### Scenario: Split on first equals sign
- **WHEN** the `.project` file contains `KEY=value=with=equals`
- **THEN** the parser MUST return `{"KEY": "value=with=equals"}`

#### Scenario: Comment line
- **WHEN** the `.project` file contains `# This is a comment`
- **THEN** the parser MUST record the comment line but not include it in the key-value dict

#### Scenario: Blank line
- **WHEN** the `.project` file contains an empty line
- **THEN** the parser MUST record the blank line and preserve it on rewrite

#### Scenario: Unknown line
- **WHEN** the `.project` file contains a line like `export KEY=value` or `@include file`
- **THEN** the parser MUST record the line as unknown and preserve it verbatim on rewrite

#### Scenario: UTF-8 encoding
- **WHEN** the `.project` file contains Unicode characters (e.g., `KEY=café`)
- **THEN** the parser MUST read and return the value as UTF-8 decoded text

### Requirement: OCPP_PROJECT_NAME reserved key

The parser SHALL recognize `OCPP_PROJECT_NAME` as a reserved key. It SHALL be parsed and serialized like any other key-value pair. The tool SHALL treat it as a non-secret value (not masked in output).

#### Scenario: Reserved key is parsed normally
- **WHEN** the `.project` file contains `OCPP_PROJECT_NAME=my-project`
- **THEN** the parser MUST return `{"OCPP_PROJECT_NAME": "my-project"}`

#### Scenario: Reserved key is not masked
- **WHEN** the `.project` file contains `OCPP_PROJECT_NAME=my-project` and diagnostic output is generated
- **THEN** the value `my-project` MUST be visible in output (not masked as `***`)

### Requirement: Parsing

The parser SHALL read the `.project` file from a given directory path, return an ordered dictionary of resolved key-value pairs, and preserve comment/blank/unknown line data for serializer use.

#### Scenario: Parse from project root
- **WHEN** the parser is called with a project root directory that contains a `.project` file
- **THEN** the parser MUST read `<project_root>/.project` and return the parsed key-value pairs

#### Scenario: Missing file returns empty
- **WHEN** the parser is called with a project root directory that does NOT contain a `.project` file
- **THEN** the parser MUST return an empty dict and no error

#### Scenario: Ordered dict preserves insertion order
- **WHEN** the `.project` file contains `A=1`, `B=2`, `C=3` in that order
- **THEN** the parser MUST return an ordered dict with keys in the same order

#### Scenario: Empty value override
- **WHEN** the `.project` file contains `KEY=` (value after `=` is empty)
- **THEN** the parser MUST return `{"KEY": ""}` — an empty string, not `None` or omitted

#### Scenario: Multiple keys with same name — last wins
- **WHEN** the `.project` file contains `KEY=first`, `KEY=second`
- **THEN** the parser MUST return `{"KEY": "second"}` (last occurrence wins)

### Requirement: Serialization

The serializer SHALL write the `.project` file back to disk preserving all comments, blank lines, unknown lines, and the original order of key-value pairs. Updated values SHALL be written for keys that have changed.

#### Scenario: Preserve comments on rewrite
- **WHEN** a `.project` file with comments is parsed, then serialized back
- **THEN** the output file MUST contain the same comment lines in the same positions

#### Scenario: Preserve blank lines on rewrite
- **WHEN** a `.project` file with blank lines is parsed, then serialized back
- **THEN** the output file MUST contain the same blank lines in the same positions

#### Scenario: Preserve unknown lines on rewrite
- **WHEN** a `.project` file with unknown lines is parsed, then serialized back
- **THEN** the output file MUST contain the same unknown lines in the same positions

#### Scenario: Updated value is written
- **WHEN** a key-value pair is modified in the dict and serialized
- **THEN** the output file MUST contain the updated value for that key

#### Scenario: New key is appended
- **WHEN** a new key-value pair is added to the dict and serialized
- **THEN** the output file MUST contain the new pair at the end of the file

### Requirement: Value masking in diagnostics

Values SHALL be masked in all diagnostic output. The masking utility SHALL replace the value portion with `***` while preserving the key. The `OCPP_PROJECT_NAME` key SHALL NOT be masked.

#### Scenario: Mask secret value
- **WHEN** a key-value pair `ANTHROPIC_API_KEY=sk-ant-123` is passed to the masking utility
- **THEN** the output MUST be `ANTHROPIC_API_KEY=***`

#### Scenario: Do not mask OCPP_PROJECT_NAME
- **WHEN** a key-value pair `OCPP_PROJECT_NAME=my-project` is passed to the masking utility
- **THEN** the output MUST be `OCPP_PROJECT_NAME=my-project`

#### Scenario: Masking is applied to all output paths
- **WHEN** any diagnostic output (logging, CLI, error messages) includes key-value pairs
- **THEN** the values MUST be masked using the masking utility

### Requirement: Validation

The parser SHALL validate variable names and values. Invalid variable names SHALL be rejected. Embedded newlines in values SHALL be rejected.

#### Scenario: Reject invalid variable name
- **WHEN** the `.project` file contains `123KEY=value` (starts with digit)
- **THEN** the parser MUST raise a validation error

#### Scenario: Reject hyphen in variable name
- **WHEN** the `.project` file contains `MY-KEY=value`
- **THEN** the parser MUST raise a validation error

#### Scenario: Reject embedded newline in value
- **WHEN** the `.project` file contains `KEY=line1\nline2`
- **THEN** the parser MUST raise a validation error

#### Scenario: Reject export prefix
- **WHEN** the `.project` file contains `export KEY=value`
- **THEN** the parser MUST raise a validation error (or treat as unknown line — the line does not match the key-value pattern)