"""
synthesis_engine.py
-------------------
Custom Multi-Variable Prompt Synthesis Engine written in pure Python.

Mathematical formulation:
Copy = f(Business Type / Brand, Location / Platform, Services / Product,
         Target Audience, USPs / Benefits, Brand Tone, Context / Pain Points / Offer)

Key benefits:
- Zero Cost & No API Keys: Never runs out of API credits or rate limits.
- Instant Generation: Generates comprehensive, tailored copy in under 1 second.
- Reliable Deployment: Runs smoothly on free hosting platforms like Streamlit Cloud with zero configuration.
"""

from __future__ import annotations
import re
from typing import Any

from .quality_checker import run_quality_check

# ---------------------------------------------------------------------------
# Tone Vocabulary & Psychological Styling Matrix
# ---------------------------------------------------------------------------

TONE_MATRIX = {
    "Premium": {
        "verb": "elevate",
        "adjective": "refined",
        "pacing": "Deliberate, elegant, and atmospheric.",
        "promise": "Curated with meticulous attention to detail and uncompromising quality.",
        "opener": "For those who appreciate uncompromising craftsmanship,",
        "closer": "Experience the distinction today.",
    },
    "Friendly": {
        "verb": "welcome",
        "adjective": "delightful",
        "pacing": "Warm, conversational, and energetic.",
        "promise": "A simple, approachable solution that fits seamlessly into your daily life.",
        "opener": "Here is something you are genuinely going to love,",
        "closer": "Say hello to an easier way.",
    },
    "Humorous": {
        "verb": "rethink",
        "adjective": "brilliant",
        "pacing": "Brisk, witty, and playful.",
        "promise": "Because life is too short to settle for boring, over-complicated alternatives.",
        "opener": "Let's be completely honest for five seconds:",
        "closer": "Do your future self a favor and check this out.",
    },
    "Educational": {
        "verb": "master",
        "adjective": "proven",
        "pacing": "Structured, informative, and value-packed.",
        "promise": "Actionable insights and reliable results grounded in thoughtful design.",
        "opener": "Here is the breakdown most people never tell you about,",
        "closer": "Take the next step in your journey.",
    },
    "Energetic": {
        "verb": "supercharge",
        "adjective": "unstoppable",
        "pacing": "Fast-paced, bold, and dynamic.",
        "promise": "High-impact performance that keeps up with your biggest ambitions.",
        "opener": "Stop waiting and start making things happen right now:",
        "closer": "Take control and feel the momentum.",
    },
    "Professional": {
        "verb": "deliver",
        "adjective": "trusted",
        "pacing": "Clear, authoritative, and credible.",
        "promise": "Industry-grade reliability engineered to exceed your standards.",
        "opener": "When excellence and precision matter most,",
        "closer": "Partner with proven quality.",
    },
}


def _get_tone_profile(tone: str) -> dict[str, str]:
    return TONE_MATRIX.get(tone, TONE_MATRIX["Friendly"])


