## 1. Backend — Merge Preview

- [ ] 1.1 Add `MergePreview` dataclass to `profiles/operations.py`
- [ ] 1.2 Implement `compute_merge(key_set, env=None)` pure function in `profiles/operations.py`
- [ ] 1.3 Add tests for `compute_merge()` in `tests/test_operations.py` covering: new keys only, overlapping keys, stored-value orphans, env-fallback orphans, empty result, custom env dict

## 2. TUI — Shared Infrastructure

- [ ] 2.1 Parameterize `ConfirmDeleteScreen.__init__` to accept an optional `message: str` that overrides the default text
- [ ] 2.2 Add provider separator and rename "Custom..." to "Custom env var..." in `KeySetEditScreen.compose()` provider options list
- [ ] 2.3 Update `_on_provider_changed` to auto-focus env var input and change placeholder when custom is selected

## 3. TUI — Edit Key Value Modal

- [ ] 3.1 Create `EditKeyValueModal` screen: shows provider/env_var as read-only, value `Input` pre-filled with current value, [Save] [Cancel] buttons, `password=True` on value input
- [ ] 3.2 Wire `enter`/`e` binding on the key table in `KeySetEditScreen` → push `EditKeyValueModal` for the selected row → on save, call `update_key_value()`, save store, refresh table

## 4. TUI — Delete Key from Table

- [ ] 4.1 Add `d`/`delete` binding on the key table in `KeySetEditScreen` → push parameterized `ConfirmDeleteScreen` with message: "Remove '{env_var}' from this key set?" → on confirm, call `remove_key()`, save store, refresh table

## 5. TUI — Import Merge Modal

- [ ] 5.1 Create `MergeImportModal` screen: accepts `MergePreview`, renders sections for new / overlap / orphan_stored / orphan_env_fallback with toggle widgets per orphan (default: keep for stored, delete for env-fallback), [Import] [Cancel] buttons
- [ ] 5.2 Implement apply logic on [Import]: add all new keys, delete toggled orphans, save store, refresh table
- [ ] 5.3 Conditionally hide empty sections; change button label to "Import All" when no orphan sections are present

## 6. TUI — Replace Scan Env Button

- [ ] 6.1 Replace "Scan Env" button with "Import from Environment" button in `KeySetEditScreen`
- [ ] 6.2 Wire button: call `compute_merge()` → if `MergePreview` is empty, show notification "No known API keys found in environment"; otherwise push `MergeImportModal`

## 7. Review Gates

- [ ] 7.1 @oracle review: verify separation of concerns, correctness of `compute_merge`, design decisions match design.md, no architectural regressions
- [ ] 7.2 @designer review: verify modal UX (spacing, layout, toggle defaults, button labels), table bindings footer visibility, provider dropdown clarity
- [ ] 7.3 @fixer review: verify all code changes are well-scoped, no missed edge cases, file consistency

## 8. Verification

- [ ] 8.1 Run existing test suite: `pytest tests/` — all existing tests must continue to pass
- [ ] 8.2 Run lint and type check: `ruff check . && ruff format --check . && mypy src/`
