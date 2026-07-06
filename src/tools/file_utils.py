from __future__ import annotations

"""
File utilities for CruiseMode.

Provides helper functions for reading, writing, and manipulating files
used across agents and tools.
"""

import os
import json
import shutil
from typing import Any


class FileUtils:
    """File system utility functions."""

    @staticmethod
    def read_text(filepath: str) -> str:
        """Read a text file and return its contents."""
        with open(filepath, "r") as f:
            return f.read()

    @staticmethod
    def write_text(filepath: str, content: str) -> None:
        """Write content to a text file, creating directories as needed."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)

    @staticmethod
    def read_json(filepath: str) -> dict[str, Any]:
        """Read and parse a JSON file."""
        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def write_json(filepath: str, data: Any, indent: int = 2) -> None:
        """Write data to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=indent, default=str)

    @staticmethod
    def copy_directory(src: str, dst: str) -> None:
        """Copy a directory tree, removing destination first if it exists."""
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    @staticmethod
    def ensure_dir(dirpath: str) -> None:
        """Create a directory and parents if they don't exist."""
        os.makedirs(dirpath, exist_ok=True)

    @staticmethod
    def list_files(directory: str, extension: str = "") -> list[str]:
        """List files in a directory, optionally filtered by extension."""
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if not extension or filename.endswith(extension):
                    files.append(os.path.join(root, filename))
        return sorted(files)
