## Context

The `.project` parser and serializer from change #2 (project-file-format) already exist and provide the `ProjectFile` class with `read()`, `write()`, `mask_values()`, and validation. The platform detection from change #1 (platform-abstraction) already exists and provides `Platform` with `project_root`, `family`, and platform-aware path utilities. What remains is the bootstrap workflow — the glue that detects a missing `.project`, gathers data, prompts the user, and writes the file.

## Goals / Non-Goals

**Goals:**
- Auto-create a `.project` file in the project root when none exists
- Derive the project name (`OCPP_PROJECT_NAME`) from the current working directory name, sanitized for use as a dotenv value
- Harvest non-empty API key values from the current environment for a fixed allowlist of variables
- Display a confirmation prompt with masked values before writing anything to disk
- Detect whether the project is a git repository; if `.project` is not in `.gitignore`, warn the user and offer to append it
- Set restrictive file permissions (0o600 or equivalent) on the written `.project` file where the platform supports it
- Exit gracefully without writing if the user declines confirmation

**Non-Goals:**
- Interactive key editing or manual key entry (future change)
- Encryption of the `.project` file at rest (out of scope for v1)
- Importing API keys from other sources such as keychains, password managers, or cloud secret stores
- Detecting stale or expired API keys
- Migrating from an existing `.project` file format

## Decisions

### 1. Project name derived from cwd directory name, sanitized

The project name is `Path.cwd().name` — the last component of the current working directory path. This is the simplest correct default: the user is presumed to be in their project root, and the directory name is a reasonable project identifier. The value is sanitized by stripping leading/trailing whitespace and replacing sequences of non-alphanumeric characters (excluding `-`, `_`, `.`) with a single `-`. This ensures the value is safe for use in a dotenv file and as a project identifier.

### 2. Fixed API key allowlist

The allowlist of environment variables to harvest is fixed at:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `GEMINI_API_KEY`
- `XAI_API_KEY`
- `MISTRAL_API_KEY`

This matches the set of LLM providers that OpenCode supports. Only non-empty values are harvested. Empty or unset variables are silently skipped. The allowlist is defined as a module-level constant (`API_KEY_ALLOWLIST`) for easy reference and future extension.

### 3. Only non-empty values harvested from current environment

`os.environ.get(key)` is called for each key in the allowlist. If the return value is `None` or an empty string after stripping whitespace, the variable is excluded from the `.project` file. This prevents writing empty or whitespace-only values.

### 4. User confirmation required before writing

Before writing the `.project` file, the bootstrap shows a summary to the user:
- Project name (unmasked — it is not a secret)
- Each API key variable name with its value masked (e.g., `ANTHROPIC_API_KEY=sk-***...abcd`)
- The file path that will be written

The user is prompted with `[y/N]` (default: no). If the user declines, no file is written and the tool exits with a message.

### 5. Gitignore check

If the project root contains a `.git` directory (indicating a git repository), the bootstrap checks whether `.project` appears in `.gitignore` (either in the project root `.gitignore` or in the global gitignore). If `.project` is not ignored, the tool prints a warning explaining that the `.project` file contains API keys and should be gitignored. The user is offered the choice to append `.project` to `.gitignore` with confirmation. If the user declines, the tool continues without modifying `.gitignore`.

### 6. File permissions set to 0o600 where supported

After writing the `.project` file, the bootstrap sets file permissions to `0o600` (owner read/write only) using `Path.chmod(0o600)`. On Windows, `chmod` has limited effect — the file is given the Windows-equivalent of owner-only access. On POSIX systems, this prevents group and other users from reading the file. The write itself is atomic (write to a temp file, then rename) to avoid partial writes.

## Risks / Trade-offs

- **API keys in plaintext on disk**: The `.project` file stores API keys in plaintext, which is a security concern if the file is accidentally committed or the machine is compromised. **Mitigation**: the tool (a) warns the user if the file is not gitignored, (b) offers to add it to `.gitignore`, (c) sets restrictive file permissions (0o600), and (d) masks values in all output. Users are also advised to use per-project API keys with restricted scopes where possible.
- **Cwd name may not be a good project name**: The directory name might be generic (e.g., `my-project`, `backend`, `app`) or contain characters unsuitable for a project identifier. **Mitigation**: the name is sanitized, and the user can edit the `.project` file afterward or run `ocpp` with a future `--name` flag. The `OCPP_PROJECT_NAME` value is only used for display and environment identification, not as a path or identifier in external systems.
- **False positive git detection**: A `.git` directory might exist even if the user does not want git integration for `.project` (e.g., a submodule or a template repo). **Mitigation**: the gitignore modification is opt-in with explicit confirmation; the warning is advisory only.
- **File permissions on Windows**: `chmod(0o600)` on Windows does not enforce the same semantics as POSIX. The file may still be readable by other users on the same machine. **Mitigation**: documented behavior; the gitignore warning is the primary defense on Windows.