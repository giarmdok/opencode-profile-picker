## 1. Implement argparse parser with all flags

- [x] 1.1 Create `ArgumentParser` with `description` for the `ocpp` tool
- [x] 1.2 Add `--preset NAME` flag (optional, string, for non-interactive preset selection)
- [x] 1.3 Add `--no-launch` flag (optional, boolean, store_true)
- [x] 1.4 Add `--project-dir PATH` flag (optional, string, default: current working directory)
- [x] 1.5 Add `--dry-run` flag (optional, boolean, store_true)
- [x] 1.6 Add `--init` flag (optional, boolean, store_true)
- [x] 1.7 Use `parse_known_args()` to collect known flags and capture remaining args as passthrough for opencode
- [x] 1.8 Validate `--project-dir` path exists, print error and exit if not

## 2. Wire bootstrap step

- [x] 2.1 Import `bootstrap.run_bootstrap` from the bootstrap module
- [x] 2.2 Check if `.project` exists in the project root: if missing or `--init` is set, call `run_bootstrap()`
- [x] 2.3 If `--init` and `.project` exists, create a `.project.bak` backup and warn the user before proceeding
- [x] 2.4 If `--dry-run`, print \"Would bootstrap .project at <path>\" instead of calling `run_bootstrap()`
- [x] 2.5 If the user declines bootstrap, print error message and exit with non-zero status

## 3. Wire project load step

- [x] 3.1 Import `project.parse_project` from the project module
- [x] 3.2 Call `parse_project()` on the `.project` file path
- [x] 3.3 If parsing fails, print error with file path, specific error, and suggestion to run `--init`
- [x] 3.4 If `--dry-run`, print \"Would load .project from <path>\" and continue

## 4. Wire venv detection step

- [x] 4.1 Import `venv.find_venv` and `venv.compute_venv_env_delta` from the venv module
- [x] 4.2 Call `find_venv()` on the project root using the platform instance
- [x] 4.3 If no venv found, print a warning and continue
- [x] 4.4 If venv found but invalid, print a warning and continue
- [x] 4.5 If venv is valid, compute the env delta via `compute_venv_env_delta()`
- [x] 4.6 If `--dry-run`, print \"Would detect venv at <path>\" or \"No venv found\"

## 5. Wire preset listing with rich

- [x] 5.1 Import `omo.discover_config`, `omo.parse_config`, `omo.list_presets` from the omo module
- [x] 5.2 Import `rich.console.Console` and `rich.table.Table` (or `rich.prompt.Prompt`)
- [x] 5.3 Call `discover_config()` to find the OMO config file path
- [x] 5.4 If OMO config not found, print a warning and skip preset selection (continue to launch)
- [x] 5.5 Call `parse_config()` and `list_presets()` to get available presets with current marker
- [x] 5.6 If `--dry-run`, print \"Would list presets from OMO config at <path>\"
- [x] 5.7 Display a `rich` table or numbered list with preset names, marking the active one

## 6. Wire preset selection (interactive or --preset)

- [x] 6.1 If `--preset NAME` is provided, validate the preset name exists in the parsed presets
- [x] 6.2 If `--preset` name is invalid, print error listing all available presets and exit with non-zero status
- [x] 6.3 If no `--preset` is provided, use `rich.prompt.Prompt` to ask the user to enter a number
- [x] 6.4 Validate the user's number input is within range; if invalid, re-prompt
- [x] 6.5 If the user presses Enter without input, skip preset selection

## 7. Wire preset write

- [x] 7.1 Import `omo.set_preset` from the omo module
- [x] 7.2 If a preset was selected (interactively or via `--preset`), call `set_preset()` with the chosen name
- [x] 7.3 If `--dry-run`, print \"Would write preset '<name>' to OMO config at <path>\" instead of executing
- [x] 7.4 Handle `omo.OmoError` exceptions with a clear error message

## 8. Wire launch step (or skip if --no-launch)

