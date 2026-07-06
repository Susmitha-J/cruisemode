from __future__ import annotations

"""
PII detector for CruiseMode.

Detects personally identifiable information in code, logs, and API responses.
"""

import re
from typing import Any


class PIIDetector:
    """Detect PII patterns in text and code."""

    # Common PII field names
    PII_FIELDS = [
        "email", "customer_email", "user_email",
        "card_number", "credit_card", "cc_number",
        "account_number", "bank_account",
        "ssn", "social_security",
        "phone", "phone_number",
        "address", "street_address",
    ]

    # Regex patterns for common PII formats
    PII_PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "card_number": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    }

    @classmethod
    def scan_text(cls, text: str) -> list[dict[str, Any]]:
        """Scan text for PII patterns."""
        detections = []

        for pii_type, pattern in cls.PII_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detections.append({
                    "type": pii_type,
                    "value_preview": cls._mask_value(match.group()),
                    "position": match.start(),
                })

        return detections

    @classmethod
    def has_pii_field_names(cls, text: str) -> list[str]:
        """Check if text references PII field names."""
        found = []
        text_lower = text.lower()
        for field in cls.PII_FIELDS:
            if field in text_lower:
                found.append(field)
        return found

    @staticmethod
    def _mask_value(value: str) -> str:
        """Mask a PII value for safe display."""
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
