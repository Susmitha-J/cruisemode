from __future__ import annotations

"""
Patch writer for CruiseMode.

Writes code patches to files and records the changes for diff generation.

# TODO: Integrate with Gemini for intelligent patch generation
"""

import os
from typing import Any


class PatchWriter:
    """Write patches to files and record changes."""

    def __init__(self):
        self.patches_applied: list[dict[str, Any]] = []

    def apply_patch(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        description: str,
    ) -> bool:
        """
        Apply a text replacement patch to a file.

        Args:
            filepath: Path to the file to patch.
            old_content: The exact text to replace.
            new_content: The replacement text.
            description: Human-readable description of the patch.

        Returns:
            True if the patch was applied, False otherwise.
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()

            if old_content not in content:
                return False

            patched = content.replace(old_content, new_content, 1)

            with open(filepath, "w") as f:
                f.write(patched)

            self.patches_applied.append({
                "file": filepath,
                "description": description,
                "old_content_preview": old_content[:100],
                "new_content_preview": new_content[:100],
            })
            return True

        except (FileNotFoundError, PermissionError):
            return False

    def get_summary(self) -> list[dict[str, Any]]:
        """Return a summary of all applied patches."""
        return self.patches_applied
