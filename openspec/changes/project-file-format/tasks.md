## 1. Create project module

- [ ] 1.1 Create `src/ocpp/project.py` with module docstring describing the `.project` file format and the public API

## 2. Implement parser (line-based, comment tracking)

- [ ] 2.1 Implement `parse_project(filepath: Path) -> tuple[OrderedDict[str, str], list[LineRecord]]` — line-based parser that reads the `.project` file, returns an ordered dict of key→value pairs and a list of line records (comments, blanks, unknowns, key-value) for serializer use
- [ ] 2.2 Implement variable name validation using `re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key)` — reject invalid names with a `ValueError`
- [ ] 2.3 Implement embedded newline detection — reject values containing `\n` with a `ValueError`
- [ ] 2.4 Handle missing file gracefully — return empty dict and empty line records

## 3. Implement serializer (preserve comments)

- [ ] 3.1 Implement `serialize_project(filepath: Path, kv: OrderedDict[str, str], lines: list[LineRecord]) -> None` — reconstructs the file line-by-line, re-emitting comments/blanks/unknowns in order and key-value lines with updated values
- [ ] 3.2 New keys not present in the original line records are appended at the end of the file

## 4. Implement value masking utility

- [ ] 4.1 Implement `mask_value(key: str, value: str) -> str` — returns `KEY=***` for all keys except `OCPP_PROJECT_NAME`, which is returned as `KEY=VALUE`
- [ ] 4.2 Implement `mask_dict(d: dict[str, str]) -> dict[str, str]` — returns a new dict with all values masked (except `OCPP_PROJECT_NAME`)

## 5. Write unit tests

- [ ] 5.1 Test parsing basic key-value pairs (single, multiple, order preservation)
- [ ] 5.2 Test parsing with comments, blank lines, and unknown lines (tracking and preservation)
- [ ] 5.3 Test parsing with empty values and duplicate keys (last-wins semantics)
- [ ] 5.4 Test serialization preserves comments, blanks, and unknown lines on round-trip
- [ ] 5.5 Test serialization with updated values and new keys appended
- [ ] 5.6 Test value masking (`OCPP_PROJECT_NAME` not masked, all other keys masked)
- [ ] 5.7 Test validation rejects invalid keys (starts with digit, hyphens, special chars)
- [ ] 5.8 Test validation rejects embedded newlines in values
- [ ] 5.9 Test missing file returns empty dict
- [ ] 5.10 Test UTF-8 encoding with Unicode characters

## 6. Verify linting and type-checking

- [ ] 6.1 Run `ruff check src/ocpp/project.py` — no errors
- [ ] 6.2 Run `ruff format --check src/ocpp/project.py` — no formatting issues
- [ ] 6.3 Run `mypy src/ocpp/project.py` — no type errors
- [ ] 6.4 Run `pytest tests/` — all tests pass