"""JSONC-tolerant config file reader/writer for OMO config files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import json5


def read_jsonc(path: Path) -> dict[str, Any] | None:
    """Parse a JSONC (JSON with comments) file.

    Returns the parsed dict, or None if the file doesn't exist or is malformed.
    """
    try:
        text = path.read_text(encoding="utf-8")
        return json5.loads(text)
    except FileNotFoundError:
        return None
    except (ValueError, Exception):
        return None


def write_json(path: Path, data: dict[str, Any]) -> bool:
    """Write a dict as JSON to a file.

    Returns True on success, False on failure.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(text + "\n", encoding="utf-8")
        return True
    except OSError:
        return False
