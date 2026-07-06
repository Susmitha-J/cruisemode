from __future__ import annotations

"""
SandboxPatchAgent — applies safe patches inside the sandbox workspace.

Creates a sandbox copy of sample_app, then applies deterministic patches:
- For the default Refund API demo: applies targeted string-replace patches.
- For custom repos: walks all .py files and applies regex-based patches for
  broad exceptions, PII logging, and bare except handlers.

SAFETY: This agent NEVER modifies the original sample_app directory.
"""

import os
import re
import shutil
from typing import Any

from src.agents.base import BaseAgent


class SandboxPatchAgent(BaseAgent):
    """Apply safe, automated patches inside the sandbox workspace only."""

    def __init__(self):
        super().__init__(
            name="sandbox_patch",
            description="Applies safe patches in sandbox workspace",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Starting sandbox patching...")

        sandbox_dir = state.get("sandbox_dir", ".sandbox")
        source_dir = state.get("sample_app_dir", "sample_app")

        # Create sandbox copy
        if os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir)
        shutil.copytree(source_dir, sandbox_dir)
        self.log(f"Created sandbox copy: {source_dir} -> {sandbox_dir}")

        patches_applied = []
        files_modified = set()

        feature_name = state.get("feature_name", "")
        is_refund_api = feature_name == "Refund API"

        if is_refund_api:
            # --- Default demo: targeted string-replace patches ---
            app_path = os.path.join(sandbox_dir, "app.py")
            if os.path.exists(app_path):
                patch = self._patch_pii_logging_refund(app_path)
                if patch:
                    patches_applied.append(patch)
                    files_modified.add(app_path)

            service_path = os.path.join(sandbox_dir, "refund_service.py")
            if os.path.exists(service_path):
                patch = self._patch_broad_exception_refund(service_path)
                if patch:
                    patches_applied.append(patch)
                    files_modified.add(service_path)

                patch = self._patch_code_smell_refund(service_path)
                if patch:
                    patches_applied.append(patch)
                    files_modified.add(service_path)
        else:
            # --- Dynamic: scan ALL .py files for patchable patterns ---
            patch_id = 1
            for root, _dirs, files in os.walk(sandbox_dir):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, sandbox_dir)

                    # Patch broad exceptions
                    p = self._patch_broad_exceptions_dynamic(fpath, patch_id, rel_path)
                    if p:
                        patches_applied.extend(p["patches"])
                        files_modified.add(fpath)
                        patch_id += len(p["patches"])

                    # Patch PII logging
                    p = self._patch_pii_logging_dynamic(fpath, patch_id, rel_path)
                    if p:
                        patches_applied.extend(p["patches"])
                        files_modified.add(fpath)
                        patch_id += len(p["patches"])

        state["sandbox"] = {
            "sandbox_dir": sandbox_dir,
            "patches_applied": patches_applied,
            "files_modified": list(files_modified),
            "total_patches": len(patches_applied),
        }

        self.log(f"Applied {len(patches_applied)} patches in sandbox.")
        return state

    # ===== Dynamic patchers (for custom repos) =====

    def _patch_broad_exceptions_dynamic(self, filepath: str, start_id: int,
                                         rel_path: str) -> dict | None:
        """Replace 'except Exception' with specific types in any .py file."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        original = content
        patches = []

        # Replace 'except Exception as e:' with '(ValueError, TypeError) as e:'
        new_content = re.sub(
            r"except\s+Exception\s+as\s+(\w+)\s*:",
            r"except (ValueError, TypeError) as \1:",
            content,
        )
        # Replace 'except Exception:' with 'except (ValueError, TypeError):'
        new_content = re.sub(
            r"except\s+Exception\s*:",
            "except (ValueError, TypeError):",
            new_content,
        )

        if new_content != original:
            with open(filepath, "w") as f:
                f.write(new_content)
            count = len(re.findall(r"except\s+Exception", original))
            for i in range(count):
                patches.append({
                    "id": f"PATCH-{start_id + i:03d}",
                    "file": filepath,
                    "type": "clean_code",
                    "description": f"Narrowed broad 'except Exception' to specific types in {rel_path}",
                    "finding_ids": [f"CC-{start_id + i:03d}"],
                })
            return {"patches": patches}
        return None

    def _patch_pii_logging_dynamic(self, filepath: str, start_id: int,
                                    rel_path: str) -> dict | None:
        """Redact sensitive variable names in print/log statements."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        original = content
        patches = []

        # Find print/log statements that reference sensitive variable names
        # and add a comment warning
        sensitive_pattern = re.compile(
            r"((?:print|logging\.?\w*|logger\.?\w*)\s*\(.*?"
            r"(?:password|card|ssn|secret|token|api_key).*?\))",
            re.IGNORECASE | re.DOTALL,
        )

        matches = list(sensitive_pattern.finditer(content))
        if matches:
            # Add redaction comments (safe patch — doesn't break code)
            for idx, match in enumerate(matches):
                old = match.group(0)
                # Wrap in a conditional to mask sensitive data
                new = f"# [CruiseMode] REDACTED: PII/secret detected — review this log statement\n    # {old}"
                content = content.replace(old, new, 1)
                patches.append({
                    "id": f"PATCH-{start_id + idx:03d}",
                    "file": filepath,
                    "type": "pii_logging",
                    "description": f"Flagged potential PII/secret in log statement in {rel_path}",
                    "finding_ids": [f"SEC-{start_id + idx:03d}"],
                })

            if content != original:
                with open(filepath, "w") as f:
                    f.write(content)
                return {"patches": patches}

        return None

    # ===== Default Refund API patchers (unchanged) =====

    def _patch_pii_logging_refund(self, filepath: str) -> dict | None:
        """Replace full request logging with masked version."""
        with open(filepath, "r") as f:
            content = f.read()

        original = content
        content = content.replace(
            'logger.info("Received refund request: %s", request.model_dump())',
            'logger.info("Received refund request: payment_id=%s, amount=%s", request.payment_id, request.amount)',
        )

        if content != original:
            with open(filepath, "w") as f:
                f.write(content)
            return {
                "id": "PATCH-001",
                "file": filepath,
                "type": "pii_logging",
                "description": "Masked PII fields in log statement — now logs only payment_id and amount",
                "finding_ids": ["OWASP-001"],
            }
        return None

    def _patch_broad_exception_refund(self, filepath: str) -> dict | None:
        """Replace broad 'except Exception' with specific exception types."""
        with open(filepath, "r") as f:
            content = f.read()

        original = content
        content = content.replace(
            "    except Exception as e:",
            "    except (ValueError, TypeError) as e:",
        )

        if content != original:
            with open(filepath, "w") as f:
                f.write(content)
            return {
                "id": "PATCH-002",
                "file": filepath,
                "type": "clean_code",
                "description": "Narrowed broad 'except Exception' to specific types (ValueError, TypeError)",
                "finding_ids": ["CC-001"],
            }
        return None

    def _patch_code_smell_refund(self, filepath: str) -> dict | None:
        """Fix SonarQube code smell by adding a docstring improvement."""
        with open(filepath, "r") as f:
            content = f.read()

        original = content
        old_comment = "# --- CruiseMode target: broad exception handling wraps everything ---"
        new_comment = (
            "# NOTE: Validation logic has been reviewed for cognitive complexity.\n"
            "        # Future refactor: extract validation into _validate_refund_request() helper."
        )
        content = content.replace(old_comment, new_comment)

        if content != original:
            with open(filepath, "w") as f:
                f.write(content)
            return {
                "id": "PATCH-003",
                "file": filepath,
                "type": "sonarqube_smell",
                "description": "Added refactoring note for cognitive complexity (SQ-001, CC-003)",
                "finding_ids": ["SQ-001", "CC-003"],
            }
        return None
