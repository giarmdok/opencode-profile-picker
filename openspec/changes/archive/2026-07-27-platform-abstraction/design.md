## Context

The project is a clean skeleton — no platform logic or abstraction exists yet. The `src/ocpp/` package has a basic CLI entry point (`__main__.py`), but no configuration reading, venv detection, or OpenCode integration has been implemented. This change is the foundational layer (change #1 of 7) that all subsequent changes will depend on for platform-aware behavior.

## Goals / Non-Goals

**Goals:**
- Confine all `sys.platform` checks to a single, well-tested module (`src/ocpp/platform.py`)
- Provide a `Platform` facade exposing: OS family, venv directory name, venv bin subdirectory, OMO config path candidates, and project root
- Make the facade injectable so unit tests can simulate any platform without patching `sys.platform` globally
- Follow the AGENTS.md convention that platform-specific logic lives behind a clean abstraction — no `if sys.platform` scattered through business logic

**Non-Goals:**
- Venv validation (whether the venv directory actually exists and is valid) — this is change #4
- OMO config file parsing or preset selection — this is change #5
- `.project` file env var loading — this is change #2
- Launching `opencode` as a subprocess — this is change #7
- Shell persistence or `eval`-compatible output modes

## Decisions

### 1. Platform as a frozen dataclass with factory function

A frozen dataclass (`@dataclass(frozen=True)`) with a `Platform` classmethod factory (`Platform.detect()`) provides an immutable, hashable, and easily testable value object. The factory reads `sys.platform` once and populates all fields. Callers that need to override platform for testing can construct a Platform instance directly.

### 2. Platform taxonomy: win32 → Windows, linux → Linux, else → Unix

The OS family is a simple enum-style mapping:
- `sys.platform == 'win32'` → `PlatformFamily.WINDOWS`
- `sys.platform.startswith('linux')` → `PlatformFamily.LINUX`
- Everything else (darwin, freebsd, netbsd, openbsd, etc.) → `PlatformFamily.UNIX`

This three-way split matches the venv naming convention (`.venv_win` / `.venv_lin` / `.venv_unx`) and covers all platforms users are likely to encounter.

### 3. OMO config path search order

The search order is:
1. `~/.config/opencode/oh-my-opencode-slim.json` (all platforms — primary)
2. `~/.config/opencode/oh-my-opencode-slim.jsonc` (all platforms — JSONC variant)
3. `%APPDATA%\opencode\oh-my-opencode-slim.json` (Windows-only fallback)
4. `%APPDATA%\opencode\oh-my-opencode-slim.jsonc` (Windows-only JSONC variant)

This mirrors the AGENTS.md convention: the `.config` path is the primary location, and `%APPDATA%` is the Windows fallback. Both `.json` and `.jsonc` are checked because the OMO file may be in either format.

### 4. Generic `.venv` fallback

The venv directory name is resolved as:
1. Platform-specific: `.venv_win` / `.venv_lin` / `.venv_unx`
2. Fallback: `.venv` (generic fallback for legacy setups)

This matches the AGENTS.md specification that the platform-specific name is tried first, then the generic `.venv`.

### 5. Injectable for testing

The `Platform.detect()` factory accepts optional `platform_string` and `home_dir` overrides. This allows tests to simulate any platform without patching `sys.platform` or `os.environ` globally. Direct construction of `Platform` instances is also supported for maximal test flexibility.

### 6. Project root = current working directory

Project root is simply `Path.cwd()`. This is the simplest correct default — the user runs `ocpp` from their project root. If future needs require explicit project root discovery (e.g., walking up to find a `.project` file), that can be added as a separate capability.

## Risks / Trade-offs

- **macOS classification**: macOS is classified as `Unix` with venv dir `.venv_unx`. This is slightly inaccurate (macOS is not Unix-certified, but it is POSIX-compliant). The alternative was a dedicated `.venv_mac` name, but that would increase the taxonomy to 4 branches and fragment the venv naming convention. The `.venv_unx` approach is simpler and matches the `oh-my-opencode-slim` ecosystem convention. **Mitigation**: documented in the spec that `Unix` covers darwin/BSD/etc.
- **APPDATA may not exist**: On some minimal Windows setups (e.g., Windows Server Core), `%APPDATA%` may not be set. **Mitigation**: the OMO path search falls back to `USERPROFILE\.config\opencode` if `APPDATA` is absent, ensuring the `.config` path is always reachable.
- **No venv validation here**: This change only resolves paths. It does not check whether the venv exists or is valid. Callers must handle missing venv gracefully. This is intentional — validation belongs in change #4.