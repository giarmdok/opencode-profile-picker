## ADDED Requirements

### Requirement: Create master password on first run
The system SHALL prompt the user to create a master password when no encrypted profile store exists. The password MUST be entered twice for confirmation. The password SHALL be used to derive an encryption key via PBKDF2-SHA256 with a randomly generated salt.

#### Scenario: First run with matching passwords
- **WHEN** no `profiles.json.enc` exists and the user enters the same password twice
- **THEN** the system generates a salt, derives an encryption key, creates an empty store, encrypts it, and writes `profiles.json.enc`

#### Scenario: First run with mismatched passwords
- **WHEN** the user enters different passwords in the two confirmation fields
- **THEN** the system displays an error and prompts the user to re-enter both passwords

#### Scenario: Password too short
- **WHEN** the user enters a password shorter than 8 characters
- **THEN** the system displays a warning and recommends a longer password but does not block creation

### Requirement: Unlock with master password
The system SHALL prompt for the master password on startup when an encrypted store exists. The password SHALL be verified by decrypting a known verification token stored in the file header.

#### Scenario: Correct password
- **WHEN** the user enters the correct master password
- **THEN** the system decrypts the store, loads profiles and key sets into memory, and proceeds to the main screen

#### Scenario: Incorrect password
- **WHEN** the user enters an incorrect master password
- **THEN** the system displays "Incorrect password" and allows retry

#### Scenario: Corrupted store file
- **WHEN** the encrypted store file is corrupted and cannot be decrypted even with the correct password
- **THEN** the system displays an error and offers to reset (delete the corrupted file and start fresh)

### Requirement: Reset master password
The system SHALL allow the user to reset the master password by deleting the encrypted store file. All stored keys SHALL be lost. The user MUST explicitly confirm this action with a warning about data loss.

#### Scenario: Confirmed reset
- **WHEN** the user confirms the reset after seeing the data loss warning
- **THEN** the system deletes `profiles.json.enc` and prompts to create a new master password

#### Scenario: Cancelled reset
- **WHEN** the user cancels the reset action
- **THEN** the store file remains unchanged and the system returns to the password prompt

### Requirement: Create a key set
The system SHALL allow the user to create a named key set. The name MUST be unique among existing key sets.

#### Scenario: Successful key set creation
- **WHEN** the user provides a unique name "personal"
- **THEN** an empty key set named "personal" is created and saved to the encrypted store

#### Scenario: Duplicate key set name
- **WHEN** the user attempts to create a key set with a name that already exists
- **THEN** the system rejects the creation and displays an error

### Requirement: Add a key to a key set
The system SHALL allow the user to add an API key to a key set by specifying the provider, environment variable name, and key value. The key value SHALL be masked during input with an option to toggle visibility.

#### Scenario: Add key with value
- **WHEN** the user adds key `OPENROUTER_API_KEY` with value `sk-or-v1-abc123` to key set "personal"
- **THEN** the key is stored encrypted in the key set and displayed as masked in the UI

#### Scenario: Add key without value (env-only)
- **WHEN** the user adds key `OPENROUTER_API_KEY` but leaves the value empty
- **THEN** the key entry is saved with a null value, indicating it will be resolved from the environment at launch time

#### Scenario: Duplicate key in same set
- **WHEN** the user attempts to add `OPENROUTER_API_KEY` to a key set that already contains it
- **THEN** the system rejects the addition and displays an error

### Requirement: Remove a key from a key set
The system SHALL allow the user to remove a key entry from a key set after confirmation.

#### Scenario: Confirmed removal
- **WHEN** the user confirms removal of `OPENROUTER_API_KEY` from key set "personal"
- **THEN** the key entry is removed from the key set and saved

### Requirement: Edit a key value
The system SHALL allow the user to change the stored value of an existing key entry in a key set.

#### Scenario: Update key value
- **WHEN** the user changes the value of `OPENROUTER_API_KEY` in key set "personal" from `sk-old` to `sk-new`
- **THEN** the new value is encrypted and stored, replacing the old value

#### Scenario: Clear key value to env-only
- **WHEN** the user clears the value of a stored key, leaving it empty
- **THEN** the key entry remains in the set with a null value, falling back to environment variable resolution

### Requirement: Delete a key set
The system SHALL allow the user to delete a key set after explicit confirmation. Any profiles referencing the deleted key set SHALL become orphaned.

#### Scenario: Confirmed deletion with warning
- **WHEN** the user confirms deletion of key set "work" which is referenced by 2 profiles
- **THEN** the system warns about the 2 affected profiles, and upon confirmation, deletes the key set and marks the profiles as orphaned

### Requirement: List all key sets
The system SHALL display all stored key sets with a count of keys in each set.

#### Scenario: Key sets with varying key counts
- **WHEN** the store contains key set "personal" with 3 keys and "work" with 1 key
- **THEN** the system displays both with their respective key counts

### Requirement: Encrypt all stored key values
The system SHALL encrypt every key value before writing to disk using Fernet symmetric encryption with the key derived from the master password. Key metadata (provider, env_var name) SHALL be stored in plaintext within the encrypted container.

#### Scenario: Store written to disk
- **WHEN** the profile store is saved
- **THEN** all key values in the JSON payload are encrypted via Fernet before the entire payload is written to `profiles.json.enc`

#### Scenario: Store read from disk
- **WHEN** the profile store is loaded with the correct master password
- **THEN** all key values are decrypted and available in memory for the session

### Requirement: Clear encryption key from memory on exit
The system SHALL clear the derived encryption key and all decrypted key values from memory when the application exits.

#### Scenario: Normal exit
- **WHEN** the user quits the application
- **THEN** the encryption key and all decrypted key values are removed from memory before the process terminates