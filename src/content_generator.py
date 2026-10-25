"""
content_generator.py
--------------------
Orchestrates campaign content generation.

Routes each generation step to either:
1. Live OpenAI API (when api_key is configured)
2. Deterministic Demo Mode (when no api_key is available)

Demo Mode guarantees:
- Clearly labeled as demo/sample content
- Deterministic and structurally realistic
- Never pretends to be live AI output
- Covers all campaign sections so users can experience the full UX
"""

from __future__ import annotations
import json
import re
from typing import Any, Optional

from .ai_service import AIService, AIServiceError, DemoModeActive, split_prompt
from .prompt_builder import build_prompt
from .quality_checker import run_quality_check
from .synthesis_engine import synthesize_campaign


# ---------------------------------------------------------------------------
# Demo Mode Sample Data
# ---------------------------------------------------------------------------

DEMO_BRIEF = {
    "summary": "[DEMO] A campaign to raise awareness for GlowUp Moisturizer among adults aged 25-40 who care about daily skincare. The campaign will use an educational and friendly tone on Instagram Reels.",
    "main_message": "GlowUp Moisturizer gives your skin the hydration it deserves every single day.",
    "key_selling_points": [
        "Lightweight formula suitable for all skin types",
        "Non-greasy and absorbs quickly",
        "Made with skin-friendly natural ingredients",
    ],
    "audience_insight": "Adults aged 25-40 looking for an effective daily moisturizer that fits into a busy routine without feeling heavy.",
    "creative_direction": "Bright, clean visuals. Friendly and educational tone. Focus on the morning routine context. Avoid clinical language.",
    "flagged_claims": ["[DEMO] No claims have been flagged. Always verify ingredient and efficacy claims before publishing."]
}

DEMO_HOOKS = [
    {"hook_number": 1, "hook_text": "[DEMO] Ever wonder why your skin feels dry 2 hours after moisturizing?", "style": "Curiosity / Open Loop", "audience_appeal": "Addresses a common skincare frustration", "why_it_works": "Opens a knowledge gap that keeps viewers watching to find the answer."},
    {"hook_number": 2, "hook_text": "[DEMO] Your morning routine is missing one step — and your skin knows it.", "style": "Pain Point Acknowledgment", "audience_appeal": "Targets people who feel their skincare isn't working", "why_it_works": "Creates a mild emotional tension that the product can resolve."},
    {"hook_number": 3, "hook_text": "[DEMO] Watch what happens when we apply this to dry skin in real time.", "style": "Demonstration-Led", "audience_appeal": "Visual learners and skeptics who want proof", "why_it_works": "Immediate visual payoff keeps the viewer engaged from the first second."},
    {"hook_number": 4, "hook_text": "[DEMO] A lightweight moisturizer that actually stays with you all day — here's why.", "style": "Bold Honest Statement", "audience_appeal": "People tired of products that over-promise", "why_it_works": "Honest framing builds trust before the product is even named."},
    {"hook_number": 5, "hook_text": "[DEMO] What if your morning skincare took under 60 seconds?", "style": "Question-Based", "audience_appeal": "Busy adults who want simplicity", "why_it_works": "Quantified question immediately frames a desirable outcome."},
    {"hook_number": 6, "hook_text": "[DEMO] Most moisturizers do this wrong — here's the difference.", "style": "Contrast / Unexpected Angle", "audience_appeal": "Skeptics and people who have tried other products", "why_it_works": "Positions the product as a category correction rather than just another option."},
    {"hook_number": 7, "hook_text": "[DEMO] Three ingredients your moisturizer should have — does yours?", "style": "Educational Opener", "audience_appeal": "People who research ingredients and want to understand products", "why_it_works": "Provides immediate value and frames the product as the educational answer."},
    {"hook_number": 8, "hook_text": "[DEMO] I tested this moisturizer every morning for a week — here's what I noticed.", "style": "Empathy and Relatability", "audience_appeal": "People who want honest, relatable product experiences", "why_it_works": "Personal test framing feels authentic and sets up a credible product story."},
    {"hook_number": 9, "hook_text": "[DEMO] Skip the complicated routine. This one step is all your skin needs.", "style": "Simplicity Hook", "audience_appeal": "Busy people overwhelmed by multi-step skincare", "why_it_works": "Directly addresses routine fatigue and promises a simple solution."},
    {"hook_number": 10, "hook_text": "[DEMO] What does a lightweight moisturizer actually feel like? Let me show you.", "style": "Demonstration Question", "audience_appeal": "First-time buyers curious about texture and feel", "why_it_works": "Combines curiosity with a demonstration promise to drive watch time."},
]

