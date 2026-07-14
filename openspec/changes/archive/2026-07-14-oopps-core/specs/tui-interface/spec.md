## ADDED Requirements

### Requirement: Unlock screen
The system SHALL present an unlock screen on startup when an encrypted profile store exists. The screen SHALL contain a password input field and an unlock button. The password input SHALL be masked by default.

#### Scenario: Unlock screen on startup
- **WHEN** the application starts and `profiles.json.enc` exists
- **THEN** the unlock screen is displayed with a masked password field and an "Unlock" button

#### Scenario: First run shows create password screen
- **WHEN** the application starts and no `profiles.json.enc` exists
- **THEN** a create-password screen is displayed with two password fields (new + confirm) and a "Create" button

### Requirement: Main screen layout
The system SHALL present a main screen with two panels: a profile list on the left and a key set summary on the right. The currently active OMO preset SHALL be displayed in a status area. A footer SHALL show available keyboard shortcuts.

#### Scenario: Main screen with profiles and key sets
- **WHEN** the user has unlocked the store and discovery is complete
- **THEN** the main screen displays the profile list, key set summary, active preset indicator, and footer with keybindings

#### Scenario: Main screen with no profiles
- **WHEN** the store contains no profiles
- **THEN** the profile list shows an empty state message and the footer highlights "New" as the primary action

### Requirement: Profile list navigation
The system SHALL allow the user to navigate the profile list using keyboard arrow keys. The currently highlighted profile SHALL be visually distinct.

#### Scenario: Arrow key navigation
- **WHEN** the user presses the down arrow key
- **THEN** the highlight moves to the next profile in the list

#### Scenario: Wrap-around navigation
- **WHEN** the user presses down on the last profile
- **THEN** the highlight wraps to the first profile (or stops at the end, depending on list widget behavior)

### Requirement: Profile edit screen
The system SHALL provide a profile edit screen with fields for profile name (new profiles only), preset selection from discovered presets, and key set selection from stored key sets. The screen SHALL show which API keys the selected preset requires and whether the selected key set provides them.

#### Scenario: Create new profile
- **WHEN** the user opens the new profile screen, enters name "go-experiment", selects preset "go", and selects key set "personal"
- **THEN** the screen shows that preset "go" requires `GOOGLE_API_KEY` and key set "personal" provides it with a checkmark

#### Scenario: Missing required key warning
- **WHEN** the user selects preset "gm" (requires Google + Mistral keys) and key set "personal" (only has Google key)
- **THEN** the screen shows a warning that `MISTRAL_API_KEY` is not provided by the selected key set

### Requirement: Key set list screen
The system SHALL provide a key set list screen showing all key sets with their key counts. The user SHALL be able to create, edit, or delete key sets from this screen.

#### Scenario: Browse key sets
- **WHEN** the user navigates to the key set list screen
- **THEN** all key sets are displayed with their key counts and available actions

### Requirement: Key set edit screen
The system SHALL provide a key set edit screen showing all keys in the set with their provider, environment variable name, and masked value. The user SHALL be able to add, edit, or remove keys. Key values SHALL be masked with a toggle to reveal.

#### Scenario: Edit key set with existing keys
- **WHEN** the user opens key set "personal" for editing
- **THEN** all keys are displayed with masked values and the user can add, edit, or remove entries

#### Scenario: Toggle key visibility
- **WHEN** the user presses the visibility toggle on a masked key value
- **THEN** the key value is displayed in plaintext; pressing again re-masks it

### Requirement: Keyboard-driven interface
The system SHALL support full keyboard navigation. All primary actions SHALL be accessible via single-key shortcuts displayed in the footer. The Escape key SHALL navigate back or cancel. Enter SHALL confirm or launch.

#### Scenario: Keyboard shortcut for new profile
- **WHEN** the user presses "N" on the main screen
- **THEN** the new profile screen opens

#### Scenario: Escape to go back
- **WHEN** the user presses Escape on the profile edit screen
- **THEN** the screen closes and returns to the main screen without saving

### Requirement: Error and warning display
The system SHALL display errors and warnings as non-blocking notifications within the TUI. Critical errors that prevent launch SHALL be displayed prominently.

#### Scenario: Launch blocked by missing keys
- **WHEN** the user attempts to launch a profile whose required keys cannot be resolved
- **THEN** a modal or prominent notification lists the missing keys and blocks the launch

### Requirement: Dark theme
The system SHALL use a dark color theme by default, consistent with terminal tool conventions.

#### Scenario: Application appearance
- **WHEN** the application is running
- **THEN** the background is dark and text is light with appropriate contrast for readability