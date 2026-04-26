"""Vault-level file discovery and wikilink resolution.

Acts as the equivalent of Obsidian's ``vault.getMarkdownFiles()`` —
returns only the markdown files that should be visible to consumers.
"""

from __future__ import annotations

from pathlib import Path

from obsidian_parse.utils.ignore import load_ignore_filters, should_ignore

_SUPPORTED_EXTENSIONS = frozenset({".md", ".canvas", ".base"})


def resolve_doc_id(
    vault_root: Path,
    file_id: str,
    *,
    known_files: list[Path] | None = None,
) -> Path | None:
    """Resolve an Obsidian file_id to a path relative to vault_root.

    file_id may be a bare stem ("ProjectA"), a path suffix ("folder/ProjectA"),
    or include an extension ("ProjectA.md"). When multiple files match, the
    shallowest path wins (Obsidian's default "shortest path" behavior).

    Pass known_files (from discover_files()) to avoid repeated filesystem
    traversal when resolving many IDs against the same vault.

    Returns a relative Path from vault_root, or None if no file is found.
    """
    # Strip known extension so matching always works on stem/suffix.
    stem_id = file_id
    for ext in _SUPPORTED_EXTENSIONS:
        if file_id.endswith(ext):
            stem_id = file_id[: -len(ext)]
            break

    has_path_sep = "/" in stem_id

    if known_files is not None:
        # In-memory filter: O(n) scan, no extra I/O.
        if has_path_sep:
            rel_candidates = [
                f.relative_to(vault_root)
                for f in known_files
                if str(f.relative_to(vault_root).with_suffix(""))
                .replace("\\", "/")
                .endswith(stem_id)
            ]
        else:
            rel_candidates = [f.relative_to(vault_root) for f in known_files if f.stem == stem_id]
    else:
        # Filesystem path: one glob covers all extensions at once, then filter.
        filters = load_ignore_filters(vault_root)
        if has_path_sep:
            raw = list(vault_root.glob(stem_id + ".*"))
        else:
            raw = list(vault_root.glob(f"**/{stem_id}.*"))
        rel_candidates = [
            f.relative_to(vault_root)
            for f in raw
            if f.suffix in _SUPPORTED_EXTENSIONS and not should_ignore(f, vault_root, filters)
        ]

    if not rel_candidates:
        return None

    # Shortest path = fewest parts; break ties alphabetically.
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