DEMO_SCRIPT = {
    "script_title": "[DEMO] The 60-Second GlowUp Morning Routine",
    "total_estimated_duration": "30 seconds",
    "content_note": "[DEMO] This is a creative script for a content creator to perform. It is NOT a real customer testimonial.",
    "scenes": [
        {"scene_number": 1, "timestamp": "0:00 - 0:05", "visual_direction": "Close-up of dry skin on the back of a hand under warm morning light.", "dialogue": "Ever wonder why your skin feels tight two hours after moisturizing?", "on_screen_text": "Sound familiar?", "shot_suggestion": "Extreme close-up", "transition": "Quick cut"},
        {"scene_number": 2, "timestamp": "0:05 - 0:12", "visual_direction": "Creator picks up a small, minimal bottle of GlowUp Moisturizer.", "dialogue": "I have been using GlowUp every morning and it is genuinely lightweight — no greasiness at all.", "on_screen_text": "GlowUp Moisturizer", "shot_suggestion": "Medium close-up on product in hand", "transition": "Soft cut"},
        {"scene_number": 3, "timestamp": "0:12 - 0:22", "visual_direction": "Creator applies moisturizer to the back of their hand. Skin looks immediately smoother.", "dialogue": "See how fast it absorbs? No white cast, no residue. Just hydration.", "on_screen_text": "Absorbs in seconds", "shot_suggestion": "Close-up of application", "transition": "Cut to face cam"},
        {"scene_number": 4, "timestamp": "0:22 - 0:30", "visual_direction": "Creator smiles at camera, holding the product.", "dialogue": "If you want a moisturizer that actually works with your skin, the link is in my bio.", "on_screen_text": "Link in bio", "shot_suggestion": "Medium shot, bright background", "transition": "End"},
    ],
    "final_cta": "Link in bio to learn more about GlowUp Moisturizer.",
    "production_notes": "[DEMO] Film in natural morning light. Keep the pacing conversational. Avoid medical or clinical language."
}

DEMO_CTAS = {
    "engagement_ctas": ["[DEMO] Drop a water drop emoji if your skin needs more hydration!", "[DEMO] Tell us your biggest skincare struggle below."],
    "website_visit_ctas": ["[DEMO] Visit our website to learn more about GlowUp.", "[DEMO] Read the full ingredient list at our site."],
    "product_discovery_ctas": ["[DEMO] See what makes GlowUp different — link in bio.", "[DEMO] Explore the full GlowUp skincare range."],
    "purchase_intent_ctas": ["[DEMO] Get your GlowUp Moisturizer today — link in bio.", "[DEMO] Add to cart and try GlowUp in your routine."],
    "recommended_primary_cta": "[DEMO] Visit our website to learn more — link in bio.",
    "cta_guidance": "[DEMO] This CTA matches a Product Awareness objective by directing traffic to learn more rather than forcing a purchase decision."
}

