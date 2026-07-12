## 1. Project Setup

- [ ] 1.1 Create `pyproject.toml` with project metadata, dependencies (textual, cryptography, json5), and dev dependencies (pyinstaller, ruff, mypy, pytest)
- [ ] 1.2 Create `src/opencode_profile_picker/` package structure with `__init__.py` and `__main__.py`
- [ ] 1.3 Create `tests/` directory with `__init__.py` and `conftest.py`
- [ ] 1.4 Configure ruff, mypy, and pytest in `pyproject.toml`
- [ ] 1.5 Verify venv setup: `pip install -e ".[dev]"` succeeds and `python -m opencode_profile_picker` runs without error

## 2. Platform Path Resolution

- [ ] 2.1 Implement `config/paths.py` with `get_opencode_config_dir()` returning platform-appropriate path (Windows: `%APPDATA%\opencode\` and `~\.config\opencode\`, Unix: `~/.config/opencode/`, respect `XDG_CONFIG_HOME`)
- [ ] 2.2 Implement `get_oopps_data_dir()` returning `~/.config/oopps/` (or platform equivalent)
- [ ] 2.3 Implement `get_opencode_executable()` to locate `opencode` on PATH
- [ ] 2.4 Write unit tests for path resolution on current platform

## 3. Config Discovery

- [ ] 3.1 Implement `config/parser.py` with `read_jsonc(path)` using json5 to parse OMO config files, returning parsed dict or None on failure
- [ ] 3.2 Implement `config/discover.py` with `discover_omo_config()` that finds `oh-my-opencode-slim.jsonc` (preferred) or `.json` in the config directory
- [ ] 3.3 Implement `extract_presets(config)` returning list of preset names from the `presets` key
- [ ] 3.4 Implement `extract_providers_from_preset(config, preset_name)` that walks agent configs and council configs to collect all model provider prefixes
- [ ] 3.5 Implement `PROVIDER_KEY_MAP` constant mapping provider prefixes to env var names (openai→OPENAI_API_KEY, anthropic→ANTHROPIC_API_KEY, google→GOOGLE_API_KEY, mistral→MISTRAL_API_KEY, xai→XAI_API_KEY, openrouter→OPENROUTER_API_KEY, github-copilot→GITHUB_TOKEN, deepseek→DEEPSEEK_API_KEY)
- [ ] 3.6 Implement `map_presets_to_keys(config)` returning `{preset_name: set[env_var]}` for all presets
- [ ] 3.7 Implement `detect_project_local_override(cwd)` checking `.opencode/oh-my-opencode-slim.json[c]` for a `preset` field
- [ ] 3.8 Write unit tests for discovery with fixture config files (valid, malformed, missing, multi-provider, with council)

## 4. Data Models

- [ ] 4.1 Implement `profiles/models.py` with `KeyEntry` dataclass (provider, env_var, value)
- [ ] 4.2 Implement `KeySet` dataclass (name, keys: dict[str, KeyEntry])
- [ ] 4.3 Implement `Profile` dataclass (name, preset, key_set)
- [ ] 4.4 Implement `ProfileStore` dataclass (version, key_sets: dict, profiles: dict) with `to_dict()` and `from_dict()` serialization

## 5. Encryption

- [ ] 5.1 Implement `profiles/crypto.py` with `derive_key(password, salt)` using PBKDF2-SHA256 with 600,000 iterations
- [ ] 5.2 Implement `generate_salt()` returning random 16-byte salt
- [ ] 5.3 Implement `encrypt_store(store_dict, key)` returning encrypted bytes with salt and verification token in header
- [ ] 5.4 Implement `decrypt_store(encrypted_bytes, password)` returning store dict or raising on wrong password
- [ ] 5.5 Implement `verify_password(encrypted_bytes, password)` returning bool without full decryption
- [ ] 5.6 Write unit tests for encrypt/decrypt roundtrip, wrong password detection, salt uniqueness

## 6. Profile Store (Encrypted Persistence)

- [ ] 6.1 Implement `profiles/store.py` with `ProfileStoreManager` class holding the decrypted store in memory
- [ ] 6.2 Implement `load(password)` reading and decrypting `profiles.json.enc`, returning manager instance
- [ ] 6.3 Implement `create(password)` for first-run: generates salt, creates empty store, encrypts and saves
- [ ] 6.4 Implement `save()` encrypting and writing the current in-memory store to disk
- [ ] 6.5 Implement `reset()` deleting `profiles.json.enc`
- [ ] 6.6 Implement `store_exists()` checking if `profiles.json.enc` exists
- [ ] 6.7 Write unit tests for load/create/save/reset cycle

## 7. Profile CRUD Operations

- [ ] 7.1 Implement `add_profile(store, name, preset, key_set)` with duplicate name check
- [ ] 7.2 Implement `get_profile(store, name)` returning Profile or None
- [ ] 7.3 Implement `list_profiles(store)` returning all profiles
- [ ] 7.4 Implement `update_profile(store, name, preset, key_set)` changing preset and/or key set
- [ ] 7.5 Implement `delete_profile(store, name)` removing profile (not key set)
- [ ] 7.6 Implement `validate_profiles(store)` checking all profile key_set references exist, returning list of orphaned profiles
- [ ] 7.7 Write unit tests for all CRUD operations including edge cases (duplicates, missing refs, empty store)

## 8. Key Set CRUD Operations

- [ ] 8.1 Implement `add_key_set(store, name)` with duplicate name check
- [ ] 8.2 Implement `get_key_set(store, name)` returning KeySet or None
- [ ] 8.3 Implement `list_key_sets(store)` returning all key sets with key counts
- [ ] 8.4 Implement `delete_key_set(store, name)` with check for referencing profiles
- [ ] 8.5 Implement `add_key(key_set, provider, env_var, value)` with duplicate env_var check
- [ ] 8.6 Implement `remove_key(key_set, env_var)`
- [ ] 8.7 Implement `update_key_value(key_set, env_var, new_value)`
- [ ] 8.8 Write unit tests for all key set CRUD operations

## 9. Preset Application

- [ ] 9.1 Implement `presets/applier.py` with `get_active_preset(config_path)` reading the current `preset` field
- [ ] 9.2 Implement `apply_preset(config_path, preset_name)` reading config, changing `preset` field, writing back (preserving `.json` vs `.jsonc` extension)
- [ ] 9.3 Handle missing config file gracefully (return warning, don't crash)
- [ ] 9.4 Handle malformed config file gracefully (return warning, don't crash)
- [ ] 9.5 Implement `is_preset_already_active(config_path, preset_name)` to skip no-op writes
- [ ] 9.6 Write unit tests with fixture config files

## 10. Key Resolution and Launching

- [ ] 10.1 Implement `keys/resolver.py` with `resolve_keys(profile, store, env)` implementing stored → env → prompt chain
- [ ] 10.2 Implement `get_required_keys(preset_name, discovery_result)` returning set of env vars needed
- [ ] 10.3 Implement `build_launch_env(resolved_keys, current_env)` merging resolved keys with current environment
- [ ] 10.4 Implement `keys/launcher.py` with `launch_opencode(env)` spawning opencode as child process
- [ ] 10.5 Platform-specific process creation: Windows with `CREATE_NEW_CONSOLE`, Unix with terminal inheritance
- [ ] 10.6 Implement `check_opencode_available()` verifying opencode is on PATH
- [ ] 10.7 Handle launch failures with clear error messages that reference key names but never key values
- [ ] 10.8 Write unit tests for key resolution chain and environment building

## 11. TUI - App Shell and Unlock Screen

- [ ] 11.1 Implement `app.py` with `OoppsApp(Textual.App)` subclass, dark theme, screen registry
- [ ] 11.2 Implement `tui/screens/unlock.py` with `UnlockScreen` — password input (masked), unlock button, error display for wrong password
- [ ] 11.3 Implement first-run variant: two password fields (new + confirm), create button, password mismatch error
- [ ] 11.4 Implement "Forgot password?" option that triggers reset flow with data loss warning and confirmation
- [ ] 11.5 Wire unlock screen to `ProfileStoreManager.load()` or `.create()` based on store existence

## 12. TUI - Main Screen

- [ ] 12.1 Implement `tui/screens/main.py` with `MainScreen` — two-panel layout (profiles left, key sets right)
- [ ] 12.2 Implement `tui/widgets/profile_list.py` — DataTable showing profile name, preset, key set; arrow key navigation; highlight current selection
- [ ] 12.3 Implement key set summary panel showing key set names and key counts
- [ ] 12.4 Implement active preset indicator in status area (reads from OMO config)
- [ ] 12.5 Implement footer with keybindings: N=New, E=Edit, D=Delete, K=Key Sets, L=Launch, Q=Quit
- [ ] 12.6 Implement empty state messages for no profiles and no key sets
- [ ] 12.7 Implement orphaned profile warning indicator (key set deleted)

## 13. TUI - Profile Edit Screen

- [ ] 13.1 Implement `tui/screens/profile_edit.py` with `ProfileEditScreen` — name field (new only), preset dropdown, key set dropdown
- [ ] 13.2 Populate preset dropdown from discovery results
- [ ] 13.3 Populate key set dropdown from store
- [ ] 13.4 Implement required-keys compatibility check: show which keys the preset needs and whether the key set provides them (✓ or ✗)
- [ ] 13.5 Implement save with validation (unique name, preset exists, key set exists)
- [ ] 13.6 Implement cancel (Escape) returning to main screen without saving

## 14. TUI - Key Set Screens

- [ ] 14.1 Implement `tui/screens/keyset_list.py` with `KeySetListScreen` — list of key sets with key counts, N=New, E=Edit, D=Delete, B=Back
- [ ] 14.2 Implement delete confirmation with warning about affected profiles
- [ ] 14.3 Implement `tui/screens/keyset_edit.py` with `KeySetEditScreen` — list of keys showing provider, env var name, masked value
- [ ] 14.4 Implement add key flow: provider selection (from known list or custom), env var name, value input (masked)
- [ ] 14.5 Implement edit key value flow with masked input
- [ ] 14.6 Implement remove key with confirmation
- [ ] 14.7 Implement `tui/widgets/key_input.py` — masked input widget with visibility toggle (show/hide button)

## 15. TUI - Launch Flow

- [ ] 15.1 Implement launch action: resolve all keys for selected profile
- [ ] 15.2 Implement missing-key prompt: if keys can't be resolved, show modal listing missing keys with option to enter now or cancel
- [ ] 15.3 Implement "save entered keys to key set" option when prompted for missing keys
- [ ] 15.4 Implement pre-launch summary showing: profile name, preset being applied, keys being injected (names only, not values)
- [ ] 15.5 Implement launch execution: apply preset, build env, spawn opencode, exit oopps
- [ ] 15.6 Implement error handling: opencode not found, spawn failure, preset write failure (warn but continue)

## 16. Entry Point and Wiring

- [ ] 16.1 Implement `__main__.py` — parse no args (v1), bootstrap app
- [ ] 16.2 Wire discovery to run on app startup (after unlock)
- [ ] 16.3 Wire store manager through app context so all screens can access it
- [ ] 16.4 Implement graceful shutdown: clear encryption key from memory on exit
- [ ] 16.5 Add `__init__.py` with package version

## 17. Packaging

- [ ] 17.1 Create PyInstaller spec file (`oopps.spec`) with hidden imports for textual, cryptography, json5
- [ ] 17.2 Add build script/command to `pyproject.toml` (e.g., `pyinstaller oopps.spec`)
- [ ] 17.3 Test packaged executable runs independently (no Python required)
- [ ] 17.4 Verify executable size is reasonable (<30 MB)

## 18. Testing and Polish

- [ ] 18.1 Write integration test: full flow from store creation → add key set → add profile → resolve keys
- [ ] 18.2 Write integration test: discovery with real OMO config fixture
- [ ] 18.3 Write integration test: preset application with fixture config (verify only preset field changes)
- [ ] 18.4 Manual smoke test on Windows: create store, add keys, create profile, launch
- [ ] 18.5 Verify all ruff checks pass: `ruff check .`
- [ ] 18.6 Verify all mypy checks pass: `mypy src/`
- [ ] 18.7 Verify all tests pass: `pytest`
- [ ] 18.8 Verify format check passes: `ruff format --check .`