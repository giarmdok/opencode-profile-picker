## Why

OpenCode users with oh-my-opencode-slim frequently switch between model configurations (presets) and API keys when moving between projects, clients, or experimentation contexts. Today this means manually editing JSON config files and juggling environment variables — error-prone, slow, and insecure when keys end up in shell history or plaintext files.

oopps (OpenCode Oh-My-OpenCode-Slim Profile Picker Software) makes this a single TUI action: pick a profile, unlock with a master password, launch.

## What Changes

- **New standalone TUI application** (`oopps`) built with Python + Textual, packaged as a single portable executable via PyInstaller or Nuitka
- **Config discovery**: scans `~/.config/opencode/` to find available OMO presets and their provider requirements
- **Encrypted key storage**: API keys encrypted at rest via Fernet (AES-128) with a PBKDF2-derived key from a user-chosen master password; `.env` and environment variable fallback for keys not stored
- **Profile system**: named combinations of an OMO preset + a key set, enabling independent switching of models and billing accounts (e.g., "go + personal keys" vs "go + work keys")
- **Preset application**: writes only the `preset` field in `oh-my-opencode-slim.json`; never touches `opencode.json` or any other config file
- **Environment injection**: sets API keys as environment variables scoped to the launched OpenCode child process; never writes keys to config files
- **Cross-platform**: Windows, macOS, Linux — platform-specific paths abstracted behind a clean interface

## Capabilities

### New Capabilities

- `config-discovery`: Scan the filesystem for OpenCode and oh-my-opencode-slim configuration, extract available preset names, and map each preset to its required API providers
- `profile-management`: Create, read, update, and delete named profiles that combine an OMO preset with a key set; profiles stored in an encrypted local file
- `key-management`: Securely store, retrieve, and manage named sets of API keys encrypted with a user-chosen master password; resolve keys via stored → environment variable → prompt fallback chain
- `preset-application`: Write the selected preset name to the global `oh-my-opencode-slim.json` file without modifying any other configuration
- `tui-interface`: Textual-based terminal UI with screens for profile browsing/selection, profile creation/editing, key set management, and master password unlock
- `launcher`: Spawn OpenCode as a child process with profile-specific environment variables injected, handling platform-specific process launching

### Modified Capabilities

_None — this is a new application with no existing capabilities to modify._

## Impact

- **New codebase**: `src/opencode_profile_picker/` with modules for discovery, profiles, keys, presets, TUI, and launching
- **Dependencies**: Textual (TUI), cryptography (Fernet encryption), json5 (JSONC parsing), PyInstaller or Nuitka (packaging)
- **File system**: reads `~/.config/opencode/oh-my-opencode-slim.json`, writes `preset` field to same file; creates `~/.config/oopps/profiles.json.enc` for encrypted profile storage
- **No external services**: fully offline, no network calls, no telemetry
- **No breaking changes**: does not modify any existing OpenCode or OMO behavior