DEMO_CAPTIONS = {
    "concise_caption": "[DEMO] Your skin deserves better hydration. Meet GlowUp — lightweight, fast-absorbing, and made for everyday.",
    "extended_caption": "[DEMO] Finding a moisturizer that actually works for your lifestyle should not be complicated. GlowUp Moisturizer is lightweight enough for daily wear, absorbs in seconds, and works across all skin types. Made with skin-friendly ingredients, it fits right into your morning routine without any fuss. Ready to try it? Link in bio to learn more.",
    "hashtags": ["#skincare", "#moisturizer", "#dailyskincare", "#glowupskin", "#skincareenthusiast", "#hydration", "#skincareproducts"],
    "caption_cta": "[DEMO] Link in bio to learn more about GlowUp Moisturizer.",
    "hashtag_strategy": "[DEMO] Tags focus on the skincare niche and product category without adding irrelevant trending hashtags."
}

DEMO_PLATFORMS = {
    "instagram_reels": {
        "creative_format": "[DEMO] Vertical 9:16, 15-30 seconds, creator-led demonstration.",
        "opening_hook": "[DEMO] Show dry skin in the first 2 seconds before the product is introduced.",
        "script_structure": "[DEMO] Problem (0-5s) then Product reveal (5-12s) then Demo (12-22s) then CTA (22-30s).",
        "caption_recommendation": "[DEMO] Short, punchy caption with 1-2 emojis and a clear link-in-bio CTA.",
        "cta": "[DEMO] Link in bio to learn more.",
        "best_practice_notes": "[DEMO] Reels generally perform better when the first 2-3 seconds deliver a strong visual hook. Keep captions brief."
    },
    "youtube_shorts": {
        "creative_format": "[DEMO] Vertical 9:16, up to 60 seconds, tutorial or demonstration format.",
        "opening_hook": "[DEMO] Lead with a relatable question or problem statement in the first 3 seconds.",
        "script_structure": "[DEMO] Hook (0-5s) then Explanation (5-20s) then Demo (20-45s) then CTA (45-60s).",
        "caption_recommendation": "[DEMO] Descriptive title. Include product name in first line of description.",
        "cta": "[DEMO] Check the product link in the description below.",
        "best_practice_notes": "[DEMO] Shorts benefit from clear educational structure. Viewers often watch for tips and tutorials."
    },
    "paid_social_ads": {
        "creative_format": "[DEMO] Square 1:1 or vertical 4:5, 15-30 seconds, hook-led with direct CTA.",
        "opening_hook": "[DEMO] Lead with the problem or product visual — no slow brand intro.",
        "script_structure": "[DEMO] Hook (0-3s) then Problem plus solution (3-15s) then Product close-up (15-25s) then CTA overlay (25-30s).",
        "caption_recommendation": "[DEMO] Keep ad copy under 125 characters. Lead with the benefit. Include CTA button text.",
        "cta": "[DEMO] Learn More or Shop Now",
        "best_practice_notes": "[DEMO] Paid ads are viewed in a competitive feed. Clarity and speed matter more than production quality."
    }
}

DEMO_CREATIVE_ANGLES = [
    {"angle": "Problem and Solution", "description": "[DEMO] Open with the dry-skin problem, then position GlowUp as the simple fix."},
    {"angle": "Product Demonstration", "description": "[DEMO] Show the product application in real time with a visible result."},
    {"angle": "Educational Explanation", "description": "[DEMO] Explain why lightweight formulas absorb better without inventing clinical claims."},
    {"angle": "Lifestyle Scenario", "description": "[DEMO] Show a relatable morning routine where GlowUp fits naturally."},
    {"angle": "Feature and Benefit", "description": "[DEMO] List each user-provided feature paired with its real-world benefit."},
    {"angle": "Honest Review Style", "description": "[DEMO] Creator shares their genuine experience in a conversational, non-scripted tone."},
]


def _build_demo_campaign(inputs: dict) -> dict:
    """
    Build a complete, structured demo campaign using the pure-Python
    Multi-Variable Prompt Synthesis Engine:
    Copy = f(Brand, Product, Target Audience, Benefits, Tone, Platform, Duration, Context)
    """
    return synthesize_campaign(inputs, label_as_demo=True)


