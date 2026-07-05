from __future__ import annotations

"""
Sandbox runner — executes commands within the sandbox workspace.

# TODO: Add Docker container isolation for production use
"""

import subprocess
import logging
from typing import Any

logger = logging.getLogger("cruisemode.sandbox.runner")


class SandboxRunner:
    """Execute commands within the sandbox workspace."""

    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = sandbox_dir

    def run_command(self, cmd: list[str], timeout: int = 60) -> dict[str, Any]:
        """Run a command in the sandbox directory."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.sandbox_dir,
                timeout=timeout,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "success": False,
            }
