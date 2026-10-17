"""
test_validators.py
Tests for the CampaignInput validation model.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validators import validate_campaign_input, CampaignInput

VALID_INPUT = {
    "brand_name": "TestBrand",
    "product_name": "TestProduct",
    "description": "A detailed product description with enough words.",
    "target_audience": "Adults aged 25-40 interested in technology",
    "objective": "Product Awareness",
    "platform": "Instagram Reels",
    "tone": "Friendly",
    "language": "English",
    "duration": 30,
    "num_hooks": 5,
    "benefits": "Feature A. Feature B. Feature C.",
    "offer": "",
    "pain_points": "",
    "avoid_words": "",
}


def test_valid_input_passes():
    campaign, errors = validate_campaign_input(VALID_INPUT)
    assert campaign is not None
    assert errors == []


def test_missing_brand_name():
    data = {**VALID_INPUT, "brand_name": ""}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_missing_product_name():
    data = {**VALID_INPUT, "product_name": ""}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_description_too_short():
    data = {**VALID_INPUT, "description": "Short"}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_description_too_long():
    data = {**VALID_INPUT, "description": "x" * 1001}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_invalid_duration():
    data = {**VALID_INPUT, "duration": 45}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_valid_durations():
    for duration in [15, 30, 60]:
        data = {**VALID_INPUT, "duration": duration}
        campaign, errors = validate_campaign_input(data)
        assert campaign is not None, f"Duration {duration} should be valid"
        assert errors == []


def test_invalid_platform():
    data = {**VALID_INPUT, "platform": "TikTok"}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0


def test_valid_platforms():
    for platform in ["Instagram Reels", "YouTube Shorts", "Paid Social Ads"]:
        data = {**VALID_INPUT, "platform": platform}
        campaign, errors = validate_campaign_input(data)
        assert campaign is not None, f"Platform {platform} should be valid"


def test_invalid_tone():
    data = {**VALID_INPUT, "tone": "Aggressive"}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None


def test_num_hooks_bounds():
    # Too few
    data = {**VALID_INPUT, "num_hooks": 2}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    # Too many
    data = {**VALID_INPUT, "num_hooks": 11}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    # Valid
    for n in [3, 5, 10]:
        data = {**VALID_INPUT, "num_hooks": n}
        campaign, errors = validate_campaign_input(data)
        assert campaign is not None, f"num_hooks={n} should be valid"


def test_optional_fields_can_be_empty():
    data = {**VALID_INPUT, "offer": "", "pain_points": "", "avoid_words": ""}
    campaign, errors = validate_campaign_input(data)
    assert campaign is not None
    assert errors == []


def test_brand_name_stripped():
    data = {**VALID_INPUT, "brand_name": "  MyBrand  "}
    campaign, errors = validate_campaign_input(data)
    assert campaign is not None
    assert campaign.brand_name == "MyBrand"


def test_invalid_objective():
    data = {**VALID_INPUT, "objective": "Make Money"}
    campaign, errors = validate_campaign_input(data)
    assert campaign is None
    assert len(errors) > 0