def synthesize_campaign(inputs: dict, label_as_demo: bool = True) -> dict:
    """
    Synthesize a complete advertising content package using the Multi-Variable Engine:
    Copy = f(Brand, Product, Target Audience, Benefits, Tone, Platform, Duration, Context)
    """
    prefix = "[DEMO] " if label_as_demo else ""

    brand = (inputs.get("brand_name") or "Your Brand").strip()
    product = (inputs.get("product_name") or "Your Product").strip()
    desc = (inputs.get("description") or f"A standout offering from {brand}.").strip()
    audience = (inputs.get("target_audience") or "enthusiastic everyday consumers").strip()
    objective = inputs.get("objective") or "Product Awareness"
    platform = inputs.get("platform") or "Instagram Reels"
    tone = inputs.get("tone") or "Friendly"
    duration = int(inputs.get("duration") or 30)
    benefits_str = (inputs.get("benefits") or "Premium quality. Fast results. Simple and reliable.").strip()
    pain_points_str = (inputs.get("pain_points") or "Wasting time on complicated alternatives.").strip()
    offer = (inputs.get("offer") or "").strip()
    avoid_words = (inputs.get("avoid_words") or "").strip()
    num_hooks = max(3, min(10, int(inputs.get("num_hooks") or 5)))

    tone_profile = _get_tone_profile(tone)

    # 1. Parse individual benefit points
    benefit_list = [b.strip() for b in re.split(r"[.\n•,]", benefits_str) if len(b.strip()) > 3]
    if not benefit_list:
        benefit_list = [
            f"Designed specifically for {audience}",
            "Delivers noticeable, consistent results",
            f"Crafted with {tone_profile['adjective']} attention to detail",
        ]
    top_benefit = benefit_list[0]

    # 2. Parse primary pain point
    pain_list = [p.strip() for p in re.split(r"[.\n•,]", pain_points_str) if len(p.strip()) > 3]
    primary_pain = pain_list[0] if pain_list else "options that fail to deliver on their promises"

    # 3. Dynamic Brief Synthesis
    brief = {
        "summary": (
            f"{prefix}A strategic {objective.lower()} campaign for {product} by {brand}, "
            f"tailored specifically for {audience}. Utilizing a {tone.lower()} tone optimized for {platform}."
        ),
        "main_message": (
            f"{product} by {brand} delivers {top_benefit.lower()} that {audience} can trust every single day."
        ),
        "key_selling_points": benefit_list[:4],
        "audience_insight": (
            f"{audience} seeking dependable ways to resolve {primary_pain.lower()} without unnecessary friction."
        ),
        "creative_direction": (
            f"Authentic creator-led presentation with a {tone.lower()} cadence. "
            f"{tone_profile['pacing']} Emphasize {top_benefit} in the opening 3 seconds for optimal {platform} retention."
        ),
        "flagged_claims": [
            f"{prefix}Review all product and efficacy claims before public distribution."
        ] if not avoid_words else [
            f"{prefix}Ensure all campaign creatives adhere to restricted keywords: {avoid_words}"
        ],
    }

    # 4. Multi-Variable Psychological Hooks
    all_hooks = [
        {
            "hook_number": 1,
            "hook_text": f"{prefix}Ever wonder why so many {audience} are switching to {product}?",
            "style": "Curiosity / Open Loop",
            "audience_appeal": f"Appeals to curiosity and peer recommendations among {audience}.",
            "why_it_works": "Opens a psychological knowledge gap that holds viewer attention through the opening seconds.",
        },
        {
            "hook_number": 2,
            "hook_text": f"{prefix}If you are tired of {primary_pain.lower()}, you need to see this.",
            "style": "Pain Point Acknowledgment",
            "audience_appeal": f"Directly resonates with frustration around {primary_pain.lower()}.",
            "why_it_works": "Immediate agitation of a real frustration creates emotional alignment with the viewer.",
        },
        {
            "hook_number": 3,
            "hook_text": f"{prefix}Watch what happens when we put {product} to the test.",
            "style": "Demonstration-Led",
            "audience_appeal": "Appeals to visual learners and skeptics who need tangible proof.",
            "why_it_works": "Promises an immediate visual payoff that discourages swiping away.",
        },
        {
            "hook_number": 4,
            "hook_text": f"{prefix}An honest breakdown of {product} from {brand} — here is why it works.",
            "style": "Bold Honest Statement",
            "audience_appeal": "Builds high credibility with discerning buyers seeking transparency.",
            "why_it_works": "Cuts through advertising noise by establishing a sincere, non-salesy frame.",
        },
        {
            "hook_number": 5,
            "hook_text": f"{prefix}What if you could experience {top_benefit.lower()} starting today?",
            "style": "Question-Based",
            "audience_appeal": f"Invites {audience} to envision immediate positive transformation.",
            "why_it_works": "A direct question requires active cognitive processing from the audience.",
        },
        {
            "hook_number": 6,
            "hook_text": f"{prefix}Most people handle this completely wrong — here is the {brand} difference.",
            "style": "Contrast / Unexpected Angle",
            "audience_appeal": "Appeals to self-improvement and optimization mindsets.",
            "why_it_works": "Positions existing habits as flawed, priming curiosity for a better solution.",
        },
        {
            "hook_number": 7,
            "hook_text": f"{prefix}3 reasons why {product} has become a staple for {audience}.",
            "style": "Educational Opener",
            "audience_appeal": "Attracts logical shoppers who appreciate structured, informative content.",
            "why_it_works": "Quantified educational lists set clear expectations and maximize watch time.",
        },
        {
            "hook_number": 8,
            "hook_text": f"{prefix}I tested {product} so you do not have to — here is my honest takeaway.",
            "style": "Empathy and Relatability",
            "audience_appeal": "Taps into creator trust and peer-to-peer recommendation dynamics.",
            "why_it_works": "Classic authentic UGC framing creates immediate approachability and warmth.",
        },
        {
            "hook_number": 9,
            "hook_text": f"{prefix}Skip the complicated alternatives. {product} keeps things simple.",
            "style": "Simplicity Hook",
            "audience_appeal": "Appeals directly to overwhelmed consumers looking for frictionless utility.",
            "why_it_works": "Promises ease of use in a marketplace filled with over-engineered options.",
        },
        {
            "hook_number": 10,
            "hook_text": f"{prefix}Stop settling for {primary_pain.lower()} when {brand} exists.",
            "style": "Empowerment Angle",
            "audience_appeal": f"Inspires {audience} to raise their standards.",
            "why_it_works": "Assertive framing triggers loss aversion and prompts decisive action.",
        },
    ]

    selected_hooks = all_hooks[:num_hooks]

    # 5. Scene-by-Scene UGC Script based on Duration
    clean_hook = selected_hooks[0]["hook_text"].replace(prefix, "")

    if duration <= 15:
        scenes = [
            {
                "scene_number": 1,
                "timestamp": "0:00 - 0:04",
                "visual_direction": f"Creator speaking directly to camera, showing frustration with {primary_pain.lower()}.",
                "dialogue": clean_hook,
                "on_screen_text": f"Tired of {primary_pain[:25]}?",
                "shot_suggestion": "Close-up selfie shot, well-lit natural environment.",
                "transition": "Fast whip-pan to product.",
            },
            {
                "scene_number": 2,
                "timestamp": "0:04 - 0:10",
                "visual_direction": f"Close-up demonstration showing {product} in action highlighting {top_benefit}.",
                "dialogue": f"This is {product} from {brand}. It gives you {top_benefit.lower()} without any hassle.",
                "on_screen_text": f"{brand} | {top_benefit}",
                "shot_suggestion": "Product in-hand, dynamic motion cut.",
                "transition": "Quick jump cut back to creator.",
            },
            {
                "scene_number": 3,
                "timestamp": "0:10 - 0:15",
                "visual_direction": f"Creator smiling, holding {product} with clear CTA overlay on screen.",
                "dialogue": f"If you are ready for a real upgrade, check the link below!" + (f" Use code {offer}!" if offer else ""),
                "on_screen_text": offer if offer else "Link in bio to try it today",
                "shot_suggestion": "Medium smiling hero shot.",
                "transition": "Hold on brand logo card.",
            },
        ]
    elif duration >= 60:
        scenes = [
            {
                "scene_number": 1,
                "timestamp": "0:00 - 0:08",
                "visual_direction": f"Creator in their authentic daily environment highlighting the struggle with {primary_pain.lower()}.",
                "dialogue": f"{clean_hook} For the longest time, dealing with {primary_pain.lower()} was such a headache.",
                "on_screen_text": f"The problem with {primary_pain[:25]}...",
                "shot_suggestion": "Engaging handheld eye-level frame.",
                "transition": "Direct cut to solution.",
            },
            {
                "scene_number": 2,
                "timestamp": "0:08 - 0:22",
                "visual_direction": f"Creator introduces {product} by {brand}, presenting it with genuine enthusiasm.",
                "dialogue": f"Then I discovered {product} by {brand}. What makes this completely different is how it delivers {top_benefit.lower()}.",
                "on_screen_text": f"Meet {product} by {brand}",
                "shot_suggestion": "Close-up unboxing and product inspection.",
                "transition": "Clean split-screen or cut.",
            },
            {
                "scene_number": 3,
                "timestamp": "0:22 - 0:42",
                "visual_direction": f"Hands-on demonstration showing key benefits: {', '.join(benefit_list[:2])}.",
                "dialogue": f"Look at how easy this is. {benefit_list[0] if len(benefit_list) > 0 else 'It works effortlessly'}. Plus, you get reliable everyday quality.",
                "on_screen_text": f"Key Highlight: {benefit_list[0]}",
                "shot_suggestion": "B-roll macro shots of practical product usage.",
                "transition": "Smooth zoom in.",
            },
            {
                "scene_number": 4,
                "timestamp": "0:42 - 0:60",
                "visual_direction": f"Creator re-frames back to camera, summarizing their satisfaction and delivering final CTA.",
                "dialogue": f"If you are part of {audience} and want real results, check out {product} today." + (f" Special offer: {offer}." if offer else ""),
                "on_screen_text": offer if offer else f"Explore {brand} — Link in bio",
                "shot_suggestion": "Warm eye-level medium hero frame with animated pointer graphic.",
                "transition": "End screen with website/handle.",
            },
        ]
    else:  # 30s default
        scenes = [
            {
                "scene_number": 1,
                "timestamp": "0:00 - 0:05",
                "visual_direction": f"Creator expressing frustration with {primary_pain.lower()}, establishing instant empathy.",
                "dialogue": clean_hook,
                "on_screen_text": f"Tired of {primary_pain[:25]}?",
                "shot_suggestion": "Extreme close-up handheld shot.",
                "transition": "Quick snap cut to product.",
            },
            {
                "scene_number": 2,
                "timestamp": "0:05 - 0:12",
                "visual_direction": f"Creator introduces {product} by {brand}, showing sleek packaging in natural lighting.",
                "dialogue": f"I have been using {product} by {brand} and it has completely changed my perspective.",
                "on_screen_text": f"{brand} {product}",
                "shot_suggestion": "Medium close-up on product in hand.",
                "transition": "Soft cinematic cut.",
            },
            {
                "scene_number": 3,
                "timestamp": "0:12 - 0:22",
                "visual_direction": f"Demonstration of {top_benefit.lower()}, showing clear visual satisfaction.",
                "dialogue": f"It delivers {top_benefit.lower()} without any of the usual fuss. It just works.",
                "on_screen_text": top_benefit[:35],
                "shot_suggestion": "Over-the-shoulder action demonstration.",
                "transition": "Cut to smiling creator.",
            },
            {
                "scene_number": 4,
                "timestamp": "0:22 - 0:30",
                "visual_direction": f"Creator smiles at camera, displaying {product} with on-screen CTA badge.",
                "dialogue": f"If you want to experience this for yourself, tap the link in my bio right now!" + (f" Special offer: {offer}!" if offer else ""),
                "on_screen_text": offer if offer else "Link in bio to learn more",
                "shot_suggestion": "Medium hero shot with dynamic lighting.",
                "transition": "Fade to brand logo.",
            },
        ]

    script = {
        "script_title": f"{prefix}The {duration}-Second {product} Story",
        "total_estimated_duration": f"{duration} seconds",
        "content_note": f"{prefix}This is a creative script for a content creator to perform. It is NOT a real customer testimonial.",
        "scenes": scenes,
        "final_cta": f"Link in bio to discover {product} by {brand}." if not offer else f"Use offer '{offer}' via the link in bio!",
        "production_notes": f"{prefix}Film in natural lighting. Maintain a conversational {tone.lower()} cadence. Keep cuts brisk and engaging.",
    }

    # 6. Strategic Categorized CTAs
    ctas = {
        "engagement_ctas": [
            f"{prefix}Would you try {product}? Tell us in the comments!",
            f"{prefix}Tag someone who needs to upgrade to {brand}!",
            f"{prefix}Drop a 🔥 in the comments if you want to see a full breakdown!",
        ],
        "website_visit_ctas": [
            f"{prefix}Explore the full {brand} collection via the link in bio.",
            f"{prefix}Visit our site to see why {audience} love {product}.",
            f"{prefix}Tap below to read complete specifications and user guides.",
        ],
        "product_discovery_ctas": [
            f"{prefix}Discover how {product} makes {top_benefit.lower()} effortless.",
            f"{prefix}Learn more about {brand}'s innovative approach — link in bio.",
            f"{prefix}Take our 30-second quiz to find your ideal match at {brand}.",
        ],
        "purchase_intent_ctas": [
            f"{prefix}Claim your {product} today with easy ordering — link in bio.",
            f"{prefix}Shop now and enjoy {tone_profile['adjective']} quality from {brand}.",
            f"{prefix}Upgrade to {product} now — tap the shop link below.",
        ],
        "recommended_primary_cta": f"{prefix}Tap the link in bio to learn more about {product}." if not offer else f"{prefix}Tap below and use '{offer}' today!",
        "cta_guidance": f"{prefix}Aligned directly with the '{objective}' objective to maximize relevant conversion without high-pressure tactics.",
    }

    # 7. Strategic Captions & Targeted Hashtags
    safe_brand_tag = "#" + re.sub(r"[^a-zA-Z0-9]", "", brand.lower())
    safe_product_tag = "#" + re.sub(r"[^a-zA-Z0-9]", "", product.lower())
    hashtags = [
        safe_brand_tag,
        safe_product_tag,
        "#creatorads",
        "#ugccontent",
        "#honestreview",
        "#productdiscovery",
        "#dailylifestyle",
    ]
    if "reels" in platform.lower():
        hashtags.extend(["#reelsviral", "#instareels"])
    elif "shorts" in platform.lower():
        hashtags.extend(["#youtubeshorts", "#shortsvideo"])

    captions = {
        "concise_caption": f"{prefix}Meet {product} by {brand}: crafted specifically for {audience} who value {top_benefit.lower()}.",
        "extended_caption": (
            f"{prefix}Ready to say goodbye to {primary_pain.lower()}? {product} from {brand} was built to provide "
            f"{top_benefit.lower()} without any unnecessary complications. Whether you are looking for dependability or ease of use, "
            f"this fits effortlessly into your routine. Ready to see the difference for yourself? Link in bio has all the details!"
            + (f" Use code: {offer}." if offer else "")
        ),
        "hashtags": hashtags,
        "caption_cta": f"{prefix}Tap the link in bio to discover {product} today.",
        "hashtag_strategy": f"{prefix}Precision targeting combining brand identifier ({safe_brand_tag}), product category, and platform discoverability tags.",
    }

    # 8. Platform-Specific Adaptations
    platform_adaptation = {
        "instagram_reels": {
            "creative_format": f"{prefix}Vertical 9:16, {min(30, duration)} seconds, snappy creator demo.",
            "opening_hook": f"{prefix}Show {product} solving {primary_pain.lower()} within the first 2 seconds.",
            "script_structure": f"{prefix}Hook (0-3s) -> Problem reveal (3-8s) -> Demonstration of {top_benefit} (8-22s) -> CTA overlay (22-30s).",
            "caption_recommendation": f"{prefix}Crisp 2-sentence caption with sticker/link in bio prompt.",
            "cta": f"{prefix}Tap the link in bio to explore {brand}.",
            "best_practice_notes": f"{prefix}Reels favor dynamic movement and immediate hook delivery in vertical 9:16 format.",
        },
        "youtube_shorts": {
            "creative_format": f"{prefix}Vertical 9:16, educational breakdown or rapid showcase format.",
            "opening_hook": f"{prefix}Lead with an educational question tailored to {audience}.",
            "script_structure": f"{prefix}Question (0-4s) -> Explanation of {brand}'s approach (4-18s) -> Feature walkthrough (18-45s) -> Outro CTA (45-60s).",
            "caption_recommendation": f"{prefix}Clear keyword-rich title with pinned comment directing to product page.",
            "cta": f"{prefix}Check the pinned comment to learn more about {product}.",
            "best_practice_notes": f"{prefix}YouTube Shorts benefit from high-information density and pinned comment links.",
        },
        "paid_social_ads": {
            "creative_format": f"{prefix}4:5 vertical or 1:1 feed square, direct-response layout with high contrast subtitles.",
            "opening_hook": f"{prefix}High-contrast visual showing {top_benefit.lower()} with clear product branding.",
            "script_structure": f"{prefix}Hook (0-3s) -> Key benefit bullets (3-12s) -> Social validation (12-20s) -> Bold CTA button (20-30s).",
            "caption_recommendation": f"{prefix}Concise ad copy focusing on the offer and core value proposition.",
            "cta": f"{prefix}Learn More / Shop Now" if not offer else f"{prefix}Claim Offer ({offer})",
            "best_practice_notes": f"{prefix}Paid social ad creative should communicate value clearly even with audio turned off.",
        },
    }

    # 9. Creative Angles
    creative_angles = [
        {"angle": "Problem and Solution", "description": f"{prefix}Highlight the friction of {primary_pain.lower()} and position {product} as the straightforward resolution."},
        {"angle": "Product Demonstration", "description": f"{prefix}Hands-on walkthrough demonstrating {top_benefit.lower()} in real-world conditions."},
        {"angle": "Educational Breakdown", "description": f"{prefix}Informative overview of how {brand} engineered {product} for {audience}."},
        {"angle": "Lifestyle Integration", "description": f"{prefix}Depict a smooth daily routine where {product} seamlessly fits in."},
        {"angle": "Feature vs. Benefit", "description": f"{prefix}Connect each technical feature of {product} to tangible everyday benefits."},
        {"angle": "Honest Review / UGC", "description": f"{prefix}Authentic creator monologue sharing genuine impressions of {product}."},
    ]

    campaign = {
        "mode": "demo" if label_as_demo else "synthesis",
        "engine": "Multi-Variable Prompt Synthesis Engine (Pure Python)",
        "demo_notice": (
            "DEMO MODE: Generated using PromptAdsCraft AI's Multi-Variable Prompt Synthesis Engine. "
            "Outputs are tailored to your brief using deterministic template intelligence without external API costs or rate limits."
        ),
        "inputs": inputs,
        "brief": brief,
        "hooks": selected_hooks,
        "script": script,
        "ctas": ctas,
        "captions": captions,
        "platform_adaptation": platform_adaptation,
        "creative_angles": creative_angles,
        "quality_review": None,
    }
    campaign["quality_review"] = run_quality_check(campaign)
    return campaign
