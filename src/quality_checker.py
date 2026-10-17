"""
quality_checker.py
------------------
Heuristic content quality checks for generated campaign content.

These checks are transparent rule-based heuristics, not AI predictions.
Scores are estimates of content completeness and safety, NOT predictions
of actual advertising performance.

Design rationale:
- Heuristic checks run instantly without API calls.
- They catch common structural and safety issues before the user publishes.
- AI-assisted review is an optional enhancement when API is available.
- All score labels clearly communicate they are estimates.
"""

from __future__ import annotations
from typing import Any
import re


# ---------------------------------------------------------------------------
# Forbidden / high-risk phrase patterns
# ---------------------------------------------------------------------------

CLINICAL_CLAIM_PATTERNS = [
    r"\bclinically (proven|tested|validated|studied)\b",
    r"\bfda (approved|cleared|certified)\b",
    r"\bscientifically proven\b",
    r"\bmedically (recommended|endorsed)\b",
    r"\bcures?\b",
    r"\bguaranteed (results?|weight loss|cure)\b",
    r"\b\d+% (of (users?|customers?|people)|effective|success)\b",
]

FALSE_SCARCITY_PATTERNS = [
    r"\blimited (time|stock|supply|offer)\b",
    r"\bonly \d+ left\b",
    r"\bselling out (fast|quickly)\b",
    r"\bact now\b",
    r"\btoday only\b",
    r"\bexpires? (today|soon|in \d+)\b",
]

TESTIMONIAL_PATTERNS = [
    r"\bour customers? (love|say|report|claim)\b",
    r"\breal (customer|user|results?)\b",
    r"\bpeople are (saying|raving|loving)\b",
    r"\bjoin (thousands|millions|hundreds) of\b",
    r"\b(five|5)[ -]star (reviews?|ratings?)\b",
]


def _find_pattern_matches(text: str, patterns: list[str]) -> list[str]:
    """Return list of matched phrases from text against pattern list."""
    text_lower = text.lower()
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text_lower)
        if found:
            if isinstance(found[0], tuple):
                matches.extend([" ".join(f) for f in found])
            else:
                matches.extend(found)
    return list(set(matches))


def _score_audience_relevance(campaign_data: dict) -> dict:
    """Check that target audience is referenced in hooks and script."""
    target = (campaign_data.get("inputs", {}).get("target_audience", "") or "").lower()
    hooks = campaign_data.get("hooks", [])
    if isinstance(hooks, list):
        hook_texts = " ".join(
            (h.get("hook_text", "") if isinstance(h, dict) else str(h)) for h in hooks
        ).lower()
    else:
        hook_texts = ""

    script = campaign_data.get("script", {})
    dialogue_parts = []
    if isinstance(script, dict):
        scenes = script.get("scenes", [])
        if isinstance(scenes, list):
            for scene in scenes:
                if isinstance(scene, dict):
                    dialogue_parts.append(str(scene.get("dialogue", "")))
                elif isinstance(scene, (str, list)):
                    dialogue_parts.append(str(scene))
    elif isinstance(script, list):
        for item in script:
            if isinstance(item, dict):
                dialogue_parts.append(str(item.get("dialogue", "")))
            else:
                dialogue_parts.append(str(item))

    dialogue = " ".join(dialogue_parts).lower()
    content_text = hook_texts + " " + dialogue
    # Simple heuristic: audience words appear in content
    audience_words = [w for w in target.split() if len(w) > 4]
    matches = sum(1 for w in audience_words if w in content_text)
    score = min(100, 60 + (matches * 10)) if hooks else 40
    finding = (
        f"Content references the target audience context."
        if score >= 70
        else "Content may not clearly address the target audience."
    )
    return {
        "score": score,
        "finding": finding,
        "recommendation": "" if score >= 70 else "Review hooks for audience-specific language.",
    }


def _score_message_clarity(campaign_data: dict) -> dict:
    """Check that main message is present and not too long."""
    brief = campaign_data.get("brief", {})
    main_msg = brief.get("main_message", "") if isinstance(brief, dict) else ""
    if not main_msg:
        return {"score": 30, "finding": "No main message found in brief.", "recommendation": "Regenerate the campaign brief."}
    word_count = len(main_msg.split())
    if word_count <= 20:
        score = 90
        finding = "Main message is concise and clear."
    elif word_count <= 40:
        score = 70
        finding = "Main message is acceptable but could be more concise."
    else:
        score = 50
        finding = "Main message is too long for quick comprehension."
    return {"score": score, "finding": finding, "recommendation": "" if score >= 70 else "Shorten the main message to under 20 words."}


def _score_hook_distinctiveness(campaign_data: dict) -> dict:
    """Check that hooks are not all starting with the same word."""
    hooks = campaign_data.get("hooks", [])
    if not hooks or not isinstance(hooks, list):
        return {"score": 20, "finding": "No hooks generated.", "recommendation": "Generate hooks first."}

    hook_texts = [
        (h.get("hook_text", "") if isinstance(h, dict) else str(h)).strip().lower()
        for h in hooks
    ]
    styles = [h.get("style", "") if isinstance(h, dict) else "" for h in hooks]
    unique_styles = len(set(styles))

    # Check first words
    first_words = [t.split()[0] if t.split() else "" for t in hook_texts]
    unique_first_words = len(set(first_words))

    total = len(hooks)
    distinctiveness = (unique_first_words / total) * 0.5 + (min(unique_styles, total) / total) * 0.5
    score = int(distinctiveness * 100)

    finding = (
        "Hooks show good variety in style and opening."
        if score >= 70
        else "Some hooks may be too similar in style or opening words."
    )
    return {
        "score": score,
        "finding": finding,
        "recommendation": "" if score >= 70 else "Ensure each hook uses a different style and opening.",
    }


