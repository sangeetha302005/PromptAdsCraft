"""
validators.py
-------------
Input validation for campaign form data.
Uses Pydantic for structured validation with clear error messages.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re


class CampaignInput(BaseModel):
    """Validated campaign input from the user form."""

    brand_name: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=10, max_length=1000)
    target_audience: str = Field(..., min_length=5, max_length=300)
    objective: str = Field(...)
    platform: str = Field(...)
    tone: str = Field(...)
    language: str = Field(default="English", max_length=50)
    duration: int = Field(...)
    num_hooks: int = Field(default=5, ge=3, le=10)
    benefits: str = Field(..., min_length=5, max_length=800)
    offer: Optional[str] = Field(default="", max_length=200)
    pain_points: Optional[str] = Field(default="", max_length=500)
    avoid_words: Optional[str] = Field(default="", max_length=300)

    @field_validator("brand_name", "product_name")
    @classmethod
    def no_special_injection(cls, v: str) -> str:
        """Basic sanitization: strip leading/trailing whitespace."""
        return v.strip()

    @field_validator("duration")
    @classmethod
    def valid_duration(cls, v: int) -> int:
        if v not in (15, 30, 60):
            raise ValueError("Duration must be 15, 30, or 60 seconds.")
        return v

    @field_validator("platform")
    @classmethod
    def valid_platform(cls, v: str) -> str:
        allowed = ["Instagram Reels", "YouTube Shorts", "Paid Social Ads"]
        if v not in allowed:
            raise ValueError(f"Platform must be one of: {', '.join(allowed)}")
        return v

    @field_validator("tone")
    @classmethod
    def valid_tone(cls, v: str) -> str:
        allowed = ["Friendly", "Humorous", "Professional", "Educational", "Energetic", "Premium"]
        if v not in allowed:
            raise ValueError(f"Tone must be one of: {', '.join(allowed)}")
        return v

    @field_validator("objective")
    @classmethod
    def valid_objective(cls, v: str) -> str:
        allowed = [
            "Product Awareness", "Lead Generation", "Direct Sales",
            "App Downloads", "Website Traffic", "Brand Engagement"
        ]
        if v not in allowed:
            raise ValueError(f"Objective must be one of: {', '.join(allowed)}")
        return v

    @field_validator("description", "benefits")
    @classmethod
    def not_only_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be empty or only whitespace.")
        return v.strip()

    @model_validator(mode="after")
    def sanitize_optional_fields(self) -> "CampaignInput":
        """Ensure optional fields are clean strings."""
        self.offer = (self.offer or "").strip()
        self.pain_points = (self.pain_points or "").strip()
        self.avoid_words = (self.avoid_words or "").strip()
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


def validate_campaign_input(data: dict) -> tuple[Optional[CampaignInput], list[str]]:
    """
    Validate raw form data dict.
    Returns (CampaignInput, []) on success or (None, [errors]) on failure.
    """
    try:
        campaign = CampaignInput(**data)
        return campaign, []
    except Exception as exc:
        errors = []
        if hasattr(exc, "errors"):
            for err in exc.errors():
                field = " > ".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(exc))
        return None, errors
