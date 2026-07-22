## ADDED Requirements

### Requirement: Bootstrap trigger
The bootstrap module SHALL check for the existence of a `.project` file in the project root directory. If the file already exists, the bootstrap SHALL exit without making any changes. If the file does not exist, the bootstrap SHALL proceed with the creation workflow.

#### Scenario: .project does not exist
- **WHEN** the bootstrap is invoked and no `.project` file exists in the project root
- **THEN** the bootstrap SHALL proceed to derive a project name and harvest API keys

#### Scenario: .project already exists
- **WHEN** the bootstrap is invoked and a `.project` file already exists in the project root
- **THEN** the bootstrap SHALL exit without modifying the existing file

### Requirement: Project name derivation
The bootstrap SHALL derive the `OCPP_PROJECT_NAME` value from the current working directory name. The derivation SHALL use the last component of `Path.cwd()`, sanitized by stripping leading/trailing whitespace and replacing sequences of non-alphanumeric characters (excluding `-`, `_`, `.`) with a single `-`. The resulting value SHALL be written as `OCPP_PROJECT_NAME=<value>` in the `.project` file.

#### Scenario: simple directory name
- **WHEN** the current working directory is `/home/user/my-project`
- **THEN** the `OCPP_PROJECT_NAME` SHALL be `my-project`

#### Scenario: directory name with special characters
- **WHEN** the current working directory is `/home/user/My   Project!!!`
- **THEN** the `OCPP_PROJECT_NAME` SHALL be sanitized to `My-Project---`

#### Scenario: directory name with leading/trailing whitespace
- **WHEN** the current working directory name has leading or trailing whitespace
- **THEN** the whitespace SHALL be stripped before use as the project name

### Requirement: API key harvesting
The bootstrap SHALL harvest non-empty values from the current environment for the following fixed allowlist of variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `MISTRAL_API_KEY`. Only variables with non-empty values (after stripping whitespace) SHALL be included in the `.project` file. Empty or unset variables SHALL be silently skipped.

#### Scenario: all keys present and non-empty
- **WHEN** all six allowlisted environment variables are set to non-empty values
- **THEN** all six SHALL be included in the `.project` file

#### Scenario: some keys empty or unset
- **WHEN** `ANTHROPIC_API_KEY` is set to `sk-abc123` and `OPENAI_API_KEY` is unset
- **THEN** only `ANTHROPIC_API_KEY` SHALL be included in the `.project` file; `OPENAI_API_KEY` SHALL be skipped

#### Scenario: key with whitespace-only value
- **WHEN** a variable is set to a whitespace-only string (e.g., `"   "`)
- **THEN** that variable SHALL be treated as empty and SHALL be skipped

### Requirement: User confirmation
The bootstrap SHALL present a confirmation prompt to the user before writing the `.project` file. The prompt SHALL display: the project name (unmasked), each API key variable name with its value masked (e.g., `ANTHROPIC_API_KEY=sk-***...abcd`), and the file path to be written. The user SHALL be prompted with `[y/N]` (default: no). If the user declines, the bootstrap SHALL exit without writing.

#### Scenario: user confirms
- **WHEN** the user is prompted with the confirmation summary and enters `y` or `Y`
- **THEN** the `.project` file SHALL be written to disk

#### Scenario: user declines
- **WHEN** the user is prompted with the confirmation summary and enters `n`, `N`, or presses Enter
- **THEN** the `.project` file SHALL NOT be written and the bootstrap SHALL exit with a message

#### Scenario: values are masked in prompt
- **WHEN** the confirmation summary is displayed
- **THEN** API key values SHALL be masked (e.g., displaying only the first few characters and trailing characters, or `***`); the full plaintext values SHALL NOT appear in the output

### Requirement: Gitignore warning
The bootstrap SHALL detect whether the project root is a git repository (by checking for the presence of a `.git` directory). If it is a git repository and `.project` is not already listed in `.gitignore` (either project-level or global), the bootstrap SHALL display a warning and offer to append `.project` to the project-level `.gitignore`. The offer SHALL require explicit user confirmation. If the user declines, the bootstrap SHALL continue without modifying `.gitignore`.

#### Scenario: git repo and .project not gitignored
- **WHEN** the project root contains a `.git` directory and `.project` is not in `.gitignore`
- **THEN** the bootstrap SHALL warn the user that `.project` contains API keys and should be gitignored, and SHALL offer to append `.project` to `.gitignore`

#### Scenario: user accepts gitignore offer
- **WHEN** the user is warned about `.project` not being gitignored and accepts the offer to append it
- **THEN** the bootstrap SHALL append `.project` to the project-level `.gitignore` file

#### Scenario: user declines gitignore offer
- **WHEN** the user is warned about `.project` not being gitignored and declines the offer
- **THEN** the bootstrap SHALL continue without modifying `.gitignore`

#### Scenario: not a git repository
- **WHEN** the project root does not contain a `.git` directory
- **THEN** the bootstrap SHALL skip the gitignore check entirely

#### Scenario: .project already gitignored
- **WHEN** the project root contains a `.git` directory and `.project` is already listed in `.gitignore`
- **THEN** the bootstrap SHALL NOT warn the user about gitignore

### Requirement: File permissions
After writing the `.project` file, the bootstrap SHALL set restrictive file permissions to `0o600` (owner read/write only) where the platform supports it. On platforms where `chmod` has limited effect (e.g., Windows), the bootstrap SHALL make a best-effort attempt and proceed without error if the permission change is not fully supported.

#### Scenario: POSIX platform
- **WHEN** the `.project` file is written on a POSIX platform (Linux, Unix)
- **THEN** the file permissions SHALL be set to `0o600` (owner read/write, no group or other access)

#### Scenario: Windows platform
- **WHEN** the `.project` file is written on Windows
- **THEN** the bootstrap SHALL call `chmod(0o600)` as a best-effort attempt and SHALL NOT fail if the permission change is not fully enforced