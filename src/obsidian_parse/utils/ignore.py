"""Vault ignore rules — mirrors Obsidian's file exclusion behaviour.

Two rules are applied:
1. Dotfiles / dotfolders: any path component starting with '.' is ignored.
2. userIgnoreFilters: regex patterns from .obsidian/app.json are matched
   against the vault-relative path (forward-slash normalised).
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def load_ignore_filters(vault_root: Path) -> list[re.Pattern[str]]:
    """Read *userIgnoreFilters* from ``.obsidian/app.json`` and compile them.

    Returns an empty list when the file is missing or unparseable.
    Invalid regex entries are silently skipped.
    """
    app_json = vault_root / ".obsidian" / "app.json"
    if not app_json.exists():
        return []

    try:
        data = json.loads(app_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    raw = data.get("userIgnoreFilters", [])
    if not isinstance(raw, list):
        return []

    compiled: list[re.Pattern[str]] = []
    for entry in raw:
        if isinstance(entry, str) and entry:
            try:
                compiled.append(re.compile(entry))
            except re.error:
                continue
    return compiled


def _has_dot_component(file_path: Path, vault_root: Path) -> bool:
    """Return True if any component of the vault-relative path starts with '.'."""
    try:
        rel = file_path.relative_to(vault_root)
    except ValueError:
        return False
    return any(part.startswith(".") for part in rel.parts)


def should_ignore(
    file_path: Path,
    vault_root: Path,
    filters: list[re.Pattern[str]],
) -> bool:
    """Decide whether *file_path* should be excluded from vault scanning.

    Args:
        file_path: Absolute path to the candidate file.
        vault_root: Absolute path to the vault root directory.
        filters: Compiled regex patterns from :func:`load_ignore_filters`.
    """
    # Rule 1: dotfiles / dotfolders
    if _has_dot_component(file_path, vault_root):
        return True

    # Rule 2: userIgnoreFilters
    if filters:
        try:
            rel = file_path.relative_to(vault_root).as_posix()
        except ValueError:
            return False
        for pattern in filters:
            if pattern.search(rel):
                return True

    return False
