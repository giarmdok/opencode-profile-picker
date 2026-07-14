# Profile Management

## Purpose

Create, list, edit, and delete profiles that combine OMO presets with API key sets. Validate profile integrity on load and handle orphaned profiles.

## Requirements

### Requirement: Create a profile
The system SHALL allow the user to create a named profile that combines an OMO preset with a key set. The profile name MUST be unique. The preset MUST exist in the discovered presets. The key set MUST exist in the stored key sets.

#### Scenario: Successful profile creation
- **WHEN** the user provides a unique name "or-work", selects preset "or", and selects key set "work"
- **THEN** the profile is saved and appears in the profile list

#### Scenario: Duplicate profile name
- **WHEN** the user attempts to create a profile with a name that already exists
- **THEN** the system rejects the creation and displays an error message

#### Scenario: Preset does not exist
- **WHEN** the user selects a preset name not found in the discovered presets
- **THEN** the system rejects the creation and displays an error message

#### Scenario: Key set does not exist
- **WHEN** the user selects a key set name not found in the stored key sets
- **THEN** the system rejects the creation and displays an error message

### Requirement: List all profiles
The system SHALL display all stored profiles with their preset name and key set name visible.

#### Scenario: Multiple profiles exist
- **WHEN** the store contains 3 profiles
- **THEN** all 3 profiles are displayed with their preset and key set names

#### Scenario: No profiles exist
- **WHEN** the store contains no profiles
- **THEN** the system displays an empty list with a prompt to create the first profile

### Requirement: Edit a profile
The system SHALL allow the user to change the preset or key set of an existing profile. The profile name SHALL NOT be changeable after creation.

#### Scenario: Change preset
- **WHEN** the user edits profile "or-work" and changes the preset from "or" to "go"
- **THEN** the profile is updated with preset "go" and key set "work" unchanged

#### Scenario: Change key set
- **WHEN** the user edits profile "or-work" and changes the key set from "work" to "personal"
- **THEN** the profile is updated with preset "or" and key set "personal"

### Requirement: Delete a profile
The system SHALL allow the user to delete a profile after explicit confirmation. Deleting a profile SHALL NOT delete the referenced key set.

#### Scenario: Confirmed deletion
- **WHEN** the user selects a profile for deletion and confirms the action
- **THEN** the profile is removed from the store and no longer appears in the list

#### Scenario: Cancelled deletion
- **WHEN** the user selects a profile for deletion but cancels the confirmation
- **THEN** the profile remains unchanged in the store

#### Scenario: Key set preserved after profile deletion
- **WHEN** a profile referencing key set "work" is deleted
- **THEN** key set "work" remains in the store and can be used by other profiles

### Requirement: Validate profile integrity at load
The system SHALL validate that each stored profile references an existing key set when the store is loaded. Profiles referencing deleted key sets SHALL be flagged.

#### Scenario: Orphaned profile detected
- **WHEN** a profile references key set "work" but "work" has been deleted from the store
- **THEN** the profile is displayed with a warning indicator and cannot be launched until its key set is reassigned
