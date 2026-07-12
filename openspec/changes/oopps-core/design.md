## Context

oopps is a greenfield Python TUI application. It runs as a standalone executable, discovers the user's oh-my-opencode-slim configuration, manages encrypted API key sets, and launches OpenCode with the selected profile applied. The application is local-only, offline, and never modifies files beyond the OMO `preset` field and its own encrypted profile store.

**Current state**: No code exists. The project has an AGENTS.md with conventions, a `.gitignore`, and an empty `src/` layout planned.

**Constraints**:
- Must work on Windows, macOS, Linux without OS-specific dependencies for core logic
- Must be packageable as a single portable executable (PyInstaller or Nuitka)
- Must not shell out to `opencode` CLI for discovery — read config files directly
- Must never delete or reformat config the user didn't touch
- Must not write API keys to any OpenCode or OMO config file

## Goals / Non-Goals

**Goals:**
- Discover available OMO presets and their provider requirements from the filesystem
- Store API keys encrypted at rest with a user-chosen master password
- Let users compose named profiles from independent preset and key set dimensions
- Apply a profile by writing the `preset` field to `oh-my-opencode-slim.json` and injecting API keys as environment variables for the launched OpenCode process
- Provide a clean TUI for all operations (Textual framework)
- Package as a single portable executable

**Non-Goals:**
- Modifying `opencode.json` or any config beyond the OMO `preset` field
- Managing project-local `.opencode/` config files (v1: global config only)
- Cloud sync, export/import, or sharing of profiles
- A CLI/flag-based interface (TUI only for v1)
- Managing OpenCode settings beyond presets and API keys
- Installing or configuring oh-my-opencode-slim itself

## Decisions

### 1. Module Architecture

```
src/opencode_profile_picker/
├── __init__.py
├── __main__.py              # Entry point: parse args, bootstrap app
├── app.py                   # Textual App subclass, screen registry
├── config/
│   ├── __init__.py
│   ├── paths.py             # Platform-specific path resolution
│   ├── discover.py          # Scan filesystem for OMO config, extract presets
│   └── parser.py            # JSONC-tolerant config file reader/writer
├── profiles/
│   ├── __init__.py
│   ├── models.py            # Profile, KeySet, KeyEntry dataclasses
│   ├── store.py             # Encrypted read/write of profiles.json.enc
│   └── crypto.py            # Fernet encryption, PBKDF2 key derivation
├── presets/
│   ├── __init__.py
│   ├── analyzer.py          # Map preset → required providers/keys
│   └── applier.py           # Write preset field to OMO config
├── keys/
│   ├── __init__.py
│   ├── resolver.py          # Key resolution: stored → env → prompt
│   └── launcher.py          # Set env vars, spawn opencode process
└── tui/
    ├── __init__.py
    ├── screens/
    │   ├── unlock.py        # Master password entry
    │   ├── main.py          # Profile list + key set summary
    │   ├── profile_edit.py  # Create/edit profile
    │   ├── keyset_list.py   # Browse key sets
    │   └── keyset_edit.py   # Add/edit keys in a set
    └── widgets/
        ├── profile_list.py  # DataTable for profiles
        └── key_input.py     # Masked key input with visibility toggle
```

**Rationale**: Flat-ish module structure grouped by domain (config, profiles, presets, keys, tui). Each domain has clear boundaries. The TUI layer is isolated from business logic — screens call into domain modules, never the reverse.

**Alternative considered**: Single flat package. Rejected because the domains (crypto, config parsing, TUI) are distinct enough to warrant separation for testability and clarity.

### 2. Encryption Scheme

```
                    User enters master password
                              │
                              ▼ PBKDF2-SHA256 (600,000 iterations)
                    32-byte encryption key
                              │
                              ▼
              ┌───────────────────────────────┐
              │  profiles.json.enc on disk    │
              │                               │
              │  {                             │
              │    "salt": "<base64>",         │  ← stored in header
              │    "verify": "<fernet-token>", │  ← encrypt("oopps-ok")
              │    "data": "<fernet-token>"    │  ← encrypt(JSON payload)
              │  }                             │
              └───────────────────────────────┘
```