- [x] 8.1 Import `launch.launch_opencode` from the launch module
- [x] 8.2 If `--no-launch` is set, skip launch, print summary, and exit with status 0
- [x] 8.3 If `--dry-run` is set, print \"Would launch opencode with merged environment\" and exit
- [x] 8.4 Build the merged environment: copy `os.environ`, overlay `.project` values, apply venv env delta
- [x] 8.5 Resolve `opencode` binary via `shutil.which`; if not found, print error and exit with non-zero status
- [x] 8.6 Call `launch_opencode()` with the merged environment and passthrough args
- [x] 8.7 On POSIX, the process is replaced by `opencode`; on Windows, `subprocess.run` is used

## 9. Implement --dry-run (show actions without executing)

- [x] 9.1 At each step, check the `--dry-run` flag before executing any write operation
- [x] 9.2 Print a descriptive message for each action that would be taken (e.g., \"Would bootstrap .project\", \"Would write preset\", \"Would launch opencode\")
- [x] 9.3 Do not call any write or launch functions when `--dry-run` is active
- [x] 9.4 Exit with status 0 after showing all planned actions

## 10. Implement argument passthrough

- [x] 10.1 Use `parse_known_args()` to separate known `ocpp` flags from unrecognized arguments
- [x] 10.2 Collect the unrecognized arguments as a `list[str]` for passthrough to `opencode`
- [x] 10.3 Pass the collected arguments to `launch_opencode()` as the `opencode_args` parameter
- [x] 10.4 Handle the case where no passthrough arguments are provided (empty list)

## 11. Implement error handling for each step

- [x] 11.1 Wrap each step in a try/except block with a specific error message
- [x] 11.2 Handle `.project` parse errors: print file path, error details, suggest `--init`
- [x] 11.3 Handle OMO config missing: print warning, list searched paths, offer to skip preset
- [x] 11.4 Handle OMO config parse errors: print file path, error details
- [x] 11.5 Handle invalid `--preset` name: print error, list available presets
- [x] 11.6 Handle missing `opencode` binary: print error, suggest installing or using `--no-launch`
- [x] 11.7 Handle invalid `--project-dir` path: print error and exit before any steps
- [x] 11.8 Ensure all error messages mask secret values (never print API keys in plaintext)

## 12. Write integration tests

- [x] 12.1 Test full flow: bootstrap skipped (`.project` exists), load succeeds, venv detected, preset selected interactively, preset written, opencode launched (mocked subprocess)
- [x] 12.2 Test full flow: bootstrap runs (`.project` missing), user confirms, then load, venv, preset, launch
- [x] 12.3 Test `--preset` flag: non-interactive preset selection, valid name
- [x] 12.4 Test `--preset` flag: invalid name exits with error listing available presets
- [x] 12.5 Test `--no-launch` flag: all steps except launch executed, exits with status 0
- [x] 12.6 Test `--dry-run` flag: shows planned actions, no files written, no subprocess launched
- [x] 12.7 Test `--init` flag: forces bootstrap even when `.project` exists, creates `.bak` backup
- [x] 12.8 Test `--project-dir` flag: overrides project root for all file lookups
- [x] 12.9 Test `--project-dir` flag: invalid path exits with error
- [x] 12.10 Test argument passthrough via `--`: passthrough args forwarded to opencode, no passthrough = empty args
- [x] 12.11 Test error handling: `.project` parse error, OMO config missing, opencode binary missing
- [x] 12.12 Test error handling: venv missing (warning, continues), venv invalid (warning, continues)
- [x] 12.13 Test rich preset listing: numbered list displayed, user input accepted, invalid input re-prompted
- [x] 12.14 Test combined flags: `--preset openrouter --no-launch --dry-run` (all three together)

## 13. Verify ruff/mypy pass

- [x] 13.1 Run `ruff check .` and fix any violations
- [x] 13.2 Run `mypy src/` and fix any type errors
- [x] 13.3 Run `pytest tests/` and confirm all CLI flow tests pass