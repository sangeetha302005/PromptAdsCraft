"""
ai_service.py
-------------
OpenAI API integration for PromptAdsCraft AI.

Design principles:
- API key is never logged or exposed in error messages.
- Model name and settings are configurable via environment variables.
- All API errors surface as typed exceptions with user-friendly messages.
- JSON responses are validated before use; malformed responses are flagged.
- Demo Mode provides deterministic sample output when no API key is set.
"""

from __future__ import annotations
import json
import os
import time
from typing import Any, Optional


class AIServiceError(Exception):
    """Raised for AI provider errors that the UI should surface."""
    pass


class DemoModeActive(Exception):
    """Raised when Demo Mode is active (no API key configured)."""
    pass


class AIService:
    """
    Wrapper around the OpenAI Chat Completions API.
    Separates provider logic from the UI and generation layers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        timeout: int = 30,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._api_key = api_key
        self._client = None

        if self._api_key:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize the OpenAI client. Errors do not expose the key."""
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                timeout=self.timeout,
            )
        except ImportError:
            raise AIServiceError(
                "The 'openai' package is not installed. Run: pip install openai"
            )
        except Exception as exc:
            raise AIServiceError(
                f"Failed to initialize AI client: {type(exc).__name__}"
            )

    @property
    def is_demo_mode(self) -> bool:
        """True when no API key is configured."""
        return not bool(self._api_key)

    def set_api_key(self, api_key: Optional[str]) -> None:
        """Dynamically update the API key and reinitialize client."""
        self._api_key = api_key.strip() if api_key else None
        self._client = None
        if self._api_key:
            self._init_client()

    def set_model(self, model: str) -> None:
        """Update model name (e.g. gpt-4o-mini, gpt-4o, etc.)."""
        self.model = model

    def test_connection(self) -> tuple[bool, str]:
        """
        Safely test OpenAI API connectivity and credential validity.
        Returns (success: bool, message: str).
        """
        if self.is_demo_mode:
            return False, "No OpenAI API key is currently configured. The app is in Demo Mode."
        try:
            if self._client is None:
                self._init_client()
            # Perform a lightweight models list call to test credentials without token charge
            self._client.models.list()
            return True, f"Connection verified successfully! OpenAI API is active and ready using model '{self.model}'."
        except Exception as exc:
            err_str = str(exc).lower()
            if "auth" in err_str or "api_key" in err_str or "api key" in err_str or "invalid" in err_str or "incorrect" in err_str or "unauthorized" in err_str:
                return False, "API key rejected: Authentication failed. Please check that your key starts with 'sk-' and is active."
            elif "quota" in err_str or "billing" in err_str:
                return False, "Quota exceeded: Your OpenAI account has exceeded its quota or has no active payment method/credits."
            elif "rate" in err_str:
                return False, "Rate limit reached: Too many requests sent in a short window. Please wait a moment."
            elif "timeout" in err_str or "connect" in err_str:
                return False, "Connection timeout: Unable to reach OpenAI servers. Please check your network connection."
            return False, f"Connection test failed ({type(exc).__name__}): {str(exc)}"

    def get_status_details(self) -> dict:
        """
        Return structured status dictionary with exact status categories:
        'Connected', 'Missing API Key', 'Invalid Key', 'Quota/Billing Issue', or 'Connection Error'.
        """
        if self.is_demo_mode:
            return {
                "status": "Missing API Key",
                "status_code": "MISSING_KEY",
                "connected": False,
                "badge": "badge-amber",
                "message": "No OpenAI API key is configured. The app runs in Demo Mode.",
            }

        ok, msg = self.test_connection()
        if ok:
            return {
                "status": "Connected",
                "status_code": "CONNECTED",
                "connected": True,
                "badge": "badge-emerald",
                "message": msg,
            }

        msg_lower = msg.lower()
        if "rejected" in msg_lower or "authentication" in msg_lower or "auth" in msg_lower or "invalid" in msg_lower:
            status_label = "Invalid Key"
            code = "INVALID_KEY"
            badge = "badge-rose"
        elif "quota" in msg_lower or "billing" in msg_lower:
            status_label = "Quota/Billing Issue"
            code = "QUOTA_EXCEEDED"
            badge = "badge-rose"
        elif "rate limit" in msg_lower:
            status_label = "Rate Limited"
            code = "RATE_LIMITED"
            badge = "badge-amber"
        elif "timeout" in msg_lower or "reach" in msg_lower or "connection" in msg_lower:
            status_label = "Connection Error"
            code = "CONNECTION_ERROR"
            badge = "badge-rose"
        else:
            status_label = "Connection Error"
            code = "CONNECTION_ERROR"
            badge = "badge-rose"

        return {
            "status": status_label,
            "status_code": code,
            "connected": False,
            "badge": badge,
            "message": msg,
        }

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request and return the response text.
        Raises AIServiceError for API failures.
        Raises DemoModeActive if no API key is set.
        """
        if self.is_demo_mode:
            raise DemoModeActive("No API key configured. Demo Mode is active.")

        if self._client is None:
            self._init_client()

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            content = response.choices[0].message.content
            if not content:
                raise AIServiceError("AI returned an empty response. Please retry.")
            return content

        except DemoModeActive:
            raise
        except AIServiceError:
            raise
        except Exception as exc:
            error_type = type(exc).__name__
            error_str = str(exc).lower()

            if "rate" in error_str or "ratelimit" in error_str:
                raise AIServiceError(
                    "Rate limit reached. Wait a moment and try again."
                )
            elif "auth" in error_str or "api_key" in error_str or "invalid" in error_str:
                raise AIServiceError(
                    "API authentication failed. Check your API key in settings."
                )
            elif "timeout" in error_str or "connect" in error_str:
                raise AIServiceError(
                    "Connection timeout. Check your internet connection and retry."
                )
            elif "quota" in error_str or "billing" in error_str:
                raise AIServiceError(
                    "API quota exceeded. Check your OpenAI account billing."
                )
            else:
                raise AIServiceError(
                    f"AI generation failed ({error_type}). Please retry."
                )

    def parse_json_response(self, response_text: str) -> dict:
        """
        Parse a JSON response from the AI.
        Returns the parsed dict or raises AIServiceError for malformed output.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            # Try to extract JSON from a text response
            import re
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            raise AIServiceError(
                "The AI returned an unexpected format. Please retry."
            ) from exc

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Convenience method: generate and parse JSON in one call.
        """
        raw = self.generate(system_prompt, user_prompt)
        return self.parse_json_response(raw)


def split_prompt(full_prompt: str) -> tuple[str, str]:
    """
    Split a template's SYSTEM: and USER: sections into separate strings
    suitable for passing to the OpenAI messages array.
    Skips comment lines.
    """
    lines = full_prompt.splitlines()
    system_lines: list[str] = []
    user_lines: list[str] = []
    current_section: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("SYSTEM:"):
            current_section = "system"
            rest = stripped[len("SYSTEM:"):].strip()
            if rest:
                system_lines.append(rest)
        elif stripped.startswith("USER:"):
            current_section = "user"
            rest = stripped[len("USER:"):].strip()
            if rest:
                user_lines.append(rest)
        else:
            if current_section == "system":
                system_lines.append(line)
            elif current_section == "user":
                user_lines.append(line)

    return "\n".join(system_lines).strip(), "\n".join(user_lines).strip()
