## Context

Change #5 of 7, depends on change #1 (platform-abstraction). The platform-abstraction module provides `Platform.omo_config_paths` — an ordered list of candidate paths for the OMO config file. The `json5` library is already available for parsing JSONC content. The OMO config file (`oh-my-opencode-slim.json` or `.jsonc`) is a user-maintained file with a top-level `"preset"` string field and a `"presets"` object containing named preset blocks. Each preset block has agent configurations (orchestrator, oracle, librarian, etc.) with model, variant, skills, and MCPs. Users may add comments and custom formatting that must be preserved on write.

## Goals / Non-Goals

**Goals:**
- Discover the global OMO config file (`.json` and `.jsonc` variants) using platform-abstraction path search
- Parse the config with `json5` to validate structure and extract preset data
- List available preset names from the `"presets"` object, marking the currently active preset
- Perform a surgical text edit of the top-level `"preset"` field value, preserving all comments and formatting
- Write via temp file + atomic rename to prevent corruption
- Create a `.bak` backup file before writing
- Prompt the user for confirmation before writing
- Handle missing config file gracefully: report a clear error message, do not crash

**Non-Goals:**
- Editing the contents of individual presets (agent models, skills, MCPs, etc.)
- Creating new presets or deleting existing presets
- Project-local OMO config overrides (`.opencode/` or `opencode.jsonc` in the project root)
- Launching `opencode` or reloading presets into a running process
- Providing a full TUI or interactive preset browser

## Decisions

### 1. Parse with json5 for validation, regex for surgical write

Reading: parse the file with `json5.loads()` to validate it is well-formed JSONC and to extract the `"preset"` value and `"presets"` keys. This gives us structured access to the data.

Writing: after parsing to validate the new value, perform a targeted regex replacement on the raw file text to change only the top-level `"preset"` value. This preserves all comments, whitespace, and formatting that a full re-serialize would destroy.

**Rationale**: `json5` handles trailing commas, comments, and single-quoted keys that are common in JSONC files. A full re-serialize via `json5.dumps()` would lose formatting. Regex on the raw text is the only way to make a surgical edit.

### 2. Top-level preset regex pattern

The regex targets the top-level `"preset"` field by matching the pattern at the start of a line or after the opening `{`:

```
(^|[\s{])"preset"\s*:\s*"[^"]*"\s*(,?)
```

This captures:
- Line start or whitespace/open-brace before the key (ensures it's not inside a nested preset block)
- The key `"preset"` with optional whitespace around the colon
- The existing quoted string value
- An optional trailing comma (preserved in the replacement)

**Mitigation for nested matches**: The `(^|[\s{])` prefix ensures we only match a `"preset"` key that appears at the top level (after `{` or at the start of a line), not inside a nested preset block like `"openrouter": { "preset": ... }`.

### 3. Fallback to full re-serialize

If the regex pattern is not found (unlikely but possible with unusual formatting), fall back to a full re-serialize using `json5.dumps()` with `indent=2`. This is a destructive fallback (loses comments) and therefore requires:
- Creating a `.bak` backup (already done)
- Explicit user confirmation with a warning that formatting may be lost
- Logging a warning

### 4. Write via temp file + atomic rename

Write the updated content to a temp file in the same directory as the target file, then use `os.replace()` (atomic rename on POSIX and Windows) to replace the original. This prevents partial writes from corrupting the config file if the process is interrupted.

### 5. Create .bak backup

Before writing, copy the original file to `<filename>.bak` in the same directory. If a `.bak` already exists, overwrite it (the latest backup is the most useful). The backup is created before any write attempt, including the regex replacement.

### 6. Confirm before writing

Before applying any write (surgical or fallback), prompt the user: "Update active preset from '<old>' to '<new>'? [y/N]". Only proceed on affirmative input. The confirmation includes the backup filename so the user knows they can restore.

### 7. Missing config file handling

If no OMO config file is found at any of the platform-abstraction candidate paths, raise a clear error message: "OMO config file not found. Expected at: <paths>". The caller (CLI module) can decide whether to abort or offer to skip. The `omo` module never crashes — it always returns a structured result or raises a typed exception.

## Risks / Trade-offs

- **Regex may match nested "preset" fields**: Inside a preset block, there may be an inner `"preset"` key (e.g., `"orchestrator": { "preset": "claude-sonnet" }`). **Mitigation**: The regex pattern anchors to the start of a line or the opening `{` brace, ensuring only the top-level field is matched.
- **json5 may fail to parse malformed JSONC**: The file may have syntax errors. **Mitigation**: Catch `json5.JSON5DecodeError` (or `ValueError`), report the parse error with the file path and line number, and abort the operation.
- **.jsonc variant may be non-standard**: Some users may have custom formatting that json5 cannot parse. **Mitigation**: json5 is designed to handle JSONC (comments, trailing commas, single quotes). If parsing fails, the error message points to the exact location.
- **Atomic rename may fail across filesystems**: `os.replace()` works on the same filesystem but may fail if the temp file is on a different volume. **Mitigation**: Create the temp file in the same directory as the target file using `tempfile.NamedTemporaryFile(dir=target_dir, delete=False)`.
- **Lost formatting on fallback path**: The full re-serialize fallback loses comments. **Mitigation**: The regex approach is the primary path and should succeed for all well-formed files. The fallback warns the user and requires explicit confirmation.