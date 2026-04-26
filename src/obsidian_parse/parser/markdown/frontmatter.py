"""YAML frontmatter extraction."""

import re
from typing import Any

import yaml

_FENCE = re.compile(r"^-{3,}\s*$", re.MULTILINE)


def extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter, return (metadata, body).

    Returns ({}, original content) if no valid frontmatter is found.
    """
    text = content.lstrip("﻿")  # strip BOM

    parts = _FENCE.split(text, maxsplit=2)
    # parts[0] must be exactly "" — any leading content means no frontmatter
    if len(parts) != 3 or parts[0] != "":
        return {}, content

    _, raw_yaml, body = parts

    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return {}, content

    # None means empty YAML block (---\n---), treat as empty dict
    if data is None:
        data = {}
    elif not isinstance(data, dict):
        return {}, content

    return data, body.lstrip("\n").lstrip("\r\n")
