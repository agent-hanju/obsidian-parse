"""Canvas file parser (.canvas JSON format)."""

import json
from pathlib import Path
from typing import Any

from obsidian_parse.parser.markdown import extract_frontmatter
from obsidian_parse.parser.markdown.block_classifier import classify_blocks
from obsidian_parse.parser.markdown.extractors import (
    extract_embeds,
    extract_tags,
    extract_wikilinks,
)
from obsidian_parse.parser.models import Embed, ParseResult, TagRef, WikiLink


def parse_canvas_content(content: str, file_id: str, path: Path) -> ParseResult:
    """Parse raw canvas JSON, extracting wikilinks from file nodes and all elements from text nodes.

    Raises ValueError on invalid JSON.
    """
    try:
        data: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid canvas JSON for {file_id}: {exc}") from exc

    wikilinks: list[WikiLink] = []
    embeds: list[Embed] = []
    tags: list[TagRef] = []
    seen_file_targets: set[str] = set()

    for node in data.get("nodes", []):
        node_type = node.get("type")

        if node_type == "file":
            raw_path = node.get("file", "")
            if not raw_path:
                continue
            p = Path(raw_path)
            target = p.stem if p.suffix == ".md" else p.stem + p.suffix
            if target and target not in seen_file_targets:
                seen_file_targets.add(target)
                wikilinks.append(WikiLink(target=target))

        elif node_type == "text":
            text: str = node.get("text", "")
            if not text:
                continue
            _, body = extract_frontmatter(text)
            blocks = classify_blocks(body)
            wikilinks.extend(extract_wikilinks(body, blocks))
            embeds.extend(extract_embeds(body, blocks))
            tags.extend(extract_tags(body, blocks))

    return ParseResult(
        file_id=file_id,
        path=path,
        wikilinks=wikilinks,
        embeds=embeds,
        tags=tags,
    )


def parse_canvas_file(file_path: Path) -> ParseResult:
    """Read and parse an Obsidian .canvas file."""
    return parse_canvas_content(
        file_path.read_text(encoding="utf-8"),
        file_path.stem + file_path.suffix,
        path=file_path,
    )
