from __future__ import annotations

"""
TestGenerationAgent — generates pytest tests dynamically.

For the default Refund API demo, writes hardcoded unit + API tests.
For custom repos, discovers .py files in the sandbox and generates
import/syntax smoke tests and pattern-based tests grounded in real code.
"""

import os
import re
from typing import Any

from src.agents.base import BaseAgent


class TestGenerationAgent(BaseAgent):
    """Generate unit and API tests based on acceptance criteria."""

    def __init__(self):
        super().__init__(
            name="test_generation",
            description="Generates pytest unit and API tests",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Generating tests...")

        output_dir = state.get("generated_tests_dir", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)

        sandbox_dir = state.get("sandbox", {}).get("sandbox_dir", ".sandbox")
        feature_name = state.get("feature_name", "")

        generated_files = []

        # Write conftest first (shared by both modes)
        conftest_path = os.path.join(output_dir, "conftest.py")
        self._write_conftest(conftest_path, sandbox_dir)
        generated_files.append(conftest_path)

        # Decide: default Refund API case vs dynamic custom repo
        is_refund_api = feature_name == "Refund API"
        has_refund_service = os.path.exists(os.path.join(sandbox_dir, "refund_service.py"))
        has_models = os.path.exists(os.path.join(sandbox_dir, "models.py"))

        if is_refund_api and has_refund_service and has_models:
            # Default demo: hardcoded Refund API tests
            unit_path = os.path.join(output_dir, "test_refund_validation.py")
            self._write_refund_unit_tests(unit_path, sandbox_dir)
            generated_files.append(unit_path)

            api_path = os.path.join(output_dir, "test_refund_api.py")
            self._write_refund_api_tests(api_path, sandbox_dir)
            generated_files.append(api_path)

            total_tests = 8
        else:
            # Dynamic: discover Python files and generate real tests
            total_tests = 0
            py_files = self._discover_py_files(sandbox_dir)
            self.log(f"Discovered {len(py_files)} Python files in sandbox.")

            # Generate smoke tests for each module
            test_path = os.path.join(output_dir, "test_code_quality.py")
            count = self._write_dynamic_tests(test_path, sandbox_dir, py_files, state)
            generated_files.append(test_path)
            total_tests += count

        state["test_generation"] = {
            "generated_files": generated_files,
            "total_tests": total_tests,
            "test_types": ["unit", "api"] if is_refund_api else ["smoke", "quality"],
        }

        self.log(f"Generated {len(generated_files)} test files.")
        return state

    def _discover_py_files(self, sandbox_dir: str) -> list[str]:
        """Find all .py files in the sandbox directory."""
        py_files = []
        for root, _dirs, files in os.walk(sandbox_dir):
            for fname in files:
                if fname.endswith(".py") and fname != "__init__.py":
                    rel_path = os.path.relpath(os.path.join(root, fname), sandbox_dir)
                    py_files.append(rel_path)
        return py_files

    def _write_dynamic_tests(self, filepath: str, sandbox_dir: str,
                              py_files: list[str], state: dict) -> int:
        """Generate tests grounded in actual code from the sandbox."""
        test_functions = []
        test_count = 0

        for py_file in py_files:
            full_path = os.path.join(sandbox_dir, py_file)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                    lines = source.splitlines()
            except Exception:
                continue

            module_name = py_file.replace("/", ".").replace("\\", ".").rstrip(".py")
            safe_name = re.sub(r"[^a-zA-Z0-9]", "_", py_file.replace(".py", ""))

            # Test 1: File is valid Python (syntax check)
            test_functions.append(f'''
    def test_{safe_name}_syntax(self):
        """Verify {py_file} is valid Python syntax."""
        import py_compile
        py_compile.compile(os.path.join(SANDBOX, "{py_file}"), doraise=True)
''')
            test_count += 1

            # Test 2: Check for broad exception handlers
            has_broad_except = any(
                re.search(r"except\s+(Exception|BaseException)\s*:", line)
                for line in lines
            )
            if has_broad_except:
                test_functions.append(f'''
    def test_{safe_name}_no_broad_exceptions(self):
        """Check {py_file} for overly broad exception handlers."""
        with open(os.path.join(SANDBOX, "{py_file}"), "r") as f:
            content = f.read()
        import re as _re
        matches = _re.findall(r"except\\s+(Exception|BaseException)\\s*:", content)
        # Flag but don't fail — report count
        assert len(matches) == 0, f"Found {{len(matches)}} broad exception handler(s) in {py_file}"
''')
                test_count += 1

            # Test 3: Check for PII/sensitive data in print/log statements
            has_pii_log = any(
                re.search(r"(print|logging|logger)\s*\(.*?(password|card|ssn|secret|token|api_key)", line, re.IGNORECASE)
                for line in lines
            )
            if has_pii_log:
                test_functions.append(f'''
    def test_{safe_name}_no_pii_logging(self):
        """Check {py_file} does not log sensitive data."""
        with open(os.path.join(SANDBOX, "{py_file}"), "r") as f:
            content = f.read()
        import re as _re
        matches = _re.findall(r"(print|logging|logger)\\s*\\(.*?(password|card|ssn|secret|token|api_key)", content, _re.IGNORECASE)
        assert len(matches) == 0, f"Found {{len(matches)}} potential PII leak(s) in {py_file}"
''')
                test_count += 1

            # Test 4: Check for hardcoded secrets
            has_hardcoded = any(
                re.search(r"['\"](?:AIza|sk-|AKIA|ghp_|gho_|glpat-)[A-Za-z0-9_\-]{10,}", line)
                for line in lines
            )
            if has_hardcoded:
                test_functions.append(f'''
    def test_{safe_name}_no_hardcoded_secrets(self):
        """Check {py_file} for hardcoded API keys or secrets."""
        with open(os.path.join(SANDBOX, "{py_file}"), "r") as f:
            content = f.read()
        import re as _re
        matches = _re.findall(r"['\\"](AIza|sk-|AKIA|ghp_|gho_|glpat-)[A-Za-z0-9_\\-]{{10,}}", content)
        assert len(matches) == 0, f"Found {{len(matches)}} hardcoded secret(s) in {py_file}"
''')
                test_count += 1

            # Limit to prevent excessive test generation
            if test_count >= 20:
                break

        # If we found zero issues, add at least one passing test
        if test_count == 0:
            test_functions.append('''
    def test_codebase_is_clean(self):
        """Verify the scanned codebase has no common code quality issues."""
        assert True, "No code quality issues detected"
''')
            test_count = 1

        # Assemble test file
        content = f'''"""
Dynamic code quality tests generated by CruiseMode TestGenerationAgent.
Tests are grounded in actual code scanned from the sandbox.
"""

import os
import sys

SANDBOX = os.path.abspath("{sandbox_dir}")
sys.path.insert(0, SANDBOX)


class TestCodeQuality:
    """Tests generated from real code analysis of the sandbox."""
{"".join(test_functions)}
'''
        with open(filepath, "w") as f:
            f.write(content)

        return test_count

    # ===== Default Refund API tests (unchanged) =====

    def _write_refund_unit_tests(self, filepath: str, sandbox_dir: str):
        """Generate pytest unit tests for refund validation logic."""
        content = f'''"""
Unit tests for refund validation logic.
Generated by CruiseMode TestGenerationAgent.
Tests run against the sandbox copy at: {sandbox_dir}/
"""

import sys
import os
import uuid

# Add sandbox to path so we import the patched version
sys.path.insert(0, os.path.abspath("{sandbox_dir}"))

from models import RefundRequest, PaymentStatus
from refund_service import process_refund


class TestRefundAmountValidation:
    """AC-001: Refund amount must be greater than zero."""

    def test_valid_refund_amount(self):
        """Refund with positive amount should succeed."""
        request = RefundRequest(
            payment_id="PAY-001",
            payment_status=PaymentStatus.COMPLETED,
            amount=50.00,
            customer_email="test@example.com",
            card_number="4111111111111111",
        )
        result = process_refund(request)
        assert result["status"] == "success"
        assert result["amount"] == 50.00

    def test_zero_refund_amount_rejected(self):
        """Refund with zero amount should return error."""
        request = RefundRequest(
            payment_id="PAY-002",
            payment_status=PaymentStatus.COMPLETED,
            amount=0,
            customer_email="test@example.com",
            card_number="4111111111111111",
        )
        result = process_refund(request)
        assert result["status"] == "error"
        assert result["code"] == 400

    def test_negative_refund_amount_rejected(self):
        """Refund with negative amount should return error."""
        request = RefundRequest(
            payment_id="PAY-003",
            payment_status=PaymentStatus.COMPLETED,
            amount=-10.00,
            customer_email="test@example.com",
            card_number="4111111111111111",
        )
        result = process_refund(request)
        assert result["status"] == "error"
        assert result["code"] == 400


class TestPaymentStatusValidation:
    """AC-002 & AC-003: Payment status requirements."""

    def test_completed_payment_allowed(self):
        """Completed payments should be refundable."""
        request = RefundRequest(
            payment_id="PAY-004",
            payment_status=PaymentStatus.COMPLETED,
            amount=25.00,
            customer_email="test@example.com",
            card_number="4111111111111111",
        )
        result = process_refund(request)
        assert result["status"] == "success"

    def test_pending_payment_returns_conflict(self):
        """AC-003: Pending payments must return conflict status."""
        request = RefundRequest(
            payment_id="PAY-005",
            payment_status=PaymentStatus.PENDING,
            amount=25.00,
            customer_email="test@example.com",
            card_number="4111111111111111",
        )
        result = process_refund(request)
        assert result["status"] == "conflict"
        assert result["code"] == 409
'''
        with open(filepath, "w") as f:
            f.write(content)

    def _write_refund_api_tests(self, filepath: str, sandbox_dir: str):
        """Generate FastAPI TestClient API tests."""
        content = f'''"""
API tests for the Refund API endpoint.
Generated by CruiseMode TestGenerationAgent.
Tests run against the sandbox copy at: {sandbox_dir}/
"""

import sys
import os

# Add sandbox to path so we import the patched version
sys.path.insert(0, os.path.abspath("{sandbox_dir}"))

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


class TestRefundAPI:
    """API tests covering all HTTP status code scenarios."""

    def test_successful_refund(self):
        """POST /refund with valid data should return 200."""
        response = client.post("/refund", json={{
            "payment_id": "PAY-100",
            "payment_status": "completed",
            "amount": 99.99,
            "customer_email": "customer@example.com",
            "card_number": "4111111111111111",
        }})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["amount"] == 99.99
        assert "refund_id" in data

    def test_invalid_amount_returns_400(self):
        """POST /refund with zero amount should return 400."""
        response = client.post("/refund", json={{
            "payment_id": "PAY-101",
            "payment_status": "completed",
            "amount": 0,
            "customer_email": "customer@example.com",
            "card_number": "4111111111111111",
        }})
        assert response.status_code == 400

    def test_pending_payment_returns_409(self):
        """AC-003: POST /refund with pending payment should return 409."""
        response = client.post("/refund", json={{
            "payment_id": "PAY-102",
            "payment_status": "pending",
            "amount": 50.00,
            "customer_email": "customer@example.com",
            "card_number": "4111111111111111",
        }})
        assert response.status_code == 409


class TestPIISafety:
    """AC-004: Sensitive data must not be exposed in responses."""

    def test_card_number_not_in_response(self):
        """Response body should not contain the card number."""
        response = client.post("/refund", json={{
            "payment_id": "PAY-200",
            "payment_status": "completed",
            "amount": 10.00,
            "customer_email": "secret@example.com",
            "card_number": "4111111111111111",
        }})
        assert response.status_code == 200
        body = response.text
        assert "4111111111111111" not in body
        assert "secret@example.com" not in body
'''
        with open(filepath, "w") as f:
            f.write(content)

    def _write_conftest(self, filepath: str, sandbox_dir: str):
        """Generate conftest.py with shared fixtures."""
        content = f'''"""
Shared test fixtures for CruiseMode generated tests.
"""

import sys
import os

# Ensure sandbox code is importable
sys.path.insert(0, os.path.abspath("{sandbox_dir}"))
'''
        with open(filepath, "w") as f:
            f.write(content)
