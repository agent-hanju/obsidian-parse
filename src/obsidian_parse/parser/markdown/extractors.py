"""Block-aware positioned extractors for wikilinks, embeds, and tags."""

import re
from collections.abc import Callable
from re import Match, Pattern
from typing import TypeVar

from obsidian_parse.parser.markdown.block_classifier import Block, BlockType, classify_blocks
from obsidian_parse.parser.models import Embed, TagRef, WikiLink

_T = TypeVar("_T")

def _strip_extension(target: str) -> str:
    if target.endswith(".md"):
        return target[:-3]
    return target


# Pattern: [[Target]] or [[Target|Alias]]
# Negative lookbehind (?<!!) excludes embeds (![[...]])
# Group 1: target+section, Group 2: alias (optional)
WIKILINK_PATTERN = re.compile(r"(?<!!)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

# Pattern: ![[Target]]
EMBED_PATTERN = re.compile(r"!\[\[([^\]]+)\]\]")

# Tag pattern: #TagName (Obsidian-compatible, Unicode-aware)
# Must start with # followed by a letter (any script) or underscore.
# Purely numeric tags like #123 are not recognized.
TAG_PATTERN = re.compile(r"(?:^|(?<=\s))#((?!\d)[\w/\-]+)", re.UNICODE)


def _line_starts(content: str) -> list[int]:
    lines = content.splitlines(keepends=True)
    starts: list[int] = []
    pos = 0
    for ln in lines:
        starts.append(pos)
        pos += len(ln)
    return starts


def _offset_to_line_col(offset: int, line_starts: list[int]) -> tuple[int, int]:
    line_idx = 0
    for i, ls in enumerate(line_starts):
        if ls <= offset:
            line_idx = i
        else:
            break
    return line_idx, offset - line_starts[line_idx]


def _inline_blocks(content: str, blocks: list[Block] | None) -> list[Block]:
    if blocks is None:
        blocks = classify_blocks(content)
    return [b for b in blocks if b.type == BlockType.INLINE]


# CommonMark §6.1 code spans: an odd number of backticks before pos means we're inside inline code.
def _is_inside_inline_code(pos: int, content: str) -> bool:
    return content[:pos].count("`") % 2 == 1


def _extract_positioned(
    content: str,
    blocks: list[Block] | None,
    line_offset: int,
    pattern: Pattern[str],
    factory: Callable[[Match[str], int, int], _T | None],
) -> list[_T]:
    """Generic positioned extractor: scans INLINE blocks for pattern matches."""
    ls = _line_starts(content)
    results: list[_T] = []
    for block in _inline_blocks(content, blocks):
        for match in pattern.finditer(block.content):
            if _is_inside_inline_code(match.start(), block.content):
                continue
            abs_offset = ls[block.line_start] + match.start()
            line, col = _offset_to_line_col(abs_offset, ls)
            item = factory(match, line_offset + line, col)
            if item is not None:
                results.append(item)
    return results


def extract_wikilinks(
    content: str,
    blocks: list[Block] | None = None,
    line_offset: int = 0,
) -> list[WikiLink]:
    """Extract wikilinks with positions, restricted to INLINE blocks."""
    _SECTION_RE = re.compile(r"([#^].+)$")

    def factory(match: Match[str], line: int, col: int) -> WikiLink | None:
        raw = match.group(1).strip()
        m = _SECTION_RE.search(raw)
        section = m.group(1) if m else None
        target = _strip_extension(raw[: m.start()].strip() if m else raw)
        alias = match.group(2).strip() if match.group(2) else None
        if not target:
            return None
        return WikiLink(target=target, section=section, alias=alias, line=line, col=col)

    return _extract_positioned(content, blocks, line_offset, WIKILINK_PATTERN, factory)


def extract_embeds(
    content: str,
    blocks: list[Block] | None = None,
    line_offset: int = 0,
) -> list[Embed]:
    """Extract embeds with positions, restricted to INLINE blocks."""
    _SECTION_RE = re.compile(r"([#^].+)$")

    def factory(match: Match[str], line: int, col: int) -> Embed | None:
        raw = match.group(1).strip()
        m = _SECTION_RE.search(raw)
        section = m.group(1) if m else None
        target = _strip_extension(raw[: m.start()].strip() if m else raw)
        return Embed(target=target, section=section, line=line, col=col) if target else None

    return _extract_positioned(content, blocks, line_offset, EMBED_PATTERN, factory)


def extract_tags(
    content: str,
    blocks: list[Block] | None = None,
    line_offset: int = 0,
) -> list[TagRef]:
    """Extract tags with positions, restricted to INLINE blocks."""
    seen: set[str] = set()

    def factory(match: Match[str], line: int, col: int) -> TagRef | None:
        name = match.group(1)
        if name in seen:
            return None
        seen.add(name)
        return TagRef(name=name, line=line, col=col)

    return _extract_positioned(content, blocks, line_offset, TAG_PATTERN, factory)
