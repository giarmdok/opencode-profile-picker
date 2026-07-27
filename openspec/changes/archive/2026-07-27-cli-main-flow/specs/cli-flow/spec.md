## ADDED Requirements

### Requirement: Full flow orchestration
The CLI entry point SHALL orchestrate the complete six-step flow in order: (1) bootstrap — create `.project` if missing or `--init` is provided, (2) load — parse the `.project` file via `project.parse_project()`, (3) venv — detect the project Python virtual environment via `venv.find_venv()`, (4) list presets — discover and parse the OMO config via `omo.discover_config()` and `omo.parse_config()`, (5) select preset — present a `rich`-based interactive preset listing or use `--preset` for non-interactive, then write via `omo.set_preset()`, (6) launch — build merged environment and launch `opencode` via `launch.launch_opencode()`. Each step SHALL only proceed if the previous step succeeds or is gracefully skipped.

#### Scenario: full flow with interactive preset selection
- **WHEN** the user runs `ocpp` from a project directory that has no `.project` file, has an OMO config with presets, has a valid venv, and has `opencode` on PATH
- **THEN** the tool SHALL run bootstrap (interactive), load the new `.project`, detect the venv, list presets via `rich`, wait for user to select a preset, write the preset, and launch `opencode` with the merged environment

#### Scenario: full flow with all prerequisites met
- **WHEN** the user runs `ocpp` from a project directory that already has a `.project` file, has an OMO config, a valid venv, and `opencode` on PATH
- **THEN** the tool SHALL skip bootstrap, load `.project`, detect venv, list presets, wait for user selection, write preset, and launch `opencode`

#### Scenario: flow stops at bootstrap if user declines
- **WHEN** the user runs `ocpp` from a project directory with no `.project` file and declines the bootstrap confirmation
- **THEN** the tool SHALL print an error message and exit with non-zero status without proceeding to later steps

### Requirement: --preset flag
The CLI SHALL support a `--preset NAME` flag that selects a preset non-interactively, skipping the `rich` preset listing prompt. The provided preset name SHALL be validated against the `"presets"` object in the parsed OMO config. If the preset name does not exist, the CLI SHALL print an error listing all available preset names and exit with non-zero status.

#### Scenario: valid --preset selection
- **WHEN** the user runs `ocpp --preset openrouter` and `"openrouter"` exists in the `"presets"` object
- **THEN** the tool SHALL skip the preset listing prompt and directly write `"openrouter"` as the active preset

#### Scenario: invalid --preset name
- **WHEN** the user runs `ocpp --preset nonexistent` and `"nonexistent"` does not exist in the `"presets"` object
- **THEN** the tool SHALL print an error message listing all available preset names and exit with non-zero status

#### Scenario: --preset with no OMO config
- **WHEN** the user runs `ocpp --preset openrouter` and no OMO config file exists
- **THEN** the tool SHALL print a warning that the OMO config is missing, skip preset selection, and continue to the launch step (or exit if `--preset` was required)

### Requirement: --no-launch flag
The CLI SHALL support a `--no-launch` flag that executes all steps up to and including the preset write, but skips the final opencode launch step. The tool SHALL print a summary of what was done and exit with status 0.

#### Scenario: --no-launch completes setup
- **WHEN** the user runs `ocpp --no-launch` with valid `.project` and OMO config
- **THEN** the tool SHALL run bootstrap, load, venv detection, preset listing, and preset write, but SHALL NOT launch `opencode`, and SHALL exit with status 0

#### Scenario: --no-launch with --preset
- **WHEN** the user runs `ocpp --preset openrouter --no-launch`
- **THEN** the tool SHALL select and write the `"openrouter"` preset non-interactively, skip launch, and exit with status 0

### Requirement: --project-dir flag
The CLI SHALL support a `--project-dir PATH` flag that overrides the project root directory. All file lookups (`.project`, venv, OMO config) SHALL be relative to the given path. The default value SHALL be the current working directory (`Path.cwd()`). If the provided path does not exist, the CLI SHALL exit with an error before executing any steps.

#### Scenario: --project-dir specifies project root
- **WHEN** the user runs `ocpp --project-dir /home/user/my-project`
- **THEN** the tool SHALL use `/home/user/my-project` as the project root for all file operations

#### Scenario: --project-dir path does not exist
- **WHEN** the user runs `ocpp --project-dir /nonexistent/path`
- **THEN** the tool SHALL print an error that the specified path does not exist and exit with non-zero status

#### Scenario: --project-dir defaults to cwd
- **WHEN** the user runs `ocpp` without `--project-dir`
- **THEN** the tool SHALL use the current working directory as the project root

### Requirement: --dry-run flag
The CLI SHALL support a `--dry-run` flag that shows the actions that would be taken without actually modifying any files or launching any processes. Each step SHALL print what it would do (e.g., "Would bootstrap .project at <path>", "Would write preset 'anthropic' to OMO config", "Would launch opencode with <env>"). No files SHALL be written, no backups created, and no subprocesses launched.

