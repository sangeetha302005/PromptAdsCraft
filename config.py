"""
config.py
---------
Centralized configuration for PromptAdsCraft AI.
Reads settings from environment variables and provides defaults.
Never exposes secrets in logs or error messages.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists (development convenience)
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
EXAMPLES_DIR = BASE_DIR / "examples"

# ---------------------------------------------------------------------------
# AI Provider
# ---------------------------------------------------------------------------

def get_api_key() -> str | None:
    """Return OpenAI API key from session state, environment, or Streamlit secrets. Never log the value."""
    try:
        import streamlit as st
        # 1. Check session state (user entered via Settings page)
        sess_key = st.session_state.get("custom_api_key", "").strip()
        if sess_key:
            return sess_key
        # 2. Check Streamlit secrets
        secret_key = st.secrets.get("OPENAI_API_KEY", "").strip()
        if secret_key:
            return secret_key
    except Exception:
        pass

    # 3. Check environment variable (.env)
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    return None


OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

CAMPAIGN_STORAGE_PATH: str = os.getenv("CAMPAIGN_STORAGE_PATH", "campaigns.json")

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

APP_NAME = "PromptAdsCraft AI"
APP_TAGLINE = "Craft smarter prompts. Create better ads."
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Content limits
# ---------------------------------------------------------------------------

MAX_BRAND_NAME_LEN = 100
MAX_PRODUCT_NAME_LEN = 150
MAX_DESCRIPTION_LEN = 1000
MAX_AUDIENCE_LEN = 300
MAX_BENEFITS_LEN = 800
MAX_PAIN_POINTS_LEN = 500
MAX_AVOID_WORDS_LEN = 300
MAX_OFFER_LEN = 200

MIN_HOOKS = 3
MAX_HOOKS = 10

SUPPORTED_PLATFORMS = ["Instagram Reels", "YouTube Shorts", "Paid Social Ads"]
SUPPORTED_TONES = ["Friendly", "Humorous", "Professional", "Educational", "Energetic", "Premium"]
SUPPORTED_DURATIONS = [15, 30, 60]
SUPPORTED_OBJECTIVES = [
    "Product Awareness",
    "Lead Generation",
    "Direct Sales",
    "App Downloads",
    "Website Traffic",
    "Brand Engagement",
]
