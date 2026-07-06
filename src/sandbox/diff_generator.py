from __future__ import annotations

"""
Diff generator — generates unified diffs between original and sandbox files.

Used by the PR report to show exactly what patches were applied.
"""

import difflib
import os


class DiffGenerator:
    """Generate diffs between original and patched files."""

    @staticmethod
    def generate_diff(original_path: str, patched_path: str) -> str:
        """
        Generate a unified diff between two files.

        Args:
            original_path: Path to the original file.
            patched_path: Path to the patched file in sandbox.

        Returns:
            Unified diff string.
        """
        try:
            with open(original_path, "r") as f:
                original_lines = f.readlines()
            with open(patched_path, "r") as f:
                patched_lines = f.readlines()
        except FileNotFoundError:
            return ""

        diff = difflib.unified_diff(
            original_lines,
            patched_lines,
            fromfile=f"a/{os.path.basename(original_path)}",
            tofile=f"b/{os.path.basename(patched_path)}",
        )
        return "".join(diff)

    @staticmethod
    def generate_all_diffs(original_dir: str, sandbox_dir: str) -> dict[str, str]:
        """Generate diffs for all changed files."""
        diffs = {}

        for root, _, files in os.walk(sandbox_dir):
            for filename in files:
                if filename.startswith(".") or filename.endswith(".pyc"):
                    continue

                patched_path = os.path.join(root, filename)
                relative = os.path.relpath(patched_path, sandbox_dir)
                original_path = os.path.join(original_dir, relative)

                if os.path.exists(original_path):
                    diff = DiffGenerator.generate_diff(original_path, patched_path)
                    if diff:
                        diffs[relative] = diff

        return diffs
