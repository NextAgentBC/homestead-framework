from copy import deepcopy
from typing import Optional


DEFAULT_DESIGN_PROFILE = {
    "name": "Editorial Operator",
    "source": "default",
    "industry": "education",
    "personality": "clear, useful, trustworthy, modern",
    "competitorUrls": [],
    "tokens": {
        "colors": {
            "ink": "#18211f",
            "muted": "#66736f",
            "paper": "#faf8f3",
            "surface": "#ffffff",
            "line": "#d9dfd7",
            "primary": "#216e5f",
            "accent": "#b54945",
            "highlight": "#c79b3b",
            "link": "#356b9f",
        },
        "typography": {
            "body": "Arial, Helvetica, sans-serif",
            "heading": "Arial, Helvetica, sans-serif",
            "mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        },
        "radius": {
            "card": "8px",
            "control": "8px",
            "pill": "999px",
        },
        "layout": {
            "contentMaxWidth": "1120px",
            "heroMinHeight": "58vh",
            "density": "comfortable",
            "cardPadding": "20px",
            "sectionGap": "54px",
        },
    },
    "voice": {
        "headlineStyle": "plain offer or brand name",
        "tone": "practical and calm",
    },
    "notes": "Default profile. Replace this with an industry- and competitor-informed profile.",
}


INDUSTRY_PRESETS = {
    "education": {
        "name": "Focused Learning",
        "personality": "credible, encouraging, structured, aspirational",
        "tokens": {
            "colors": {
                "ink": "#14213d",
                "muted": "#627084",
                "paper": "#f7f8fb",
                "surface": "#ffffff",
                "line": "#d8deea",
                "primary": "#22577a",
                "accent": "#c44536",
                "highlight": "#f3b23c",
                "link": "#2f6fbb",
            },
            "typography": {
                "body": "Inter, Arial, Helvetica, sans-serif",
                "heading": "Inter, Arial, Helvetica, sans-serif",
            },
            "layout": {"density": "comfortable", "heroMinHeight": "56vh"},
        },
        "voice": {"tone": "clear, supportive, evidence-minded"},
    },
    "accounting": {
        "name": "Professional Ledger",
        "personality": "precise, steady, discreet, professional",
        "tokens": {
            "colors": {
                "ink": "#15201d",
                "muted": "#65706d",
                "paper": "#f6f7f4",
                "surface": "#ffffff",
                "line": "#d9dfda",
                "primary": "#1f5f4a",
                "accent": "#8f3f3b",
                "highlight": "#b88a2d",
                "link": "#275f91",
            },
            "typography": {
                "body": "Source Sans 3, Arial, Helvetica, sans-serif",
                "heading": "Source Sans 3, Arial, Helvetica, sans-serif",
            },
            "layout": {"density": "compact", "heroMinHeight": "50vh"},
        },
        "voice": {"tone": "precise, plainspoken, risk-aware"},
    },
    "retail": {
        "name": "Local Retail Signal",
        "personality": "warm, direct, visual, conversion-minded",
        "tokens": {
            "colors": {
                "ink": "#221b17",
                "muted": "#766b64",
                "paper": "#fbf7f0",
                "surface": "#ffffff",
                "line": "#eadfd3",
                "primary": "#a6422b",
                "accent": "#28666e",
                "highlight": "#d79a2b",
                "link": "#2f6b8f",
            },
            "typography": {
                "body": "Nunito Sans, Arial, Helvetica, sans-serif",
                "heading": "Nunito Sans, Arial, Helvetica, sans-serif",
            },
            "layout": {"density": "comfortable", "heroMinHeight": "60vh"},
        },
        "voice": {"tone": "friendly, concrete, product-aware"},
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def profile_for_industry(industry: str, competitor_urls: Optional[list[str]] = None) -> dict:
    normalized = (industry or "education").strip().lower()
    preset = INDUSTRY_PRESETS.get(normalized, {})
    profile = deep_merge(DEFAULT_DESIGN_PROFILE, preset)
    profile["industry"] = normalized
    profile["source"] = "industry-preset"
    profile["competitorUrls"] = competitor_urls or []
    return profile
