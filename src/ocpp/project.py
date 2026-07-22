""".project file parser/serializer with value masking.

The .project file is dotenv-style ``KEY=value`` with ``#`` comments.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "LineRecord",
    "OCPP_PROJECT_NAME",
    "mask_dict",
    "mask_value",
    "parse_project",
    "serialize_project",
]

OCPP_PROJECT_NAME = "OCPP_PROJECT_NAME"

_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)")
_VARNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class LineRecord:
    """A single line from a .project file, preserving its type and raw text."""

    line_type: str  # "comment", "blank", "unknown", "kv"
    raw: str  # the raw line text (without newline)
    key: str | None = None  # only set for "kv" lines


def parse_project(filepath: Path) -> tuple[OrderedDict[str, str], list[LineRecord]]:
    """Read a .project file and return (key→value dict, line records).

    The dict preserves insertion order (last-wins for duplicates).
    The line records preserve every line for round-trip serialization.

    A missing file is not an error — returns (empty dict, empty list).
    """
    if not filepath.is_file():
        return OrderedDict(), []

    raw = filepath.read_text(encoding="utf-8")
    _check_embedded_newlines(raw)

    kv: OrderedDict[str, str] = OrderedDict()
    lines: list[LineRecord] = []

    for line in raw.splitlines():
        if not line:
            lines.append(LineRecord(line_type="blank", raw=line))
        elif line.startswith("#"):
            lines.append(LineRecord(line_type="comment", raw=line))
        else:
            m = _KV_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                kv[key] = value
                lines.append(LineRecord(line_type="kv", raw=line, key=key))
            else:
                _validate_line(line)
                lines.append(LineRecord(line_type="unknown", raw=line))

    return kv, lines


def _check_embedded_newlines(raw: str) -> None:
    """Raise ValueError if any kv pair's value spans multiple lines.

    A multi-line value is detected when a kv line is followed by a line
    that is not a comment, blank, or a line containing ``=``.
    """
    for m in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", raw, re.MULTILINE):
        next_start = m.end() + 1  # skip the trailing \n
        if next_start < len(raw):
            rest = raw[next_start:]
            next_line = rest.split("\n", 1)[0]
            if next_line and not next_line.startswith("#") and "=" not in next_line:
                raise ValueError(f"Value for key {m.group(1)!r} contains embedded newline")


def _validate_line(line: str) -> None:
    """Raise ValueError if *line* looks like an attempted kv with an invalid key.

    Lines whose key part contains whitespace (e.g. ``export FOO=bar``) are
    treated as unknown lines and not validated.
    """
    if "=" not in line:
        return
    key_part = line.split("=", 1)[0]
    if not key_part:
        return
    # If the key part contains whitespace, this is not an attempted kv pair
    if " " in key_part or "\t" in key_part:
        return
    if key_part[0].isdigit():
        raise ValueError(f"Invalid variable name: {key_part!r}")
    if (key_part[0].isalpha() or key_part[0] == "_") and not _VARNAME_RE.match(key_part):
        raise ValueError(f"Invalid variable name: {key_part!r}")


def serialize_project(
    filepath: Path,
    kv: OrderedDict[str, str],
    lines: list[LineRecord],
) -> None:
    """Reconstruct a .project file from line records and updated key-value pairs.

    Comments, blanks, and unknown lines are emitted verbatim in their original
    order. Key-value lines are re-emitted with the value from *kv* (which may
    have been updated). New keys not present in the original line records are
    appended at the end.
    """
    seen_keys: set[str] = set()
    out_lines: list[str] = []

    for rec in lines:
        if rec.line_type == "kv" and rec.key is not None:
            seen_keys.add(rec.key)
            value = kv.get(rec.key, "")
            out_lines.append(f"{rec.key}={value}")
        else:
            out_lines.append(rec.raw)

    # Append new keys not in original line records
    for key, value in kv.items():
        if key not in seen_keys:
            out_lines.append(f"{key}={value}")

    text = "\n".join(out_lines) + "\n"
    filepath.write_text(text, encoding="utf-8")


def mask_value(key: str, value: str) -> str:
    """Return a masked representation ``KEY=***`` for most keys.

    The reserved key ``OCPP_PROJECT_NAME`` is not masked.
    """
    if key == OCPP_PROJECT_NAME:
        return f"{key}={value}"
    return f"{key}=***"


def mask_dict(d: dict[str, str]) -> dict[str, str]:
    """Return a new dict with all values masked (except OCPP_PROJECT_NAME)."""
    return {k: (v if k == OCPP_PROJECT_NAME else "***") for k, v in d.items()}
