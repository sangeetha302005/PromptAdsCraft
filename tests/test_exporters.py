"""
test_exporters.py
Tests for Markdown and JSON export functions.
"""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exporters import export_as_json, export_as_markdown, export_as_txt


SAMPLE_CAMPAIGN = {
    "inputs": {
        "brand_name": "ExportBrand",
        "product_name": "ExportProduct",
        "platform": "Instagram Reels",
        "tone": "Friendly",
        "duration": 30,
    },
    "brief": {
        "summary": "Test campaign summary.",
        "main_message": "Test main message.",
        "key_selling_points": ["Point A", "Point B"],
        "audience_insight": "Test insight.",
        "creative_direction": "Test direction.",
        "flagged_claims": [],
    },
    "hooks": [
        {"hook_number": 1, "hook_text": "Test hook text.", "style": "Curiosity", "audience_appeal": "Broad", "why_it_works": "It works."},
    ],
    "script": {
        "script_title": "Test Script",
        "total_estimated_duration": "30 seconds",
        "content_note": "Test note.",
        "scenes": [
            {"scene_number": 1, "timestamp": "0:00-0:10", "visual_direction": "Close-up.",
             "dialogue": "Hello.", "on_screen_text": "Text", "shot_suggestion": "Wide", "transition": "Cut"},
        ],
        "final_cta": "Shop now.",
        "production_notes": "Film outside.",
    },
    "ctas": {
        "engagement_ctas": ["Comment!"],
        "website_visit_ctas": ["Visit us."],
        "product_discovery_ctas": ["Discover more."],
        "purchase_intent_ctas": ["Buy now."],
        "recommended_primary_cta": "Learn more.",
        "cta_guidance": "Matches objective.",
    },
    "captions": {
        "concise_caption": "Short caption.",
        "extended_caption": "Longer caption with more detail.",
        "hashtags": ["#test", "#export"],
        "caption_cta": "Link in bio.",
        "hashtag_strategy": "Relevant tags only.",
    },
    "platform_adaptation": {
        "instagram_reels": {
            "creative_format": "Vertical",
            "opening_hook": "Test hook",
            "script_structure": "Hook-Demo-CTA",
            "caption_recommendation": "Short",
            "cta": "Link in bio",
            "best_practice_notes": "Notes here.",
        },
    },
    "creative_angles": [
        {"angle": "Problem & Solution", "description": "Start with the problem."},
    ],
    "quality_review": {
        "overall_score": 80,
        "score_disclaimer": "Estimates only.",
        "checklist": {},
        "flagged_items": [],
        "overall_recommendation": "Looks good.",
    },
}


def test_export_as_json_is_valid_json():
    result = export_as_json(SAMPLE_CAMPAIGN)
    parsed = json.loads(result)
    assert "campaign" in parsed
    assert "export_info" in parsed


def test_export_as_json_includes_disclaimer():
    result = export_as_json(SAMPLE_CAMPAIGN)
    parsed = json.loads(result)
    assert "disclaimer" in parsed["export_info"]
    assert len(parsed["export_info"]["disclaimer"]) > 0


def test_export_as_json_preserves_inputs():
    result = export_as_json(SAMPLE_CAMPAIGN)
    parsed = json.loads(result)
    assert parsed["campaign"]["inputs"]["brand_name"] == "ExportBrand"


def test_export_as_json_has_tool_name():
    result = export_as_json(SAMPLE_CAMPAIGN)
    parsed = json.loads(result)
    assert "PromptAdsCraft" in parsed["export_info"]["tool"]


def test_export_as_markdown_is_string():
    result = export_as_markdown(SAMPLE_CAMPAIGN)
    assert isinstance(result, str)
    assert len(result) > 100


def test_export_as_markdown_contains_brand():
    result = export_as_markdown(SAMPLE_CAMPAIGN)
    assert "ExportBrand" in result


def test_export_as_markdown_contains_sections():
    result = export_as_markdown(SAMPLE_CAMPAIGN)
    assert "Campaign Summary" in result
    assert "Advertising Hooks" in result
    assert "Video Script" in result or "UGC" in result
    assert "Calls to Action" in result
    assert "Captions" in result
    assert "Platform" in result
    assert "Quality Review" in result


def test_export_as_markdown_contains_disclaimer():
    result = export_as_markdown(SAMPLE_CAMPAIGN)
    assert "disclaimer" in result.lower() or "review" in result.lower()


def test_export_empty_campaign_does_not_crash():
    result_md = export_as_markdown({})
    assert isinstance(result_md, str)
    result_json = export_as_json({})
    assert isinstance(result_json, str)
    parsed = json.loads(result_json)
    assert "campaign" in parsed


def test_export_as_txt_contains_key_elements():
    result_txt = export_as_txt(SAMPLE_CAMPAIGN)
    assert isinstance(result_txt, str)
    assert "ExportBrand" in result_txt
    assert "ExportProduct" in result_txt
    assert "Advertising Hooks" in result_txt
    assert "UGC Video Script" in result_txt
    assert "Calls to Action" in result_txt
    assert "Captions & Hashtags" in result_txt
    assert "Disclaimer" in result_txt


def test_export_as_txt_empty_campaign():
    result_txt = export_as_txt({})
    assert isinstance(result_txt, str)
    assert "PromptAdsCraft AI" in result_txt
