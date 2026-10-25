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
    Dual-Engine AI client supporting:
    1. Google Gemini API (gemini-1.5-flash) - generous free tier
    2. OpenAI Chat Completions API (gpt-4o-mini, gpt-4o, etc.)
    3. Safe fallback handling so the UI never crashes
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        timeout: int = 30,
        gemini_api_key: Optional[str] = None,
        provider: str = "auto",
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._api_key = api_key.strip() if api_key else None
        self._gemini_api_key = gemini_api_key.strip() if gemini_api_key else None
        self.provider = provider
        self._client = None

        if self.active_provider == "openai" and self._api_key:
            self._init_client()

    @property
    def active_provider(self) -> str:
        """Resolve active AI provider: 'gemini' or 'openai'."""
        if self.provider == "gemini":
            return "gemini"
        if self.provider == "openai":
            return "openai"
        # Auto-detection
        if self._gemini_api_key and not self._api_key:
            return "gemini"
        if self._api_key and self._api_key.startswith("AIza"):
            return "gemini"
        return "openai"

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
        """True when no valid external API key is configured."""
        if self.active_provider == "gemini":
            key = self._gemini_api_key or self._api_key
            return not bool(key and not key.startswith("sk-proj-your"))
        return not bool(self._api_key)

    def set_api_key(self, api_key: Optional[str]) -> None:
        """Dynamically update the API key and reinitialize client."""
        self._api_key = api_key.strip() if api_key else None
        self._client = None
        if self.active_provider == "openai" and self._api_key:
            self._init_client()

    def set_gemini_api_key(self, key: Optional[str]) -> None:
        """Set or update Google Gemini API key."""
        self._gemini_api_key = key.strip() if key else None

    def set_model(self, model: str) -> None:
        """Update model name (e.g. gpt-4o-mini, gemini-1.5-flash, etc.)."""
        self.model = model

    def test_connection(self) -> tuple[bool, str]:
        """
        Safely test API connectivity and credential validity for the active provider.
        Returns (success: bool, message: str).
        """
        if self.is_demo_mode:
            return False, "No external API key is currently configured. The app runs in Demo Mode on the built-in Multi-Variable Synthesis Engine."

        if self.active_provider == "gemini":
            import requests
            key = self._gemini_api_key or self._api_key
            if not key:
                return False, "No Gemini API key configured."
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash?key={key}"
                resp = requests.get(endpoint, timeout=10)
                if resp.status_code == 200:
                    return True, "Connection verified successfully! Google Gemini 1.5 Flash API is active and ready."
                elif resp.status_code in (400, 401, 403):
                    return False, "API key rejected: Google Gemini authentication failed. Check your API key."
                elif resp.status_code == 429:
                    return False, "Quota exceeded: Gemini API rate limit or project quota reached."
                return False, f"Gemini API returned HTTP status {resp.status_code}."
            except Exception as exc:
                return False, f"Connection timeout: Unable to reach Google Gemini servers ({str(exc)})."

        # OpenAI testing
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

    def generate_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Send generation request to Google Gemini API (gemini-1.5-flash)."""
        import requests
        key = self._gemini_api_key or self._api_key
        if not key:
            raise DemoModeActive("No Google Gemini API key configured.")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        combined_prompt = (
            f"SYSTEM INSTRUCTION:\n{system_prompt}\n\n"
            f"USER TASK:\n{user_prompt}\n\n"
            "CRITICAL: Return ONLY a valid JSON object matching the requested schema. No surrounding markdown backticks or commentary."
        )
        payload = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json",
            },
        }
        try:
            resp = requests.post(endpoint, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                if text:
                    return text
                raise AIServiceError("Google Gemini returned an empty response. Please retry.")
            elif resp.status_code in (400, 401, 403):
                raise AIServiceError("Gemini API authentication failed. Check your API key in Settings.")
            elif resp.status_code == 429:
                raise AIServiceError("Gemini API rate limit or project quota reached. Please wait a moment.")
            else:
                raise AIServiceError(f"Gemini API error (HTTP {resp.status_code}).")
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(f"Gemini connection failure ({type(exc).__name__}): {str(exc)}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request and return the response text.
        Routes to Google Gemini or OpenAI based on configuration.
        Raises AIServiceError for API failures.
        Raises DemoModeActive if no API key is set.
        """
        if self.is_demo_mode:
            raise DemoModeActive("No API key configured. Demo Mode is active.")

        if self.active_provider == "gemini":
            return self.generate_gemini(system_prompt, user_prompt)

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