def _score_cta_relevance(campaign_data: dict) -> dict:
    """Check that CTAs exist and match the campaign objective."""
    ctas = campaign_data.get("ctas", {})
    if not isinstance(ctas, dict):
        return {"score": 30, "finding": "No CTAs generated.", "recommendation": "Generate CTAs before reviewing."}

    primary_cta = ctas.get("recommended_primary_cta", "")

    if not primary_cta:
        return {"score": 30, "finding": "No CTAs generated.", "recommendation": "Generate CTAs before reviewing."}

    total_ctas = sum(
        len(ctas.get(k, []))
        for k in ["engagement_ctas", "website_visit_ctas", "product_discovery_ctas", "purchase_intent_ctas"]
        if isinstance(ctas.get(k), list)
    )
    score = min(100, 60 + total_ctas * 5)
    finding = f"{total_ctas} CTAs generated across categories."
    return {"score": score, "finding": finding, "recommendation": "" if score >= 70 else "Generate more CTA variations."}


def _score_platform_suitability(campaign_data: dict) -> dict:
    """Check that platform adaptation is present."""
    platform_data = campaign_data.get("platform_adaptation", {})
    inputs = campaign_data.get("inputs", {})
    platform = inputs.get("platform", "")
    duration = inputs.get("duration", 30)

    if not platform_data:
        return {"score": 40, "finding": "No platform adaptation generated.", "recommendation": "Generate platform adaptations."}

    # Check duration appropriateness
    if platform == "YouTube Shorts" and duration > 60:
        return {"score": 60, "finding": "Duration may exceed YouTube Shorts limit.", "recommendation": "Use 15-60 second duration for Shorts."}

    score = 85
    present_platforms = [k for k in ["instagram_reels", "youtube_shorts", "paid_social_ads"] if platform_data.get(k)]
    finding = f"Platform adaptation present for {len(present_platforms)} platform(s)."
    return {"score": score, "finding": finding, "recommendation": ""}


def _score_claim_verification(campaign_data: dict) -> dict:
    """Scan all generated text for high-risk claim patterns."""
    all_text = json_to_text(campaign_data)
    clinical_matches = _find_pattern_matches(all_text, CLINICAL_CLAIM_PATTERNS)
    scarcity_matches = _find_pattern_matches(all_text, FALSE_SCARCITY_PATTERNS)

    all_matches = clinical_matches + scarcity_matches
    if not all_matches:
        return {"score": 95, "finding": "No high-risk claim patterns detected.", "recommendation": ""}
    else:
        score = max(20, 80 - len(all_matches) * 15)
        return {
            "score": score,
            "finding": f"Potential unverified claims detected: {', '.join(all_matches[:5])}",
            "recommendation": "Review and verify all claims before publishing. Remove unverified statistics or guarantees.",
        }


def _score_testimonial_language(campaign_data: dict) -> dict:
    """Scan for misleading testimonial-style language."""
    all_text = json_to_text(campaign_data)
    testimonial_matches = _find_pattern_matches(all_text, TESTIMONIAL_PATTERNS)

    if not testimonial_matches:
        return {"score": 95, "finding": "No misleading testimonial language detected.", "recommendation": ""}
    else:
        score = max(30, 80 - len(testimonial_matches) * 20)
        return {
            "score": score,
            "finding": f"Potential testimonial language found: {', '.join(testimonial_matches[:3])}",
            "recommendation": "Ensure no fabricated customer reviews or experiences are presented as real.",
        }


def json_to_text(data: Any) -> str:
    """Recursively extract all string values from a nested dict/list."""
    if isinstance(data, str):
        return data + " "
    elif isinstance(data, dict):
        return " ".join(json_to_text(v) for v in data.values())
    elif isinstance(data, list):
        return " ".join(json_to_text(item) for item in data)
    return ""


def run_quality_check(campaign_data: dict) -> dict:
    """
    Run all heuristic quality checks and return a structured quality report.
    This is the primary public function for the quality checker module.
    """
    checklist = {
        "audience_relevance": _score_audience_relevance(campaign_data),
        "message_clarity": _score_message_clarity(campaign_data),
        "hook_distinctiveness": _score_hook_distinctiveness(campaign_data),
        "cta_relevance": _score_cta_relevance(campaign_data),
        "platform_suitability": _score_platform_suitability(campaign_data),
        "claim_verification": _score_claim_verification(campaign_data),
        "testimonial_language": _score_testimonial_language(campaign_data),
    }

    scores = [v["score"] for v in checklist.values()]
    overall = int(sum(scores) / len(scores))

    # Collect flagged items from low-scoring criteria
    flagged = []
    for criterion, result in checklist.items():
        if result["score"] < 70 and result.get("recommendation"):
            flagged.append(f"{criterion.replace('_', ' ').title()}: {result['recommendation']}")

    # Also add specific claim matches as flagged items
    claim_finding = checklist["claim_verification"]["finding"]
    testimonial_finding = checklist["testimonial_language"]["finding"]
    if "detected:" in claim_finding:
        flagged.append(f"Verify before publishing: {claim_finding}")
    if "found:" in testimonial_finding:
        flagged.append(f"Review testimonial language: {testimonial_finding}")

    recommendation = (
        "Content quality looks good. Review flagged items before publishing."
        if overall >= 70
        else "Several quality issues need attention before this content is ready to publish."
    )

    return {
        "overall_score": overall,
        "score_disclaimer": (
            "These scores are heuristic content quality estimates based on structural and safety checks. "
            "They are NOT predictions of advertising performance, reach, or conversion rates."
        ),
        "checklist": checklist,
        "flagged_items": flagged,
        "overall_recommendation": recommendation,
    }
