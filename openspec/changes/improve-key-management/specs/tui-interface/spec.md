## ADDED Requirements

### Requirement: Import from environment button on key set edit screen
The system SHALL provide an "Import from Environment" button on the key set edit screen that triggers the import merge flow. The existing "Scan Env" button SHALL be replaced.

#### Scenario: Import button visible
- **WHEN** the user is on the key set edit screen
- **THEN** an "Import from Environment" button is visible

#### Scenario: Import triggers merge preview
- **WHEN** the user clicks "Import from Environment" and known API keys are found in the environment
- **THEN** the import merge modal opens displaying the merge preview

## MODIFIED Requirements

### Requirement: Key set edit screen
The system SHALL provide a key set edit screen showing all keys in the set with their provider, environment variable name, and masked value. The user SHALL be able to add, edit, or remove keys. Key editing SHALL be accessed by keyboard bindings on the key table. Key values SHALL be masked with a toggle to reveal.

#### Scenario: Edit key set with existing keys
- **WHEN** the user opens key set "personal" for editing
- **THEN** all keys are displayed with masked values and the user can add, edit, or remove entries using keyboard bindings shown in the footer

#### Scenario: Edit key value via keyboard binding
- **WHEN** the user highlights a key row and presses `enter` or `e`
- **THEN** an edit value modal opens with the current value pre-filled and the provider and env var name displayed for context

#### Scenario: Delete key via keyboard binding
- **WHEN** the user highlights a key row and presses `d` or `delete`
- **THEN** a confirmation dialog appears asking "Remove '{env_var}' from this key set?"

#### Scenario: Toggle key visibility
- **WHEN** the user presses the visibility toggle on a masked key value
- **THEN** the key value is displayed in plaintext; pressing again re-masks it

### Requirement: Keyboard-driven interface
The system SHALL support full keyboard navigation. All primary actions SHALL be accessible via single-key shortcuts displayed in the footer. The Escape key SHALL navigate back or cancel. Enter SHALL confirm or launch. DataTable rows SHALL support row-level action bindings (enter to edit selected row, d to delete) where applicable.

#### Scenario: Keyboard shortcut for new profile
- **WHEN** the user presses "N" on the main screen
- **THEN** the new profile screen opens

#### Scenario: Escape to go back
- **WHEN** the user presses Escape on the profile edit screen
- **THEN** the screen closes and returns to the main screen without saving

#### Scenario: Row-level edit binding on key table
- **WHEN** the user presses `enter` on a highlighted key row in the key set edit screen
- **THEN** the edit value modal opens for that key

#### Scenario: Row-level delete binding on key table
- **WHEN** the user presses `d` on a highlighted key row in the key set edit screen
- **THEN** the delete confirmation dialog opens for that key
