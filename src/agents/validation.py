from __future__ import annotations

"""
ValidationAgent — runs pytest against generated tests and the sandbox app.

Captures stdout, stderr, return code, and test pass/fail status.
Stores results in the shared workflow state.
"""

import subprocess
import sys
import time
from typing import Any

from src.agents.base import BaseAgent


class ValidationAgent(BaseAgent):
    """Run pytest against generated tests and capture results."""

    def __init__(self):
        super().__init__(
            name="validation",
            description="Runs pytest validation against sandbox code",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Running local validation (pytest)...")

        generated_tests_dir = state.get("generated_tests_dir", "generated_tests")

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", generated_tests_dir, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            return_code = -1
            stdout = ""
            stderr = "Test execution timed out after 120 seconds."
        except FileNotFoundError:
            return_code = -1
            stdout = ""
            stderr = "pytest not found. Ensure it is installed."

        duration = round(time.time() - start_time, 2)

        # Parse pytest output for counts
        passed, failed, errors = self._parse_pytest_output(stdout)
        total = passed + failed + errors

        if return_code == 0:
            status = "PASSED"
        elif return_code == 1:
            status = "FAILED"
        else:
            status = "ERROR"

        state["validation"] = {
            "status": status,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "return_code": return_code,
            "duration_seconds": duration,
            "stdout": stdout,
            "stderr": stderr,
        }

        self.log(f"Validation complete: {status} ({passed}/{total} passed) in {duration}s")
        return state

    def _parse_pytest_output(self, stdout: str) -> tuple[int, int, int]:
        """Parse pytest output to extract pass/fail/error counts."""
        import re

        passed = failed = errors = 0

        # Look for the summary line like "5 passed, 1 failed"
        match = re.search(r"(\d+) passed", stdout)
        if match:
            passed = int(match.group(1))

        match = re.search(r"(\d+) failed", stdout)
        if match:
            failed = int(match.group(1))

        match = re.search(r"(\d+) error", stdout)
        if match:
            errors = int(match.group(1))

        return passed, failed, errors
