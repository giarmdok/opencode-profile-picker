## 1. Implement argparse parser with all flags

- [ ] 1.1 Create `ArgumentParser` with `description` for the `ocpp` tool
- [ ] 1.2 Add `--preset NAME` flag (optional, string, for non-interactive preset selection)
- [ ] 1.3 Add `--no-launch` flag (optional, boolean, store_true)
- [ ] 1.4 Add `--project-dir PATH` flag (optional, string, default: current working directory)
- [ ] 1.5 Add `--dry-run` flag (optional, boolean, store_true)
- [ ] 1.6 Add `--init` flag (optional, boolean, store_true)
- [ ] 1.7 Use `parse_known_args()` to collect known flags and capture remaining args as passthrough for opencode
- [ ] 1.8 Validate `--project-dir` path exists, print error and exit if not

## 2. Wire bootstrap step

- [ ] 2.1 Import `bootstrap.run_bootstrap` from the bootstrap module
- [ ] 2.2 Check if `.project` exists in the project root: if missing or `--init` is set, call `run_bootstrap()`
- [ ] 2.3 If `--init` and `.project` exists, create a `.project.bak` backup and warn the user before proceeding
- [ ] 2.4 If `--dry-run`, print "Would bootstrap .project at <path>" instead of calling `run_bootstrap()`
- [ ] 2.5 If the user declines bootstrap, print error message and exit with non-zero status

## 3. Wire project load step

- [ ] 3.1 Import `project.parse_project` from the project module
- [ ] 3.2 Call `parse_project()` on the `.project` file path
- [ ] 3.3 If parsing fails, print error with file path, specific error, and suggestion to run `--init`
- [ ] 3.4 If `--dry-run`, print "Would load .project from <path>" and continue

## 4. Wire venv detection step

- [ ] 4.1 Import `venv.find_venv` and `venv.compute_venv_env_delta` from the venv module
- [ ] 4.2 Call `find_venv()` on the project root using the platform instance
- [ ] 4.3 If no venv found, print a warning and continue
- [ ] 4.4 If venv found but invalid, print a warning and continue
- [ ] 4.5 If venv is valid, compute the env delta via `compute_venv_env_delta()`
- [ ] 4.6 If `--dry-run`, print "Would detect venv at <path>" or "No venv found"

## 5. Wire preset listing with rich

- [ ] 5.1 Import `omo.discover_config`, `omo.parse_config`, `omo.list_presets` from the omo module
- [ ] 5.2 Import `rich.console.Console` and `rich.table.Table` (or `rich.prompt.Prompt`)
- [ ] 5.3 Call `discover_config()` to find the OMO config file path
- [ ] 5.4 If OMO config not found, print a warning and skip preset selection (continue to launch)
- [ ] 5.5 Call `parse_config()` and `list_presets()` to get available presets with current marker
- [ ] 5.6 If `--dry-run`, print "Would list presets from OMO config at <path>"
- [ ] 5.7 Display a `rich` table or numbered list with preset names, marking the active one

## 6. Wire preset selection (interactive or --preset)

- [ ] 6.1 If `--preset NAME` is provided, validate the preset name exists in the parsed presets
- [ ] 6.2 If `--preset` name is invalid, print error listing all available presets and exit with non-zero status
- [ ] 6.3 If no `--preset` is provided, use `rich.prompt.Prompt` to ask the user to enter a number
- [ ] 6.4 Validate the user's number input is within range; if invalid, re-prompt
- [ ] 6.5 If the user presses Enter without input, skip preset selection

## 7. Wire preset write

- [ ] 7.1 Import `omo.set_preset` from the omo module
- [ ] 7.2 If a preset was selected (interactively or via `--preset`), call `set_preset()` with the chosen name
- [ ] 7.3 If `--dry-run`, print "Would write preset '<name>' to OMO config at <path>" instead of executing
- [ ] 7.4 Handle `omo.OmoError` exceptions with a clear error message

## 8. Wire launch step (or skip if --no-launch)

