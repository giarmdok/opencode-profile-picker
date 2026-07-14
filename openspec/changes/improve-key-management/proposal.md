## Why

The key set edit screen is half-built: users can add keys via a form and scan the environment with a naive import, but the table of existing keys is read-only. There is no way to edit a key's value, delete a key, or perform a controlled import that surfaces conflicts. This makes key set management frustrating — the only way to fix a mistake or handle merge conflicts is to delete and recreate the key set entirely.

## What Changes

- **Row-level key editing**: Add keyboard bindings (`enter`/`e` to edit, `d`/`delete` to remove) to the key table in the key set edit screen. Editing opens a modal pre-filled with the current values; deleting requires confirmation.
- **Import from environment with merge preview**: Replace the naive "Scan Env" button with a proper import flow. A new backend function `compute_merge()` produces a structured preview of what will be added, overwritten, or orphaned. A modal screen presents this preview with per-orphan keep/delete toggles before the user commits.
- **Provider selector improvement**: Add a visual separator before the "Custom env var..." option in the provider dropdown and auto-focus the env var input with a contextual placeholder when custom is selected.
- **`ConfirmDeleteScreen` parameterization**: Accept a custom message string so it can be reused for key deletion confirmation (currently hardcoded).

## Capabilities

### New Capabilities

- `key-import`: Import API keys from the current environment into a key set with a merge preview that distinguishes new keys, overwrites, and orphans (including the distinction between stored-value orphans and env-fallback orphans).

### Modified Capabilities

- `tui-interface`: The key set edit screen gains row-level edit/delete bindings (`enter`/`e`, `d`/`delete`) and a new import merge modal. The "Key set edit screen" requirement already states users SHALL be able to "add, edit, or remove keys" — this change implements the edit and remove interactions that are currently missing. The new import modal is an additional screen.

## Impact

- **`profiles/operations.py`**: New `compute_merge()` pure function and `MergePreview` dataclass.
- **`tui/screens/keyset_edit.py`**: New bindings, row-level action handlers, reuse of add-key form for edit modal.
- **`tui/screens/`**: New `MergeImportModal` screen (or equivalent modal).
- **`tui/screens/confirm_delete.py`**: Minor parameterization to accept a message string.
- **`tests/test_operations.py`**: New tests for `compute_merge()`.
- **`tests/test_keys.py`**: Existing coverage for resolver/launcher — no changes needed unless import integration touches them.
