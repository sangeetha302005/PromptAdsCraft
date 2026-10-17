"""
test_prompt_builder.py
Tests for the prompt template loading and variable substitution system.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompt_builder import (
    build_prompt,
    extract_user_section,
    get_template_metadata,
    sanitized_preview,
    get_all_template_names,
    SafeDict,
)


def test_safe_dict_missing_key():
    d = SafeDict({"name": "test"})
    assert d["name"] == "test"
    assert d["missing"] == "{missing}"


def test_build_prompt_substitution():
    """Test that build_prompt correctly substitutes variables."""
    result = build_prompt("campaign_brief.txt", {
        "brand_name": "TestBrand",
        "product_name": "TestProduct",
        "description": "A great product.",
        "target_audience": "Adults",
        "objective": "Awareness",
        "platform": "Instagram Reels",
        "tone": "Friendly",
        "duration": "30",
        "language": "English",
        "benefits": "Fast. Lightweight.",
        "offer": "",
        "pain_points": "",
        "avoid_words": "",
    })
    assert "TestBrand" in result
    assert "TestProduct" in result


def test_build_prompt_missing_variable_leaves_placeholder():
    """Missing variables should appear as {variable_name} not raise an error."""
    result = build_prompt("campaign_brief.txt", {
        "brand_name": "OnlyBrand",
        # All other vars missing
    })
    assert "OnlyBrand" in result
    assert "{product_name}" in result or "product_name" in result


def test_build_prompt_file_not_found():
    with pytest.raises(FileNotFoundError):
        build_prompt("nonexistent_template.txt", {})


def test_extract_user_section():
    sample_prompt = """
# Comment line
SYSTEM:
You are a marketing expert.

USER:
Create a campaign for {brand_name}.
Audience: {target_audience}.
"""
    result = extract_user_section(sample_prompt)
    assert "Create a campaign" in result
    assert "You are a marketing expert" not in result
    assert "# Comment line" not in result


def test_get_template_metadata():
    metadata = get_template_metadata("campaign_brief.txt")
    assert isinstance(metadata, dict)
    # Should have at least a version or purpose key
    assert len(metadata) > 0


def test_get_all_template_names():
    names = get_all_template_names()
    assert isinstance(names, list)
    assert len(names) > 0
    expected = ["campaign_brief.txt", "hooks.txt", "ugc_script.txt", "cta.txt",
                "captions.txt", "platform_adaptation.txt", "quality_review.txt"]
    for name in expected:
        assert name in names, f"{name} should be in template list"


def test_sanitized_preview_excludes_system():
    result = sanitized_preview("campaign_brief.txt", {
        "brand_name": "PreviewBrand",
        "product_name": "PreviewProduct",
        "description": "Test description here.",
        "target_audience": "Test audience",
        "objective": "Awareness",
        "platform": "Instagram Reels",
        "tone": "Friendly",
        "duration": "30",
        "language": "English",
        "benefits": "Feature A.",
        "offer": "",
        "pain_points": "",
        "avoid_words": "",
    })
    assert "PreviewBrand" in result
    # System instructions should not appear in preview
    assert "You are a responsible senior marketing strategist" not in result
