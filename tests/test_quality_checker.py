"""
test_quality_checker.py
Tests for the heuristic quality checking module.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality_checker import (
    run_quality_check,
    _find_pattern_matches,
    CLINICAL_CLAIM_PATTERNS,
    FALSE_SCARCITY_PATTERNS,
    TESTIMONIAL_PATTERNS,
    json_to_text,
)


SAMPLE_CAMPAIGN = {
    "inputs": {
        "brand_name": "TestBrand",
        "product_name": "TestProduct",
        "target_audience": "adults interested in skincare",
        "objective": "Product Awareness",
        "platform": "Instagram Reels",
        "duration": 30,
    },
    "brief": {
        "summary": "A friendly product awareness campaign for TestProduct.",
        "main_message": "TestProduct keeps your skin hydrated.",
        "key_selling_points": ["Lightweight", "Non-greasy"],
    },
    "hooks": [
        {"hook_number": 1, "hook_text": "Ever wonder why your skin feels dry?", "style": "Curiosity", "audience_appeal": "Skincare interest", "why_it_works": "Opens a gap."},
        {"hook_number": 2, "hook_text": "Your routine is missing one step.", "style": "Pain Point", "audience_appeal": "Frustration", "why_it_works": "Relates to pain."},
        {"hook_number": 3, "hook_text": "Watch the difference in real time.", "style": "Demo", "audience_appeal": "Visual", "why_it_works": "Shows rather than tells."},
    ],
    "script": {
        "scenes": [
            {"scene_number": 1, "dialogue": "This moisturizer is lightweight and absorbs fast."},
            {"scene_number": 2, "dialogue": "No greasiness at all — great for adults."},
        ]
    },
    "ctas": {
        "engagement_ctas": ["Comment below!"],
        "website_visit_ctas": ["Visit our site."],
        "product_discovery_ctas": ["See the range."],
        "purchase_intent_ctas": ["Shop now."],
        "recommended_primary_cta": "Learn more — link in bio.",
    },
    "platform_adaptation": {
        "instagram_reels": {"creative_format": "Vertical 9:16"},
    },
}


def test_run_quality_check_returns_structure():
    result = run_quality_check(SAMPLE_CAMPAIGN)
    assert "overall_score" in result
    assert "checklist" in result
    assert "flagged_items" in result
    assert "score_disclaimer" in result
    assert "overall_recommendation" in result


def test_overall_score_in_range():
    result = run_quality_check(SAMPLE_CAMPAIGN)
    assert 0 <= result["overall_score"] <= 100


def test_checklist_has_all_criteria():
    result = run_quality_check(SAMPLE_CAMPAIGN)
    checklist = result["checklist"]
    required = [
        "audience_relevance", "message_clarity", "hook_distinctiveness",
        "cta_relevance", "platform_suitability", "claim_verification",
        "testimonial_language",
    ]
    for criterion in required:
        assert criterion in checklist, f"{criterion} missing from checklist"


def test_each_criterion_has_score_and_finding():
    result = run_quality_check(SAMPLE_CAMPAIGN)
    for name, item in result["checklist"].items():
        assert "score" in item, f"{name} missing score"
        assert "finding" in item, f"{name} missing finding"
        assert 0 <= item["score"] <= 100, f"{name} score out of range"


def test_clinical_claim_detected():
    campaign = {**SAMPLE_CAMPAIGN}
    campaign["brief"] = {**SAMPLE_CAMPAIGN["brief"], "main_message": "Clinically proven to reduce dryness by 90%."}
    result = run_quality_check(campaign)
    # Should flag clinical claim
    claim_result = result["checklist"]["claim_verification"]
    assert claim_result["score"] < 80


def test_false_scarcity_detected():
    matches = _find_pattern_matches("act now — limited time offer!", FALSE_SCARCITY_PATTERNS)
    assert len(matches) > 0


def test_testimonial_pattern_detected():
    matches = _find_pattern_matches("Join thousands of happy customers", TESTIMONIAL_PATTERNS)
    assert len(matches) > 0


def test_no_flags_clean_content():
    result = run_quality_check(SAMPLE_CAMPAIGN)
    claim_result = result["checklist"]["claim_verification"]
    # Clean content should have high claim score
    assert claim_result["score"] >= 70


def test_json_to_text_flat():
    result = json_to_text({"key": "value", "other": "text"})
    assert "value" in result
    assert "text" in result


def test_json_to_text_nested():
    data = {"a": {"b": "nested text", "c": ["list item"]}}
    result = json_to_text(data)
    assert "nested text" in result
    assert "list item" in result


def test_empty_campaign_does_not_crash():
    result = run_quality_check({})
    assert "overall_score" in result
    assert result["overall_score"] >= 0
