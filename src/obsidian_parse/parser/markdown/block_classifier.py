"""Line-level block classifier for markdown content."""

import re
from dataclasses import dataclass
from enum import Enum

# CommonMark §4.6 HTML block detection.
# Type 7 (arbitrary complete tag on its own line) is intentionally omitted:
# in Obsidian notes, a lone <b> or <foo> is almost always inline intent.
#
# Type 1: <script|pre|style|textarea  →  ends at </script|pre|style|textarea>
_HTML_TYPE1_START = re.compile(r"^<(script|pre|style|textarea)(\s|>|$)", re.IGNORECASE)
_HTML_TYPE1_END = re.compile(r"</(script|pre|style|textarea)>", re.IGNORECASE)

# Type 2: <!--  →  ends at -->
_HTML_TYPE2_START = re.compile(r"^<!--")
_HTML_TYPE2_END = re.compile(r"-->")

# Type 3: <?  →  ends at ?>
_HTML_TYPE3_START = re.compile(r"^<\?")
_HTML_TYPE3_END = re.compile(r"\?>")

# Type 4: <! followed by ASCII uppercase  →  ends at >
_HTML_TYPE4_START = re.compile(r"^<![A-Z]")
_HTML_TYPE4_END = re.compile(r">")

# Type 5: <![CDATA[  →  ends at ]]>
_HTML_TYPE5_START = re.compile(r"^<!\[CDATA\[")
_HTML_TYPE5_END = re.compile(r"\]\]>")

# Type 6: block-level tags  →  ends at blank line
_HTML_TYPE6_START = re.compile(
    r"^<(/?)("
    r"address|article|aside|base|basefont|blockquote|body|caption|center|"
    r"col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|"
    r"figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|"
    r"legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|"
    r"option|p|section|source|summary|table|tbody|td|tfoot|th|thead|title|"
    r"tr|track|ul"
    r")(\s|>|/>|$)",
    re.IGNORECASE,
)

# (start_pattern, end_pattern | None)  — None means "ends at blank line"
_HTML_BLOCK_RULES: list[tuple[re.Pattern[str], re.Pattern[str] | None]] = [
    (_HTML_TYPE1_START, _HTML_TYPE1_END),
    (_HTML_TYPE2_START, _HTML_TYPE2_END),
    (_HTML_TYPE3_START, _HTML_TYPE3_END),
    (_HTML_TYPE4_START, _HTML_TYPE4_END),
    (_HTML_TYPE5_START, _HTML_TYPE5_END),
    (_HTML_TYPE6_START, None),
]


class BlockType(Enum):
    CODE_FENCE = "code_fence"
    INLINE = "inline"
    HTML = "html"


@dataclass
class Block:
    type: BlockType
    line_start: int
    line_end: int
    content: str


def _match_html_end(end_pattern: re.Pattern[str] | None, lines: list[str], i: int, n: int) -> int:
    """Return the index just past the end of the current HTML block."""
    if end_pattern is None:
        while i < n and lines[i].strip():
            i += 1
    else:
        while i < n and not end_pattern.search(lines[i]):
            i += 1
        if i < n:
            i += 1  # consume the line containing the end marker
    return i


def _match_html_start(stripped: str) -> tuple[bool, re.Pattern[str] | None]:
    """Return (matched, end_pattern) for the first matching HTML block rule."""
    for start_pat, end_pat in _HTML_BLOCK_RULES:
        if start_pat.match(stripped):
            return True, end_pat
    return False, None


def _match_fence_end(lines: list[str], i: int, n: int, fence: str, fence_char: str) -> int:
    """Return the index just past the closing fence line."""
    while i < n:
        closing = lines[i].rstrip().lstrip()
        if closing.startswith(fence) and not closing.lstrip(fence_char):
            i += 1  # consume closing fence
            break
        i += 1
    return i


def classify_blocks(content: str) -> list[Block]:
    """Classify markdown content into typed blocks in a single pass.

    Processing order: code fences → block-level HTML → inline.
    Only block-level HTML tags (CommonMark §4.6 types 1–6) are treated as
    opaque; inline tags like <em> or <span> remain part of INLINE blocks.
    Type 7 is excluded — see module-level comment.

    Args:
        content: Markdown body string (frontmatter already stripped).

    Returns:
        List of Block objects covering the entire content, in order.
    """
    lines = content.splitlines(keepends=True)
    blocks: list[Block] = []
    n = len(lines)
    i = 0
    inline_start = 0

    def flush_inline(end: int) -> None:
        if inline_start < end:
            blocks.append(
                Block(BlockType.INLINE, inline_start, end - 1, "".join(lines[inline_start:end]))
            )

    while i < n:
        raw = lines[i].rstrip()
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.lstrip()

        if indent <= 3 and (stripped.startswith("```") or stripped.startswith("~~~")):
            flush_inline(i)
            fence_char = stripped[0]
            fence_len = len(stripped) - len(stripped.lstrip(fence_char))
            start = i
            i = _match_fence_end(lines, i + 1, n, fence_char * fence_len, fence_char)
            blocks.append(Block(BlockType.CODE_FENCE, start, i - 1, "".join(lines[start:i])))
            inline_start = i
            continue

        if indent <= 3:
            matched, html_end = _match_html_start(stripped)
            if matched:
                flush_inline(i)
                start = i
                i = _match_html_end(html_end, lines, i + 1, n)
                blocks.append(Block(BlockType.HTML, start, i - 1, "".join(lines[start:i])))
                inline_start = i
                continue

        i += 1

    flush_inline(n)
    return blocks