- **PBKDF2-SHA256** with 600,000 iterations (OWASP 2023 recommendation) to derive key from password
- **Fernet** (AES-128-CBC + HMAC-SHA256) for symmetric encryption of the JSON payload
- **Salt** stored in the file header — unique per file, generated on first run
- **Verification token**: encrypt the known string `"oopps-ok"` with the derived key. On unlock, decrypt and check. Wrong password → detected immediately without corrupting data
- **Key in memory**: derived key held in the `Store` object for the session lifetime. Cleared on app exit
- **Password reset**: delete `profiles.json.enc`, create new file with new password. All stored keys are lost — clearly communicated to user

**Alternative considered**: OS keychain via `keyring` library. Rejected because the user explicitly wants cross-platform file-based encryption with a master password. Keychain also adds platform-specific behavior that complicates the "portable executable" goal.

**Alternative considered**: Plaintext with 0600 permissions. Rejected — user wants encryption at rest.

### 3. Data Model

```python
@dataclass
class KeyEntry:
    """A single API key entry."""
    provider: str          # e.g. "openrouter", "anthropic"
    env_var: str           # e.g. "OPENROUTER_API_KEY"
    value: str | None      # None = not stored, use env fallback

@dataclass  
class KeySet:
    """Named collection of API keys."""
    name: str              # e.g. "personal", "work"
    keys: dict[str, KeyEntry]  # env_var → KeyEntry

@dataclass
class Profile:
    """A named combination of preset + key set."""
    name: str              # e.g. "or-personal"
    preset: str            # OMO preset name, e.g. "or"
    key_set: str           # KeySet name, e.g. "personal"

@dataclass
class ProfileStore:
    """Top-level encrypted store."""
    version: int           # schema version (1)
    key_sets: dict[str, KeySet]
    profiles: dict[str, Profile]
```

**On-disk JSON structure** (before encryption):
```json
{
  "version": 1,
  "key_sets": {
    "personal": {
      "name": "personal",
      "keys": {
        "OPENROUTER_API_KEY": {
          "provider": "openrouter",
          "env_var": "OPENROUTER_API_KEY",
          "value": "sk-or-v1-abc123..."
        }
      }
    }
  },
  "profiles": {
    "or-personal": {
      "name": "or-personal",
      "preset": "or",
      "key_set": "personal"
    }
  }
}
```

**Rationale**: Key sets and profiles are separate top-level collections. A profile references a key set by name. This enables the independent switching the user wants — change the preset without changing keys, or change keys without changing the preset. The `value` field being `null` means "use environment variable" — no key stored, but the entry exists so the user knows it's expected.

### 4. Config Discovery

**Scan locations** (platform-aware, via `paths.py`):

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%\opencode\` and `%USERPROFILE%\.config\opencode\` |
| macOS | `~/.config/opencode/` |
| Linux | `~/.config/opencode/` and `$XDG_CONFIG_HOME/opencode/` |

**Discovery process**:
1. Find `oh-my-opencode-slim.json` or `.jsonc` (prefer `.jsonc`)
2. Parse with `json5` (tolerates comments, trailing commas)
3. Extract `presets` keys → list of available preset names
4. For each preset, walk agent configs to collect all `model` fields
5. Map model prefixes to required environment variables using a built-in provider table:

```python
PROVIDER_KEY_MAP = {
    "openai":        "OPENAI_API_KEY",
    "anthropic":     "ANTHROPIC_API_KEY",
    "google":        "GOOGLE_API_KEY",
    "mistral":       "MISTRAL_API_KEY",
    "xai":           "XAI_API_KEY",
    "openrouter":    "OPENROUTER_API_KEY",
    "github-copilot":"GITHUB_TOKEN",
    "deepseek":      "DEEPSEEK_API_KEY",
    # ... extensible
}
```

6. Also check `council.presets` for councillor models → additional required keys
7. Return: `{preset_name: [required_env_vars]}`

**Rationale**: Parse config files directly rather than shelling out to `opencode`. This is faster, works offline, and doesn't require OpenCode to be installed. The provider→key mapping is a static table that can be extended.

**Alternative considered**: Shell out to `opencode config` or similar. Rejected per AGENTS.md constraint and because it adds a runtime dependency on OpenCode being installed.

### 5. Preset Application

**What gets written**: Only the `preset` field at the top level of `oh-my-opencode-slim.json`.

**How**:
1. Read the file with `json5`
2. Change `data["preset"] = profile.preset`
3. Write back with `json.dumps(data, indent=2)` — preserves JSON (not JSONC) formatting
4. If the original was `.jsonc`, write to the `.jsonc` file (preserve extension)

**What does NOT get written**: Agent configs, skills, MCPs, council settings, or any other field. The preset definition itself is never modified — only which preset is active.

**Edge cases**:
- File doesn't exist → warn user, skip preset application, still apply keys and launch
- File is malformed → warn user, skip preset application
- Project-local `.opencode/oh-my-opencode-slim.json` exists with its own `preset` → detect and show note: "Project overrides preset — oopps manages the global default"

**Rationale**: Minimal mutation. The user's preset definitions are sacred. We only change the selector. This also means oopps can't break anything — worst case, the user manually changes the preset back.

### 6. Key Resolution Chain

```
Launch profile "or-personal"
        │
        ▼
