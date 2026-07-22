## Why

The `ocpp` tool must read the global `oh-my-opencode-slim` configuration to discover available OMO presets, let the user choose one, and update the active preset. The OMO config file is JSON/JSONC with user-maintained comments and formatting that must be preserved when writing. Without this capability, `ocpp` cannot determine which presets (openrouter, mistral, google, openai, xai, anthropic) are available or switch between them.

## What Changes

A new `src/ocpp/omo.py` module is created that provides OMO config operations:

- **Discovery**: Find the `oh-my-opencode-slim.json` (or `.jsonc`) file using the platform-abstraction path search
- **Parsing and validation**: Parse with `json5` to validate structure; confirm top-level `"preset"` and `"presets"` fields exist
- **Preset listing**: Expose the current `"preset"` value and list all available `"presets"` names with per-preset summary
- **Surgical preset write**: Targeted text edit (regex) on the raw file to replace the top-level `"preset"` value, preserving all comments and formatting; write via temp file + atomic rename; create `.bak` backup before writing; confirm before writing
- **Error handling**: Handle missing config file gracefully (report error, don't crash)

## Capabilities

### New Capabilities
- `omo-config`: Discover, parse, validate, and list presets from the global OMO config file; surgically write the `"preset"` field while preserving formatting

### Modified Capabilities
<!-- No existing capabilities are modified by this change -->

## Impact

- **New module**: `src/ocpp/omo.py`
- **No existing code is modified** — this is pure addition
- **Depends on**: change #1 (platform-abstraction) for OMO config path search
- **New dependencies**: `json5` (already available in the project)
- **No CLI changes yet** — preset selection wiring to the CLI is change #7