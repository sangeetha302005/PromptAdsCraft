"""
test_ai_service_and_generator.py
--------------------------------
Tests for AIService, ContentGenerator, Demo Mode, and malformed AI responses.
Uses mocking to ensure no real API keys or paid API calls are needed.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_service import AIService, AIServiceError, DemoModeActive, split_prompt
from src.content_generator import ContentGenerator, _build_demo_campaign

SAMPLE_INPUTS = {
    "brand_name": "TestBrand",
    "product_name": "TestProduct",
    "description": "A great test product for testing AI services and demo modes.",
    "target_audience": "Software engineers and QA testers",
    "objective": "Product Awareness",
    "platform": "Instagram Reels",
    "tone": "Friendly",
    "language": "English",
    "duration": 30,
    "num_hooks": 5,
    "benefits": "Lightweight. Fast. Reliable.",
    "offer": "",
    "pain_points": "Slow tests and brittle setups.",
    "avoid_words": "guaranteed, 100% cure",
}


def test_ai_service_demo_mode_when_no_key():
    """AIService should default to demo mode if no key provided."""
    service = AIService(api_key=None)
    assert service.is_demo_mode is True

    with pytest.raises(DemoModeActive):
        service.generate("System prompt", "User prompt")


def test_ai_service_with_key():
    """AIService is not in demo mode when an API key is provided."""
    with patch.object(AIService, "_init_client"):
        service = AIService(api_key="sk-test-key-12345")
        assert service.is_demo_mode is False


def test_ai_service_parse_json_valid():
    service = AIService(api_key=None)
    valid_json = '{"key": "value", "count": 42}'
    parsed = service.parse_json_response(valid_json)
    assert parsed == {"key": "value", "count": 42}


def test_ai_service_parse_json_embedded():
    service = AIService(api_key=None)
    embedded_json = 'Here is the response:\n{"key": "value"}\nHope this helps!'
    parsed = service.parse_json_response(embedded_json)
    assert parsed == {"key": "value"}


def test_ai_service_parse_json_malformed_raises_error():
    service = AIService(api_key=None)
    malformed = 'This is completely invalid JSON { not closed'
    with pytest.raises(AIServiceError) as exc_info:
        service.parse_json_response(malformed)
    assert "unexpected format" in str(exc_info.value).lower()


def test_split_prompt():
    prompt_text = """
# Header comment
# Another comment
SYSTEM:
You are an expert copywriter.
Keep it concise.

