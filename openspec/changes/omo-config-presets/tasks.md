## 1. Create omo module

- [ ] 1.1 Create `src/ocpp/omo.py` with a public API: `discover_config()`, `parse_config()`, `list_presets()`, `set_preset()`
- [ ] 1.2 Define a custom exception class (e.g., `OmoError`) for typed error handling
- [ ] 1.3 Ensure `__all__` exports the public API and exception class

## 2. Implement config discovery

- [ ] 2.1 Accept a list of candidate paths (from `Platform.omo_config_paths`) and return the first existing path
- [ ] 2.2 Check both `.json` and `.jsonc` variants from the platform-abstraction search order
- [ ] 2.3 Raise `FileNotFoundError` with a descriptive message listing all searched paths when no config is found

## 3. Implement parsing and validation with json5

- [ ] 3.1 Read the discovered config file content as raw text
- [ ] 3.2 Parse with `json5.loads()`, catching `ValueError` and reporting the file path and parse error location
- [ ] 3.3 Validate that parsed result is a `dict` with a top-level `"preset"` key (string) and `"presets"` key (dict)
- [ ] 3.4 Raise `OmoError` with a clear message for each validation failure

## 4. Implement preset listing

- [ ] 4.1 Extract the current `"preset"` value from the parsed config
- [ ] 4.2 Extract preset names from the `"presets"` object keys
- [ ] 4.3 Return a list of preset names with the current preset marked
- [ ] 4.4 Handle the case where the current preset name is not in the `"presets"` object (report it as missing)

## 5. Implement surgical preset write

- [ ] 5.1 Build the regex pattern to match top-level `"preset": "..."` (anchor to line start or `{` character)
- [ ] 5.2 Read the raw file text, apply the regex replacement for the new preset value
- [ ] 5.3 If the regex does not match, fall back to `json5.dumps()` full re-serialize with a warning
- [ ] 5.4 Write the updated content to a temp file in the same directory using `tempfile.NamedTemporaryFile(dir=target_dir, delete=False)`
- [ ] 5.5 Atomically rename the temp file to the target path using `os.replace()`
- [ ] 5.6 Create a `.bak` backup copy of the original file before any write attempt
- [ ] 5.7 Overwrite existing `.bak` if one already exists

## 6. Implement confirmation prompt

- [ ] 6.1 Before writing, display the old and new preset values and the backup filename
- [ ] 6.2 Prompt the user: `"Update active preset from '<old>' to '<new>'? [y/N]"`
- [ ] 6.3 Only proceed on affirmative input (`y`/`Y`/`yes`/`YES`)
- [ ] 6.4 On the fallback re-serialize path, add an extra warning about potential formatting loss to the confirmation prompt

## 7. Write unit tests

- [ ] 7.1 Test OMO config discovery: `.json` file found, `.jsonc` file found, Windows fallback path, no config found
- [ ] 7.2 Test parsing valid config (with `"preset"` and `"presets"` fields)
- [ ] 7.3 Test parsing malformed config (invalid JSONC syntax)
- [ ] 7.4 Test parsing config with missing or invalid fields (missing preset, missing presets, wrong types)
- [ ] 7.5 Test preset listing: multiple presets, current preset marked, current preset not in presets object, empty presets
- [ ] 7.6 Test surgical write: preset value changed, comments preserved, formatting preserved, trailing comma preserved
- [ ] 7.7 Test surgical write creates `.bak` backup
- [ ] 7.8 Test surgical write uses temp file + atomic rename
- [ ] 7.9 Test regex fallback: when regex does not match, falls back to re-serialize with warning
- [ ] 7.10 Test user confirmation: affirmative proceeds, negative aborts
- [ ] 7.11 Test missing config error message and graceful handling
- [ ] 7.12 Test malformed config error message

## 8. Verify linting and type checking

- [ ] 8.1 Run `ruff check .` and fix any violations
- [ ] 8.2 Run `mypy src/` and fix any type errors
- [ ] 8.3 Run `pytest tests/` and confirm all omo tests pass