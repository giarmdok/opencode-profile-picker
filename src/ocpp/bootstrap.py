"""Auto-create a .project file with project name and harvested API keys."""

from __future__ import annotations

import logging
import os
import re
from collections import OrderedDict
from pathlib import Path

from ocpp.platform import Platform
from ocpp.project import OCPP_PROJECT_NAME, LineRecord, mask_value, serialize_project

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
    """Return sanitized last component of *project_root*.

    Strip whitespace, replace sequences of non-alphanumeric characters
    (excluding ``-``, ``_``, ``.``) with a single ``-``.
    """
    name = project_root.name.strip()
    # Replace sequences of any character that is not alphanumeric, -, _, or .
    # with a single -
    name = re.sub(r"[^a-zA-Z0-9\-_.]+", "-", name)
    # Strip leading/trailing hyphens
    name = name.strip("-")
    return name


def harvest_api_keys() -> dict[str, str]:
    """Iterate *API_KEY_ALLOWLIST*, collect non-empty values from ``os.environ``.

    Skip ``None``, empty string, and whitespace-only values.
    """
    result: dict[str, str] = {}
    for key in API_KEY_ALLOWLIST:
        value = os.environ.get(key)
        if value is not None and value.strip():
            result[key] = value
    return result


def check_gitignore(project_root: Path) -> bool:
    """Return ``True`` if ``.project`` is already gitignored.

    Check the project-level ``.gitignore`` for a line matching ``'.project'``.
    If no ``.git`` directory exists, return ``True`` (not a git repo,
    no warning needed).
    """
    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        return True

    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.is_file():
        return False

    text = gitignore_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        # Ignore empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == ".project":
            return True
    return False


def offer_gitignore_append(project_root: Path) -> None:
    """If ``.project`` is not gitignored and ``.git`` exists, prompt the user.

    Warn and offer to append ``'.project'`` to ``.gitignore``.
    If declined, continue without modifying.
    """
    if check_gitignore(project_root):
        return

    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        return

    print("Warning: .project contains API keys but is not in .gitignore.")
    answer = input("Append '.project' to .gitignore? [y/N] ").strip().lower()
    if answer == "y" or answer == "yes":
        gitignore_path = project_root / ".gitignore"
        with gitignore_path.open("a", encoding="utf-8") as fh:
            fh.write("\n.project\n")
        logger.info("Appended '.project' to .gitignore")


def run_bootstrap(platform: Platform, confirm: bool = True) -> bool:
    """Full bootstrap workflow.

    1. Check if ``.project`` exists in ``platform.project_root`` —
       if yes, return ``True`` (skip).
    2. Derive project name from ``platform.project_root.name``.
    3. Harvest API keys from ``os.environ``.
    4. If *confirm*: show summary with masked values, prompt ``[y/N]``.
    5. Check gitignore, offer to append if needed.
    6. Write ``.project`` file using :func:`serialize_project`.
    7. Set file permissions to ``0o600`` (handle Windows gracefully).
    8. Return ``True`` if created, ``False`` if user declined.
    """
    project_root = platform.project_root
    project_file = project_root / ".project"

    # Step 1: skip if .project already exists
    if project_file.is_file():
        return True

    # Step 2: derive project name
    project_name = derive_project_name(project_root)

    # Step 3: harvest API keys
    api_keys = harvest_api_keys()

    # Step 4: confirmation prompt
    if confirm:
        print(f"\nCreating .project file at: {project_root / '.project'}\n")
        print(f"  {mask_value(OCPP_PROJECT_NAME, project_name)}")
        for key in API_KEY_ALLOWLIST:
            if key in api_keys:
                print(f"  {mask_value(key, api_keys[key])}")
        print()
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            return False

    # Step 5: check gitignore
    offer_gitignore_append(project_root)

    # Step 6: build kv and write file
    kv: OrderedDict[str, str] = OrderedDict()
    kv[OCPP_PROJECT_NAME] = project_name
    for key in API_KEY_ALLOWLIST:
        if key in api_keys:
            kv[key] = api_keys[key]

    # Add comment header
    lines: list[LineRecord] = [
        LineRecord(line_type="comment", raw="# ocpp project file"),
    ]

    serialize_project(project_file, kv, lines)

    # Step 7: set file permissions
    try:
        project_file.chmod(0o600)
    except Exception:
        logger.debug("Could not set file permissions on %s", project_file)

    return True