class ContentGenerator:
    """
    Dual-Engine Campaign Content Orchestrator:
    1. Built-in Multi-Variable Prompt Synthesis Engine (Default / Free / Instant)
       Written in pure Python: Copy = f(Business, Location, Services, Audience, USPs, Tone, Context)
    2. Google Gemini / OpenAI Live AI Engine (if key configured)
    3. Seamless Auto-Fallback: If live API fails, seamlessly synthesizes campaign without crashing
    """

    def __init__(self, ai_service: AIService):
        self.ai = ai_service

    def generate_full_campaign(
        self,
        inputs: dict,
        progress_callback=None,
        force_demo: bool = False,
        fallback_to_synthesis: bool = False,
        label_as_demo: bool = True,
    ) -> dict:
        """
        Generate a complete campaign package.
        progress_callback(step: str, pct: float) is called at each stage if provided.
        Returns the full campaign dict.
        """
        if force_demo or self.ai.is_demo_mode:
            if progress_callback:
                for step, pct in [
                    ("Preparing Multi-Variable Synthesis Engine...", 0.1),
                    ("Synthesizing tailored campaign brief...", 0.2),
                    ("Crafting high-converting hooks...", 0.35),
                    ("Building scene-by-scene UGC script...", 0.5),
                    ("Formulating targeted calls to action...", 0.65),
                    ("Creating captions and strategic hashtags...", 0.75),
                    ("Running content quality and safety checks...", 0.9),
                    ("Done!", 1.0),
                ]:
                    progress_callback(step, pct)
            return synthesize_campaign(inputs, label_as_demo=label_as_demo)

        campaign = {"mode": "live", "inputs": inputs}

        def _step(label: str, pct: float):
            if progress_callback:
                progress_callback(label, pct)

        try:
            _step("Generating campaign brief...", 0.05)
            campaign["brief"] = self._generate_brief(inputs)

            _step("Generating advertising hooks...", 0.2)
            campaign["hooks"] = self._generate_hooks(inputs, campaign["brief"])

            _step("Writing UGC video script...", 0.35)
            primary_hook = campaign["hooks"][0]["hook_text"] if campaign["hooks"] else ""
            primary_cta = "Visit our website to learn more."
            campaign["script"] = self._generate_script(inputs, campaign["brief"], primary_hook, primary_cta)

            _step("Generating calls to action...", 0.5)
            campaign["ctas"] = self._generate_ctas(inputs)
            primary_cta = campaign["ctas"].get("recommended_primary_cta", primary_cta)

            _step("Creating captions and hashtags...", 0.62)
            campaign["captions"] = self._generate_captions(inputs, campaign["brief"], primary_cta)

            _step("Adapting for platforms...", 0.74)
            campaign["platform_adaptation"] = self._generate_platform_adaptation(
                inputs, campaign["brief"], primary_hook, primary_cta
            )

            _step("Generating creative angles...", 0.84)
            campaign["creative_angles"] = self._generate_creative_angles(inputs, campaign["brief"])

            _step("Running quality checks...", 0.93)
            campaign["quality_review"] = run_quality_check(campaign)

            _step("Complete!", 1.0)
            return campaign
        except Exception as exc:
            if fallback_to_synthesis:
                if progress_callback:
                    progress_callback("⚡ Seamlessly falling back to Multi-Variable Synthesis Engine...", 0.95)
                fallback_res = _build_demo_campaign(inputs)
                fallback_res["fallback_notice"] = (
                    f"Live API request encountered an issue ({type(exc).__name__}). "
                    "Successfully generated your complete campaign package using the built-in Multi-Variable Prompt Synthesis Engine."
                )
                if progress_callback:
                    progress_callback("Done!", 1.0)
                return fallback_res
            raise

    def _call_ai(self, template_name: str, variables: dict) -> dict:
        full_prompt = build_prompt(template_name, variables)
        system_prompt, user_prompt = split_prompt(full_prompt)
        return self.ai.generate_json(system_prompt, user_prompt)

    def _generate_brief(self, inputs: dict) -> dict:
        return self._call_ai("campaign_brief.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "description": inputs.get("description", ""),
            "target_audience": inputs.get("target_audience", ""),
            "objective": inputs.get("objective", ""),
            "platform": inputs.get("platform", ""),
            "tone": inputs.get("tone", ""),
            "duration": inputs.get("duration", 30),
            "language": inputs.get("language", "English"),
            "benefits": inputs.get("benefits", ""),
            "offer": inputs.get("offer", ""),
            "pain_points": inputs.get("pain_points", ""),
            "avoid_words": inputs.get("avoid_words", ""),
        })

    def _generate_hooks(self, inputs: dict, brief: dict) -> list:
        result = self._call_ai("hooks.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "target_audience": inputs.get("target_audience", ""),
            "tone": inputs.get("tone", ""),
            "platform": inputs.get("platform", ""),
            "duration": inputs.get("duration", 30),
            "num_hooks": inputs.get("num_hooks", 5),
            "benefits": inputs.get("benefits", ""),
            "brief_summary": brief.get("summary", ""),
            "avoid_words": inputs.get("avoid_words", ""),
        })
        if isinstance(result, list):
            return result
        for key in ["hooks", "results", "items"]:
            if isinstance(result.get(key), list):
                return result[key]
        if "hook_text" in result:
            return [result]
        return []

    def _generate_script(self, inputs: dict, brief: dict, hook_text: str, cta: str) -> dict:
        return self._call_ai("ugc_script.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "target_audience": inputs.get("target_audience", ""),
            "tone": inputs.get("tone", ""),
            "platform": inputs.get("platform", ""),
            "duration": inputs.get("duration", 30),
            "hook_text": hook_text,
            "benefits": inputs.get("benefits", ""),
            "offer": inputs.get("offer", ""),
            "pain_points": inputs.get("pain_points", ""),
            "brief_summary": brief.get("summary", ""),
            "cta": cta,
            "avoid_words": inputs.get("avoid_words", ""),
        })

    def _generate_ctas(self, inputs: dict) -> dict:
        return self._call_ai("cta.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "objective": inputs.get("objective", ""),
            "platform": inputs.get("platform", ""),
            "tone": inputs.get("tone", ""),
            "benefits": inputs.get("benefits", ""),
            "offer": inputs.get("offer", ""),
            "avoid_words": inputs.get("avoid_words", ""),
        })

    def _generate_captions(self, inputs: dict, brief: dict, primary_cta: str) -> dict:
        return self._call_ai("captions.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "platform": inputs.get("platform", ""),
            "tone": inputs.get("tone", ""),
            "benefits": inputs.get("benefits", ""),
            "brief_summary": brief.get("summary", ""),
            "primary_cta": primary_cta,
            "avoid_words": inputs.get("avoid_words", ""),
        })

    def _generate_platform_adaptation(self, inputs: dict, brief: dict, primary_hook: str, primary_cta: str) -> dict:
        return self._call_ai("platform_adaptation.txt", {
            "brand_name": inputs.get("brand_name", ""),
            "product_name": inputs.get("product_name", ""),
            "duration": inputs.get("duration", 30),
            "tone": inputs.get("tone", ""),
            "brief_summary": brief.get("summary", ""),
            "primary_hook": primary_hook,
            "primary_cta": primary_cta,
            "benefits": inputs.get("benefits", ""),
            "avoid_words": inputs.get("avoid_words", ""),
        })

    def _generate_creative_angles(self, inputs: dict, brief: dict) -> list:
        system_prompt = (
            "You are a creative advertising strategist. Generate 6 distinct creative angles "
            "for this campaign. Return a JSON object with key 'angles', containing an array of objects, "
            "each with 'angle' (name) and 'description' (one sentence explaining the approach). "
            "Do not invent claims or statistics. Base angles only on the provided information."
        )
        user_prompt = (
            f"Brand: {inputs.get('brand_name', '')}\n"
            f"Product: {inputs.get('product_name', '')}\n"
            f"Benefits: {inputs.get('benefits', '')}\n"
            f"Audience: {inputs.get('target_audience', '')}\n"
            f"Tone: {inputs.get('tone', '')}\n"
            f"Campaign Summary: {brief.get('summary', '')}"
        )
        try:
            result = self.ai.generate_json(system_prompt, user_prompt)
            angles = result.get("angles", [])
            return angles if isinstance(angles, list) else []
        except Exception:
            return [
                {"angle": "Problem and Solution", "description": "Open with the core problem this product addresses."},
                {"angle": "Product Demonstration", "description": "Show the product in use with visible results."},
                {"angle": "Educational Explanation", "description": "Explain how and why the product works."},
                {"angle": "Lifestyle Scenario", "description": "Show the product fitting naturally into daily life."},
                {"angle": "Feature and Benefit", "description": "Pair each product feature with a user benefit."},
                {"angle": "Contrast", "description": "Show life before and after using the product."},
            ]

    # -----------------------------------------------------------------------
    # Public Feature-Specific Generation & Section Regeneration Methods
    # -----------------------------------------------------------------------

    def generate_brief(self, inputs: dict) -> dict:
        """Generate only the campaign brief."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["brief"]
        return self._generate_brief(inputs)

    def generate_hooks(self, inputs: dict, brief: Optional[dict] = None) -> list:
        """Generate only advertising hooks."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["hooks"]
        if not brief:
            brief = self._generate_brief(inputs)
        return self._generate_hooks(inputs, brief)

    def generate_script(
        self,
        inputs: dict,
        brief: Optional[dict] = None,
        hook_text: Optional[str] = None,
        cta: Optional[str] = None,
    ) -> dict:
        """Generate only the UGC video script."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["script"]
        if not brief:
            brief = self._generate_brief(inputs)
        if not hook_text:
            hooks = self._generate_hooks(inputs, brief)
            hook_text = hooks[0]["hook_text"] if hooks else "Look at this game changer!"
        if not cta:
            cta = "Check the link to learn more!"
        return self._generate_script(inputs, brief, hook_text, cta)

    def generate_ctas(self, inputs: dict) -> dict:
        """Generate only calls to action."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["ctas"]
        return self._generate_ctas(inputs)

    def generate_captions(
        self,
        inputs: dict,
        brief: Optional[dict] = None,
        primary_cta: Optional[str] = None,
    ) -> dict:
        """Generate only captions and hashtags."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["captions"]
        if not brief:
            brief = self._generate_brief(inputs)
        if not primary_cta:
            ctas = self._generate_ctas(inputs)
            primary_cta = ctas.get("recommended_primary_cta", "Learn more today!")
        return self._generate_captions(inputs, brief, primary_cta)

    def generate_platform_adaptation(
        self,
        inputs: dict,
        brief: Optional[dict] = None,
        primary_hook: Optional[str] = None,
        primary_cta: Optional[str] = None,
    ) -> dict:
        """Generate only platform-specific adaptations."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["platform_adaptation"]
        if not brief:
            brief = self._generate_brief(inputs)
        if not primary_hook:
            hooks = self._generate_hooks(inputs, brief)
            primary_hook = hooks[0]["hook_text"] if hooks else "Stop scrolling!"
        if not primary_cta:
            ctas = self._generate_ctas(inputs)
            primary_cta = ctas.get("recommended_primary_cta", "Learn more today!")
        return self._generate_platform_adaptation(inputs, brief, primary_hook, primary_cta)

    def generate_creative_angles(self, inputs: dict, brief: Optional[dict] = None) -> list:
        """Generate alternative creative angles."""
        if self.ai.is_demo_mode:
            synth = synthesize_campaign(inputs, label_as_demo=False)
            return synth["creative_angles"]
        if not brief:
            brief = self._generate_brief(inputs)
        return self._generate_creative_angles(inputs, brief)

