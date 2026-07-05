from __future__ import annotations

"""
Test runner for CruiseMode.

Wraps subprocess pytest execution and captures structured results.
"""

import subprocess
import re
import sys
from typing import Any


class TestRunner:
    """Run pytest and capture structured results."""

    @staticmethod
    def run_pytest(test_path: str, verbose: bool = True, timeout: int = 120) -> dict[str, Any]:
        """
        Run pytest on the given path and return structured results.

        Args:
            test_path: Path to test file or directory.
            verbose: Whether to use verbose output.
            timeout: Timeout in seconds.

        Returns:
            Dict with status, counts, stdout, stderr, return_code.
        """
        cmd = [sys.executable, "-m", "pytest", test_path]
        if verbose:
            cmd.append("-v")
        cmd.append("--tb=short")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return TestRunner._parse_result(result)
        except subprocess.TimeoutExpired:
            return {
                "status": "ERROR",
                "message": f"Timed out after {timeout}s",
                "return_code": -1,
                "stdout": "",
                "stderr": "",
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "total_tests": 0,
            }
        except FileNotFoundError:
            return {
                "status": "ERROR",
                "message": "pytest not found",
                "return_code": -1,
                "stdout": "",
                "stderr": "",
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "total_tests": 0,
            }

    @staticmethod
    def _parse_result(result: subprocess.CompletedProcess) -> dict[str, Any]:
        """Parse subprocess result into structured dict."""
        passed = failed = errors = 0

        match = re.search(r"(\d+) passed", result.stdout)
        if match:
            passed = int(match.group(1))

        match = re.search(r"(\d+) failed", result.stdout)
        if match:
            failed = int(match.group(1))

        match = re.search(r"(\d+) error", result.stdout)
        if match:
            errors = int(match.group(1))

        status = "PASSED" if result.returncode == 0 else "FAILED" if result.returncode == 1 else "ERROR"

        return {
            "status": status,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total_tests": passed + failed + errors,
        }
