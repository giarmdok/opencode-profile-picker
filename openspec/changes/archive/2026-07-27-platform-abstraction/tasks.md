## 1. Create platform module with Platform dataclass

- [ ] 1.1 Create `src/ocpp/platform.py` with a `PlatformFamily` enum (`WINDOWS`, `LINUX`, `UNIX`) and a frozen `Platform` dataclass containing fields: `family`, `venv_dir_name`, `venv_bin_subdir`, `omo_config_paths: list[Path]`, `project_root: Path`
- [ ] 1.2 Add a `Platform.detect()` classmethod factory that reads `sys.platform` and populates all fields, accepting optional `platform_string` and `home_dir` overrides
- [ ] 1.3 Ensure `__all__` exports `Platform`, `PlatformFamily` in the module

## 2. Implement platform detection logic

- [ ] 2.1 Map `sys.platform` to `PlatformFamily`: `'win32'` → `WINDOWS`, starts with `'linux'` → `LINUX`, else → `UNIX`
- [ ] 2.2 Map `PlatformFamily` to venv directory name: `WINDOWS` → `.venv_win`, `LINUX` → `.venv_lin`, `UNIX` → `.venv_unx`
- [ ] 2.3 Map `PlatformFamily` to venv bin subdirectory: `WINDOWS` → `Scripts`, `LINUX`/`UNIX` → `bin`

## 3. Implement OMO config path search

- [ ] 3.1 Build the primary candidate path: `~/.config/opencode/oh-my-opencode-slim.json` (using the configured or real home directory)
- [ ] 3.2 Build the `.jsonc` variant: `~/.config/opencode/oh-my-opencode-slim.jsonc`
- [ ] 3.3 On Windows, build the `%APPDATA%` fallback paths: `%APPDATA%\opencode\oh-my-opencode-slim.json` and `.jsonc` variant; if `%APPDATA%` is not set, fall back to `~\.config\opencode\`
- [ ] 3.4 Return all candidate paths in priority order as a `list[Path]`

## 4. Implement project root resolution

- [ ] 4.1 Set `project_root` to `Path.cwd()` in the `Platform.detect()` factory

## 5. Write unit tests

- [ ] 5.1 Test platform classification: win32 → Windows, linux → Linux, darwin → Unix, freebsd → Unix, unknown → Unix
- [ ] 5.2 Test venv directory name resolution: `.venv_win` / `.venv_lin` / `.venv_unx` per family, plus `.venv` generic fallback
- [ ] 5.3 Test venv bin subdirectory: `Scripts` for Windows, `bin` for Linux/Unix
- [ ] 5.4 Test OMO config path search order: `.config` paths first, `.json` before `.jsonc`, `%APPDATA%` paths included only on Windows
- [ ] 5.5 Test OMO config path with `%APPDATA%` absent: falls back to `~\.config\opencode\`
- [ ] 5.6 Test `.venv` generic fallback is always available regardless of platform
- [ ] 5.7 Test injectable platform: override `platform_string` and `home_dir`, verify all fields reflect the overrides
- [ ] 5.8 Test direct construction of `Platform` instance bypasses detection

## 6. Verify linting and type checking

- [ ] 6.1 Run `ruff check .` and fix any violations
- [ ] 6.2 Run `mypy src/` and fix any type errors
- [ ] 6.3 Run `pytest tests/` and confirm all platform tests pass