from copy import deepcopy
from typing import Optional


# Font faces are loaded once in the frontend layout and exposed as CSS vars.
# Templates choose a face through their typography tokens.
SANS = "var(--font-sans), system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
SERIF = "var(--font-display), Georgia, 'Times New Roman', serif"
GROTESK = "var(--font-grotesk), var(--font-sans), system-ui, sans-serif"
# Warm characterful serif (restaurant / beauty / editorial) and a tall athletic
# condensed (fitness / sport). Loaded once in the frontend layout.
FRAUNCES = "var(--font-fraunces), var(--font-display), Georgia, 'Times New Roman', serif"
CONDENSED = "var(--font-condensed), 'Oswald', 'Arial Narrow', var(--font-sans), system-ui, sans-serif"
MONO = "var(--font-mono-stack, ui-monospace), SFMono-Regular, Menlo, Monaco, Consolas, monospace"


DEFAULT_STATS_SECTION = {
    "type": "stats",
    "content": {
        "items": [
            {"value": "Daily", "label": "Fresh content"},
            {"value": "1-click", "label": "Publish"},
            {"value": "100%", "label": "Yours to own"},
            {"value": "SEO", "label": "Built in"},
        ]
    },
}

DEFAULT_LOGOS_SECTION = {
    "type": "logos",
    "content": {
        "heading": "Built with",
        "items": [{"label": "Next.js"}, {"label": "Flask"}, {"label": "PostgreSQL"}, {"label": "Cloudflare"}],
    },
}

DEFAULT_SECTIONS = [
    {
        "type": "hero",
        "variant": "split",
        "content": {
            "kicker": "Your site, your rules",
            "headline": "A website you fully own.",
            "headlineAccent": "Publish daily. Grow steadily.",
            "subhead": "A modern site with a daily blog, newsletter, and clean pages — built to grow with you.",
            "cta": {"label": "Read the blog", "href": "/blog"},
            "secondaryCta": {"label": "Contact", "href": "/contact"},
        },
    },
    DEFAULT_STATS_SECTION,
    DEFAULT_LOGOS_SECTION,
    {
        "type": "problem",
        "variant": "cards",
        "content": {
            "heading": "Sound familiar?",
            "subhead": "The usual website setup gets in the way more than it helps.",
            "items": [
                {"icon": "layers", "title": "Scattered tools", "body": "Content, email, and your site live in three different places."},
                {"icon": "gauge", "title": "Slow to update", "body": "Every small change means waiting on someone else."},
                {"icon": "shield", "title": "Not really yours", "body": "Your audience and data sit on someone else's platform."},
            ],
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
        "type": "comparison",
        "content": {
            "heading": "Why this framework",
            "left": {"title": "The usual way", "items": ["Locked into a platform", "Pay per seat, forever", "Hard to customize", "Your data is theirs"]},
            "right": {"title": "Homestead", "items": ["Your own server + domain", "One-time setup, no rent", "Fully yours to restyle", "You own everything"]},
        },
    },
    {
        "type": "testimonials",
        "content": {
            "heading": "What people say",
            "items": [
                {"quote": "Set up our whole site in an afternoon — and it looks the part.", "author": "A. Founder", "role": "Small studio"},
                {"quote": "The daily posts keep coming without me lifting a finger.", "author": "M. Writer", "role": "Creator"},
                {"quote": "Finally a site I actually own end to end.", "author": "J. Owner", "role": "Local business"},
            ],
        },
    },
    {
        "type": "pricing",
        "content": {
            "heading": "Simple to run",
            "subhead": "Example tiers — make them your own.",
            "items": [
                {"name": "Starter", "price": "$0", "period": "/forever", "features": ["1 site", "Daily blog", "Newsletter"], "cta": {"label": "Get started", "href": "/contact"}},
                {"name": "Pro", "price": "$99", "period": "/one-time", "features": ["Custom design", "Unlimited pages", "Priority support"], "featured": True, "cta": {"label": "Choose Pro", "href": "/contact"}},
                {"name": "Agency", "price": "Custom", "period": "", "features": ["Multiple sites", "White-label", "Dedicated help"], "cta": {"label": "Contact us", "href": "/contact"}},
            ],
        },
    },
    {
        "type": "faq",
        "content": {
            "heading": "Questions",
            "items": [
                {"q": "Do I need to know how to code?", "a": "No — manage pages, blog, and design by chatting with your agent. Code is there if you want it."},
                {"q": "Is it really mine?", "a": "Yes. It runs on your server and domain; your content and audience are yours."},
                {"q": "Can I change the whole look?", "a": "Yes — switch a style preset or fine-tune colors, fonts, and sections anytime."},
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
            "line": "#e2e6dd",
            "primary": "#216e5f",
            "accent": "#b54945",
            "highlight": "#c79b3b",
            "link": "#356b9f",
            # Inverse surface = the deep "contrast band" behind a fullbleed hero
            # and the CTA banner. Tokenized so a template/agent can recolor it
            # instead of it being hard-coded dark in the stylesheet.
            "surfaceInverse": "#0b0f1a",
            "inkInverse": "#f6f9ff",
            # Text/icon color that sits on a primary-filled surface (buttons,
            # checkmarks). Lets light-primary palettes flip to dark on-color.
            "onPrimary": "#ffffff",
        },
        "typography": {
            "body": SANS,
            "heading": SANS,
            "mono": MONO,
        },
        "radius": {
            "card": "16px",
            "control": "11px",
            "pill": "999px",
        },
        "layout": {
            "contentMaxWidth": "1120px",
            "heroMinHeight": "72vh",
            "density": "comfortable",
            "cardPadding": "24px",
            "sectionGap": "104px",
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
                "line": "#dde3ee",
                "primary": "#22577a",
                "accent": "#c44536",
                "highlight": "#f3b23c",
                "link": "#2f6fbb",
            },
            "typography": {"body": SANS, "heading": SANS},
            "layout": {"density": "comfortable", "heroMinHeight": "70vh"},
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
                "line": "#dde2dc",
                "primary": "#1f5f4a",
                "accent": "#8f3f3b",
                "highlight": "#b88a2d",
                "link": "#275f91",
            },
            "typography": {"body": SANS, "heading": SANS},
            "layout": {"density": "compact", "heroMinHeight": "62vh"},
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
                "line": "#ece1d4",
                "primary": "#a6422b",
                "accent": "#28666e",
                "highlight": "#d79a2b",
                "link": "#2f6b8f",
            },
            "typography": {"body": SANS, "heading": SANS},
            "layout": {"density": "comfortable", "heroMinHeight": "66vh"},
        },
        "voice": {"tone": "friendly, concrete, product-aware"},
    },
    "nonprofit": {
        "name": "Community Cause",
        "personality": "warm, hopeful, community-minded, sincere",
        "tokens": {
            "colors": {
                "ink": "#1e2a22", "muted": "#5f6f63", "paper": "#f4f7f1", "surface": "#ffffff",
                "line": "#dde6d8", "primary": "#2f7d4f", "accent": "#d98b3b", "highlight": "#e0b13c", "link": "#2f6f8f",
            },
            "typography": {"body": SANS, "heading": SANS},
            "layout": {"density": "comfortable", "heroMinHeight": "70vh"},
        },
        "voice": {"tone": "warm, hopeful, action-oriented"},
    },
    "hospitality": {
        "name": "Open Door Hospitality",
        "personality": "inviting, relaxed, refined, generous",
        "tokens": {
            "colors": {
                "ink": "#14222b", "muted": "#5b6b73", "paper": "#f3f7f8", "surface": "#ffffff",
                "line": "#d9e6e8", "primary": "#1f7a8c", "accent": "#c98a3e", "highlight": "#e0b15a", "link": "#2f7f9a",
            },
            "typography": {"body": SANS, "heading": SERIF},
            "layout": {"density": "comfortable", "heroMinHeight": "78vh"},
        },
        "voice": {"tone": "inviting, relaxed, gracious"},
    },
    "construction": {
        "name": "Solid Ground Trades",
        "personality": "dependable, straightforward, hardworking, sturdy",
        "tokens": {
            "colors": {
                "ink": "#1d1b16", "muted": "#6f685c", "paper": "#f6f4ef", "surface": "#ffffff",
                "line": "#e4dccd", "primary": "#b5631e", "accent": "#2f4858", "highlight": "#e0a93c", "link": "#2f5f7a",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "layout": {"density": "compact", "heroMinHeight": "68vh"},
        },
        "voice": {"tone": "dependable, plainspoken, results-first"},
    },
}


