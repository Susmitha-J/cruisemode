from __future__ import annotations

"""
Code scanner utilities for CruiseMode.

Provides static analysis helpers for detecting PII logging, broad exceptions,
and other common code issues.

# TODO: Integrate with real static analysis tools (pylint, bandit, semgrep)
"""

import re
from typing import Any


class CodeScanner:
    """Static code analysis utilities."""

    # Patterns that indicate PII logging
    PII_LOG_PATTERNS = [
        r'logger\.\w+\(.*model_dump\(\)',
        r'logger\.\w+\(.*\.dict\(\)',
        r'print\(.*request\)',
        r'logging\.\w+\(.*email',
        r'logging\.\w+\(.*card_number',
        r'logging\.\w+\(.*account_number',
    ]

    # Patterns for broad exception handling
    BROAD_EXCEPTION_PATTERNS = [
        r'except\s+Exception\s*:',
        r'except\s+Exception\s+as\s+\w+\s*:',
        r'except\s*:',
    ]

    @staticmethod
    def scan_file(filepath: str) -> list[dict[str, Any]]:
        """Scan a single file for common issues."""
        findings = []

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except (FileNotFoundError, PermissionError):
            return findings

        for line_num, line in enumerate(lines, start=1):
            # Check for PII logging
            for pattern in CodeScanner.PII_LOG_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "file": filepath,
                        "line": line_num,
                        "type": "pii_logging",
                        "severity": "HIGH",
                        "content": line.strip(),
                    })

            # Check for broad exceptions
            for pattern in CodeScanner.BROAD_EXCEPTION_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "file": filepath,
                        "line": line_num,
                        "type": "broad_exception",
                        "severity": "MEDIUM",
                        "content": line.strip(),
                    })

        return findings
