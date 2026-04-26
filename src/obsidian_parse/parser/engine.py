"""Parser dispatcher and file collection orchestrator."""

import warnings
from collections.abc import Callable
from pathlib import Path

from obsidian_parse.parser.canvas_parser import parse_canvas_file
from obsidian_parse.parser.markdown_parser import parse_markdown_content, parse_markdown_file
from obsidian_parse.parser.models import ParseResult
from obsidian_parse.utils.errors import (
    NoMarkdownFilesError,
    NoPathsProvidedError,
    PathNotFoundError,
    UnsupportedFileTypeError,
)
from obsidian_parse.utils.vault import discover_files

__all__ = [
    "ParseResult",
    "parse",
    "parse_file",
    "parse_markdown_content",
    "parse_markdown_file",
]

_DISPATCH: dict[str, Callable[[Path], ParseResult]] = {
    ".md": parse_markdown_file,
    ".canvas": parse_canvas_file,
    ".base": lambda p: ParseResult(file_id=p.stem + p.suffix, path=p),
}


def parse_file(file_path: Path) -> ParseResult:
    """Dispatch to the correct parser based on file extension.

    Raises UnsupportedFileTypeError for unregistered extensions.
    """
    parser = _DISPATCH.get(file_path.suffix)
    if parser is None:
        raise UnsupportedFileTypeError(str(file_path))
    return parser(file_path)


def _parse_safely(file_path: Path, results: list[ParseResult]) -> None:
    try:
        results.append(parse_file(file_path))
    except (OSError, ValueError) as exc:
        warnings.warn(f"Skipping {file_path}: {exc}", stacklevel=3)


def parse(paths: list[str]) -> list[ParseResult]:
    """Collect parse results from multiple file or directory paths.

    Raises NoPathsProvidedError, PathNotFoundError, or NoMarkdownFilesError
    when paths are empty, missing, or contain no parseable files.
    """
    if not paths:
        raise NoPathsProvidedError()

    all_results: list[ParseResult] = []
    found_any_path = False

    for path_str in paths:
        path = Path(path_str)

        if not path.exists():
            continue

        found_any_path = True

        if path.is_file() and path.suffix in {".md", ".canvas", ".base"}:
            _parse_safely(path, all_results)
        elif path.is_dir():
            for vault_file in discover_files(path):
                _parse_safely(vault_file, all_results)

    if not found_any_path:
        raise PathNotFoundError(paths)

    if not all_results:
        raise NoMarkdownFilesError(paths)

    return all_results
