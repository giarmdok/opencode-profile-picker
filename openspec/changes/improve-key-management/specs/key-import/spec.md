## ADDED Requirements

### Requirement: Compute merge preview from environment
The system SHALL provide a pure function `compute_merge()` that compares a key set against the current environment and returns a structured preview of what would change when importing.

The function SHALL:
- Accept a `KeySet` and an optional environment dict (defaulting to `os.environ`)
- Check which known API key environment variables (from `PROVIDER_KEY_MAP`) are set in the environment
- Diff the set of active env vars against the key set's existing keys
- Return a `MergePreview` containing four categorized lists

#### Scenario: New keys found in environment
- **WHEN** the environment has `OPENROUTER_API_KEY` set and the key set does not contain it
- **THEN** `MergePreview.new` contains a `KeyEntry` for `OPENROUTER_API_KEY` with `provider="openrouter"` and `value=None`

#### Scenario: Overlapping keys (already present)
- **WHEN** the environment has `OPENAI_API_KEY` set and the key set already contains an entry for `OPENAI_API_KEY`
- **THEN** `MergePreview.overlap` contains the existing `KeyEntry` for `OPENAI_API_KEY`

#### Scenario: Orphaned keys with stored value
- **WHEN** the key set contains `ANTHROPIC_API_KEY` with a non-None value but the environment does not have `ANTHROPIC_API_KEY` set
- **THEN** `MergePreview.orphan_stored` contains that `KeyEntry`

#### Scenario: Orphaned keys with env fallback
- **WHEN** the key set contains `MISTRAL_API_KEY` with value=None but the environment does not have `MISTRAL_API_KEY` set
- **THEN** `MergePreview.orphan_env_fallback` contains that `KeyEntry`

#### Scenario: No changes to import
- **WHEN** the environment has no known API keys set and the key set is empty
- **THEN** `MergePreview.new`, `overlap`, `orphan_stored`, and `orphan_env_fallback` are all empty lists

### Requirement: Apply import merge results
The system SHALL apply the results of an import merge by adding new keys and removing orphan keys selected for deletion.

The apply operation SHALL:
- Add all keys in `MergePreview.new` to the key set with their provider and None value (env fallback)
- NOT modify keys in `MergePreview.overlap` (they are already present)
- Delete only the orphan keys explicitly confirmed for deletion by the user
- Persist the changes to the encrypted store

#### Scenario: Apply with new keys and selected orphans deleted
- **WHEN** the merge preview has 2 new keys and the user selects 1 orphan for deletion
- **THEN** the key set contains the 2 new keys, the 1 orphan is removed, and remaining orphans are unchanged

#### Scenario: Partial orphan deletion
- **WHEN** the merge preview has 3 orphans and the user selects 2 for deletion
- **THEN** those 2 orphans are removed from the key set and the third remains

### Requirement: Import merge modal
The system SHALL present an import merge preview modal when the user triggers "Import from Environment" and changes are detected.

The modal SHALL display:
- A section listing new keys to be added (provider and env var name)
- A section listing overlapping keys that already exist (informational only)
- A section for each orphan category with per-key keep/delete toggles
- Default toggles: "keep" for stored-value orphans, "delete" for env-fallback orphans
- An "Import" button to apply changes and a "Cancel" button to discard

#### Scenario: Import modal with all categories
- **WHEN** the merge preview has new keys, overlapping keys, and both types of orphans
- **THEN** the modal displays all four sections with appropriate labels and default toggles

#### Scenario: Import modal with only new keys
- **WHEN** the merge preview has new keys but no overlapping or orphan keys
- **THEN** the modal displays only the new keys section and the button label is "Import All"

#### Scenario: Import modal with no new keys
- **WHEN** the merge preview has only overlapping and orphan keys (nothing new to add)
- **THEN** the modal still opens, showing only the relevant sections

#### Scenario: Cancel import
- **WHEN** the user opens the import modal and presses Cancel
- **THEN** no changes are made to the key set and the modal closes

### Requirement: No keys to import notification
The system SHALL display a non-blocking notification when the "Import from Environment" action finds no known API keys in the environment.

#### Scenario: No keys in environment
- **WHEN** the user triggers import but no known provider environment variables are set
- **THEN** the edit screen displays a notification "No known API keys found in environment" and no modal opens