#### Scenario: --dry-run shows bootstrap plan
- **WHEN** the user runs `ocpp --dry-run` from a directory with no `.project`
- **THEN** the tool SHALL print "Would bootstrap .project at <path>" and exit without creating the file

#### Scenario: --dry-run shows preset plan
- **WHEN** the user runs `ocpp --dry-run --preset openrouter`
- **THEN** the tool SHALL print "Would write preset 'openrouter' to OMO config" and exit without modifying the config

#### Scenario: --dry-run shows launch plan
- **WHEN** the user runs `ocpp --dry-run` with all prerequisites met
- **THEN** the tool SHALL print "Would launch opencode with merged environment" and exit without launching

### Requirement: --init flag
The CLI SHALL support an `--init` flag that forces the bootstrap step to run even if a `.project` file already exists. Before overwriting, the existing `.project` SHALL be backed up to `.project.bak` in the same directory. The user SHALL be warned about the backup and asked for confirmation before proceeding.

#### Scenario: --init forces bootstrap with existing .project
- **WHEN** the user runs `ocpp --init` and a `.project` file already exists
- **THEN** the tool SHALL create a backup (`.project.bak`), warn the user, and proceed with the bootstrap workflow

#### Scenario: --init creates fresh .project
- **WHEN** the user runs `ocpp --init` and no `.project` file exists
- **THEN** the tool SHALL run the bootstrap workflow normally (same as without `--init`)

### Requirement: Argument passthrough via --
The CLI SHALL support a `--` separator. All arguments after `--` SHALL be passed through to the `opencode` subprocess as-is, appended to the command line. The CLI SHALL use `argparse.parse_known_args()` to extract known flags and collect remaining arguments as passthrough.

#### Scenario: passthrough arguments forwarded to opencode
- **WHEN** the user runs `ocpp --preset openrouter -- --model claude-3-opus --temperature 0.7`
- **THEN** the tool SHALL launch `opencode --model claude-3-opus --temperature 0.7` with the merged environment

#### Scenario: no passthrough arguments
- **WHEN** the user runs `ocpp --preset openrouter` without `--`
- **THEN** the tool SHALL launch `opencode` with no additional arguments

#### Scenario: passthrough with --no-launch (no launch happens)
- **WHEN** the user runs `ocpp --no-launch -- --model claude-3-opus`
- **THEN** the passthrough arguments SHALL be collected but SHALL NOT be used since launch is skipped

### Requirement: Preset listing with rich
The CLI SHALL use `rich` to display the list of available presets. The display SHALL be a numbered list or table showing each preset name and indicating the currently active preset. The user SHALL select a preset by entering its number. If the user enters an invalid number or presses Enter without input, the preset selection SHALL be skipped.

#### Scenario: preset listing displayed as numbered list
- **WHEN** the OMO config has three presets: `openrouter`, `anthropic`, `google` with `openrouter` as the current
- **THEN** the CLI SHALL display a `rich` table or numbered list with `1: openrouter (active)`, `2: anthropic`, `3: google`

#### Scenario: user selects a preset by number
- **WHEN** the preset listing is displayed and the user enters `2`
- **THEN** the tool SHALL select `anthropic` and proceed to write it

#### Scenario: user skips preset selection
- **WHEN** the preset listing is displayed and the user presses Enter without entering a number
- **THEN** the tool SHALL skip the preset write and proceed to the launch step

#### Scenario: user enters invalid number
- **WHEN** the preset listing is displayed and the user enters `99` (out of range)
- **THEN** the tool SHALL print an error message and re-prompt the user

### Requirement: Error handling
The CLI SHALL provide clear, actionable error messages for each failure mode. Error messages SHALL include: what went wrong, the relevant file path or value, and a suggested action to resolve the issue. The tool SHALL exit with a non-zero status code on errors. Secret values (API keys) SHALL be masked in all error messages.

#### Scenario: .project parse error
- **WHEN** the `.project` file contains invalid syntax (e.g., a key starting with a digit)
- **THEN** the CLI SHALL print "Error parsing .project at <path>: <specific error>. Run `ocpp --init` to create a fresh .project." and exit with non-zero status

#### Scenario: OMO config not found
- **WHEN** no OMO config file exists at any candidate path
- **THEN** the CLI SHALL print "OMO config not found. Searched: <paths>. Preset selection skipped. Run `oh-my-opencode-slim setup` to create one." and continue to the launch step (or exit if `--preset` was used)

#### Scenario: opencode binary not found
- **WHEN** `shutil.which("opencode")` returns `None` at the launch step
- **THEN** the CLI SHALL print "opencode binary not found. Install opencode (https://github.com/opencode-ai/opencode) or use `--no-launch` to skip launching." and exit with non-zero status

#### Scenario: venv invalid warning
- **WHEN** a venv directory exists but the interpreter executable is missing
- **THEN** the CLI SHALL print a warning "Venv found at <path> but interpreter missing. Continuing without venv activation." and proceed to next steps

#### Scenario: no venv found warning
- **WHEN** no venv directory is found
- **THEN** the CLI SHALL print a warning "No Python venv found in project root. Continuing without venv activation." and proceed to next steps