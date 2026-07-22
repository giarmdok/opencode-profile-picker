## Context

No `.project` parser or serializer exists yet in the codebase. The project is currently a skeleton with a CLI entry point and a platform abstraction module (change #1). The `.project` file format must be simple, human-editable, diff-friendly, and safe for storing API credentials. It must support round-trip preservation of comments and formatting so that users who edit the file manually do not lose their annotations. The format must not introduce new external dependencies — stdlib only.

## Goals / Non-Goals

**Goals:**

- Define a precise `.project` dotenv-style grammar: `KEY=value`, one per line, `#` line comments, split on first `=`, no interpolation, no command substitution, UTF-8
- Implement a line-based parser that returns an ordered `dict[str, str]` while tracking comment lines and blank lines separately
- Implement a serializer that writes back the file preserving all comments, blank lines, and unknown lines
- Mask all secret values in diagnostic output as `KEY=***` — never print or log actual secret values
- Support `OCPP_PROJECT_NAME` as a reserved key with no special parsing behavior beyond recognition
- Validate variable names against `[A-Za-z_][A-Za-z0-9_]*` and reject embedded newlines in values
- Implement "empty value override" semantics: `KEY=` produces an empty string and overrides inherited values with emptiness

**Non-Goals:**

- Bootstrap creation of `.project` files (interactive prompts, default values) — this is change #3
- Environment variable application to the subprocess environment — this is change #6
- Encryption or secret management (e.g., keyring integration, encrypted storage) — out of scope for v1
- `.env` file compatibility or full dotenv semantics (e.g., `export` prefix, multiline values with `\n`, variable interpolation `${VAR}`) — explicitly excluded
- Shell persistence or `eval`-compatible output modes
- Cross-file variable resolution or inheritance chains

## Decisions

### 1. Dotenv-style format: `KEY=value`, `#` comments, split on first `=`, no interpolation

A minimal dotenv subset is chosen because it is the most familiar format for environment variable configuration. Every developer knows `KEY=value`. The grammar is deliberately constrained:

- Lines matching `^\s*#` are comments (preserved verbatim)
- Lines matching `^\s*$` are blank (preserved verbatim)
- Lines matching `^[A-Za-z_][A-Za-z0-9_]*=.*` are key-value pairs — split on the first `=`
- Everything else is an "unknown line" (preserved verbatim)
- No `export` prefix, no quoting rules, no escape sequences, no interpolation

### 2. Custom ~30-line parser, not `python-dotenv`

A custom parser is implemented instead of the popular `python-dotenv` library for three reasons:

1. **Exact control over override semantics**: The parser must distinguish between "key not present" and "key present with empty value" — `python-dotenv` does not expose this distinction cleanly
2. **Comment preservation**: The serializer must preserve comments through a rewrite cycle, which requires the parser to track comment lines as separate data
3. **Zero new dependencies**: The stdlib (`pathlib`, `re`) is sufficient for this simple grammar

### 3. `OCPP_PROJECT_NAME` as a reserved key

The `OCPP_PROJECT_NAME` key is reserved for identifying the project by name. It is parsed and serialized like any other key, but the tool recognizes it as a reserved key. No special behavior (e.g., auto-generation, default values) is implemented in this change — that belongs in change #3.

### 4. Values masked as `KEY=***` in all output

All diagnostic output (logging, CLI output, error messages) must mask secret values. The masking utility replaces the value portion with `***` while preserving the key. This is a separate utility function that can be applied to any key-value pair before display. The `OCPP_PROJECT_NAME` key is not masked (it is not a secret), but all other keys are.

### 5. Preserve unknown lines and comments on rewrite

The serializer reconstructs the file line-by-line using the comment/blank/unknown-line data tracked by the parser. Key-value pairs are re-emitted in their original order, with updated values. This ensures that manual edits (comments, formatting, ordering) survive a programmatic rewrite.

### 6. UTF-8 encoding

The file is always read and written as UTF-8. This is the default for Python's `Path.read_text()` / `Path.write_text()`. No BOM, no other encoding support.

## Risks / Trade-offs

- **Users may expect full dotenv semantics**: Developers familiar with `python-dotenv` or `direnv` may expect `export` prefix, multiline values, variable interpolation, or `.env` compatibility. **Mitigation**: The constrained grammar is documented explicitly in the spec and in the module docstring. A clear error message is raised for lines that look like `export KEY=value`.
- **Comment preservation is inherently fragile**: Line-based preservation works correctly for the common case (comments before a key, blank lines between sections), but reordering keys or deleting keys will leave orphaned comments. **Mitigation**: The serializer re-emits comments in their original position. If a key is removed from the dict, the comments associated with it become orphaned — this is an acceptable trade-off; the user can clean up orphaned comments manually.
- **No quoting/escaping means values with leading/trailing whitespace or `#` are ambiguous**: A value like `KEY= value with # hash` would be parsed as `value with ` (trailing space) and the `# hash` would be treated as a comment. **Mitigation**: Document this limitation clearly. Users who need special characters should use alternative approaches (e.g., base64 encoding, or a dedicated config file).
- **Custom parser vs. library maintenance**: A custom parser means we own the bugs. **Mitigation**: The grammar is simple enough (~30 lines) that the correctness surface is tiny. Comprehensive unit tests cover edge cases (empty values, comments, unknown lines, invalid keys).