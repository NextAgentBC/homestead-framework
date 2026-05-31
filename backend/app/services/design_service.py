from copy import deepcopy
from typing import Optional


DEFAULT_SECTIONS = [
    {
        "type": "hero",
        "variant": "split",
        "content": {
            "kicker": "",
            "headline": "",
            "subhead": "A modern site with a daily blog, newsletter, and clean pages — built to grow with you.",
            "cta": {"label": "Read the blog", "href": "/blog"},
            "secondaryCta": {"label": "Contact", "href": "/contact"},
        },
    },
    {
        "type": "features",
        "variant": "cards",
        "content": {
            "heading": "What we do",
            "items": [
                {"icon": "sparkles", "title": "Fresh content", "body": "A steady stream of useful, on-brand articles."},
                {"icon": "mail", "title": "Stay in touch", "body": "Grow an audience with a simple newsletter."},
                {"icon": "shield", "title": "Yours to own", "body": "Your domain, your data, your design."},
            ],
        },
    },
    {
        "type": "cta",
        "variant": "banner",
        "content": {
            "headline": "Ready to get started?",
            "subhead": "Have a question or want to work together?",
            "cta": {"label": "Get in touch", "href": "/contact"},
        },
    },
]


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
            "body": "var(--font-sans), system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            "heading": "var(--font-sans), system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
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
    "sections": DEFAULT_SECTIONS,
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


def normalized_profile(data: dict, industry: str = "education") -> dict:
    base = profile_for_industry(industry)
    profile = deep_merge(base, data or {})
    profile["tokens"] = deep_merge(base["tokens"], profile.get("tokens") or {})
    profile["voice"] = deep_merge(base["voice"], profile.get("voice") or {})
    if not isinstance(profile.get("competitorUrls"), list):
        profile["competitorUrls"] = []
    if not isinstance(profile.get("sections"), list) or not profile.get("sections"):
        profile["sections"] = base.get("sections") or DEFAULT_SECTIONS
    return profile


# Named style families. Each = palette (+ optional radius/layout) and a section
# composition. "Inspired-by" curated looks, not brand clones.
STYLE_PRESETS = {
    "minimal": {
        "name": "Minimal (Apple-inspired)",
        "personality": "calm, spacious, premium, confident",
        "tokens": {
            "colors": {
                "ink": "#1d1d1f", "muted": "#6e6e73", "paper": "#fbfbfd", "surface": "#ffffff",
                "line": "#e6e6eb", "primary": "#0a6cff", "accent": "#e8505b", "highlight": "#f5a623", "link": "#0a6cff",
            },
            "radius": {"card": "18px", "control": "12px", "pill": "999px"},
            "layout": {"density": "spacious", "heroMinHeight": "86vh", "sectionGap": "120px"},
        },
        "voice": {"headlineStyle": "short, bold, benefit-led", "tone": "calm and premium"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {"kicker": "", "headline": "", "subhead": "Clean, fast, and made to last.", "cta": {"label": "Get started", "href": "/contact"}, "secondaryCta": {"label": "Read the blog", "href": "/blog"}}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Why us", "items": [
                {"icon": "gauge", "title": "Fast", "body": "Built for speed and clarity."},
                {"icon": "layers", "title": "Refined", "body": "Considered design, no clutter."},
                {"icon": "shield", "title": "Yours", "body": "Your domain, data, and brand."},
            ]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Start today.", "subhead": "", "cta": {"label": "Get started", "href": "/contact"}}},
        ],
    },
    "bold-dark": {
        "name": "Bold Dark (Tesla-inspired)",
        "personality": "dramatic, high-contrast, confident, modern",
        "tokens": {
            "colors": {
                "ink": "#f4f6fb", "muted": "#9aa7b8", "paper": "#0c0f16", "surface": "#161a23",
                "line": "#283041", "primary": "#e23b3b", "accent": "#4f8cff", "highlight": "#f2c14e", "link": "#6aa8ff",
            },
            "radius": {"card": "14px", "control": "10px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "92vh", "sectionGap": "110px"},
        },
        "voice": {"headlineStyle": "bold, declarative", "tone": "confident and bold"},
        "sections": [
            {"type": "hero", "variant": "fullbleed", "content": {"kicker": "", "headline": "", "subhead": "Power, presence, performance.", "cta": {"label": "Explore", "href": "/blog"}, "secondaryCta": {"label": "Contact", "href": "/contact"}}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Built different", "items": [
                {"icon": "zap", "title": "Bold", "body": "High-contrast, hard to ignore."},
                {"icon": "gauge", "title": "Fast", "body": "Performance you can feel."},
                {"icon": "sparkles", "title": "Modern", "body": "A look that feels current."},
            ]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Experience it.", "subhead": "", "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
    },
    "editorial": {
        "name": "Editorial (warm default)",
        "personality": "clear, useful, trustworthy, modern",
        "tokens": {},
        "sections": DEFAULT_SECTIONS,
    },
}


def apply_style(name: str) -> dict:
    """Return a full design-profile dict for a named style preset (empty dict if unknown)."""
    preset = STYLE_PRESETS.get((name or "").strip().lower())
    if not preset:
        return {}
    overrides = {k: v for k, v in preset.items() if k != "name"}
    profile = deep_merge(DEFAULT_DESIGN_PROFILE, overrides)
    profile["name"] = preset.get("name", profile.get("name"))
    profile["source"] = f"style-preset:{(name or '').strip().lower()}"
    profile["tokens"] = deep_merge(DEFAULT_DESIGN_PROFILE["tokens"], preset.get("tokens") or {})
    profile["sections"] = preset.get("sections") or DEFAULT_SECTIONS
    return profile