┌──────────────────┐
│ 1. Check store   │──▶ Found? ──▶ Use decrypted value
│    (encrypted)   │
└──────┬───────────┘
       │ Not found / null
       ▼
┌──────────────────┐
│ 2. Check env var │──▶ Found? ──▶ Use env value
│    (os.environ)  │
└──────┬───────────┘
       │ Not found
       ▼
┌──────────────────┐
│ 3. Prompt user   │──▶ Enter key now ──▶ Optionally save to key set
│    (TUI modal)   │     or skip
└──────────────────┘
```

**At launch time**:
1. Resolve all required keys for the profile's preset
2. Build an `env` dict with resolved key values
3. Merge with current environment (inherit existing env vars)
4. Spawn `opencode` as a child process with the merged environment
5. The child process inherits the env vars; the parent (oopps) does not leak them

**Rationale**: The stored → env → prompt chain gives maximum flexibility. Users who prefer env vars never need to store keys. Users who want convenience can store them encrypted. The prompt fallback handles the "I forgot to set this up" case gracefully.

### 7. TUI Architecture (Textual)

**Screen flow**:
```
App Start
    │
    ▼
UnlockScreen ──────────────────────────────┐
    │ (password correct)                    │ (first run: create password)
    ▼                                       │
MainScreen                                  │
    │                                       │
    ├── [N]ew ──▶ ProfileEditScreen         │
    │               │                       │
    │               └── [S]ave ──▶ MainScreen
    │                                       │
    ├── [E]dit ──▶ ProfileEditScreen        │
    │                                       │
    ├── [D]elete ──▶ Confirm modal          │
    │                                       │
    ├── [K]ey Sets ──▶ KeySetListScreen     │
    │                   │                   │
    │                   ├── [N]ew ──▶ KeySetEditScreen
    │                   ├── [E]dit ──▶ KeySetEditScreen
    │                   └── [B]ack ──▶ MainScreen
    │                                       │
    └── [L]aunch ──▶ Apply + spawn opencode │
                     (oopps exits)          │
```

**MainScreen layout** (conceptual):
```
┌──────────────────────────────────────────────────────────────┐
│  oopps                                    [🔒 unlocked]      │
│                                                              │
│  Profiles                        Key Sets                    │
│  ┌────────────────────────┐     ┌────────────────────────┐  │
│  │ ▶ or-personal          │     │ personal   3 keys      │  │
│  │   or-work              │     │ work       2 keys      │  │
│  │   go-personal          │     └────────────────────────┘  │
│  └────────────────────────┘                                  │
│                                                              │
│  Active preset: or (OpenRouter)                              │
│                                                              │
│  [N]ew  [E]dit  [D]elete  [K]ey Sets  [L]aunch  [Q]uit     │
└──────────────────────────────────────────────────────────────┘
```

**Key decisions**:
- Use Textual's `Screen` stack for navigation (push/pop)
- `DataTable` for profile and key set lists
- `Input` with `password=True` for key entry, with a toggle to show/hide
- `Footer` for keybindings
- Dark theme by default (consistent with terminal tools)
- No CSS files — use Textual's Python CSS-in-Python (`DEFAULT_CSS` class variable)

**Rationale**: Textual over Rich. Rich is for styled terminal output; Textual is for interactive TUI applications with focus management, keybindings, and screen navigation. The screen stack pattern maps naturally to the navigation flow.

**Alternative considered**: Rich with simple `input()` prompts. Rejected — the user explicitly wants a TUI with browsing, selection, and editing capabilities that require Textual's widget system.

### 8. Platform Abstraction

```python
# paths.py
def get_opencode_config_dir() -> Path:
    """Return the OpenCode user config directory."""
    ...

