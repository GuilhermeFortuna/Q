from pathlib import Path
from typing import Optional


def get_parent_directory(any_subdir: str = "pyproject.toml") -> Optional[Path]:
    """Find the project root by searching for a marker file/folder upwards from the current working directory."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / any_subdir).exists():
            return parent
    return None
