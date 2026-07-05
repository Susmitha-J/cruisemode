from __future__ import annotations

"""
Gemini client for CruiseMode.

Provides a wrapper for Google Gemini API calls. Falls back to deterministic
mock responses when no API key is configured, so the demo works offline.

# TODO: Replace mock responses with real Gemini API calls when GOOGLE_API_KEY
#       or GEMINI_API_KEY is configured. Future integration with:
#       - google-genai SDK
#       - Vertex AI Gemini endpoint
#       - RAPIDS-powered batch inference
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("cruisemode.gemini")


class GeminiClient:
    """
    Wrapper for Gemini LLM API.

    If no API key is configured, returns deterministic mock responses
    so the local demo runs without external dependencies.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._enabled = bool(self.api_key)

        if self._enabled:
            logger.info("Gemini client initialized with API key.")
            # TODO: Initialize google-genai client here
            # from google import genai
            # self.client = genai.Client(api_key=self.api_key)
        else:
            logger.info("Gemini client running in MOCK mode (no API key configured).")

    @property
    def is_enabled(self) -> bool:
        """Whether real Gemini API calls are enabled."""
        return self._enabled

    def generate_text(self, prompt: str) -> str:
        """
        Generate text from a prompt using Gemini or mock fallback.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            Generated text response.
        """
        if self._enabled:
            return self._call_gemini(prompt)
        return self._mock_response(prompt)

    def _call_gemini(self, prompt: str) -> str:
        """
        Call the real Gemini API.

        # TODO: Implement actual Gemini API call:
        # response = self.client.models.generate_content(
        #     model=self.model,
        #     contents=prompt,
        # )
        # return response.text
        """
        logger.warning("Real Gemini API call not yet implemented. Using mock.")
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Return a deterministic mock response based on prompt keywords.

        This ensures the demo works fully offline without an API key.
        """
        prompt_lower = prompt.lower()

        if "acceptance criteria" in prompt_lower:
            return "Parsed 5 acceptance criteria from the input file."
        elif "scan" in prompt_lower or "analysis" in prompt_lower:
            return "Analyzed 12 findings across 4 scan reports. 9 auto-patchable, 3 require review."
        elif "patch" in prompt_lower:
            return "Applied 3 safe patches: PII masking, exception narrowing, code smell annotation."
        elif "oss" in prompt_lower or "dependency" in prompt_lower:
            return "1 CRITICAL OSS vulnerability found (pyjwt CVE-2022-29217). Human approval required."
        elif "test" in prompt_lower:
            return "Generated 8 tests (5 unit, 3 API) covering all acceptance criteria."
        elif "validation" in prompt_lower:
            return "All 8 tests passed. Local validation successful."
        elif "report" in prompt_lower or "pr" in prompt_lower:
            return "PR report generated. Recommendation: REVIEW_NEEDED (critical OSS finding)."
        else:
            return f"[Mock Gemini response for: {prompt[:50]}...]"
