"""Shared data models for all parsers."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WikiLink:
    """A wikilink extracted from markdown content."""

    target: str
    section: str | None = None  # heading (#Section) or block id (^blockid)
    alias: str | None = None
    line: int | None = None
    col: int | None = None


@dataclass
class Embed:
    """An embed extracted from markdown content."""

    target: str
    section: str | None = None  # heading (#Section) or block id (^blockid)
    line: int | None = None
    col: int | None = None


@dataclass
class TagRef:
    """A tag extracted from markdown content with source position."""

    name: str
    line: int | None = None
    col: int | None = None


@dataclass
class ParseResult:
    """Result of parsing any supported file type."""

    file_id: str
    path: Path
    frontmatter: dict[str, Any] = field(default_factory=dict[str, Any])
    wikilinks: list[WikiLink] = field(default_factory=list[WikiLink])
    embeds: list[Embed] = field(default_factory=list[Embed])
    tags: list[TagRef] = field(default_factory=list[TagRef])

    @property
    def wikilink_targets(self) -> list[str]:
        """Deduplicated wikilink targets, order preserved."""
        seen: set[str] = set()
        result: list[str] = []
        for w in self.wikilinks:
            if w.target not in seen:
                seen.add(w.target)
                result.append(w.target)
        return result

    @property
    def embed_targets(self) -> list[str]:
        """Deduplicated embed targets, order preserved."""
        seen: set[str] = set()
        result: list[str] = []
        for e in self.embeds:
            if e.target not in seen:
                seen.add(e.target)
                result.append(e.target)
        return result

    @property
    def tag_names(self) -> list[str]:
        """Body tags (from tags field) merged with frontmatter tags, deduplicated."""
        seen: set[str] = set()
        result: list[str] = []
        for t in self.tags:
            if t.name not in seen:
                seen.add(t.name)
                result.append(t.name)
        fm_raw: list[Any] | str | None = self.frontmatter.get("tags") or self.frontmatter.get("tag")
        fm_tags: list[str] = []
        if isinstance(fm_raw, list):
            fm_tags = [str(t) for t in fm_raw if t is not None]
        elif isinstance(fm_raw, str):
            fm_tags = [fm_raw]
        for ft in fm_tags:
            if ft not in seen:
                seen.add(ft)
                result.append(ft)
        return result


__all__ = ["WikiLink", "Embed", "TagRef", "ParseResult"]