USER:
Write an ad for {brand_name}.
"""
    system, user = split_prompt(prompt_text)
    assert "You are an expert copywriter." in system
    assert "Keep it concise." in system
    assert "Write an ad for {brand_name}." in user
    assert "SYSTEM:" not in system
    assert "USER:" not in user
    assert "# Header" not in system
    assert "# Header" not in user


def test_content_generator_demo_mode():
    """ContentGenerator produces deterministic sample output in Demo Mode without API calls."""
    ai = AIService(api_key=None)
    generator = ContentGenerator(ai)
    
    progress_steps = []
    def on_progress(step, pct):
        progress_steps.append((step, pct))

    campaign = generator.generate_full_campaign(SAMPLE_INPUTS, progress_callback=on_progress)

    assert campaign["mode"] == "demo"
    assert "demo_notice" in campaign
    assert "DEMO MODE" in campaign["demo_notice"]
    assert len(campaign["hooks"]) == SAMPLE_INPUTS["num_hooks"]
    assert "scenes" in campaign["script"]
    assert "recommended_primary_cta" in campaign["ctas"]
    assert "instagram_reels" in campaign["platform_adaptation"]
    assert len(campaign["creative_angles"]) > 0
    assert "quality_review" in campaign
    assert campaign["quality_review"]["overall_score"] > 0
    assert len(progress_steps) > 0


def test_build_demo_campaign_direct():
    campaign = _build_demo_campaign(SAMPLE_INPUTS)
    assert campaign["mode"] == "demo"
    assert campaign["brief"]["summary"].startswith("[DEMO]")
    for hook in campaign["hooks"]:
        assert hook["hook_text"].startswith("[DEMO]")


def test_content_generator_live_mode_mocked():
    """ContentGenerator orchestrates live AI pipeline when api_key is present."""
    with patch.object(AIService, "_init_client"):
        ai = AIService(api_key="sk-fake-key")
        
        # Mock generate_json method on ai
        def mock_generate_json(system, user):
            s = system.lower()
            if "marketing strategist" in s:
                return {
                    "summary": "Mock summary",
                    "main_message": "Mock main message",
                    "key_selling_points": ["Point 1", "Point 2"],
                    "audience_insight": "Insight",
                    "creative_direction": "Direction",
                    "flagged_claims": [],
                }
            elif "video advertising copywriter" in s:
                return [
                    {
                        "hook_number": 1,
                        "hook_text": "Mock hook text",
                        "style": "Curiosity",
                        "audience_appeal": "Appeal",
                        "why_it_works": "Works",
                    }
                ]
            elif "scriptwriter" in s or "ugc" in s:
                return {
                    "script_title": "Mock script",
                    "total_estimated_duration": "30 seconds",
                    "content_note": "Mock note",
                    "scenes": [
                        {
                            "scene_number": 1,
                            "timestamp": "0:00 - 0:10",
                            "visual_direction": "Visual",
                            "dialogue": "Hello world",
                            "on_screen_text": "",
                            "shot_suggestion": "Close up",
                            "transition": "Cut",
                        }
                    ],
                    "final_cta": "Click now",
                    "production_notes": "None",
                }
            elif "direct-response" in s:
                return {
                    "engagement_ctas": ["Comment below"],
                    "website_visit_ctas": ["Visit site"],
                    "product_discovery_ctas": ["Learn more"],
                    "purchase_intent_ctas": ["Buy now"],
                    "recommended_primary_cta": "Visit site",
                    "cta_guidance": "Good match",
                }
            elif "social media copywriter" in s:
                return {
                    "concise_caption": "Short caption",
                    "extended_caption": "Long caption",
                    "hashtags": ["#tag1", "#tag2"],
                    "caption_cta": "Visit site",
                    "hashtag_strategy": "Niche tags",
                }
            elif "cross-platform" in s:
                return {
                    "instagram_reels": {"creative_format": "9:16"},
                    "youtube_shorts": {"creative_format": "9:16"},
                    "paid_social_ads": {"creative_format": "1:1"},
                }
            elif "creative advertising strategist" in s or "angles" in s:
                return {
                    "angles": [
                        {"angle": "Angle 1", "description": "Desc 1"},
                    ]
                }
            return {}

        ai.generate_json = MagicMock(side_effect=mock_generate_json)
        generator = ContentGenerator(ai)
        
        result = generator.generate_full_campaign(SAMPLE_INPUTS)
        assert result["mode"] == "live"
        assert result["brief"]["summary"] == "Mock summary"
        assert len(result["hooks"]) == 1
        assert result["hooks"][0]["hook_text"] == "Mock hook text"
        assert result["script"]["script_title"] == "Mock script"
        assert result["quality_review"]["overall_score"] > 0


def test_ai_service_set_api_key_and_model():
    service = AIService(api_key=None)
    assert service.is_demo_mode is True
    with patch.object(AIService, "_init_client"):
        service.set_api_key("sk-new-key-1234")
        assert service.is_demo_mode is False
        service.set_model("gpt-4o")
        assert service.model == "gpt-4o"


def test_ai_service_test_connection_in_demo_mode():
    service = AIService(api_key=None)
    success, msg = service.test_connection()
    assert success is False
    assert "Demo Mode" in msg


def test_ai_service_test_connection_success():
    with patch.object(AIService, "_init_client"):
        service = AIService(api_key="sk-test-key")
        mock_client = MagicMock()
        mock_client.models.list.return_value = ["gpt-4o-mini"]
        service._client = mock_client
        success, msg = service.test_connection()
        assert success is True
        assert "verified successfully" in msg


def test_ai_service_get_status_details():
    # 1. Missing Key
    service = AIService(api_key=None)
    details = service.get_status_details()
    assert details["status"] == "Missing API Key"
    assert details["connected"] is False

    # 2. Connected
    with patch.object(AIService, "_init_client"):
        service_live = AIService(api_key="sk-test-key")
        mock_client = MagicMock()
        mock_client.models.list.return_value = ["gpt-4o-mini"]
        service_live._client = mock_client
        details = service_live.get_status_details()
        assert details["status"] == "Connected"
        assert details["connected"] is True

    # 3. Invalid Key
    with patch.object(AIService, "_init_client"):
        service_bad = AIService(api_key="sk-bad-key")
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Incorrect API key provided")
        service_bad._client = mock_client
        details = service_bad.get_status_details()
        assert details["status"] == "Invalid Key"
        assert details["connected"] is False

    # 4. Quota Exceeded
    with patch.object(AIService, "_init_client"):
        service_quota = AIService(api_key="sk-quota-key")
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("You exceeded your current quota")
        service_quota._client = mock_client
        details = service_quota.get_status_details()
        assert details["status"] == "Quota/Billing Issue"
        assert details["connected"] is False

    # 5. Connection / Timeout Error
    with patch.object(AIService, "_init_client"):
        service_timeout = AIService(api_key="sk-timeout-key")
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection timeout while reaching OpenAI")
        service_timeout._client = mock_client
        details = service_timeout.get_status_details()
        assert details["status"] == "Connection Error"
        assert details["connected"] is False


def test_live_generation_failure_does_not_silently_fallback_to_demo():
    """Verify that in Live Mode, API errors raise AIServiceError and never silently return demo data."""
    with patch.object(AIService, "_init_client"):
        service = AIService(api_key="sk-real-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API rate limit exceeded")
        service._client = mock_client

        generator = ContentGenerator(service)
        with pytest.raises(AIServiceError) as exc_info:
            generator.generate_full_campaign(SAMPLE_INPUTS)

        assert "rate limit" in str(exc_info.value).lower()
