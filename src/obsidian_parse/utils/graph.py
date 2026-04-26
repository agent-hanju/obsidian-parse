"""Utilities for converting ParseResults to graph structures."""

from obsidian_parse.parser.models import ParseResult
from obsidian_parse.utils.tags import expand_nested_tag


def results_to_d3(results: list[ParseResult]) -> dict[str, list[dict[str, str]]]:
    """Convert a list of ParseResults to a D3-compatible graph dict.

    Returns:
        { "nodes": [{"id", "type", "label"}], "links": [{"source", "target", "relation"}] }
        relation is one of: "wikilink", "embed", "tag", "parent"
    """
    nodes: dict[str, dict[str, str]] = {}
    links: list[dict[str, str]] = []
    seen_parent_links: set[tuple[str, str]] = set()

    for result in results:
        file_id = result.file_id
        nodes.setdefault(file_id, {"id": file_id, "type": "file", "label": file_id})

        for target in result.wikilink_targets:
            nodes.setdefault(target, {"id": target, "type": "file", "label": target})
            links.append({"source": file_id, "target": target, "relation": "wikilink"})

        for target in result.embed_targets:
            nodes.setdefault(target, {"id": target, "type": "file", "label": target})
            links.append({"source": file_id, "target": target, "relation": "embed"})

        for tag in result.tag_names:
            tag_id = f"#{tag}"
            nodes.setdefault(tag_id, {"id": tag_id, "type": "tag", "label": tag})
            links.append({"source": file_id, "target": tag_id, "relation": "tag"})

            ancestors = expand_nested_tag(tag)
            for i in range(len(ancestors) - 1):
                parent_id, child_id = f"#{ancestors[i]}", f"#{ancestors[i + 1]}"
                nodes.setdefault(parent_id, {"id": parent_id, "type": "tag", "label": ancestors[i]})
                if (parent_id, child_id) not in seen_parent_links:
                    seen_parent_links.add((parent_id, child_id))
                    links.append({"source": parent_id, "target": child_id, "relation": "parent"})

    return {"nodes": list(nodes.values()), "links": links}
