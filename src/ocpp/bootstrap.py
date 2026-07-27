"""Auto-create a .project file with project name and harvested API keys."""

from __future__ import annotations

import logging
import os
import re
from collections import OrderedDict
from pathlib import Path

from ocpp.platform import Platform
from ocpp.project import (
    OCPP_PROJECT_NAME,
    LineRecord,
    mask_dict,
    serialize_project,
)

__all__ = [
    "API_KEY_ALLOWLIST",
    "check_gitignore",
    "derive_project_name",
    "harvest_api_keys",
    "offer_gitignore_append",
    "run_bootstrap",
]

logger = logging.getLogger(__name__)

API_KEY_ALLOWLIST = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "XAI_API_KEY",
    "MISTRAL_API_KEY",
]


def derive_project_name(project_root: Path) -> str:
    """Return sanitized last component of *project_root*."""
    name = project_root.name.strip()
    name = re.sub(r"[^a-zA-Z0-9\-_.]+", "-", name)
    name = name.strip("-")
    return name


def harvest_api_keys() -> dict[str, str]:
    """Return a dict of API keys found in the environment."""
    found_keys: dict[str, str] = {}
    for key in API_KEY_ALLOWLIST:
        value = os.environ.get(key)
        if value:
            found_keys[key] = value
    return found_keys


def check_gitignore(project_root: Path) -> bool:
    """Return ``True`` if ``.project`` is already gitignored."""
    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        return True

    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.is_file():
        return False

    text = gitignore_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == ".project":
            return True
    return False


def offer_gitignore_append(project_root: Path) -> None:
    """If ``.project`` is not gitignored and ``.git`` exists, prompt the user."""
    if check_gitignore(project_root):
        return

    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        return

    print("Warning: .project contains API keys but is not in .gitignore.")
    answer = input("Append '.project' to .gitignore? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        gitignore_path = project_root / ".gitignore"
        with gitignore_path.open("a", encoding="utf-8") as fh:
            fh.write("\n.project\n")
        logger.info("Appended '.project' to .gitignore")


def run_bootstrap(platform: Platform, confirm: bool = True) -> bool:
    """Full bootstrap workflow."""
    project_root = platform.project_root
    project_file = project_root / ".project"

    if project_file.is_file():
        return True

    project_name = derive_project_name(project_root)
    api_keys = harvest_api_keys()

    project_kv: OrderedDict[str, str] = OrderedDict()
    project_kv[OCPP_PROJECT_NAME] = project_name
    for key, value in api_keys.items():
        project_kv[key] = value

    if confirm:
        print(f"\nCreating .project file at: {project_root / '.project'}\n")
        masked_kv = mask_dict(project_kv)
        for key, value in masked_kv.items():
            print(f"  {key}={value}")
        print()
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            return False

    offer_gitignore_append(project_root)

    lines: list[LineRecord] = [
        LineRecord(line_type="comment", raw="# ocpp project file"),
    ]

    serialize_project(project_file, project_kv, lines)

    try:
        project_file.chmod(0o600)
    except Exception:
        logger.debug("Could not set file permissions on %s", project_file)

    return True
