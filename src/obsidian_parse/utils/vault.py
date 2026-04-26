"""Vault-level file discovery."""

from __future__ import annotations

from pathlib import Path

from obsidian_parse.utils.ignore import load_ignore_filters, should_ignore

_SUPPORTED_EXTENSIONS = frozenset({".md", ".canvas", ".base"})


def find_file_by_id(
    vault_root: Path,
    file_id: str,
    *,
    known_files: list[Path] | None = None,
) -> Path | None:
    """Resolve a file_id to a path relative to vault_root.

    file_id follows the obsidian-parse convention:
      - bare stem or "stem.md"  → matches .md files only
      - "stem.canvas" / "stem.base" → matches that exact extension

    When multiple files match, the shallowest path wins (Obsidian's
    shortest-path behavior). Pass known_files to avoid repeated filesystem
    traversal when resolving many IDs against the same vault.

    Returns a relative Path from vault_root, or None if no file is found.
    """
    if file_id.endswith(".md"):
        stem_id = file_id[:-3]
        search_exts = frozenset({".md"})
    elif file_id.endswith(".canvas"):
        stem_id = file_id[:-7]
        search_exts = frozenset({".canvas"})
    elif file_id.endswith(".base"):
        stem_id = file_id[:-5]
        search_exts = frozenset({".base"})
    else:
        stem_id = file_id
        search_exts = frozenset({".md"})

    has_path_sep = "/" in stem_id

    if known_files is not None:
        if has_path_sep:
            rel_candidates = [
                f.relative_to(vault_root)
                for f in known_files
                if f.suffix in search_exts
                and str(f.relative_to(vault_root).with_suffix(""))
                .replace("\\", "/")
                .endswith(stem_id)
            ]
        else:
            rel_candidates = [
                f.relative_to(vault_root)
                for f in known_files
                if f.suffix in search_exts and f.stem == stem_id
            ]
    else:
        filters = load_ignore_filters(vault_root)
        if has_path_sep:
            raw = [f for ext in search_exts for f in vault_root.glob(stem_id + ext)]
        else:
            raw = [f for ext in search_exts for f in vault_root.glob(f"**/{stem_id}{ext}")]
        rel_candidates = [
            f.relative_to(vault_root)
            for f in raw
            if not should_ignore(f, vault_root, filters)
        ]

    if not rel_candidates:
        return None

    rel_candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return rel_candidates[0]


def discover_files(
    vault_root: Path, extensions: frozenset[str] = _SUPPORTED_EXTENSIONS
) -> list[Path]:
    """Return all non-ignored files with supported extensions under *vault_root*, sorted."""
    filters = load_ignore_filters(vault_root)
    result: list[Path] = []
    for ext in extensions:
        result.extend(
            f
            for f in sorted(vault_root.glob(f"**/*{ext}"))
            if not should_ignore(f, vault_root, filters)
        )
    return sorted(result)
