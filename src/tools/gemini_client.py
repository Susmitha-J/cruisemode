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
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self._enabled = bool(self.api_key)
        self.client = None

        if self._enabled:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                logger.info(f"Gemini client initialized with model: {self.model}")
            except ImportError:
                logger.warning("google-generativeai package not installed. Running in mock mode.")
                self._enabled = False
        else:
            logger.info("Gemini client running in MOCK mode (no API key configured).")

    @property
    def is_enabled(self) -> bool:
        """Whether real Gemini API calls are enabled."""
        return self._enabled

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        """
        Generate text from a prompt using Gemini or mock fallback.

        Args:
            prompt: The text prompt to send to the model.
            system_instruction: Optional system instruction for grounding / hallucination prevention.

        Returns:
            Generated text response.
        """
        if self._enabled and self.client:
            return self._call_gemini(prompt, system_instruction)
        return self._mock_response(prompt)

    def _call_gemini(self, prompt: str, system_instruction: str | None = None) -> str:
        """Call the real Gemini API with a try-except fallback."""
        try:
            import google.generativeai as genai
            if system_instruction:
                model = genai.GenerativeModel(self.model, system_instruction=system_instruction)
            else:
                model = self.client
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}. Falling back to mock.")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Return a deterministic mock response based on prompt keywords.
        Supports conversational chatbot questions for the hackathon demo.
        """
        prompt_lower = prompt.lower()

        # Conversational questions
        if "pii" in prompt_lower or "logging" in prompt_lower:
            return (
                "The PII logging issue in `sample_app/app.py` was successfully patched in the sandbox. "
                "The original code logged the full request including the user's email and card number, "
                "which has been masked to log only the safe `payment_id` and `amount`."
            )
        elif "broad exception" in prompt_lower or "narrow" in prompt_lower or "except exception" in prompt_lower:
            return (
                "Broad exception blocks (`except Exception:`) catch all errors indiscriminately, masking "
                "unexpected bugs, system interrupts, and syntax errors, which makes debugging extremely difficult. "
                "The patch narrowed the exception to specific expected types like `(ValueError, TypeError)` "
                "so unexpected failures propagate correctly."
            )
        elif "complex" in prompt_lower or "complexity" in prompt_lower or "cognitive" in prompt_lower:
            return (
                "Cognitive complexity measures how difficult the control flow of a function is to understand. "
                "Functions with high nesting and multiple branches are prone to errors and hard to test. "
                "The patch added a clean code annotation/refactoring note to address this complexity during the next code review cycle."
            )
        elif "jenkins" in prompt_lower or "trigger" in prompt_lower or "proceed" in prompt_lower:
            return (
                "Yes, local validation has passed, meaning it is safe to hand off to the Jenkins pipeline. "
                "However, the developer should review the logged OSS alerts and verify the dependency upgrade manually."
            )
        elif "why did cruisemode not patch oss" in prompt_lower or "not patch oss" in prompt_lower:
            return (
                "CruiseMode does not auto-patch OSS dependencies because dependency upgrades require regression testing, "
                "compatibility review, and downstream security validation."
            )
        elif "why is the status ready_with_alerts" in prompt_lower or "ready_with_alerts" in prompt_lower or "status" in prompt_lower:
            return (
                "The final status is `READY_WITH_ALERTS` because all local pytest runs passed (9/9 passed) and "
                "3 safe sandbox patches were successfully applied, but a CRITICAL OSS dependency alert exists "
                "(pyjwt@2.3.0 / CVE-2022-29217). Dependency upgrades require manual testing and downstream verification."
            )
        elif "review before pr" in prompt_lower or "should i review" in prompt_lower or "should the developer review" in prompt_lower:
            return (
                "Before submitting the PR, you should review the side-by-side git diff of the sandbox patches "
                "(PII log masking, broad exception narrowing, and SonarQube complexity annotations) and the critical OSS advisory alert for `pyjwt`."
            )
        elif "hello" in prompt_lower or "hi " in prompt_lower or "hey" in prompt_lower:
            return (
                "Hello! I am your CruiseMode AI Advisor. I can help explain the code patches applied in "
                "the sandbox workspace, discuss the scan findings, or provide recommendations for your Jenkins build."
            )

        # Keyword mapping for agent runs
        elif "acceptance criteria" in prompt_lower:
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
            return "PR report generated. Recommendation: READY_WITH_ALERTS (critical OSS alerts present)."
        else:
            return "The current run artifacts do not contain enough information."

