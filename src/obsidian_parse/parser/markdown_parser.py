"""Markdown file parser (.md format)."""

from pathlib import Path

from obsidian_parse.parser.markdown import extract_frontmatter
from obsidian_parse.parser.markdown.block_classifier import classify_blocks
from obsidian_parse.parser.markdown.extractors import (
    extract_embeds,
    extract_tags,
    extract_wikilinks,
)
from obsidian_parse.parser.models import ParseResult


def parse_markdown_content(content: str, file_id: str, path: Path) -> ParseResult:
    """Parse raw markdown content, returning all extracted elements."""
    frontmatter_data, body = extract_frontmatter(content)
    blocks = classify_blocks(body)

    return ParseResult(
        file_id=file_id,
        path=path,
        frontmatter=frontmatter_data,
        wikilinks=extract_wikilinks(body, blocks),
        embeds=extract_embeds(body, blocks),
        tags=extract_tags(body, blocks),
    )


def parse_markdown_file(file_path: Path) -> ParseResult:
    """Read and parse a .md file."""
    content = file_path.read_text(encoding="utf-8")
    return parse_markdown_content(content, file_path.stem, path=file_path)