- [ ] 8.1 Import `launch.launch_opencode` from the launch module
- [ ] 8.2 If `--no-launch` is set, skip launch, print summary, and exit with status 0
- [ ] 8.3 If `--dry-run` is set, print "Would launch opencode with merged environment" and exit
- [ ] 8.4 Build the merged environment: copy `os.environ`, overlay `.project` values, apply venv env delta
- [ ] 8.5 Resolve `opencode` binary via `shutil.which`; if not found, print error and exit with non-zero status
- [ ] 8.6 Call `launch_opencode()` with the merged environment and passthrough args
- [ ] 8.7 On POSIX, the process is replaced by `opencode`; on Windows, `subprocess.run` is used

## 9. Implement --dry-run (show actions without executing)

- [ ] 9.1 At each step, check the `--dry-run` flag before executing any write operation
- [ ] 9.2 Print a descriptive message for each action that would be taken (e.g., "Would bootstrap .project", "Would write preset", "Would launch opencode")
- [ ] 9.3 Do not call any write or launch functions when `--dry-run` is active
- [ ] 9.4 Exit with status 0 after showing all planned actions

## 10. Implement argument passthrough

- [ ] 10.1 Use `parse_known_args()` to separate known `ocpp` flags from unrecognized arguments
- [ ] 10.2 Collect the unrecognized arguments as a `list[str]` for passthrough to `opencode`
- [ ] 10.3 Pass the collected arguments to `launch_opencode()` as the `opencode_args` parameter
- [ ] 10.4 Handle the case where no passthrough arguments are provided (empty list)

## 11. Implement error handling for each step

- [ ] 11.1 Wrap each step in a try/except block with a specific error message
- [ ] 11.2 Handle `.project` parse errors: print file path, error details, suggest `--init`
- [ ] 11.3 Handle OMO config missing: print warning, list searched paths, offer to skip preset
- [ ] 11.4 Handle OMO config parse errors: print file path, error details
- [ ] 11.5 Handle invalid `--preset` name: print error, list available presets
- [ ] 11.6 Handle missing `opencode` binary: print error, suggest installing or using `--no-launch`
- [ ] 11.7 Handle invalid `--project-dir` path: print error and exit before any steps
- [ ] 11.8 Ensure all error messages mask secret values (never print API keys in plaintext)

## 12. Write integration tests

- [ ] 12.1 Test full flow: bootstrap skipped (`.project` exists), load succeeds, venv detected, preset selected interactively, preset written, opencode launched (mocked subprocess)
- [ ] 12.2 Test full flow: bootstrap runs (`.project` missing), user confirms, then load, venv, preset, launch
- [ ] 12.3 Test `--preset` flag: non-interactive preset selection, valid name
- [ ] 12.4 Test `--preset` flag: invalid name exits with error listing available presets
- [ ] 12.5 Test `--no-launch` flag: all steps except launch executed, exits with status 0
- [ ] 12.6 Test `--dry-run` flag: shows planned actions, no files written, no subprocess launched
- [ ] 12.7 Test `--init` flag: forces bootstrap even when `.project` exists, creates `.bak` backup
- [ ] 12.8 Test `--project-dir` flag: overrides project root for all file lookups
- [ ] 12.9 Test `--project-dir` flag: invalid path exits with error
- [ ] 12.10 Test argument passthrough via `--`: passthrough args forwarded to opencode, no passthrough = empty args
- [ ] 12.11 Test error handling: `.project` parse error, OMO config missing, opencode binary missing
- [ ] 12.12 Test error handling: venv missing (warning, continues), venv invalid (warning, continues)
- [ ] 12.13 Test rich preset listing: numbered list displayed, user input accepted, invalid input re-prompted
- [ ] 12.14 Test combined flags: `--preset openrouter --no-launch --dry-run` (all three together)

## 13. Verify ruff/mypy pass

- [ ] 13.1 Run `ruff check .` and fix any violations
- [ ] 13.2 Run `mypy src/` and fix any type errors
- [ ] 13.3 Run `pytest tests/` and confirm all CLI flow tests pass