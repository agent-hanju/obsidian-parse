# obsidian-parse

Extract knowledge graph metadata from Obsidian-style markdown vaults.

A helper library for Obsidian parsing — covering only what standard code can't: Obsidian-specific syntax (wikilinks, embeds, nested tags), vault ignore rules, shortest-path link resolution, and graph output. Filesystem traversal, text search, and other general-purpose tasks are intentionally left to the caller.

Parses `.md`, `.canvas`, and `.base` files to extract wikilinks, embeds, tags, and frontmatter — then converts them into a D3-compatible graph structure for visualization or downstream analysis.

## Installation

```bash
uv add obsidian-parse
```

Or with pip:

```bash
pip install obsidian-parse
```

## Quick Start

```python
from obsidian_parse import parse, results_to_d3

# Parse an entire vault directory
results = parse(["/path/to/your/vault"])

# Convert to D3 graph format
graph = results_to_d3(results)
# graph = {"nodes": [...], "links": [...]}
```

## What It Extracts

| Element | Syntax | Example |
|---|---|---|
| WikiLink | `[[Note]]` | `[[Project Ideas\|alias]]` |
| Embed | `![[file]]` | `![[image.png]]` |
| Tag | `#tagname` | `#topic/subtopic` |
| Frontmatter | YAML header | `tags: [python, tools]` |

Extraction is block-aware: wikilinks and tags inside code fences or HTML blocks are intentionally ignored.

## API

### `parse(paths)`

Accepts a list of file or directory paths. Directories are scanned recursively. Respects `.obsidian/app.json` ignore rules and skips dotfiles/dotfolders.

Returns a list of `ParseResult` objects.

Raises:
- `NoPathsProvidedError` — if `paths` is empty
- `PathNotFoundError` — if none of the paths exist
- `NoMarkdownFilesError` — if paths exist but contain no parseable files

### `ParseResult`

| Property | Type | Description |
|---|---|---|
| `file_id` | `str` | Filename stem, used as node ID |
| `path` | `Path` | Original file path |
| `frontmatter` | `dict` | Parsed YAML frontmatter |
| `wikilinks` | `list[WikiLink]` | Wikilinks with line/col positions |
| `embeds` | `list[Embed]` | Embeds with line/col positions |
| `tags` | `list[TagRef]` | Tags with line/col positions |
| `wikilink_targets` | `list[str]` | Deduplicated link targets (computed) |
| `embed_targets` | `list[str]` | Deduplicated embed targets (computed) |
| `tag_names` | `list[str]` | Merged body + frontmatter tags (computed) |

### `parse_file(file_path)`

Parses a single file by dispatching to the correct parser based on extension.

Raises `UnsupportedFileTypeError` for unregistered extensions.

### `parse_markdown_file(file_path)`

Reads and parses a single `.md` file directly, returning a `ParseResult`.

### `parse_markdown_content(content, file_id, path)`

Parses raw markdown string content without reading from disk. Useful for testing or in-memory workflows.

### `WikiLink`

| Field | Type | Description |
|---|---|---|
| `target` | `str` | Link target (note name) |
| `section` | `str \| None` | Heading (`#Section`) or block ref (`^id`) |
| `alias` | `str \| None` | Display alias after `\|` |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

### `Embed`

| Field | Type | Description |
|---|---|---|
| `target` | `str` | Embed target filename |
| `section` | `str \| None` | Heading or block id |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

### `TagRef`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Tag name without leading `#` |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

### `expand_nested_tag(tag)`

Expands a nested tag string into all ancestor tags.

```python
from obsidian_parse.utils.tags import expand_nested_tag

expand_nested_tag("a/b/c")    # ["a", "a/b", "a/b/c"]
expand_nested_tag("/foo/bar") # ["/foo", "/foo/bar"]
expand_nested_tag("a//b/c")  # ["a", "a//b", "a//b/c"]
```

The first `/` of each consecutive slash run is the hierarchy separator; remaining slashes become part of the next segment's name. A leading slash run is part of the first segment's name, never a separator.

### `results_to_d3(results)`

Converts a list of `ParseResult` into a dict:

```python
{
    "nodes": [
        {"id": "note-a", "type": "file", "label": "note-a"},
        {"id": "#python", "type": "tag", "label": "python"},
    ],
    "links": [
        {"source": "note-a", "target": "note-b", "relation": "wikilink"},
        {"source": "note-a", "target": "#python", "relation": "tag"},
        {"source": "#python/tools", "target": "#python", "relation": "parent"},
    ]
}
```

Link relations: `wikilink`, `embed`, `tag`, `parent` (tag hierarchy).

## Supported File Types

- **`.md`** — Markdown with YAML frontmatter
- **`.canvas`** — Obsidian canvas JSON; extracts wikilinks from file-type nodes and all elements from text nodes
- **`.base`** — Obsidian base files; recorded as graph nodes (filename/path only, no link extraction)

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Lint
ruff check src/

# Type check
mypy src/
```

## License

MIT
