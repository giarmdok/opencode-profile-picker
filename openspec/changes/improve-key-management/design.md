## Context

The key set edit screen (`keyset_edit.py`) currently supports adding keys via a form and a naive "Scan Env" import that silently skips existing keys. The key table is read-only — no edit or delete interactions. The existing backend operations (`profiles/operations.py`) has `add_key`, `remove_key`, and `update_key_value` already implemented and tested, but only `add_key` is connected to the TUI.

## Goals / Non-Goals

**Goals:**
- Make each key row in the table interactable: edit its value or delete it
- Replace "Scan Env" with a proper import flow that shows what will happen before committing
- Distinguish orphan keys with stored values (keep candidates) from env-fallback orphans (delete candidates)
- Improve provider selector discoverability (the "Custom..." path)

**Non-Goals:**
- Changing the data model (`KeyEntry`, `KeySet`, `ProfileStore` are unchanged)
- Changing the encryption layer
- Backend API changes to provider/environment variable mapping
- Adding filtering, sorting, or bulk operations on keys
- Reordering keys within a key set

## Decisions

### Decision 1: Keyboard bindings for row-level editing

**Choice:** `enter`/`e` to edit value, `d`/`delete` to delete, with screen-level `BINDINGS`.

**Rationale:** Every other screen in the app uses screen-level bindings (`MainScreen`, `KeySetListScreen`). The DataTable already has `cursor_type = "row"` set. Adding bindings is the natural extension.

**Rejected:** Inline cell editing — DataTable's cell-oriented editing is awkward for value changes (must navigate to the right column), doesn't support dropdowns for provider, and has no built-in delete action. Would need separate bindings anyway.

**Edit interaction:** Pressing `enter` or `e` on a selected key row pushes a small modal with the value field pre-populated (the add-key form's value input pattern, but as a focused modal). The provider and env_var fields are **read-only display** in the edit modal — editing the key identity (env_var) would be a remove+add, which is a separate workflow. Value-only editing matches the existing `update_key_value()` operation and the spec requirement "Edit a key value."

**Delete interaction:** Pressing `d` or `delete` pushes `ConfirmDeleteScreen` with the message: *"Remove '{env_var}' from this key set?"*

### Decision 2: Import merge UX — backend function + summary modal

**Choice:** New `compute_merge()` pure function in `operations.py` + a `MergeImportModal` screen. The modal displays a preview with three categories, toggles for orphans, and a single [Import] commit button.

**Rationale:** The backend function is trivially testable in `test_operations.py` with zero Textual dependency. The modal is a new, focused screen class (analogous to `ConfirmDeleteScreen`) — clean separation of concerns, no state creep in `KeySetEditScreen`.

**Rejected:**
- *Multi-step wizard:* Overkill. Most imports will have zero or few orphans. Stepping through screens for each orphan is tedious; stepping through screens when there are zero is wasteful.
- *Inline preview in existing screen:* DataTable can't embed interactive toggles per cell. Would require a dual-mode screen (normal mode vs. import preview mode) that fragments keyboard navigation.

**Conditions that collapse the modal:**
- No env keys found at all → show an error notification in the edit screen, no modal
- New keys only (no orphans, no overlap) → still show the modal for transparency, but hide empty sections, button says "Import All"

### Decision 3: MergePreview data shape

```python
@dataclass
class MergePreview:
    new: list[KeyEntry]              # env vars set, not in key set
    overlap: list[KeyEntry]          # env vars set, already in key set (info only)
    orphan_stored: list[KeyEntry]    # in key set, not in env, value is not None
    orphan_env_fallback: list[KeyEntry]  # in key set, not in env, value is None
```

**Rationale for `overlap` (not "overwrite"):** The import does not capture env values into the store (that would require reading raw key values from environment, which is a security concern and not part of the current `scan_env_for_keys()` design). "Overlap" means "already present — nothing to do" and is purely informational in the modal. The user sees these keys listed but they require no action.

**Rationale for the orphan split:** Stored-value orphans (user explicitly saved a key) are keep candidates — the user intentionally stored this. Env-fallback orphans (value is None) depend entirely on the environment being set, so they're useless when the env var is missing — strong delete candidates. The modal should default toggles accordingly: keep on for stored orphans, delete on for env-fallback orphans.

**`compute_merge` interface:**
```python
def compute_merge(
    key_set: KeySet,
    env: dict[str, str] | None = None,
) -> MergePreview
```
Takes the keyset and optionally an env dict (defaults to `os.environ`). Determines which known env vars are set by checking against `PROVIDER_KEY_MAP`, then diffs against the keyset.

### Decision 4: Provider selector improvements

**Choice:** Add a disabled visual separator entry before "Custom env var..." in the dropdown. When custom is selected, auto-focus the env var input and change its placeholder.

**Rationale:** Minimal code change, no new widgets. The provider field stays as display metadata — stripping it from the data model was considered and rejected (user preference for display richness).

**Implementation:** Add a `("──────────", None)` separator entry (disabled) to the Select options list before `("Custom env var...", "__custom__")`. In `_on_provider_changed`, when `value == "__custom__"`: focus `#env-var-input`, set placeholder to `"Enter any environment variable name..."`.

### Decision 5: ConfirmDeleteScreen parameterization

**Choice:** Accept an optional `message` argument in `__init__` that overrides the default hardcoded text.

**Rationale:** The screen is already used for profile deletion with a generic message. Key deletion needs a specific message: *"Remove '{env_var}' from this key set?"*. A single constructor parameter keeps the change minimal — no need for a new screen class.

### Decision 6: Reusing the add-key form for editing

**Choice:** Extract the value input pattern (masked, with visibility toggle) into a focused edit-value modal, rather than reusing the entire add-key form.

**Rationale:** The add-key form has three fields (provider dropdown, env var input, value input). Editing a key only needs the value field — provider and env_var identify the key and shouldn't change. Reusing the full form would confuse (three fields where only one matters) and risk accidental key identity changes.

**Implementation:** A small `EditKeyValueModal` screen with:
- Read-only display of the key's provider and env_var for context
- A single `Input` widget with `password=True` for the new value
- The current value pre-filled (or empty string if None)
- Buttons: [Save] / [Cancel]

## Risks / Trade-offs

- **[Risk]** The env var check in `compute_merge` uses `PROVIDER_KEY_MAP` to determine which env vars are "known." Custom env vars added by the user are not in this map and won't appear in import results. → **Mitigation:** This is acceptable — import is for known providers by definition. Custom keys are manually added.
- **[Risk]** `MergeImportModal` toggles for orphans use Textual `Switch` or toggle `Button` widgets. If there are many orphans, the modal could overflow the terminal height. → **Mitigation:** Make the orphan list scrollable within the modal. If there are >10 orphans, the modal should use a scrollable container.
- **[Trade-off]** Editing only the value (not provider/env_var) in the edit modal means changing a key's identity requires delete-then-add. → **Acceptable:** This is infrequent and keeps the modal simple. The delete+add path is clear.
- **[Trade-off]** The import modal shows "overlap" keys as informational but non-actionable. This adds visual weight for no functional purpose. → **Acceptable:** The transparency is worth the screen space — users should know nothing was missed. If zero overlap, the section is hidden.