def get_oopps_data_dir() -> Path:
    """Return the oopps data directory (~/.config/oopps/)."""
    ...

def get_shell_profile_path() -> Path | None:
    """Return the user's shell profile file path."""
    ...
```

Platform detection happens exactly once per function. The rest of the codebase calls these functions and works with `Path` objects. No `if sys.platform` scattered through business logic.

**Process launching** (`launcher.py`):
- Use `subprocess.Popen` with `env` parameter
- On Windows: `CREATE_NEW_CONSOLE` flag so OpenCode gets its own terminal window
- On Unix: inherit terminal, OpenCode takes over the TTY

**Rationale**: Per AGENTS.md convention. Clean abstraction layer prevents platform-specific bugs from leaking into business logic.

### 9. Packaging

**Choice: PyInstaller** (with Nuitka as fallback).

PyInstaller is more mature for Python TUI applications, has better Textual compatibility, and produces smaller binaries for this use case. Nuitka compilation can be slow and has known issues with some Textual dependencies.

**Build target**: Single-file executable (`--onefile`). The executable bundles Python runtime, all dependencies, and the application code. No Python installation required on the target machine.

**Size estimate**: ~15-25 MB (Python runtime + Textual + cryptography + json5).

### 10. Dependencies

| Package | Version | Purpose | Why this one |
|---------|---------|---------|-------------|
| `textual` | ≥2.0 | TUI framework | Best-in-class Python TUI, active maintenance |
| `cryptography` | ≥43.0 | Fernet encryption, PBKDF2 | Standard library for crypto, no native deps issues |
| `json5` | ≥0.9 | JSONC parsing | Handles comments, trailing commas in OMO config |
| `pyinstaller` | ≥6.0 | Packaging (dev dep) | Mature, reliable single-file builds |

**Not included**:
- `keyring` — user chose file-based encryption over OS keychain
- `rich` — Textual bundles Rich internally
- `click`/`typer` — no CLI interface in v1
- `pydantic` — dataclasses are sufficient for this data model

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Master password forgotten** → all stored keys lost | Clear warning at setup. Keys can be re-entered. Env var fallback still works. |
| **Encrypted file corruption** → profiles lost | Single file, easy to back up. Document backup location in README. |
| **JSONC formatting loss** → writing `preset` field may strip comments from OMO config | Acceptable for v1. The `preset` field is a simple string value. Users who heavily comment their OMO config can use `.json` format. Future: use a JSONC-preserving writer. |
| **Provider→key mapping incomplete** → unknown providers not detected | Extensible static table. Users can contribute mappings. Unknown providers show as "unknown" in TUI with the model string displayed. |
| **Textual + PyInstaller compatibility** → packaging issues | Known path. Textual has PyInstaller hooks. Test packaging early in development. |
| **OpenCode not installed** → launch fails | Detect `opencode` on PATH before offering launch. Show clear error if not found. |
| **Multiple OpenCode config locations** → which one to write? | v1: only global `~/.config/opencode/`. Detect project-local config and show informational note. |

## Open Questions

1. **Should oopps exit after launching OpenCode, or stay running?** Exit is simpler (no process management). Stay running could allow re-picking without re-entering the master password. Leaning toward exit for v1.

2. **Should the master password have a confirmation field on creation?** Yes — standard practice, prevents typos that would lock the user out.

3. **Should we support `OH_MY_OPENCODE_SLIM_PRESET` env var override instead of writing the config file?** The OMO system supports this. It's less persistent (resets on shell restart) but zero-touch. Could be a configurable option per profile. Defer to v2.

4. **What happens if the OMO config has no presets defined?** Show available presets as empty. User can still manage key sets and launch OpenCode with env vars. The preset selector in profile edit would show "(none)".