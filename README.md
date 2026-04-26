# obsidian-parse

[![PyPI version](https://img.shields.io/pypi/v/obsidian-parse)](https://pypi.org/project/obsidian-parse/)
[![Python versions](https://img.shields.io/pypi/pyversions/obsidian-parse)](https://pypi.org/project/obsidian-parse/)
[![License](https://img.shields.io/pypi/l/obsidian-parse)](https://github.com/agent-hanju/obsidian-parse/blob/main/LICENSE)

If you're building tools on top of an Obsidian vault — graph visualizers, backlink finders, migration scripts, or second-brain analytics — obsidian-parse gives you the structured data to work with.

Parses `.md`, `.canvas`, and `.base` files to extract wikilinks, embeds, tags, and frontmatter, then converts them into a D3-compatible knowledge graph. Covers Obsidian-specific syntax (wikilinks, embeds, nested tags, canvas nodes, vault ignore rules, shortest-path link resolution) and leaves everything else to the caller.

---

## Use Cases

- **Knowledge graph visualization** — feed the D3 output directly into force-directed graph layouts
- **Backlink analysis** — find all notes that link to a given note, detect orphaned notes
- **Tag auditing** — enumerate all tags used across a vault, expand nested hierarchies
- **Vault migration tooling** — extract link structure before reformatting or moving notes
- **Static site generation** — resolve wikilinks to build nav and cross-reference systems
- **Second-brain analytics** — track how topics connect across your personal knowledge base

---

## Installation

```bash
uv add obsidian-parse
```

```bash
pip install obsidian-parse
```

---

## Quick Start

```python
from obsidian_parse import parse, results_to_d3

results = parse(["/path/to/vault"])

for r in results:
    print(r.file_id)            # "Project Ideas"
    print(r.wikilink_targets)   # ["Daily Notes", "Tasks.canvas"]
    print(r.tag_names)          # ["python", "python/tools", "status/done"]

graph = results_to_d3(results)
# → {"nodes": [...], "links": [...]}
```

---

## Output Examples

### ParseResult

```python
results = parse(["/vault"])
r = results[0]

r.file_id        # "Project Ideas"
r.path           # PosixPath('/vault/Projects/Project Ideas.md')
r.frontmatter    # {"tags": ["python", "tools"], "status": "active"}
r.wikilink_targets  # ["Daily Notes", "Tasks.canvas", "References/Paper"]
r.tag_names      # ["python", "tools", "python/tools"]  (body + frontmatter, merged)

r.wikilinks[0]
# WikiLink(target="Daily Notes", section="#Week 3", alias="this week", line=5, col=0)

r.wikilinks[1]
# WikiLink(target="Paper", section="^abc123", alias=None, line=12, col=4)
```

### D3 Graph

```python
graph = results_to_d3(results)
```

```json
{
  "nodes": [
    {"id": "Project Ideas", "type": "file", "label": "Project Ideas"},
    {"id": "Daily Notes",   "type": "file", "label": "Daily Notes"},
    {"id": "Tasks.canvas",  "type": "file", "label": "Tasks.canvas"},
    {"id": "#python",       "type": "tag",  "label": "python"},
    {"id": "#python/tools", "type": "tag",  "label": "python/tools"}
  ],
  "links": [
    {"source": "Project Ideas", "target": "Daily Notes",  "relation": "wikilink"},
    {"source": "Project Ideas", "target": "Tasks.canvas", "relation": "wikilink"},
    {"source": "Project Ideas", "target": "#python",      "relation": "tag"},
    {"source": "#python/tools", "target": "#python",      "relation": "parent"}
  ]
}
```

Link `relation` values: `wikilink`, `embed`, `tag`, `parent` (tag hierarchy).

---

## API

### `parse(paths)`

Accepts a list of file or directory paths. Directories are scanned recursively. Respects `.obsidian/app.json` ignore rules and skips dotfiles/dotfolders.

Returns a list of `ParseResult` objects.

Raises:
- `NoPathsProvidedError` — if `paths` is empty
- `PathNotFoundError` — if none of the paths exist
- `NoMarkdownFilesError` — if paths exist but contain no parseable files

---

### `ParseResult`

| Property | Type | Description |
|---|---|---|
| `file_id` | `str` | Node ID — `.md` extension omitted, `.canvas`/`.base` kept (e.g. `"Note"`, `"Board.canvas"`) |
| `path` | `Path` | Original file path |
| `frontmatter` | `dict` | Parsed YAML frontmatter |
| `wikilinks` | `list[WikiLink]` | Wikilinks with line/col positions |
| `embeds` | `list[Embed]` | Embeds with line/col positions |
| `tags` | `list[TagRef]` | Tags with line/col positions |
| `wikilink_targets` | `list[str]` | Deduplicated link targets (computed) |
| `embed_targets` | `list[str]` | Deduplicated embed targets (computed) |
| `tag_names` | `list[str]` | Merged body + frontmatter tags (computed) |

---

### `WikiLink`

| Field | Type | Description |
|---|---|---|
| `target` | `str` | Link target — `.md` extension omitted, other extensions kept |
| `section` | `str \| None` | Heading (`#Section`) or block ref (`^id`) |
| `alias` | `str \| None` | Display alias after `\|` |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

### `Embed`

| Field | Type | Description |
|---|---|---|
| `target` | `str` | Embed target — `.md` extension omitted, other extensions kept |
| `section` | `str \| None` | Heading or block ref |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

### `TagRef`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Tag name without leading `#` |
| `line` | `int \| None` | Source line number |
| `col` | `int \| None` | Source column number |

---

### `parse_file(file_path)`

Parses a single file by dispatching to the correct parser based on extension.

Raises `UnsupportedFileTypeError` for unregistered extensions.

### `parse_markdown_file(file_path)`

Reads and parses a single `.md` file directly, returning a `ParseResult`.

### `parse_markdown_content(content, file_id, path)`

Parses raw markdown string content without reading from disk. Useful for testing or in-memory workflows.

---

### `find_file_by_id(vault_root, file_id, *, known_files=None)`

Resolves a `file_id` to a vault-relative path.

- Bare stem or `"stem.md"` → searches `.md` files only
- `"stem.canvas"` / `"stem.base"` → searches that exact extension

When multiple files match, the shallowest path wins (Obsidian's shortest-path behavior). Pass `known_files` (from `discover_files()`) to avoid repeated filesystem traversal.

```python
from pathlib import Path
from obsidian_parse import find_file_by_id

vault = Path("/path/to/vault")
find_file_by_id(vault, "Note")          # → Path("folder/Note.md") or None
find_file_by_id(vault, "Board.canvas")  # → Path("Board.canvas") or None
```

---

### `expand_nested_tag(tag)`

Expands a nested tag into all ancestor segments.

```python
from obsidian_parse.utils.tags import expand_nested_tag

expand_nested_tag("topic/subtopic/leaf")  # ["topic", "topic/subtopic", "topic/subtopic/leaf"]
```

---

### `results_to_d3(results)`

Converts a list of `ParseResult` into a D3-compatible dict with `nodes` and `links`.

---

## Supported File Types

| Extension | Parsing |
|---|---|
| `.md` | Frontmatter, wikilinks, embeds, tags |
| `.canvas` | Wikilinks from file nodes; wikilinks + tags from text nodes |
| `.base` | Registered as graph nodes (no link extraction) |

Extraction is **block-aware**: wikilinks and tags inside code fences or HTML blocks are ignored.

---

## Development

```bash
uv sync --group dev   # install with dev dependencies
ruff check src/       # lint
mypy src/             # type check
```

---

## License

MIT
