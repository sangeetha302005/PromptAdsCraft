"""
exporters.py
------------
Export campaign results as Markdown or JSON.
All exports are generated in-memory and returned as strings
so the caller (Streamlit) can offer them as download buttons.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any


def _safe_get(data: dict, *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dicts."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def export_as_json(campaign_data: dict) -> str:
    """
    Serialize the full campaign result dict as formatted JSON.
    Returns a UTF-8 string.
    """
    export = {
        "export_info": {
            "tool": "PromptAdsCraft AI",
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": (
                "Generated content is for review purposes. "
                "Verify all claims before publishing. "
                "This is not a guarantee of advertising performance."
            ),
        },
        "campaign": campaign_data,
    }
    return json.dumps(export, indent=2, ensure_ascii=False)


def export_as_markdown(campaign_data: dict) -> str:
    """
    Render campaign results as a structured Markdown document.
    Returns a UTF-8 string suitable for .md file download.
    """
    inputs = campaign_data.get("inputs", {})
    brief = campaign_data.get("brief", {})
    hooks = campaign_data.get("hooks", [])
    script = campaign_data.get("script", {})
    ctas = campaign_data.get("ctas", {})
    captions = campaign_data.get("captions", {})
    platforms = campaign_data.get("platform_adaptation", {})
    creative_angles = campaign_data.get("creative_angles", [])
    quality = campaign_data.get("quality_review", {})

    brand = inputs.get("brand_name", "Unknown Brand")
    product = inputs.get("product_name", "Unknown Product")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# PromptAdsCraft AI — Campaign Report",
        f"",
        f"**Brand:** {brand}  ",
        f"**Product:** {product}  ",
        f"**Generated:** {now}  ",
        f"",
        f"> **Disclaimer:** Review all content before publishing. Verify any claims.",
        f"  This report is not a performance guarantee.",
        f"",
        f"---",
        f"",
        f"## 1. Campaign Summary",
        f"",
        f"**Summary:** {brief.get('summary', 'N/A')}  ",
        f"**Main Message:** {brief.get('main_message', 'N/A')}  ",
        f"**Audience Insight:** {brief.get('audience_insight', 'N/A')}  ",
        f"**Creative Direction:** {brief.get('creative_direction', 'N/A')}  ",
        f"",
    ]

    # Key selling points
    ksp = brief.get("key_selling_points", [])
    if ksp:
        lines.append("**Key Selling Points:**")
        for point in ksp:
            lines.append(f"- {point}")
        lines.append("")

    # Flagged claims
    flagged = brief.get("flagged_claims", [])
    if flagged:
        lines.append("**⚠️ Claims to Verify Before Publishing:**")
        for claim in flagged:
            lines.append(f"- {claim}")
        lines.append("")

    lines += [
        f"---",
        f"",
        f"## 2. Advertising Hooks",
        f"",
    ]
    for hook in hooks:
        lines += [
            f"### Hook {hook.get('hook_number', '?')}: {hook.get('style', '')}",
            f"",
            f"> {hook.get('hook_text', '')}",
            f"",
            f"**Appeal:** {hook.get('audience_appeal', '')}  ",
            f"**Why it works:** {hook.get('why_it_works', '')}  ",
            f"",
        ]

    lines += ["---", "", "## 3. UGC Video Script", ""]
    if script:
        lines += [
            f"**Title:** {script.get('script_title', '')}  ",
            f"**Duration:** {script.get('total_estimated_duration', '')}  ",
            f"*{script.get('content_note', '')}*  ",
            f"",
        ]
        for scene in script.get("scenes", []):
            lines += [
                f"### Scene {scene.get('scene_number', '?')} — {scene.get('timestamp', '')}",
                f"",
                f"**Visual:** {scene.get('visual_direction', '')}  ",
                f"**Dialogue:** {scene.get('dialogue', '')}  ",
                f"**On-screen text:** {scene.get('on_screen_text', '') or 'None'}  ",
                f"**Shot:** {scene.get('shot_suggestion', '')}  ",
                f"**Transition:** {scene.get('transition', '')}  ",
                f"",
            ]
        lines += [
            f"**Final CTA:** {script.get('final_cta', '')}  ",
            f"**Production Notes:** {script.get('production_notes', '')}  ",
            f"",
        ]

    lines += ["---", "", "## 4. Calls to Action", ""]
    if ctas:
        for category, label in [
            ("engagement_ctas", "Engagement"),
            ("website_visit_ctas", "Website Visit"),
            ("product_discovery_ctas", "Product Discovery"),
            ("purchase_intent_ctas", "Purchase Intent"),
        ]:
            items = ctas.get(category, [])
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
        lines += [
            f"**Recommended Primary CTA:** {ctas.get('recommended_primary_cta', '')}  ",
            f"**Guidance:** {ctas.get('cta_guidance', '')}  ",
            f"",
        ]

    lines += ["---", "", "## 5. Captions & Hashtags", ""]
    if captions:
        lines += [
            f"**Concise Caption:**  ",
            f"> {captions.get('concise_caption', '')}  ",
            f"",
            f"**Extended Caption:**  ",
            f"> {captions.get('extended_caption', '')}  ",
            f"",
            f"**Hashtags:** {' '.join(captions.get('hashtags', []))}  ",
            f"**Caption CTA:** {captions.get('caption_cta', '')}  ",
            f"",
        ]

    lines += ["---", "", "## 6. Platform Adaptations", ""]
    for plat_key, plat_label in [
        ("instagram_reels", "Instagram Reels"),
        ("youtube_shorts", "YouTube Shorts"),
        ("paid_social_ads", "Paid Social Ads"),
    ]:
        plat = platforms.get(plat_key, {})
        if plat:
            lines += [
                f"### {plat_label}",
                f"",
                f"**Format:** {plat.get('creative_format', '')}  ",
                f"**Opening Hook:** {plat.get('opening_hook', '')}  ",
                f"**Structure:** {plat.get('script_structure', '')}  ",
                f"**Caption:** {plat.get('caption_recommendation', '')}  ",
                f"**CTA:** {plat.get('cta', '')}  ",
                f"**Notes:** {plat.get('best_practice_notes', '')}  ",
                f"",
            ]

    lines += ["---", "", "## 7. Alternative Creative Angles", ""]
    for angle in creative_angles:
        if isinstance(angle, dict):
            lines += [
                f"**{angle.get('angle', '')}:** {angle.get('description', '')}  ",
                f"",
            ]
        elif isinstance(angle, str):
            lines.append(f"- {angle}")

    lines += ["---", "", "## 8. Quality Review", ""]
    if quality:
        lines += [
            f"**Overall Score:** {quality.get('overall_score', 'N/A')}/100  ",
            f"*{quality.get('score_disclaimer', '')}*  ",
            f"",
        ]
        checklist = quality.get("checklist", {})
        for criterion, label in [
            ("audience_relevance", "Audience Relevance"),
            ("message_clarity", "Message Clarity"),
            ("hook_distinctiveness", "Hook Distinctiveness"),
            ("cta_relevance", "CTA Relevance"),
            ("platform_suitability", "Platform Suitability"),
            ("claim_verification", "Claim Verification"),
            ("testimonial_language", "Testimonial Language"),
        ]:
            item = checklist.get(criterion, {})
            if item:
                lines += [
                    f"**{label}** ({item.get('score', '?')}/100): {item.get('finding', '')}  ",
                    f"  *Recommendation: {item.get('recommendation', 'None')}*  ",
                    f"",
                ]
        flagged_items = quality.get("flagged_items", [])
        if flagged_items:
            lines.append("**⚠️ Items Requiring Human Review:**")
            for item in flagged_items:
                lines.append(f"- {item}")
            lines.append("")
        lines += [
            f"**Overall Recommendation:** {quality.get('overall_recommendation', '')}  ",
            f"",
        ]

    lines += [
        "---",
        "",
        "*Generated by PromptAdsCraft AI. Review all content before publishing. ",
        "This tool assists with content creation but does not guarantee ad performance.*",
    ]

    return "\n".join(lines)


def export_as_txt(campaign_data: dict) -> str:
    """
    Render campaign results as a clean plain text document.
    Returns a UTF-8 string suitable for .txt file download.
    """
    md = export_as_markdown(campaign_data)
    # Strip markdown headers, bold, italics, quotes for clean text representation
    import re
    text = re.sub(r'#+\s*', '', md)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'>\s*', '', text)
    text = re.sub(r'---+', '----------------------------------------', text)
    return text.strip()

