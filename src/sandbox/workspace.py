from __future__ import annotations

"""
Sandbox workspace manager for CruiseMode.

Creates and manages isolated workspace copies where patches are safely applied.
The original source files are never modified.
"""

import os
import shutil
import logging

logger = logging.getLogger("cruisemode.sandbox")


class SandboxWorkspace:
    """
    Manages a sandbox copy of the target application.

    All patches are applied inside the sandbox. The original source
    directory is never modified.
    """

    def __init__(self, source_dir: str, sandbox_dir: str = ".sandbox"):
        self.source_dir = source_dir
        self.sandbox_dir = sandbox_dir
        self._created = False

    def create(self) -> str:
        """Create a sandbox copy of the source directory."""
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
            logger.info(f"Removed existing sandbox: {self.sandbox_dir}")

        shutil.copytree(self.source_dir, self.sandbox_dir)
        self._created = True
        logger.info(f"Created sandbox: {self.source_dir} -> {self.sandbox_dir}")
        return self.sandbox_dir

    def destroy(self) -> None:
        """Remove the sandbox workspace."""
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
            self._created = False
            logger.info(f"Destroyed sandbox: {self.sandbox_dir}")

    def list_files(self) -> list[str]:
        """List all files in the sandbox."""
        files = []
        for root, _, filenames in os.walk(self.sandbox_dir):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return sorted(files)

    @property
    def is_active(self) -> bool:
        return self._created and os.path.exists(self.sandbox_dir)
