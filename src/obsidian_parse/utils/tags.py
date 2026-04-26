"""Tag hierarchy utilities."""

import re

# Matches the first '/' of each consecutive slash run (not preceded by another '/').
_FIRST_IN_RUN = re.compile(r"(?<!/)/")
_LEADING_SLASHES = re.compile(r"^/+")


def expand_nested_tag(tag: str) -> list[str]:
    """Expand a nested tag into all ancestor tags.

    The first '/' of each consecutive slash run is the hierarchy separator;
    remaining slashes in the run become part of the next segment's name.
    A leading slash run is part of the first segment's name, never a separator.

    Examples:
      "a/b/c"    → ["a", "a/b", "a/b/c"]
      "/foo/bar"  → ["/foo", "/foo/bar"]
      "a//b/c"   → ["a", "a//b", "a//b/c"]
      "//a/b//c" → ["//a", "//a/b", "//a/b//c"]
    """
    m = _LEADING_SLASHES.match(tag)
    leading = m.group() if m else ""
    rest = tag[len(leading) :]

    parts: list[str] = _FIRST_IN_RUN.split(rest) if rest else []

    if leading:
        parts = [leading + parts[0]] + parts[1:] if parts else [leading]

    segments = [s for s in parts if s]
    return ["/".join(segments[:i]) for i in range(1, len(segments) + 1)]