# Industry name (and common synonyms) → a full style template key. Lets
# profile_for_industry("dental clinic" → "healthcare") return a complete,
# section-filled template instead of just a recolor. Industries NOT listed here
# (education / accounting / retail / nonprofit / …) keep their token-only preset.
INDUSTRY_STYLE_ALIASES = {
    "tech": "tech", "saas": "tech", "software": "tech", "technology": "tech", "startup": "tech", "ai": "tech",
    "healthcare": "healthcare", "health": "healthcare", "medical": "healthcare", "clinic": "healthcare",
    "dental": "healthcare", "dentist": "healthcare", "wellness": "healthcare", "therapy": "healthcare",
    "restaurant": "restaurant", "food": "restaurant", "cafe": "restaurant", "coffee": "restaurant",
    "bakery": "restaurant", "catering": "restaurant", "bar": "restaurant",
    "realestate": "realestate", "real-estate": "realestate", "real estate": "realestate",
    "property": "realestate", "realty": "realestate", "architecture": "realestate", "interior": "realestate",
    "fitness": "fitness", "gym": "fitness", "sport": "fitness", "sports": "fitness", "trainer": "fitness", "yoga": "fitness",
    "beauty": "beauty", "salon": "beauty", "spa": "beauty", "cosmetics": "beauty", "skincare": "beauty", "hair": "beauty",
    "legal": "legal", "law": "legal", "lawyer": "legal", "attorney": "legal", "advisory": "legal", "consulting": "legal",
    "creative": "creative", "agency": "creative", "studio": "creative", "design": "creative",
    "portfolio": "creative", "marketing": "creative", "photography": "creative",
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
    # If the industry maps to a full style template, use it as the base so the
    # site gets a complete, section-filled design — not just a recolor. An
    # industry that IS a preset key (education, beauty, nonprofit, finance, …)
    # uses that preset directly; aliases (dental→healthcare, gym→fitness, …) map
    # first. Otherwise fall through to the token-only INDUSTRY_PRESETS recolor.
    style_key = INDUSTRY_STYLE_ALIASES.get(normalized) or (normalized if normalized in STYLE_PRESETS else None)
    if style_key:
        styled = apply_style(style_key)
        if styled:
            styled["industry"] = normalized
            styled["source"] = "industry-preset"
            styled["competitorUrls"] = competitor_urls or []
            return styled
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


# =====================================================================
# Named style families — switchable templates. Each = a full palette
# (+ radius / layout / typography) and a section composition. The frontend
# derives light/dark mode from the palette and a [data-theme] hook from the
# preset key, so each template renders with its own depth and typographic
# character — not just a recolor. "Inspired-by" curated looks, never clones.
# =====================================================================
STYLE_PRESETS = {
    # Aurora — calm, spacious, premium. Apple / Linear / Stripe energy.
    "minimal": {
        "name": "Aurora — Minimal",
        "personality": "calm, spacious, premium, confident",
        "tokens": {
            "colors": {
                "ink": "#0b1220", "muted": "#5b6573", "paper": "#fbfcfe", "surface": "#ffffff",
                "line": "#e7e9f0", "primary": "#2563eb", "accent": "#6366f1", "highlight": "#f59e0b", "link": "#2563eb",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "20px", "control": "13px", "pill": "999px"},
            "layout": {"density": "spacious", "heroMinHeight": "88vh", "sectionGap": "128px", "contentMaxWidth": "1120px", "cardPadding": "28px"},
        },
        "voice": {"headlineStyle": "short, bold, benefit-led", "tone": "calm and premium"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "Premium by default",
                "headline": "Clean, fast,", "headlineAccent": "made to last.",
                "subhead": "A refined site that loads fast, reads beautifully, and stays out of the way — so your work is the thing people notice.",
                "cta": {"label": "Get started", "href": "/contact"}, "secondaryCta": {"label": "Read the blog", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "100", "label": "Lighthouse-ready"}, {"value": "Daily", "label": "Fresh writing"},
                {"value": "SEO", "label": "Built in"}, {"value": "0", "label": "Platform lock-in"}]}},
            DEFAULT_LOGOS_SECTION,
            {"type": "features", "variant": "minimal", "content": {"heading": "Everything needed, nothing extra.", "subhead": "A calmer stack for publishing and keeping your audience close.", "items": [
                {"icon": "gauge", "title": "Fast", "body": "Built for speed and clarity on every device."},
                {"icon": "layers", "title": "Refined", "body": "Considered type, spacing, and color — no clutter."},
                {"icon": "shield", "title": "Yours", "body": "Your domain, your data, your brand."}]}},
            {"type": "comparison", "content": {"heading": "Simple beats scattered.",
                "left": {"title": "Before", "items": ["Separate site and newsletter tools", "Monthly platform rent", "Hard-to-edit templates", "Data spread across services"]},
                "right": {"title": "This site", "items": ["One clean publishing workflow", "Runs on your own stack", "Design updates instantly", "Content stays portable"]}}},
            {"type": "faq", "content": {"heading": "Questions", "items": [
                {"q": "Do I need to code?", "a": "No — manage pages, posts, and design by chatting with your agent."},
                {"q": "Can I change the whole look?", "a": "Yes — switch a template or fine-tune colors, fonts, and sections anytime."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Start today.", "subhead": "Spin up a clean site and grow from there.", "cta": {"label": "Get started", "href": "/contact"}}},
        ],
    },
    # Eclipse — dramatic dark, high-contrast, modern. Tesla / Vercel energy.
    "bold-dark": {
        "name": "Eclipse — Bold Dark",
        "personality": "dramatic, high-contrast, confident, modern",
        "tokens": {
            "colors": {
                "ink": "#f4f6fb", "muted": "#9aa6bd", "paper": "#0b0d14", "surface": "#14171f",
                "line": "#272c3a", "primary": "#7c5cff", "accent": "#ff5d8f", "highlight": "#f2c14e", "link": "#a899ff",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "radius": {"card": "16px", "control": "11px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "94vh", "sectionGap": "118px", "contentMaxWidth": "1140px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "bold, declarative", "tone": "confident and bold"},
        "sections": [
            {"type": "hero", "variant": "fullbleed", "content": {
                "badge": "Bold by design",
                "headline": "Power. Presence.", "headlineAccent": "Performance.",
                "subhead": "A dramatic, high-contrast presence that commands attention the moment it loads.",
                "cta": {"label": "Explore", "href": "/blog"}, "secondaryCta": {"label": "Contact", "href": "/contact"}}},
            {"type": "stats", "content": {"items": [
                {"value": "60fps", "label": "Smooth by default"}, {"value": "Dark", "label": "Native mode"},
                {"value": "AA", "label": "Contrast-checked"}, {"value": "1", "label": "Site you own"}]}},
            DEFAULT_LOGOS_SECTION,
            {"type": "features", "variant": "minimal", "content": {"heading": "Built different.", "subhead": "High contrast, high clarity, hard to ignore.", "items": [
                {"icon": "zap", "title": "Bold", "body": "Deep canvas, electric accents, real hierarchy."},
                {"icon": "gauge", "title": "Fast", "body": "Performance you can feel on first paint."},
                {"icon": "sparkles", "title": "Modern", "body": "A look that feels current, not templated."}]}},
            {"type": "comparison", "content": {"heading": "Stand out, on purpose.",
                "left": {"title": "Generic theme", "items": ["Looks like everyone else", "Flat, low contrast", "Light-only", "Slow, heavy assets"]},
                "right": {"title": "Eclipse", "items": ["A presence of its own", "Dramatic depth & glow", "Dark-native design", "Fast, considered build"]}}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Experience it.", "subhead": "See the difference a real design makes.", "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
    },
    # Atelier — warm, editorial, content-first. Serif display + drop-cap long-form.
    "editorial": {
        "name": "Atelier — Editorial",
        "personality": "warm, literary, considered, trustworthy",
        "tokens": {
            "colors": {
                "ink": "#241d18", "muted": "#6f655c", "paper": "#f7f2ea", "surface": "#fffdf9",
                "line": "#e7dccc", "primary": "#a14d2a", "accent": "#3f6f63", "highlight": "#bb8a36", "link": "#9c4a22",
            },
            "typography": {"body": SANS, "heading": SERIF},
            "radius": {"card": "12px", "control": "9px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "72vh", "sectionGap": "108px", "contentMaxWidth": "1080px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "editorial, human, specific", "tone": "warm and considered"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Words that carry",
                "headline": "Writing worth", "headlineAccent": "returning to.",
                "subhead": "A warm, editorial home for essays, notes, and a newsletter — designed to be read, not just scrolled past.",
                "cta": {"label": "Read the blog", "href": "/blog"}, "secondaryCta": {"label": "Say hello", "href": "/contact"}}},
            {"type": "stats", "content": {"items": [
                {"value": "Daily", "label": "New writing"}, {"value": "1", "label": "Calm home"},
                {"value": "0", "label": "Ads or trackers"}, {"value": "100%", "label": "Yours"}]}},
            {"type": "problem", "variant": "cards", "content": {"heading": "Most sites fight the reader.", "subhead": "Cramped measures, restless layouts, borrowed identities.", "items": [
                {"icon": "layers", "title": "Cluttered", "body": "Ten things shouting before the first sentence lands."},
                {"icon": "gauge", "title": "Restless", "body": "Pop-ups and motion that pull attention away."},
                {"icon": "book", "title": "Forgettable", "body": "Nothing that feels like a place of its own."}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "Made for reading.", "items": [
                {"icon": "book", "title": "Real typography", "body": "A serif display and a generous measure, set with care."},
                {"icon": "mail", "title": "A quiet newsletter", "body": "Let readers follow without another platform."},
                {"icon": "shield", "title": "A place of your own", "body": "Your words, your domain, your design."}]}},
            {"type": "testimonials", "content": {"heading": "Readers notice.", "items": [
                {"quote": "It finally reads like a magazine, not a dashboard.", "author": "R. Ellison", "role": "Essayist"},
                {"quote": "People actually finish the posts now.", "author": "D. Marsh", "role": "Newsletter writer"},
                {"quote": "It feels like mine — not a template.", "author": "P. Quan", "role": "Studio owner"}]}},
            {"type": "faq", "content": {"heading": "Good to know", "items": [
                {"q": "Can I write in Markdown?", "a": "Yes — posts and pages are Markdown, rendered into this editorial type system."},
                {"q": "Is the look fixed?", "a": "No — switch templates or fine-tune type, color, and sections whenever you like."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Start writing.", "subhead": "A calm, beautiful home for your words.", "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
    },
    # Meridian — structured, trustworthy, B2B. Denser navy/teal corporate look.
    "corporate": {
        "name": "Meridian — Professional",
        "personality": "trustworthy, structured, credible, precise",
        "tokens": {
            "colors": {
                "ink": "#101828", "muted": "#586172", "paper": "#f4f7fb", "surface": "#ffffff",
                "line": "#dce3ef", "primary": "#1c4e8a", "accent": "#0f766e", "highlight": "#b7791f", "link": "#1c5fb0",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "12px", "control": "9px", "pill": "999px"},
            "layout": {"density": "compact", "heroMinHeight": "70vh", "sectionGap": "100px", "contentMaxWidth": "1180px", "cardPadding": "24px"},
        },
        "voice": {"headlineStyle": "clear, credible, outcome-led", "tone": "professional and precise"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Built for serious work",
                "headline": "A credible home for", "headlineAccent": "your business.",
                "subhead": "Clear structure, trustworthy design, and the pages your customers expect — set up once, fully owned.",
                "cta": {"label": "Book a call", "href": "/contact"}, "secondaryCta": {"label": "See the blog", "href": "/blog"}}},
            {"type": "logos", "content": {"heading": "A dependable stack", "items": [{"label": "Next.js"}, {"label": "Flask"}, {"label": "PostgreSQL"}, {"label": "Cloudflare"}]}},
            {"type": "stats", "content": {"items": [
                {"value": "99.9%", "label": "Uptime-ready"}, {"value": "<1s", "label": "Typical load"},
                {"value": "SEO", "label": "Built in"}, {"value": "24/7", "label": "Always on"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "What you get", "subhead": "The essentials, done properly.", "items": [
                {"icon": "shield", "title": "Trust by design", "body": "Clean structure and accessible contrast throughout."},
                {"icon": "gauge", "title": "Fast & reliable", "body": "Lightweight pages that load quickly, everywhere."},
                {"icon": "layers", "title": "Easy to extend", "body": "Add pages, services, and posts as you grow."}]}},
            {"type": "comparison", "content": {"heading": "Why teams choose this",
                "left": {"title": "Page builders", "items": ["Monthly per-seat pricing", "Heavy, slow pages", "Generic look", "Locked-in content"]},
                "right": {"title": "Meridian", "items": ["One-time setup", "Fast, lean delivery", "A credible identity", "Portable, owned data"]}}},
            {"type": "testimonials", "content": {"heading": "Trusted by operators", "items": [
                {"quote": "It looks like a company we'd hire.", "author": "S. Patel", "role": "Founder, consultancy"},
                {"quote": "Set up once, runs itself since.", "author": "K. Brooks", "role": "Ops lead"},
                {"quote": "Fast, clean, and clearly ours.", "author": "L. Romano", "role": "Managing director"}]}},
            {"type": "pricing", "content": {"heading": "Straightforward pricing", "subhead": "Example tiers — adapt to your offer.",
                "items": [
                    {"name": "Starter", "price": "$0", "period": "/forever", "features": ["1 site", "Blog + newsletter", "Core pages"], "cta": {"label": "Get started", "href": "/contact"}},
                    {"name": "Business", "price": "$99", "period": "/one-time", "features": ["Custom design", "Unlimited pages", "Priority support"], "featured": True, "cta": {"label": "Choose Business", "href": "/contact"}},
                    {"name": "Enterprise", "price": "Custom", "period": "", "features": ["Multiple sites", "White-label", "Dedicated help"], "cta": {"label": "Contact sales", "href": "/contact"}}]}},
            {"type": "faq", "content": {"heading": "Common questions", "items": [
                {"q": "Can we use our own domain?", "a": "Yes — it runs on your domain and server, behind Cloudflare."},
                {"q": "Can you match our brand?", "a": "Yes — colors, fonts, and sections are all adjustable."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Ready to look the part?", "subhead": "Set up a credible site you fully own.", "cta": {"label": "Book a call", "href": "/contact"}}},
        ],
    },
    # Nimbus — modern SaaS / tech. Indigo + cyan, geometric grotesk, product-forward.
    "tech": {
        "name": "Nimbus — Tech / SaaS",
        "personality": "modern, precise, product-forward, confident",
        "tokens": {
            "colors": {
                "ink": "#0d1424", "muted": "#5a6478", "paper": "#f7f9fc", "surface": "#ffffff",
                "line": "#e6eaf2", "primary": "#4f46e5", "accent": "#06b6d4", "highlight": "#f59e0b", "link": "#4f46e5",
                "surfaceInverse": "#0b1020", "inkInverse": "#eef2ff", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "radius": {"card": "18px", "control": "12px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "88vh", "sectionGap": "120px", "contentMaxWidth": "1140px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "crisp, benefit-led, product-forward", "tone": "confident and modern"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "Ship faster",
                "headline": "The platform your", "headlineAccent": "team will love.",
                "subhead": "Launch, measure, and iterate from one clean workspace — no glue code, no busywork.",
                "cta": {"label": "Start free", "href": "/contact"}, "secondaryCta": {"label": "See how it works", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "10x", "label": "Faster setup"}, {"value": "99.9%", "label": "Uptime"},
                {"value": "<200ms", "label": "API latency"}, {"value": "SOC 2", "label": "Ready"}]}},
            {"type": "logos", "content": {"heading": "Integrates with your stack", "items": [{"label": "Slack"}, {"label": "GitHub"}, {"label": "Stripe"}, {"label": "Zapier"}, {"label": "Notion"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Everything you need to scale.", "subhead": "Built for teams that move fast and break nothing.", "items": [
                {"icon": "zap", "title": "Fast by default", "body": "Sub-second loads and a snappy API your users feel."},
                {"icon": "shield", "title": "Secure & compliant", "body": "Encryption, audit logs, and SSO out of the box."},
                {"icon": "gauge", "title": "Observable", "body": "Dashboards and alerts so nothing slips by."}]}},
            {"type": "comparison", "content": {"heading": "Why teams switch",
                "left": {"title": "Stitched-together tools", "items": ["Five dashboards, no source of truth", "Brittle integrations", "Per-seat pricing creep", "Slow, generic support"]},
                "right": {"title": "Nimbus", "items": ["One workspace, one truth", "Native integrations", "Predictable pricing", "Engineers on support"]}}},
            {"type": "pricing", "content": {"heading": "Pricing that scales with you", "subhead": "Start free. Upgrade when it pays for itself.",
                "items": [
                    {"name": "Free", "price": "$0", "period": "/mo", "features": ["1 project", "Community support", "Core API"], "cta": {"label": "Get started", "href": "/contact"}},
                    {"name": "Team", "price": "$49", "period": "/mo", "features": ["Unlimited projects", "SSO + audit logs", "Priority support"], "featured": True, "cta": {"label": "Start trial", "href": "/contact"}},
                    {"name": "Enterprise", "price": "Custom", "period": "", "features": ["SLA + SOC 2", "Dedicated infra", "Solutions engineer"], "cta": {"label": "Talk to sales", "href": "/contact"}}]}},
            {"type": "faq", "content": {"heading": "Questions", "items": [
                {"q": "How long does setup take?", "a": "Most teams are live the same day — connect your stack and go."},
                {"q": "Can I self-host?", "a": "Yes — it runs on your own server and domain, fully owned."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Ready to ship faster?", "subhead": "Spin up a workspace in minutes.", "cta": {"label": "Start free", "href": "/contact"}}},
        ],
    },
    # Vitalis — calm, trustworthy healthcare. Teal + soft blue, rounded, patient-first.
    "healthcare": {
        "name": "Vitalis — Health & Care",
        "personality": "reassuring, clean, caring, credible",
        "tokens": {
            "colors": {
                "ink": "#102a2c", "muted": "#566a6b", "paper": "#f1f8f6", "surface": "#ffffff",
                "line": "#d8e8e4", "primary": "#0d7e77", "accent": "#2f6fb0", "highlight": "#f0a838", "link": "#0e7a86",
                "surfaceInverse": "#0c1f21", "inkInverse": "#ecf7f4", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "22px", "control": "14px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "72vh", "sectionGap": "104px", "contentMaxWidth": "1120px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "warm, plain, reassuring", "tone": "caring and clear"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Care you can trust",
                "headline": "Health care that puts", "headlineAccent": "you first.",
                "subhead": "Friendly, modern care with same-week appointments and clinicians who actually listen.",
                "cta": {"label": "Book an appointment", "href": "/contact"}, "secondaryCta": {"label": "Our services", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "30k+", "label": "Patients cared for"}, {"value": "Same-week", "label": "Appointments"},
                {"value": "4.9★", "label": "Patient rating"}, {"value": "15+", "label": "Years of care"}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "Care, the way it should be", "subhead": "Modern medicine with a human touch.", "items": [
                {"icon": "shield", "title": "Trusted clinicians", "body": "Board-certified providers who take the time to listen."},
                {"icon": "gauge", "title": "Short wait times", "body": "Same-week appointments and on-time visits."},
                {"icon": "cloud", "title": "Care anywhere", "body": "Secure telehealth and an easy patient portal."}]}},
            {"type": "problem", "variant": "cards", "content": {"heading": "Tired of the runaround?", "subhead": "Care shouldn't be this hard.", "items": [
                {"icon": "layers", "title": "Long waits", "body": "Weeks for an appointment, hours in the lobby."},
                {"icon": "gauge", "title": "Rushed visits", "body": "Ten minutes and out the door with no answers."},
                {"icon": "shield", "title": "Confusing bills", "body": "Surprise charges and no one to explain them."}]}},
            {"type": "testimonials", "content": {"heading": "What our patients say", "items": [
                {"quote": "They actually listened and explained everything. I felt cared for.", "author": "Maria L.", "role": "Patient"},
                {"quote": "Booked Monday, seen Wednesday. Unheard of.", "author": "James P.", "role": "Patient"},
                {"quote": "The portal makes everything simple — results, refills, messages.", "author": "Aisha K.", "role": "Patient"}]}},
            {"type": "faq", "content": {"heading": "Common questions", "items": [
                {"q": "Do you take my insurance?", "a": "We accept most major plans — call and we'll confirm your coverage in minutes."},
                {"q": "Can I see someone this week?", "a": "Yes — we hold same-week slots for new and existing patients."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Your health, looked after.", "subhead": "Book a visit in under two minutes.", "cta": {"label": "Book now", "href": "/contact"}}},
        ],
    },
    # Saffron — warm, appetizing restaurant / café. Paprika + olive, Fraunces serif.
    "restaurant": {
        "name": "Saffron — Restaurant & Café",
        "personality": "warm, appetizing, inviting, characterful",
        "tokens": {
            "colors": {
                "ink": "#2a1a12", "muted": "#7a685c", "paper": "#fbf3e8", "surface": "#fffaf2",
                "line": "#ecdcc7", "primary": "#c0461f", "accent": "#5c6b3a", "highlight": "#d9a13a", "link": "#a8431f",
                "surfaceInverse": "#20120b", "inkInverse": "#fbeede", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": FRAUNCES},
            "radius": {"card": "14px", "control": "10px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "84vh", "sectionGap": "108px", "contentMaxWidth": "1100px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "warm, sensory, inviting", "tone": "warm and appetizing"},
        "sections": [
            {"type": "hero", "variant": "fullbleed", "content": {
                "badge": "Now taking reservations",
                "headline": "Seasonal plates,", "headlineAccent": "made to gather.",
                "subhead": "A neighborhood kitchen serving honest, market-fresh food and a short, lovely wine list.",
                "cta": {"label": "Reserve a table", "href": "/contact"}, "secondaryCta": {"label": "See the menu", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "Daily", "label": "Market-fresh"}, {"value": "Est. 2014", "label": "Family-run"},
                {"value": "4.8★", "label": "1,200 reviews"}, {"value": "Local", "label": "Sourced"}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "What's cooking", "subhead": "A menu that changes with the season.", "items": [
                {"icon": "sparkles", "title": "Wood-fired", "body": "Blistered crusts and smoky vegetables from the open hearth."},
                {"icon": "book", "title": "Short & seasonal", "body": "A focused menu so every dish is at its peak."},
                {"icon": "mail", "title": "Private events", "body": "Let us host your celebration, dinner, or tasting."}]}},
            {"type": "testimonials", "content": {"heading": "Loved by our regulars", "items": [
                {"quote": "The best meal we've had all year — and we'll be back next week.", "author": "Dana R.", "role": "Regular"},
                {"quote": "Cozy, warm, and the kitchen clearly cares. Our new favorite.", "author": "Marco T.", "role": "Local"},
                {"quote": "Booked it for a birthday — the staff made it unforgettable.", "author": "Priya S.", "role": "Guest"}]}},
            {"type": "faq", "content": {"heading": "Good to know", "items": [
                {"q": "Do you take walk-ins?", "a": "Always — the bar and patio are first-come, and we hold tables for reservations."},
                {"q": "Any dietary options?", "a": "Yes — vegetarian, vegan, and gluten-free dishes change with the season."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Hungry yet?", "subhead": "Reserve your table — we'll save you a seat.", "cta": {"label": "Reserve now", "href": "/contact"}}},
        ],
    },
    # Cornerstone — structured real estate / architecture. Slate + brass, serif, tight grid.
    "realestate": {
        "name": "Cornerstone — Real Estate & Architecture",
        "personality": "assured, premium, grounded, structured",
        "tokens": {
            "colors": {
                "ink": "#1b1d22", "muted": "#6a6f78", "paper": "#f5f5f2", "surface": "#ffffff",
                "line": "#e3e3dd", "primary": "#2b3440", "accent": "#a47e3b", "highlight": "#c9a86a", "link": "#46627e",
                "surfaceInverse": "#14171c", "inkInverse": "#f0efe9", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SERIF},
            "radius": {"card": "8px", "control": "6px", "pill": "999px"},
            "layout": {"density": "compact", "heroMinHeight": "76vh", "sectionGap": "100px", "contentMaxWidth": "1180px", "cardPadding": "24px"},
        },
        "voice": {"headlineStyle": "assured, location-led", "tone": "polished and grounded"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Property, done properly",
                "headline": "Find the address that", "headlineAccent": "feels like home.",
                "subhead": "Local expertise, honest advice, and a calm hand through every step of the move.",
                "cta": {"label": "Book a viewing", "href": "/contact"}, "secondaryCta": {"label": "Browse listings", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "$2.1B", "label": "Sold to date"}, {"value": "1,400+", "label": "Homes closed"},
                {"value": "21 days", "label": "Avg. to offer"}, {"value": "98%", "label": "Of asking"}]}},
            {"type": "logos", "content": {"heading": "Featured in", "items": [{"label": "Architectural Digest"}, {"label": "Dwell"}, {"label": "The Times"}, {"label": "Mansion Global"}]}},
            {"type": "comparison", "content": {"heading": "A better way to move",
                "left": {"title": "The usual agent", "items": ["Lists and waits", "Generic photos", "Hard to reach", "One-size advice"]},
                "right": {"title": "Cornerstone", "items": ["Priced with real data", "Architectural photography", "Direct line to your agent", "A plan built around you"]}}},
            {"type": "testimonials", "content": {"heading": "From our clients", "items": [
                {"quote": "Sold above asking in under three weeks. Calm, sharp, and honest throughout.", "author": "The Halls", "role": "Sellers"},
                {"quote": "They understood the building's character and found exactly the right buyer.", "author": "L. Moreau", "role": "Architect"},
                {"quote": "First-time buyers and they made it feel effortless.", "author": "Sam & Nia", "role": "Buyers"}]}},
            {"type": "faq", "content": {"heading": "Questions", "items": [
                {"q": "What are your fees?", "a": "A simple, transparent commission agreed up front — no surprises at closing."},
                {"q": "Do you handle rentals too?", "a": "Yes — sales, lettings, and property management across the city."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Thinking of making a move?", "subhead": "Get a free, no-pressure valuation.", "cta": {"label": "Request a valuation", "href": "/contact"}}},
        ],
    },
    # Ignite — high-energy fitness / sport. Dark canvas, condensed display, volt accent.
    "fitness": {
        "name": "Ignite — Fitness & Sport",
        "personality": "high-energy, bold, motivating, athletic",
        "tokens": {
            "colors": {
                "ink": "#eef2f0", "muted": "#9aa6a1", "paper": "#0d1110", "surface": "#161b19",
                "line": "#29302d", "primary": "#e0452a", "accent": "#9ae64d", "highlight": "#c6ff3a", "link": "#ff7d52",
                "surfaceInverse": "#06090a", "inkInverse": "#eef2f0", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": CONDENSED},
            "radius": {"card": "12px", "control": "8px", "pill": "8px"},
            "layout": {"density": "comfortable", "heroMinHeight": "92vh", "sectionGap": "112px", "contentMaxWidth": "1160px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "punchy, imperative, motivating", "tone": "high-energy and direct"},
        "sections": [
            {"type": "hero", "variant": "fullbleed", "content": {
                "badge": "First class free",
                "headline": "Stronger starts", "headlineAccent": "today.",
                "subhead": "Coach-led training, real community, and a plan that meets you where you are.",
                "cta": {"label": "Start free trial", "href": "/contact"}, "secondaryCta": {"label": "See classes", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "120+", "label": "Classes / week"}, {"value": "3,000+", "label": "Members strong"},
                {"value": "24/7", "label": "Gym access"}, {"value": "12", "label": "Expert coaches"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Train your way", "subhead": "Strength, conditioning, and recovery under one roof.", "items": [
                {"icon": "zap", "title": "Strength", "body": "Coached lifting programs that actually progress."},
                {"icon": "gauge", "title": "Conditioning", "body": "HIIT and endurance classes that push your limits."},
                {"icon": "shield", "title": "Recovery", "body": "Mobility, sauna, and recovery built into your week."}]}},
            {"type": "comparison", "content": {"heading": "Not your average gym",
                "left": {"title": "Big-box gym", "items": ["Rows of empty machines", "No guidance", "Cancel-anytime guilt trip", "Zero community"]},
                "right": {"title": "Ignite", "items": ["Coach-led every session", "A plan built for you", "Flexible, honest membership", "A crew that shows up"]}}},
            {"type": "pricing", "content": {"heading": "Membership", "subhead": "No contracts. Cancel anytime.",
                "items": [
                    {"name": "Day Pass", "price": "$15", "period": "/day", "features": ["All classes", "Full gym floor", "Locker + sauna"], "cta": {"label": "Drop in", "href": "/contact"}},
                    {"name": "Unlimited", "price": "$99", "period": "/mo", "features": ["Unlimited classes", "24/7 access", "Free guest passes"], "featured": True, "cta": {"label": "Join now", "href": "/contact"}},
                    {"name": "Coached", "price": "$199", "period": "/mo", "features": ["Everything in Unlimited", "1:1 coaching", "Custom programming"], "cta": {"label": "Go all in", "href": "/contact"}}]}},
            {"type": "testimonials", "content": {"heading": "Real members, real results", "items": [
                {"quote": "Down 18 pounds and finally strong. The coaches make it stick.", "author": "Tyler M.", "role": "Member, 1 year"},
                {"quote": "I dreaded the gym. Now it's the best hour of my day.", "author": "Renee K.", "role": "Member"},
                {"quote": "The community is unreal. You can't skip when people are waiting for you.", "author": "Devon A.", "role": "Member"}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Your first class is on us.", "subhead": "No pressure. Just show up.", "cta": {"label": "Claim free class", "href": "/contact"}}},
        ],
    },
    # Lumière — elegant beauty / spa / medical-aesthetics. Blush + mauve, Fraunces
    # serif, soft and airy. A COMPLETE, image-ready industry template: a full-bleed
    # photo hero, a treatments grid, a studio lookbook gallery, a booking flow, and
    # a photo CTA — with stable block ids + a declared `images` spec (prompts the
    # rebrand pipeline generates + attaches). This is the reference shape for adding
    # any new industry template.
    "beauty": {
        "name": "Lumière — Beauty & Skincare Studio",
        "personality": "elegant, calming, refined, welcoming",
        "tokens": {
            "colors": {
                "ink": "#2e2230", "muted": "#7d6f7a", "paper": "#fbf3f5", "surface": "#fffafc",
                "line": "#f0e0e6", "primary": "#9d4a62", "accent": "#8a6a9a", "highlight": "#cf9f6a", "link": "#9a5578",
                "surfaceInverse": "#241620", "inkInverse": "#fbeef2", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": FRAUNCES},
            "radius": {"card": "22px", "control": "16px", "pill": "999px"},
            "layout": {"density": "spacious", "heroMinHeight": "80vh", "sectionGap": "116px", "contentMaxWidth": "1100px", "cardPadding": "28px"},
        },
        "voice": {"headlineStyle": "elegant, inviting, sensorial", "tone": "calm, honest, unhurried — never hype"},
        "sections": [
            {"id": "b_beauty_hero", "type": "hero", "variant": "fullbleed", "content": {
                "badge": "Beauty & Skincare Studio",
                "headline": "Skin and self,", "headlineAccent": "glowing together.",
                "subhead": "Facials, skin coaching, and quiet body rituals — calm, professional, and natural. We take good care of you, without the hype.",
                "image": "", "imageFocal": "center", "imageAlt": "A calm guest with luminous, glowing skin",
                "imagePrompt": "a serene woman with luminous dewy glowing skin and soft natural makeup, eyes gently closed, calm relaxed expression, wrapped in a soft cream towel, clean minimal background with generous negative space",
                "cta": {"label": "Book a consultation", "href": "/contact"}, "secondaryCta": {"label": "View treatments", "href": "/services"}}},
            {"id": "b_beauty_stats", "type": "stats", "content": {"items": [
                {"value": "4.9★", "label": "Guest rating"}, {"value": "20+", "label": "Treatments"},
                {"value": "1:1", "label": "Custom plans"}, {"value": "Clean", "label": "Products only"}]}},
            {"id": "b_beauty_treat", "type": "features", "variant": "cards", "content": {
                "heading": "Signature treatments", "subhead": "From the first consult to your at-home routine, every step is built around your skin.", "items": [
                    {"icon": "sparkles", "title": "Cleanse & glow", "body": "Deep cleansing, hydration, and gentle brightening — an everyday facial for fast, visible results."},
                    {"icon": "layers", "title": "Skin coaching", "body": "Staged care plans for sensitivity, dullness, dryness, and pores."},
                    {"icon": "shield", "title": "Relax & restore", "body": "Face, neck and shoulder relief and soothing massage — beauty that's also real rest."}]}},
            {"id": "b_beauty_gallery", "type": "gallery", "variant": "grid", "content": {
                "heading": "Inside the studio", "subhead": "A calm, private space — and a few quiet moments from our treatments.", "items": [
                    {"image": "", "caption": "A treatment in progress", "imagePrompt": "close-up of a gentle facial treatment, esthetician hands applying cream to luminous glowing skin, calm and clean"},
                    {"image": "", "caption": "Our studio", "imagePrompt": "calm minimal beauty studio treatment room, soft draped linen, a few green plants, warm wood and stone accents, diffused daylight"},
                    {"image": "", "caption": "Gentle, curated products", "imagePrompt": "minimal flatlay of premium skincare products, amber glass dropper bottles and ceramic cream jars, dried flowers, pale marble surface"},
                    {"image": "", "caption": "Time to truly rest", "imagePrompt": "a woman relaxing during a spa session, soft towel, a lit candle and rolled towels nearby, eyes closed, peaceful"}]}},
            {"id": "b_beauty_steps", "type": "steps", "content": {
                "heading": "How booking works", "subhead": "You don't need to know the treatments — just tell us what you're after.", "items": [
                    {"title": "Online consult", "body": "Tell us about your skin, budget, and what you'd like to improve."},
                    {"title": "In-studio assessment", "body": "We confirm the right treatment and what to keep in mind."},
                    {"title": "Custom treatment", "body": "We adjust products, technique, and timing to your skin on the day."},
                    {"title": "At-home advice", "body": "Simple, doable aftercare — no over-treating."}]}},
            {"id": "b_beauty_quotes", "type": "testimonials", "content": {"heading": "What guests say", "items": [
                {"quote": "It wasn't a dramatic change — I just looked clean, bright, and really comfortable.", "author": "Hannah W.", "role": "Facial guest"},
                {"quote": "The space is calm and there's no upselling. I felt at ease on my very first visit.", "author": "Sofia D.", "role": "Skin coaching guest"},
                {"quote": "The at-home advice afterward was genuinely useful — my skin is much more stable now.", "author": "Mei L.", "role": "Member"}]}},
            {"id": "b_beauty_pricing", "type": "pricing", "content": {"heading": "Featured packages", "subhead": "Prices flex with the treatment and your skin; these work well as a starting point.",
                "items": [
                    {"name": "Quick glow", "price": "$68", "period": "/visit", "features": ["30-min essential facial", "Cleanse + hydrate", "Great for a lunch break"], "cta": {"label": "Book", "href": "/contact"}},
                    {"name": "Signature care", "price": "$128", "period": "/visit", "features": ["75-min custom treatment", "Face, neck & shoulder relief", "At-home aftercare advice"], "featured": True, "cta": {"label": "Book", "href": "/contact"}},
                    {"name": "Monthly plan", "price": "$299", "period": "/mo", "features": ["3 treatments a month", "Staged skin tracking", "Priority booking"], "cta": {"label": "Enquire", "href": "/contact"}}]}},
            {"id": "b_beauty_faq", "type": "faq", "content": {"heading": "Before you visit", "items": [
                {"q": "Which treatment should I pick first?", "a": "Book a consultation — we adjust on the day based on your skin, so you don't have to decide alone."},
                {"q": "Can I come in with sensitive skin?", "a": "Yes. We assess first and start gentle, avoiding over-cleansing and irritation."},
                {"q": "How far ahead should I book?", "a": "2–3 days ahead is best. Weekends and evenings fill up fast; members get priority."}]}},
            {"id": "b_beauty_cta", "type": "cta", "variant": "banner", "content": {
                "headline": "Not sure which treatment fits?", "subhead": "Leave your contact and we'll give you a simple recommendation based on your skin, schedule, and budget.",
                "image": "", "imagePrompt": "soft-focus calm spa scene, a gentle facial skincare treatment in progress, esthetician hands, dewy glowing skin, peaceful atmosphere, diffused light",
                "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
        # Imagery this template needs — the rebrand pipeline generates each prompt and
        # attaches the result to the target block's image field (item = list index).
        "images": [
            {"block": "b_beauty_hero", "field": "image", "aspect": "16:9", "prompt": "a serene woman with luminous dewy glowing skin and soft natural makeup, eyes gently closed, calm relaxed expression, wrapped in a soft cream towel, clean minimal background with generous negative space"},
            {"block": "b_beauty_gallery", "item": 0, "field": "image", "aspect": "1:1", "prompt": "close-up of a gentle facial treatment, esthetician hands applying cream to luminous glowing skin, calm and clean"},
            {"block": "b_beauty_gallery", "item": 1, "field": "image", "aspect": "1:1", "prompt": "calm minimal beauty studio treatment room, soft draped linen, a few green plants, warm wood and stone accents, diffused daylight"},
            {"block": "b_beauty_gallery", "item": 2, "field": "image", "aspect": "1:1", "prompt": "minimal flatlay of premium skincare products, amber glass dropper bottles and ceramic cream jars, dried flowers, pale marble surface"},
            {"block": "b_beauty_gallery", "item": 3, "field": "image", "aspect": "1:1", "prompt": "a woman relaxing during a spa session, soft towel, a lit candle and rolled towels nearby, eyes closed, peaceful"},
            {"block": "b_beauty_cta", "field": "image", "aspect": "16:9", "prompt": "soft-focus calm spa scene, a gentle facial skincare treatment in progress, esthetician hands, dewy glowing skin, peaceful atmosphere, diffused light"},
        ],
        "imageStyle": "warm neutral palette of beige cream and soft blush rose, soft natural window light, editorial beauty photography, shallow depth of field, serene minimal high-end spa aesthetic, photorealistic, no text, no watermark, no logo",
    },
    # Sterling — authoritative law / advisory. Deep navy + gold, serif, conservative.
    "legal": {
        "name": "Sterling — Law & Advisory",
        "personality": "authoritative, precise, discreet, trustworthy",
        "tokens": {
            "colors": {
                "ink": "#0f1a32", "muted": "#5e6a82", "paper": "#f6f7fa", "surface": "#ffffff",
                "line": "#dde2ec", "primary": "#1b3a6b", "accent": "#8a6d3b", "highlight": "#b8924c", "link": "#285a9c",
                "surfaceInverse": "#0b1426", "inkInverse": "#eef2f9", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SERIF},
            "radius": {"card": "8px", "control": "6px", "pill": "999px"},
            "layout": {"density": "compact", "heroMinHeight": "68vh", "sectionGap": "100px", "contentMaxWidth": "1160px", "cardPadding": "24px"},
        },
        "voice": {"headlineStyle": "authoritative, precise, outcome-led", "tone": "measured and credible"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Counsel you can rely on",
                "headline": "Clear advice when", "headlineAccent": "it matters most.",
                "subhead": "Senior lawyers, straight answers, and a steady hand through every matter — large or small.",
                "cta": {"label": "Request a consultation", "href": "/contact"}, "secondaryCta": {"label": "Practice areas", "href": "/blog"}}},
            {"type": "logos", "content": {"heading": "Recognized by", "items": [{"label": "Chambers"}, {"label": "Legal 500"}, {"label": "Best Lawyers"}, {"label": "Super Lawyers"}]}},
            {"type": "stats", "content": {"items": [
                {"value": "40+", "label": "Years combined"}, {"value": "$500M+", "label": "Recovered"},
                {"value": "95%", "label": "Favorable outcomes"}, {"value": "24h", "label": "Response time"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "How we help", "subhead": "Focused practice areas, senior attention on every file.", "items": [
                {"icon": "shield", "title": "Corporate & commercial", "body": "Formation, contracts, and deals done right."},
                {"icon": "book", "title": "Disputes & litigation", "body": "Prepared, persuasive, and pragmatic in the room."},
                {"icon": "layers", "title": "Private client", "body": "Wills, estates, and the matters closest to home."}]}},
            {"type": "comparison", "content": {"heading": "The Sterling difference",
                "left": {"title": "Big firms", "items": ["Passed to junior staff", "Billed for every email", "Hard to reach", "Jargon over clarity"]},
                "right": {"title": "Sterling", "items": ["Senior lawyer on your file", "Clear, agreed fees", "Direct line to counsel", "Plain-English advice"]}}},
            {"type": "testimonials", "content": {"heading": "Client confidence", "items": [
                {"quote": "Calm, sharp, and completely on top of the detail. The outcome spoke for itself.", "author": "Director", "role": "Manufacturing client"},
                {"quote": "They explained the risk plainly and got us a result fast.", "author": "Founder", "role": "Tech client"},
                {"quote": "Handled a difficult estate with real care and discretion.", "author": "Private client", "role": "Estate matter"}]}},
            {"type": "faq", "content": {"heading": "Common questions", "items": [
                {"q": "How are fees structured?", "a": "Transparently — fixed fees where possible, agreed in writing before we start."},
                {"q": "Is a first consultation free?", "a": "Yes — an initial consultation to understand your matter is complimentary."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Need clear counsel?", "subhead": "Request a confidential consultation today.", "cta": {"label": "Request a consultation", "href": "/contact"}}},
        ],
    },
    # Kinetic — bold creative studio / agency. Near-black + acid accent, oversized grotesk.
    "creative": {
        "name": "Kinetic — Studio & Agency",
        "personality": "bold, expressive, contemporary, confident",
        "tokens": {
            "colors": {
                "ink": "#0a0a0a", "muted": "#6a6a6a", "paper": "#f4f4f0", "surface": "#ffffff",
                "line": "#e2e2dc", "primary": "#141414", "accent": "#ff4d2e", "highlight": "#d6ff3f", "link": "#ff4d2e",
                "surfaceInverse": "#0a0a0a", "inkInverse": "#f4f4f0", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "radius": {"card": "6px", "control": "4px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "88vh", "sectionGap": "120px", "contentMaxWidth": "1160px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "bold, oversized, expressive", "tone": "confident and creative"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "Studio for hire",
                "headline": "Ideas worth", "headlineAccent": "staring at.",
                "subhead": "A small studio making brands, sites, and campaigns that refuse to blend in.",
                "cta": {"label": "Start a project", "href": "/contact"}, "secondaryCta": {"label": "See the work", "href": "/blog"}}},
            {"type": "logos", "content": {"heading": "Selected clients", "items": [{"label": "Aēsop"}, {"label": "MUBI"}, {"label": "Monzo"}, {"label": "Patagonia"}, {"label": "Frieze"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "What we make", "subhead": "Strategy, identity, and the craft to ship it.", "items": [
                {"icon": "sparkles", "title": "Brand identity", "body": "Names, logos, and systems with a point of view."},
                {"icon": "layers", "title": "Websites", "body": "Fast, distinctive sites built to convert and last."},
                {"icon": "zap", "title": "Campaigns", "body": "Launches and films that earn attention, not buy it."}]}},
            {"type": "comparison", "content": {"heading": "Why work with us",
                "left": {"title": "The big agency", "items": ["Layers of account managers", "Templated thinking", "Slow, costly rounds", "You're one of fifty"]},
                "right": {"title": "Kinetic", "items": ["Founders on every project", "Original every time", "Tight, senior team", "You're the only one"]}}},
            {"type": "testimonials", "content": {"heading": "Kind words", "items": [
                {"quote": "They gave us an identity people actually talk about. Sales followed.", "author": "CEO", "role": "DTC brand"},
                {"quote": "Fast, fearless, and ridiculously talented. Just hire them.", "author": "CMO", "role": "Fintech"},
                {"quote": "The site doubled our conversion and won an award. Both.", "author": "Founder", "role": "Studio"}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Got something to launch?", "subhead": "Tell us what you're building.", "cta": {"label": "Start a project", "href": "/contact"}}},
        ],
    },
    # Onyx — luxe: near-black + gold, Fraunces serif, generous space. Premium/luxury.
    "luxe": {
        "name": "Onyx — Luxe",
        "personality": "elegant, premium, understated, high-contrast",
        "tokens": {
            "colors": {
                "ink": "#f4efe6", "muted": "#a99f8c", "paper": "#0c0b09", "surface": "#16140f",
                "line": "#2a2620", "primary": "#c9a24a", "accent": "#c9a24a", "highlight": "#d9bd6e", "link": "#d9bd6e",
                "surfaceInverse": "#060504", "inkInverse": "#f4efe6", "onPrimary": "#14110c",
            },
            "typography": {"body": SANS, "heading": FRAUNCES},
            "radius": {"card": "4px", "control": "3px", "pill": "999px"},
            "layout": {"density": "spacious", "heroMinHeight": "92vh", "sectionGap": "132px", "contentMaxWidth": "1080px", "cardPadding": "30px"},
        },
        "voice": {"headlineStyle": "elegant, restrained, premium", "tone": "understated luxury"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "By design",
                "headline": "Crafted to be", "headlineAccent": "remembered.",
                "subhead": "A quiet, premium presence — considered type, deep contrast, and room to breathe. Nothing shouts; everything lingers.",
                "cta": {"label": "Begin", "href": "/contact"}, "secondaryCta": {"label": "View work", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "1:1", "label": "Made to order"}, {"value": "Gold", "label": "Standard"},
                {"value": "Quiet", "label": "Luxury"}, {"value": "Yours", "label": "Entirely"}]}},
            {"type": "logos", "content": {"heading": "In good company", "items": [{"label": "Aurum"}, {"label": "Noir"}, {"label": "Maison"}, {"label": "Élan"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Considered, end to end.", "subhead": "Restraint is the luxury.", "items": [
                {"icon": "sparkles", "title": "Refined", "body": "Every detail weighed — type, space, and tone."},
                {"icon": "shield", "title": "Enduring", "body": "Built to age well, not to chase trends."},
                {"icon": "layers", "title": "Bespoke", "body": "Made for you, owned by you, like nothing else."}]}},
            {"type": "comparison", "content": {"heading": "Quiet beats loud.",
                "left": {"title": "Off the shelf", "items": ["Templated and obvious", "Busy and bright", "Built to convert, fast", "Looks like the rest"]},
                "right": {"title": "Onyx", "items": ["Bespoke and discreet", "Calm, deep, gold-touched", "Built to last", "Unmistakably yours"]}}},
            {"type": "testimonials", "content": {"heading": "Quietly admired", "items": [
                {"quote": "It feels expensive in the best way — calm, sure of itself.", "author": "A. Laurent", "role": "Maison"},
                {"quote": "Understated and unforgettable. Exactly the brand we wanted.", "author": "R. Vance", "role": "Atelier"},
                {"quote": "People slow down on it. That's the whole point.", "author": "M. Sole", "role": "Studio"}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Make something lasting.", "subhead": "A quiet conversation to begin.", "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
    },
    # Scholar — education: friendly blue + warm amber, rounded, trustworthy.
    "education": {
        "name": "Scholar — Education",
        "personality": "friendly, credible, encouraging, clear",
        "tokens": {
            "colors": {
                "ink": "#16263d", "muted": "#5a6b82", "paper": "#f5f8fc", "surface": "#ffffff",
                "line": "#dce6f2", "primary": "#2b6cb0", "accent": "#dd6b20", "highlight": "#ecc94b", "link": "#2b6cb0",
                "surfaceInverse": "#0e1c30", "inkInverse": "#eef4fb", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "18px", "control": "12px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "74vh", "sectionGap": "108px", "contentMaxWidth": "1120px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "warm, clear, encouraging", "tone": "supportive and credible"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Learn with confidence",
                "headline": "Teaching that", "headlineAccent": "actually sticks.",
                "subhead": "Clear lessons, real progress, and a teacher who meets you where you are.",
                "cta": {"label": "Book a free trial", "href": "/contact"}, "secondaryCta": {"label": "Read the blog", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "1,200+", "label": "Students taught"}, {"value": "4.9★", "label": "Parent rating"},
                {"value": "10+ yrs", "label": "Experience"}, {"value": "1:1", "label": "Attention"}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "How we teach", "subhead": "Structure, clarity, and encouragement.", "items": [
                {"icon": "book", "title": "Clear curriculum", "body": "A plan you can follow, milestone by milestone."},
                {"icon": "gauge", "title": "Real progress", "body": "Regular check-ins so you always know where you stand."},
                {"icon": "shield", "title": "Caring support", "body": "Patient teachers who make hard things click."}]}},
            {"type": "comparison", "content": {"heading": "Why families choose us",
                "left": {"title": "Big tutoring chains", "items": ["A different tutor each time", "One-size lessons", "Slow to adapt", "Hard to reach"]},
                "right": {"title": "With us", "items": ["Your dedicated teacher", "Built around the student", "Adapts every week", "Always responsive"]}}},
            {"type": "testimonials", "content": {"heading": "What parents say", "items": [
                {"quote": "Her grades jumped a full level in one term — and she actually enjoys it now.", "author": "A parent", "role": "Grade 9"},
                {"quote": "Patient, clear, and genuinely kind. Exactly what we hoped for.", "author": "A parent", "role": "Grade 11"},
                {"quote": "Booked a trial, never looked back.", "author": "A parent", "role": "Grade 7"}]}},
            {"type": "faq", "content": {"heading": "Common questions", "items": [
                {"q": "Do you teach online or in person?", "a": "Both — whatever works best for the student."},
                {"q": "Can we start with a trial?", "a": "Yes — a free first session to make sure it's a fit."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Ready to see progress?", "subhead": "Book a free trial lesson today.", "cta": {"label": "Book a trial", "href": "/contact"}}},
        ],
    },
    # Grove — nonprofit: warm green + amber, humane, mission-driven.
    "nonprofit": {
        "name": "Grove — Nonprofit",
        "personality": "warm, hopeful, sincere, community-minded",
        "tokens": {
            "colors": {
                "ink": "#1e2a22", "muted": "#5f6f63", "paper": "#f3f8f1", "surface": "#ffffff",
                "line": "#dde8d8", "primary": "#2f855a", "accent": "#dd6b20", "highlight": "#ecc94b", "link": "#2f7d6f",
                "surfaceInverse": "#0e1c14", "inkInverse": "#eef5ee", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "20px", "control": "14px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "74vh", "sectionGap": "108px", "contentMaxWidth": "1120px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "warm, hopeful, action-led", "tone": "sincere and inviting"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "Join the cause",
                "headline": "Together,", "headlineAccent": "we can do more.",
                "subhead": "Real change, made by ordinary people who show up. Your support goes further than you think.",
                "cta": {"label": "Donate", "href": "/contact"}, "secondaryCta": {"label": "Volunteer", "href": "/contact"}}},
            {"type": "stats", "content": {"items": [
                {"value": "50k+", "label": "People helped"}, {"value": "120", "label": "Volunteers"},
                {"value": "92%", "label": "Goes to programs"}, {"value": "15 yrs", "label": "On the ground"}]}},
            {"type": "problem", "variant": "cards", "content": {"heading": "The need is real.", "subhead": "And it's closer than you think.", "items": [
                {"icon": "layers", "title": "Too many left out", "body": "Families slipping through the cracks every day."},
                {"icon": "gauge", "title": "Help can't wait", "body": "Small support now prevents bigger crises later."},
                {"icon": "shield", "title": "Trust matters", "body": "Every dollar accounted for, every story real."}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "How we help", "items": [
                {"icon": "sparkles", "title": "Direct support", "body": "Meeting immediate needs with dignity."},
                {"icon": "book", "title": "Long-term programs", "body": "Building skills and stability that last."},
                {"icon": "mail", "title": "Community", "body": "Connecting people who care to people who need it."}]}},
            {"type": "testimonials", "content": {"heading": "Voices we serve", "items": [
                {"quote": "They didn't just help — they treated us like family.", "author": "A. R.", "role": "Program member"},
                {"quote": "I volunteer because I see exactly where it goes.", "author": "J. M.", "role": "Volunteer"},
                {"quote": "This is what hope looks like, up close.", "author": "Local partner", "role": "Community"}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Be part of it.", "subhead": "Give, volunteer, or just spread the word.", "cta": {"label": "Get involved", "href": "/contact"}}},
        ],
    },
    # Vault — finance: emerald + trust-blue, structured, credible.
    "finance": {
        "name": "Vault — Finance",
        "personality": "trustworthy, precise, calm, credible",
        "tokens": {
            "colors": {
                "ink": "#0f211d", "muted": "#5a6e68", "paper": "#f4f8f6", "surface": "#ffffff",
                "line": "#d8e4df", "primary": "#0b6e4f", "accent": "#1c4e8a", "highlight": "#b8924c", "link": "#0b6e5f",
                "surfaceInverse": "#08140f", "inkInverse": "#eef4f1", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": SANS},
            "radius": {"card": "10px", "control": "7px", "pill": "999px"},
            "layout": {"density": "compact", "heroMinHeight": "70vh", "sectionGap": "100px", "contentMaxWidth": "1160px", "cardPadding": "24px"},
        },
        "voice": {"headlineStyle": "clear, credible, outcome-led", "tone": "calm and precise"},
        "sections": [
            {"type": "hero", "variant": "split", "content": {
                "kicker": "Money, managed well",
                "headline": "Grow it. Protect it.", "headlineAccent": "Understand it.",
                "subhead": "Clear advice and steady hands for your money — no jargon, no surprises.",
                "cta": {"label": "Book a consultation", "href": "/contact"}, "secondaryCta": {"label": "Learn more", "href": "/blog"}}},
            {"type": "logos", "content": {"heading": "Regulated & insured", "items": [{"label": "SIPC"}, {"label": "FINRA"}, {"label": "SEC"}, {"label": "Bonded"}]}},
            {"type": "stats", "content": {"items": [
                {"value": "$2B+", "label": "Under advice"}, {"value": "20 yrs", "label": "Track record"},
                {"value": "0", "label": "Hidden fees"}, {"value": "24/7", "label": "Account access"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "What we do", "subhead": "The essentials, done with care.", "items": [
                {"icon": "shield", "title": "Plan", "body": "A clear roadmap for your goals and timeline."},
                {"icon": "gauge", "title": "Invest", "body": "Disciplined, diversified, and tax-aware."},
                {"icon": "layers", "title": "Protect", "body": "Insurance and estate planning that hold up."}]}},
            {"type": "comparison", "content": {"heading": "A better standard",
                "left": {"title": "Typical advisor", "items": ["Hidden commissions", "Generic portfolios", "Hard to reach", "Jargon-heavy"]},
                "right": {"title": "Vault", "items": ["Transparent fees", "Built for you", "Always available", "Plain-English advice"]}}},
            {"type": "pricing", "content": {"heading": "Simple, transparent fees", "subhead": "No surprises.", "items": [
                {"name": "Starter", "price": "0.5%", "period": "/yr", "features": ["Core plan", "Annual review", "Online access"], "cta": {"label": "Start", "href": "/contact"}},
                {"name": "Wealth", "price": "0.8%", "period": "/yr", "features": ["Full plan", "Quarterly reviews", "Tax + estate"], "featured": True, "cta": {"label": "Choose", "href": "/contact"}},
                {"name": "Family office", "price": "Custom", "period": "", "features": ["Dedicated team", "Bespoke", "Concierge"], "cta": {"label": "Contact", "href": "/contact"}}]}},
            {"type": "faq", "content": {"heading": "Questions", "items": [
                {"q": "Are you a fiduciary?", "a": "Yes — we're legally bound to act in your best interest."},
                {"q": "What's the minimum?", "a": "We work with a range of clients — let's talk about your situation."}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Take the first step.", "subhead": "A free, no-pressure consultation.", "cta": {"label": "Book a call", "href": "/contact"}}},
        ],
    },
    # Pop — playful: purple + pink + yellow, very rounded, fun.
    "playful": {
        "name": "Pop — Playful",
        "personality": "fun, energetic, friendly, bold",
        "tokens": {
            "colors": {
                "ink": "#2d1b4e", "muted": "#7a6a95", "paper": "#fef6fb", "surface": "#ffffff",
                "line": "#f0e4f5", "primary": "#7c3aed", "accent": "#ec4899", "highlight": "#f59e0b", "link": "#db2777",
                "surfaceInverse": "#1a0f2e", "inkInverse": "#fdf4ff", "onPrimary": "#ffffff",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "radius": {"card": "28px", "control": "18px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "84vh", "sectionGap": "116px", "contentMaxWidth": "1120px", "cardPadding": "28px"},
        },
        "voice": {"headlineStyle": "punchy, fun, upbeat", "tone": "friendly and energetic"},
        "sections": [
            {"type": "hero", "variant": "centered", "content": {
                "badge": "Hello there 👋",
                "headline": "Make it", "headlineAccent": "wonderfully fun.",
                "subhead": "Bright, bold, and a joy to use — a site that makes people smile the moment it loads.",
                "cta": {"label": "Let's go", "href": "/contact"}, "secondaryCta": {"label": "See more", "href": "/blog"}}},
            {"type": "stats", "content": {"items": [
                {"value": "😄", "label": "Joy, by default"}, {"value": "Bold", "label": "Colors"},
                {"value": "Fast", "label": "& bouncy"}, {"value": "Yours", "label": "100%"}]}},
            {"type": "features", "variant": "cards", "content": {"heading": "Why it's fun", "items": [
                {"icon": "sparkles", "title": "Bright", "body": "Big color, big rounded shapes, big personality."},
                {"icon": "zap", "title": "Lively", "body": "Snappy and playful on every tap."},
                {"icon": "mail", "title": "Friendly", "body": "Warm copy that talks like a human."}]}},
            {"type": "comparison", "content": {"heading": "Fun beats boring",
                "left": {"title": "Beige website", "items": ["Looks like everyone else", "Stiff and corporate", "Forgettable", "No personality"]},
                "right": {"title": "Pop", "items": ["Unmistakably you", "Playful and warm", "Memorable", "Full of character"]}}},
            {"type": "testimonials", "content": {"heading": "People love it", "items": [
                {"quote": "Our bounce rate dropped — people actually stick around now.", "author": "A. Founder", "role": "DTC brand"},
                {"quote": "It made our brand feel alive.", "author": "M. Creator", "role": "Studio"},
                {"quote": "So fun. Everyone comments on it.", "author": "J. Owner", "role": "Shop"}]}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Ready to have fun?", "subhead": "Let's make something people love.", "cta": {"label": "Start now", "href": "/contact"}}},
        ],
    },
    # Pulse — neon: near-black + cyan/magenta neon, cyberpunk, dark.
    "neon": {
        "name": "Pulse — Neon",
        "personality": "futuristic, electric, bold, high-tech",
        "tokens": {
            "colors": {
                "ink": "#e6f7ff", "muted": "#7d96a8", "paper": "#07090f", "surface": "#0e131d",
                "line": "#1e2636", "primary": "#06d6f0", "accent": "#ff2bd6", "highlight": "#c6ff3a", "link": "#5cf2ff",
                "surfaceInverse": "#04060a", "inkInverse": "#e6f7ff", "onPrimary": "#04060a",
            },
            "typography": {"body": SANS, "heading": GROTESK},
            "radius": {"card": "12px", "control": "8px", "pill": "999px"},
            "layout": {"density": "comfortable", "heroMinHeight": "92vh", "sectionGap": "118px", "contentMaxWidth": "1160px", "cardPadding": "26px"},
        },
        "voice": {"headlineStyle": "bold, electric, future-facing", "tone": "high-energy and modern"},
        "sections": [
            {"type": "hero", "variant": "fullbleed", "content": {
                "badge": "Online now",
                "headline": "Built for", "headlineAccent": "what's next.",
                "subhead": "A high-voltage presence that glows in the dark and moves at the speed of now.",
                "cta": {"label": "Enter", "href": "/blog"}, "secondaryCta": {"label": "Contact", "href": "/contact"}}},
            {"type": "stats", "content": {"items": [
                {"value": "120fps", "label": "Buttery"}, {"value": "Neon", "label": "Native"},
                {"value": "0ms", "label": "Hesitation"}, {"value": "∞", "label": "Energy"}]}},
            {"type": "logos", "content": {"heading": "Powering", "items": [{"label": "Nova"}, {"label": "Hyperloop"}, {"label": "Volt"}, {"label": "Synth"}]}},
            {"type": "features", "variant": "minimal", "content": {"heading": "Charged different.", "subhead": "Dark, glowing, hard to look away from.", "items": [
                {"icon": "zap", "title": "Electric", "body": "Neon accents on a deep black canvas."},
                {"icon": "gauge", "title": "Fast", "body": "Performance you feel instantly."},
                {"icon": "sparkles", "title": "Future", "body": "A look that's three years ahead."}]}},
            {"type": "comparison", "content": {"heading": "Stand out, after dark",
                "left": {"title": "Flat & beige", "items": ["Blends into the feed", "No motion, no glow", "Light-only", "Forgettable"]},
                "right": {"title": "Pulse", "items": ["Impossible to ignore", "Neon depth & glow", "Dark-native", "Three years ahead"]}}},
            {"type": "cta", "variant": "banner", "content": {"headline": "Plug in.", "subhead": "See what the future feels like.", "cta": {"label": "Get in touch", "href": "/contact"}}},
        ],
    },
}


# =====================================================================
# Bringing every industry up to the "beauty" bar. _industry_home() builds the
# same complete, image-ready 9-block home (full-bleed photo hero, treatments,
# lookbook gallery, process steps, testimonials, pricing, faq, photo CTA — stable
# block ids + a declared `images` spec) from a compact per-industry spec. Adding a
# new industry template is then just one entry in _RICH_INDUSTRY_SPECS.
# =====================================================================
def _industry_home(spec: dict) -> dict:
    p = spec["prefix"]
    h, feat, gal, st = spec["hero"], spec["feat"], spec["gallery"], spec["steps"]
    q, pr, fq, c, im = spec["quotes"], spec["pricing"], spec["faq"], spec["cta"], spec["imgs"]
    sections = [
        {"id": f"b_{p}_hero", "type": "hero", "variant": "fullbleed", "content": {
            "badge": h[0], "headline": h[1], "headlineAccent": h[2], "subhead": h[3],
            "image": "", "imageFocal": "center", "imagePrompt": im["hero"],
            "cta": {"label": h[4], "href": h[5]}, "secondaryCta": {"label": h[6], "href": h[7]}}},
        {"id": f"b_{p}_stats", "type": "stats", "content": {"items": [{"value": v, "label": l} for v, l in spec["stats"]]}},
        {"id": f"b_{p}_feat", "type": "features", "variant": "cards", "content": {
            "heading": feat[0], "subhead": feat[1], "items": [{"icon": i, "title": t, "body": b} for i, t, b in feat[2]]}},
        {"id": f"b_{p}_gallery", "type": "gallery", "variant": "grid", "content": {
            "heading": gal[0], "subhead": gal[1],
            "items": [{"image": "", "caption": cap, "imagePrompt": im[f"g{k}"]} for k, cap in enumerate(gal[2])]}},
        {"id": f"b_{p}_steps", "type": "steps", "content": {
            "heading": st[0], "subhead": st[1], "items": [{"title": t, "body": b} for t, b in st[2]]}},
        {"id": f"b_{p}_quotes", "type": "testimonials", "content": {
            "heading": q[0], "items": [{"quote": qq, "author": a, "role": r} for qq, a, r in q[1]]}},
        {"id": f"b_{p}_pricing", "type": "pricing", "content": {"heading": pr[0], "subhead": pr[1], "items": [
            {"name": n, "price": pp, "period": per, "features": list(ff), "cta": {"label": "Enquire", "href": "/contact"},
             **({"featured": True} if ft else {})} for (n, pp, per, ff, ft) in pr[2]]}},
        {"id": f"b_{p}_faq", "type": "faq", "content": {"heading": fq[0], "items": [{"q": qq, "a": aa} for qq, aa in fq[1]]}},
        {"id": f"b_{p}_cta", "type": "cta", "variant": "banner", "content": {
            "headline": c[0], "subhead": c[1], "image": "", "imagePrompt": im["cta"], "cta": {"label": c[2], "href": "/contact"}}},
    ]
    images = [{"block": f"b_{p}_hero", "field": "image", "aspect": "16:9", "prompt": im["hero"]}] + \
        [{"block": f"b_{p}_gallery", "item": k, "field": "image", "aspect": "1:1", "prompt": im[f"g{k}"]} for k in range(4)] + \
        [{"block": f"b_{p}_cta", "field": "image", "aspect": "16:9", "prompt": im["cta"]}]
    return {"sections": sections, "images": images, "imageStyle": spec["imageStyle"]}


_RICH_INDUSTRY_SPECS = {
    "restaurant": {
        "prefix": "rest",
        "hero": ["Now taking reservations", "A table worth", "coming back to.",
                 "Seasonal plates, an easy room, and a short, considered list. Walk-ins welcome; book ahead for weekends.",
                 "Book a table", "/contact", "See the menu", "/services"],
        "stats": [("4.8★", "Diner rating"), ("Daily", "Market-fresh"), ("12", "Years open"), ("Local", "Sourced")],
        "feat": ("What we cook", "Seasonal, simple, done well.", [
            ("sparkles", "Seasonal plates", "A menu that follows the market — bright, simple, generous."),
            ("layers", "Natural wine", "A short list chosen to match the food, not show off."),
            ("shield", "A warm room", "Unfussy service in a room you won't want to leave.")]),
        "gallery": ("On the table", "A few dishes and the room.", ["Tonight's plates", "The dining room", "From the pass", "A glass to start"]),
        "steps": ("How to dine", "Reserve, arrive, relax.", [
            ("Book", "Reserve online, or walk in midweek."), ("Arrive", "Settle into the room with a glass."),
            ("Eat", "Let the kitchen guide you, or order à la carte."), ("Stay", "Linger over dessert — no rush.")]),
        "quotes": ("Regulars say", [
            ("The kind of place you bring everyone you love.", "Dana R.", "Regular"),
            ("Every plate tasted like someone cared.", "Marco T.", "Guest"),
            ("Our Friday standing reservation.", "The Lees", "Members")]),
        "pricing": ("Menus", "Set menus or à la carte.", [
            ("Lunch prix-fixe", "$32", "/person", ["Two courses", "Seasonal choices", "Mon–Fri"], False),
            ("Chef's tasting", "$85", "/person", ["Six courses", "Optional pairings", "Best of the season"], True),
            ("À la carte", "Varies", "", ["Order as you like", "Daily specials", "Bar snacks"], False)]),
        "faq": ("Good to know", [
            ("Do you take walk-ins?", "Yes midweek; weekends book up — reserve ahead."),
            ("Dietary needs?", "Tell us when booking and the kitchen will happily adapt.")]),
        "cta": ("Hungry yet?", "Book a table or just walk in — we'll take care of the rest.", "Book a table"),
        "imgs": {"hero": "a warm inviting restaurant dining room at golden hour, candlelit tables, soft bokeh, intimate atmosphere",
                 "g0": "a beautifully plated seasonal dish on a ceramic plate, overhead, natural light, rustic table",
                 "g1": "cozy restaurant interior, warm wood, soft pendant lighting, full of atmosphere",
                 "g2": "a chef's hands plating a dish at the pass, gentle steam, focused, warm kitchen light",
                 "g3": "two glasses of natural wine on a table, soft evening light, bokeh",
                 "cta": "a happy table of friends dining together, warm candlelight, laughter, soft focus"},
        "imageStyle": "warm golden-hour light, rich earthy tones, shallow depth of field, editorial food and restaurant photography, inviting and atmospheric, photorealistic, no text, no watermark, no logo",
    },
    "healthcare": {
        "prefix": "clin",
        "hero": ["Accepting new patients", "Care that", "listens first.",
                 "Friendly, modern medicine with same-week appointments and clinicians who take the time to understand you.",
                 "Book an appointment", "/contact", "Our services", "/services"],
        "stats": [("Same-week", "Appointments"), ("4.9★", "Patient rating"), ("15k+", "Patients seen"), ("Board", "Certified")],
        "feat": ("How we help", "Thorough, unhurried, modern.", [
            ("shield", "Primary care", "Routine visits, screenings, and the everyday things, done properly."),
            ("sparkles", "Same-week visits", "Get seen quickly when something's wrong — no long waits."),
            ("layers", "Clear plans", "You leave knowing exactly what's next, in plain language.")]),
        "gallery": ("Our clinic", "Calm, clean, and welcoming.", ["The waiting room", "A consult room", "Our team at work", "Modern equipment"]),
        "steps": ("Your visit", "Simple from start to finish.", [
            ("Book", "Request a time online or call us."), ("Check in", "Quick paperwork, then you're seen on time."),
            ("Consult", "An unhurried visit — questions always welcome."), ("Follow-up", "A clear plan and easy follow-up.")]),
        "quotes": ("Patients say", [
            ("They actually listened and didn't rush me.", "Karen P.", "Patient"),
            ("Got an appointment the same week. A lifesaver.", "Tom B.", "Patient"),
            ("Everything was explained clearly and kindly.", "Aisha M.", "Patient")]),
        "pricing": ("Visit types", "Transparent, up front.", [
            ("New patient", "$120", "/visit", ["45-min consult", "Full history", "Care plan"], False),
            ("Follow-up", "$80", "/visit", ["Focused check-in", "Adjust the plan", "Quick & easy"], True),
            ("Annual physical", "$180", "/visit", ["Comprehensive exam", "Screenings", "Wellness plan"], False)]),
        "faq": ("Before you come", [
            ("Do you take my insurance?", "We work with most major plans — ask us and we'll confirm."),
            ("How soon can I be seen?", "Most patients get a same-week appointment.")]),
        "cta": ("Feeling unwell?", "Book an appointment and get seen by someone who listens.", "Book an appointment"),
        "imgs": {"hero": "a warm reassuring doctor talking with a patient in a bright modern clinic, natural light, calm and professional",
                 "g0": "a clean modern medical waiting room, soft natural light, plants, welcoming",
                 "g1": "a bright tidy consultation room, modern and calm",
                 "g2": "a friendly healthcare team in a modern clinic, approachable and professional",
                 "g3": "clean modern medical equipment detail, soft light, reassuring",
                 "cta": "a patient and clinician shaking hands warmly in a bright clinic, trust, soft focus"},
        "imageStyle": "bright clean natural light, soft blue and warm neutral tones, reassuring and professional, modern healthcare photography, photorealistic, no text, no watermark, no logo",
    },
    "legal": {
        "prefix": "law",
        "hero": ["Trusted counsel", "Steady counsel", "when it matters.",
                 "Clear advice and careful advocacy — for the moments that shape your business and your life.",
                 "Request a consultation", "/contact", "Practice areas", "/services"],
        "stats": [("25+", "Years"), ("Fixed", "Fees where possible"), ("500+", "Matters handled"), ("Discreet", "Always")],
        "feat": ("Practice areas", "Where we help most.", [
            ("shield", "Business & contracts", "Formation, agreements, and the fine print that protects you."),
            ("layers", "Real estate", "Purchases, leases, and closings handled cleanly."),
            ("sparkles", "Estates & wills", "Plan ahead and protect the people who matter.")]),
        "gallery": ("The firm", "Considered and calm.", ["Our office", "The library", "A working session", "Meeting room"]),
        "steps": ("How we work", "Clear from day one.", [
            ("Consult", "A frank first conversation about your situation."),
            ("Plan", "A clear strategy and a fee you agree to up front."),
            ("Act", "Careful, timely work with no surprises."), ("Resolve", "We see it through and keep you informed.")]),
        "quotes": ("Clients say", [
            ("Calm, clear, and always a step ahead.", "R. Halloran", "Client"),
            ("Explained my options without the jargon.", "S. Okafor", "Client"),
            ("Fees agreed up front — no surprises.", "M. & J. Reyes", "Clients")]),
        "pricing": ("Fees", "Transparent and agreed up front.", [
            ("Consultation", "$200", "/hour", ["Frank assessment", "Clear options", "No obligation"], False),
            ("Fixed-fee matter", "Quoted", "", ["Agreed up front", "No hourly surprises", "Defined scope"], True),
            ("Retainer", "Custom", "", ["Ongoing counsel", "Priority access", "Predictable cost"], False)]),
        "faq": ("Good to know", [
            ("How are fees structured?", "Fixed fees wherever possible, agreed in writing before we start."),
            ("Is a first call confidential?", "Always — your first conversation is private and without obligation.")]),
        "cta": ("Need advice you can trust?", "Request a consultation — the first conversation is confidential.", "Request a consultation"),
        "imgs": {"hero": "a distinguished law office interior with floor-to-ceiling bookshelves, warm directional light, leather and wood, authoritative and calm",
                 "g0": "an elegant law firm office, deep wood, brass details, refined",
                 "g1": "a wall of law books in a warm library, soft light",
                 "g2": "two professionals in a calm meeting, a document on the table, trust, muted tones",
                 "g3": "a refined boardroom with a long table, soft daylight",
                 "cta": "a confident, warm handshake in a refined office, soft light, trust, soft focus"},
        "imageStyle": "deep navy and warm gold tones, refined directional light, authoritative and timeless, editorial corporate photography, photorealistic, no text, no watermark, no logo",
    },
    "fitness": {
        "prefix": "fit",
        "hero": ["First class free", "Stronger,", "every week.",
                 "Coaching that meets you where you are — small classes, real progress, and a room that actually feels good to walk into.",
                 "Start free", "/contact", "See classes", "/services"],
        "stats": [("4.9★", "Member rating"), ("First", "Class free"), ("20+", "Classes / week"), ("Small", "Group sizes")],
        "feat": ("Train with us", "Coached, not crowded.", [
            ("zap", "Strength", "Build real strength with proper coaching and progression."),
            ("gauge", "Conditioning", "Heart-pumping sessions that scale to any level."),
            ("sparkles", "Mobility", "Move better and feel good — recovery matters.")]),
        "gallery": ("Inside the gym", "Bright, clean, and motivating.", ["The training floor", "A class in motion", "Free weights", "Recovery space"]),
        "steps": ("Getting started", "From first visit to first win.", [
            ("Book free", "Claim your first class — no commitment."), ("Assess", "A quick chat about your goals and starting point."),
            ("Train", "Small classes with a coach who knows your name."), ("Progress", "Track real gains and keep showing up.")]),
        "quotes": ("Members say", [
            ("Strongest I've been in years — and I actually enjoy it.", "Priya N.", "Member"),
            ("Coaches who care and a room with zero ego.", "Dev S.", "Member"),
            ("Lost 20lb and gained a community.", "Ben K.", "Member")]),
        "pricing": ("Memberships", "Simple, no lock-in.", [
            ("Drop-in", "$22", "/class", ["Any class", "No commitment", "Great to start"], False),
            ("Unlimited", "$149", "/mo", ["All classes", "Free first class", "Cancel anytime"], True),
            ("Coaching", "$249", "/mo", ["Unlimited classes", "Monthly check-ins", "Custom programming"], False)]),
        "faq": ("Good to know", [
            ("I'm a total beginner — is that ok?", "Absolutely. Every class scales, and your first one is free."),
            ("Do I need to book classes?", "Yes — small group sizes mean a spot is always yours.")]),
        "cta": ("Ready to start?", "Your first class is on us — come see how it feels.", "Start free"),
        "imgs": {"hero": "a bright modern gym with people training in a small group class, energetic but clean, natural light, motivating",
                 "g0": "a clean modern gym training floor with equipment, bright daylight, inviting",
                 "g1": "people mid-workout in a group fitness class, motion and energy, natural light",
                 "g2": "free weights neatly racked in a modern gym, soft light, detail",
                 "g3": "a calm stretching and recovery area in a gym, plants, natural light",
                 "cta": "a coach high-fiving a member after a workout, genuine, bright gym, soft focus"},
        "imageStyle": "bright energetic natural light, clean modern tones with a bold accent, dynamic but premium fitness photography, photorealistic, no text, no watermark, no logo",
    },
    "education": {
        "prefix": "edu",
        "hero": ["Now enrolling", "Learning that", "actually sticks.",
                 "Clear lessons, real progress, and a teacher who meets every student where they are — online or in person.",
                 "Book a free trial", "/contact", "See programs", "/services"],
        "stats": [("1,200+", "Students taught"), ("4.9★", "Parent rating"), ("10+ yrs", "Teaching"), ("1:1", "Attention")],
        "feat": ("How we teach", "Structure, clarity, and encouragement.", [
            ("book", "Clear curriculum", "A plan you can follow, milestone by milestone, with no gaps left behind."),
            ("gauge", "Real progress", "Regular check-ins and reports so you always know where things stand."),
            ("shield", "Caring teachers", "Patient, encouraging tutors who make hard ideas finally click.")]),
        "gallery": ("Inside the classroom", "Where the learning happens.", ["A lesson in progress", "Our study space", "One-on-one help", "Happy results"]),
        "steps": ("How to start", "From first call to first win.", [
            ("Free trial", "Book a no-pressure trial lesson to see the fit."), ("Assess", "We find the level and set clear goals together."),
            ("Learn", "Weekly lessons tailored to the student's pace."), ("Track", "Progress reports keep everyone on the same page.")]),
        "quotes": ("What parents say", [
            ("Her grades jumped a full level in one term — and she enjoys it now.", "A parent", "Grade 9"),
            ("Patient, clear, and genuinely kind. Exactly what we hoped for.", "A parent", "Grade 11"),
            ("Booked a trial, never looked back.", "A parent", "Grade 7")]),
        "pricing": ("Programs", "Simple, flexible plans.", [
            ("Single lesson", "$60", "/hour", ["1:1 tutoring", "Any subject", "Flexible scheduling"], False),
            ("Termly plan", "$540", "/10 lessons", ["Save per lesson", "Progress reports", "Priority booking"], True),
            ("Small group", "$35", "/seat", ["2–4 students", "Same level", "Collaborative learning"], False)]),
        "faq": ("Common questions", [
            ("Do you teach online or in person?", "Both — whatever works best for the student and family."),
            ("Can we start with a trial?", "Yes — a free first lesson so you can make sure it's a fit.")]),
        "cta": ("Ready to see progress?", "Book a free trial lesson — no pressure, no commitment.", "Book a free trial"),
        "imgs": {"hero": "a warm encouraging tutor helping a happy student at a bright study table with books and a laptop, natural light, focused and positive",
                 "g0": "a tutor and student working together at a desk, engaged, bright classroom, natural light",
                 "g1": "a calm modern study space with bookshelves and a big table, warm daylight",
                 "g2": "close-up of a student writing in a workbook while a teacher points and explains, encouraging",
                 "g3": "a smiling student holding a graded test with a thumbs up, bright and hopeful",
                 "cta": "a teacher and student sharing a high-five at a study desk, genuine joy, warm light, soft focus"},
        "imageStyle": "bright warm natural light, friendly approachable blue and amber tones, encouraging and credible education photography, photorealistic, no text, no watermark, no logo",
    },
    "realestate": {
        "prefix": "re",
        "hero": ["Now listing", "Find the address that", "feels like home.",
                 "Local expertise, honest advice, and a calm hand through every step of buying or selling.",
                 "Book a viewing", "/contact", "Browse listings", "/services"],
        "stats": [("$2.1B", "Sold to date"), ("1,400+", "Homes closed"), ("21 days", "Avg. to offer"), ("98%", "Of asking")],
        "feat": ("How we help", "From first viewing to the keys.", [
            ("shield", "Sell for more", "Real pricing data and standout photography that move homes fast."),
            ("layers", "Buy with confidence", "Off-market access and honest advice on every property."),
            ("gauge", "Smooth closings", "We manage the paperwork and the timeline so you don't have to.")]),
        "gallery": ("Featured spaces", "A look at what we list.", ["A bright living room", "A modern kitchen", "Curb appeal", "A calm bedroom"]),
        "steps": ("How it works", "Four simple steps.", [
            ("Meet", "Tell us your goals and timeline over a free consult."), ("Plan", "We price with real data and build a tailored strategy."),
            ("Go live", "Pro photos, listings, and viewings that convert."), ("Close", "We handle offers and paperwork to a clean close.")]),
        "quotes": ("From our clients", [
            ("Sold above asking in under three weeks. Calm, sharp, and honest throughout.", "The Halls", "Sellers"),
            ("They found exactly the right home for us — and made it easy.", "L. Moreau", "Buyer"),
            ("First-time buyers and they made it feel effortless.", "Sam & Nia", "Buyers")]),
        "pricing": ("How we charge", "Transparent, agreed up front.", [
            ("Buyer's agent", "Free", "", ["We're paid by the sale", "Off-market access", "Negotiation on your side"], False),
            ("Seller's package", "2.5%", "/sale", ["Pro photography", "Full marketing", "Open houses & viewings"], True),
            ("Rentals & mgmt", "8%", "/mo", ["Tenant screening", "Rent collection", "Maintenance handling"], False)]),
        "faq": ("Questions", [
            ("What are your fees?", "A simple, transparent commission agreed up front — no surprises at closing."),
            ("Do you handle rentals too?", "Yes — sales, lettings, and property management across the city.")]),
        "cta": ("Thinking of making a move?", "Get a free, no-pressure valuation of your home.", "Request a valuation"),
        "imgs": {"hero": "a beautiful modern home exterior at golden hour with warm lights on, inviting, professional real estate photography",
                 "g0": "a bright airy living room with large windows and tasteful furniture, natural light",
                 "g1": "a sleek modern kitchen with an island, clean and luxurious, daylight",
                 "g2": "an attractive house facade with a landscaped front yard, blue sky, curb appeal",
                 "g3": "a serene staged bedroom with soft linens and morning light",
                 "cta": "a happy couple receiving keys in front of their new home, joyful, soft focus"},
        "imageStyle": "bright natural daylight, clean architectural slate and warm neutral tones, premium real estate and interior photography, photorealistic, no text, no watermark, no logo",
    },
    "creative": {
        "prefix": "studio",
        "hero": ["Studio for hire", "Ideas worth", "staring at.",
                 "A small studio making brands, sites, and campaigns that refuse to blend in.",
                 "Start a project", "/contact", "See the work", "/services"],
        "stats": [("120+", "Projects shipped"), ("4.9★", "Client rating"), ("12", "Awards"), ("Senior", "Team only")],
        "feat": ("What we make", "Strategy, identity, and the craft to ship it.", [
            ("sparkles", "Brand identity", "Names, logos, and systems with a real point of view."),
            ("layers", "Websites", "Fast, distinctive sites built to convert and last."),
            ("zap", "Campaigns", "Launches and films that earn attention, not buy it.")]),
        "gallery": ("Selected work", "A few things we're proud of.", ["A brand identity", "A website design", "A campaign still", "A packaging design"]),
        "steps": ("How we work", "A tight, senior process.", [
            ("Discover", "We dig into your goals, audience, and edge."), ("Concept", "A few bold directions, not a hundred safe ones."),
            ("Craft", "We design, build, and polish to a high finish."), ("Launch", "We ship it and help it land with impact.")]),
        "quotes": ("Kind words", [
            ("They gave us an identity people actually talk about. Sales followed.", "CEO", "DTC brand"),
            ("Fast, fearless, and ridiculously talented. Just hire them.", "CMO", "Fintech"),
            ("The site doubled our conversion and won an award. Both.", "Founder", "Studio")]),
        "pricing": ("Engagements", "Pick the scope that fits.", [
            ("Brand sprint", "$6k", "/project", ["Logo + identity", "Brand guidelines", "2-week turnaround"], False),
            ("Website", "$18k", "/project", ["Design + build", "CMS + handoff", "Built to convert"], True),
            ("Retainer", "$5k", "/mo", ["Ongoing design", "Priority access", "A senior team"], False)]),
        "faq": ("Good to know", [
            ("Who actually does the work?", "Founders and senior designers — never juniors or account layers."),
            ("How fast can you start?", "Usually within a week; sprints can be quicker.")]),
        "cta": ("Got something to launch?", "Tell us what you're building — we'll bring the craft.", "Start a project"),
        "imgs": {"hero": "a bold creative studio workspace with mood boards and design prints on the wall, energetic, natural light",
                 "g0": "a striking brand identity flatlay with logo and color swatches on a clean desk",
                 "g1": "a designer's screen showing a beautiful website mockup, modern studio, soft light",
                 "g2": "a cinematic campaign film still, bold and artful, high contrast",
                 "g3": "premium product packaging design on a minimal surface, studio lighting",
                 "cta": "a creative team collaborating energetically around a table of sketches, candid, soft focus"},
        "imageStyle": "bold high-contrast studio lighting, confident contemporary tones with a punchy accent, editorial design and agency photography, photorealistic, no text, no watermark, no logo",
    },
    "tech": {
        "prefix": "saas",
        "hero": ["Ship faster", "The platform your", "team will love.",
                 "Launch, measure, and iterate from one clean workspace — no glue code, no busywork.",
                 "Start free", "/contact", "See how it works", "/services"],
        "stats": [("10x", "Faster setup"), ("99.9%", "Uptime"), ("<200ms", "API latency"), ("SOC 2", "Ready")],
        "feat": ("Everything you need to scale", "Built for teams that move fast and break nothing.", [
            ("zap", "Fast by default", "Sub-second loads and a snappy API your users feel."),
            ("shield", "Secure & compliant", "Encryption, audit logs, and SSO out of the box."),
            ("gauge", "Observable", "Dashboards and alerts so nothing slips by.")]),
        "gallery": ("Inside the product", "A look at the workspace.", ["The dashboard", "Team collaboration", "Analytics view", "Mobile app"]),
        "steps": ("Get started", "Live the same day.", [
            ("Sign up", "Create your workspace in under a minute."), ("Connect", "Plug in your stack with native integrations."),
            ("Build", "Ship your first workflow with no glue code."), ("Scale", "Grow with usage-based pricing that's predictable.")]),
        "quotes": ("Loved by teams", [
            ("We replaced five tools with one. The team is faster and happier.", "S. Patel", "Head of Ops"),
            ("Setup took an afternoon. Support actually knows the product.", "K. Brooks", "CTO"),
            ("The fastest, cleanest tool in our stack by far.", "L. Romano", "Eng lead")]),
        "pricing": ("Pricing that scales", "Start free. Upgrade when it pays for itself.", [
            ("Free", "$0", "/mo", ["1 project", "Community support", "Core API"], False),
            ("Team", "$49", "/mo", ["Unlimited projects", "SSO + audit logs", "Priority support"], True),
            ("Enterprise", "Custom", "", ["SLA + SOC 2", "Dedicated infra", "Solutions engineer"], False)]),
        "faq": ("Questions", [
            ("How long does setup take?", "Most teams are live the same day — connect your stack and go."),
            ("Can I self-host?", "Yes — it runs on your own server and domain, fully owned.")]),
        "cta": ("Ready to ship faster?", "Spin up a workspace in minutes — free to start.", "Start free"),
        "imgs": {"hero": "a sleek modern SaaS dashboard on a laptop in a bright office, clean UI, professional, natural light",
                 "g0": "a clean analytics dashboard on a large monitor, modern workspace",
                 "g1": "a diverse product team collaborating at a desk with laptops, bright office",
                 "g2": "colorful data visualizations and charts on a screen, crisp and modern",
                 "g3": "a smartphone showing a clean mobile app interface, minimal, soft light",
                 "cta": "a happy developer team celebrating a launch in a modern office, candid, soft focus"},
        "imageStyle": "bright clean natural light, modern indigo and cyan tech tones, crisp product and workspace photography, photorealistic, no text, no watermark, no logo",
    },
    "nonprofit": {
        "prefix": "ngo",
        "hero": ["Join the cause", "Together,", "we can do more.",
                 "Real change, made by ordinary people who show up. Your support goes further than you think.",
                 "Donate", "/contact", "Volunteer", "/services"],
        "stats": [("50k+", "People helped"), ("120", "Volunteers"), ("92%", "Goes to programs"), ("15 yrs", "On the ground")],
        "feat": ("How we help", "Direct, lasting, and accountable.", [
            ("sparkles", "Direct support", "Meeting immediate needs with dignity and care."),
            ("book", "Long-term programs", "Building skills and stability that last beyond a crisis."),
            ("mail", "Community", "Connecting people who care to people who need it.")]),
        "gallery": ("Our work", "Moments from the field.", ["Helping hands", "A community event", "Volunteers at work", "A family we served"]),
        "steps": ("How to help", "A few ways to make a difference.", [
            ("Give", "A one-time or monthly gift — every dollar tracked."), ("Volunteer", "Lend a few hours; we'll match you to a need."),
            ("Spread the word", "Share our work and grow the circle of support."), ("See the impact", "We report exactly where your help goes.")]),
        "quotes": ("Voices we serve", [
            ("They didn't just help — they treated us like family.", "A. R.", "Program member"),
            ("I volunteer because I see exactly where it goes.", "J. M.", "Volunteer"),
            ("This is what hope looks like, up close.", "Local partner", "Community")]),
        "pricing": ("Ways to give", "Any amount makes a difference.", [
            ("One-time", "Any", "", ["Goes straight to programs", "Tax-deductible", "Instant receipt"], False),
            ("Monthly", "$25", "/mo", ["Sustained impact", "Cancel anytime", "Member updates"], True),
            ("Partner", "Custom", "", ["Corporate matching", "Event sponsorship", "Named programs"], False)]),
        "faq": ("Good to know", [
            ("Where does my donation go?", "92% goes directly to programs — we publish a full annual report."),
            ("Is my gift tax-deductible?", "Yes — you'll get a receipt by email right away.")]),
        "cta": ("Be part of it.", "Give, volunteer, or just spread the word — it all helps.", "Get involved"),
        "imgs": {"hero": "volunteers and community members smiling together outdoors at a charity event, warm and hopeful, natural light",
                 "g0": "many hands joined together in a circle of support, warm and hopeful, soft light",
                 "g1": "a lively community volunteer event outdoors, people helping, bright day",
                 "g2": "volunteers sorting donations and supplies, busy and purposeful",
                 "g3": "a grateful family smiling warmly, candid portrait, hopeful",
                 "cta": "a diverse group of volunteers in matching shirts smiling together, genuine, soft focus"},
        "imageStyle": "warm natural daylight, hopeful green and amber tones, sincere documentary nonprofit photography, photorealistic, no text, no watermark, no logo",
    },
    "finance": {
        "prefix": "fin",
        "hero": ["Now taking clients", "Grow it. Protect it.", "Understand it.",
                 "Clear advice and steady hands for your money — no jargon, no surprises.",
                 "Book a consultation", "/contact", "Our services", "/services"],
        "stats": [("$2B+", "Under advice"), ("20 yrs", "Track record"), ("0", "Hidden fees"), ("24/7", "Account access")],
        "feat": ("What we do", "The essentials, done with care.", [
            ("shield", "Plan", "A clear roadmap for your goals and your timeline."),
            ("gauge", "Invest", "Disciplined, diversified, and tax-aware portfolios."),
            ("layers", "Protect", "Insurance and estate planning that actually holds up.")]),
        "gallery": ("Our practice", "Calm, professional, and clear.", ["A client meeting", "Our office", "Planning together", "A clear report"]),
        "steps": ("How we work", "Clear from day one.", [
            ("Consult", "A free first conversation about your situation."), ("Plan", "A written plan with transparent, agreed fees."),
            ("Invest", "We put the plan to work, tax-aware throughout."), ("Review", "Regular check-ins so the plan tracks your life.")]),
        "quotes": ("Client confidence", [
            ("They explained everything plainly and got us on track fast.", "R. Halloran", "Client"),
            ("Transparent fees and real advice. A breath of fresh air.", "S. Okafor", "Client"),
            ("I finally understand my money — and I sleep better.", "M. & J. Reyes", "Clients")]),
        "pricing": ("Transparent fees", "No surprises, ever.", [
            ("Starter", "0.5%", "/yr", ["Core plan", "Annual review", "Online access"], False),
            ("Wealth", "0.8%", "/yr", ["Full plan", "Quarterly reviews", "Tax + estate"], True),
            ("Family office", "Custom", "", ["Dedicated team", "Bespoke planning", "Concierge service"], False)]),
        "faq": ("Questions", [
            ("Are you a fiduciary?", "Yes — we're legally bound to act in your best interest."),
            ("What's the minimum?", "We work with a range of clients — let's talk about your situation.")]),
        "cta": ("Take the first step.", "Book a free, no-pressure consultation today.", "Book a consultation"),
        "imgs": {"hero": "a professional financial advisor meeting warmly with a client at a desk, charts on screen, bright office, trustworthy",
                 "g0": "two people in a calm financial consultation, documents on the table, trust",
                 "g1": "a sleek professional office with a city view, calm and credible",
                 "g2": "clear financial charts and planning documents on a desk, organized",
                 "g3": "a clean printed financial report with glasses and a pen, professional detail",
                 "cta": "a confident handshake between advisor and happy client in a bright office, soft focus"},
        "imageStyle": "bright professional natural light, trustworthy emerald and navy tones, calm credible finance photography, photorealistic, no text, no watermark, no logo",
    },
}

# Upgrade those industry presets in place to the complete, image-ready home (keeps
# each preset's own tokens / voice / name; only the composition + imagery are leveled up).
for _ind, _spec in _RICH_INDUSTRY_SPECS.items():
    if _ind in STYLE_PRESETS:
        _built = _industry_home(_spec)
        STYLE_PRESETS[_ind]["sections"] = _built["sections"]
        STYLE_PRESETS[_ind]["images"] = _built["images"]
        STYLE_PRESETS[_ind]["imageStyle"] = _built["imageStyle"]


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


# Industries offered in the visitor "try an industry" preview demo, in display order
# (the owner's key verticals first). Each maps to a full, image-ready template.
DEMO_INDUSTRIES = ["beauty", "education", "restaurant", "healthcare", "fitness",
                   "legal", "realestate", "creative", "tech", "finance", "nonprofit"]


def demo_industries() -> list:
    """[{key, name}] for the industries a visitor can preview — each maps to a complete
    template (see STYLE_PRESETS)."""
    return [{"key": k, "name": STYLE_PRESETS[k].get("name", k)} for k in DEMO_INDUSTRIES if k in STYLE_PRESETS]
