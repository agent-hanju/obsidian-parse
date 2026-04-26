"""Custom exceptions for Unobsidian."""


class UnobsidianError(Exception):
    """Base exception for Unobsidian errors."""

    pass


class NodeNotFoundError(UnobsidianError):
    """Node not found in graph."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node not found: {node_id}")


class NoPathsProvidedError(UnobsidianError):
    """No paths were provided."""

    def __init__(self) -> None:
        super().__init__("No paths provided.")


class PathNotFoundError(UnobsidianError):
    """None of the provided paths exist."""

    def __init__(self, paths: list[str]):
        self.paths = paths
        super().__init__(f"None of the provided paths exist: {', '.join(paths)}")


class NoMarkdownFilesError(UnobsidianError):
    """Paths exist but contain no parseable markdown files."""

    def __init__(self, paths: list[str]):
        self.paths = paths
        super().__init__(f"No markdown files found in: {', '.join(paths)}")


class UnsupportedFileTypeError(UnobsidianError):
    """File type is not supported by any registered parser."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Unsupported file type: {file_path}")


class VaultNotFoundError(UnobsidianError):
    """Vault name not found in registry."""

    def __init__(self, vault: str, available: list[str]):
        self.vault = vault
        self.available = available
        super().__init__(f"Unknown vault '{vault}'. Available vaults: {', '.join(available)}")
