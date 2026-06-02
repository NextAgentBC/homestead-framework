"""Block composition engine.

Single source of truth for the typed-block library (the "blocks" an
OpenClaw/Codex agent can compose pages from via natural language) plus the
pure functions that add / update / move / remove / duplicate blocks inside an
ordered ``sections`` list.

Storage is unchanged: a page's composition is the ``sections`` JSON already on
``DesignProfile`` (the home page) and ``Page``. This module adds stable block
ids and manifest-driven validation on top of that list — no DB migration.

The frontend ``SectionRenderer`` is the *view* for these types; this manifest
is the *schema*. Keep field names in sync with ``frontend/components/sections.tsx``.
"""

from copy import deepcopy
from typing import Optional
import uuid


class BlockError(ValueError):
    """Raised for unknown type/variant/id or a bad position — message is
    machine-readable so the calling agent can self-correct."""


# Icons the frontend SectionIcon map supports (mirror of sections.tsx ICONS).
ICONS = ["sparkles", "mail", "shield", "gauge", "layers", "zap", "book", "cloud"]


# --- The typed-block library -------------------------------------------------
# Each block: type, label, category, description, variants (first = default),
# fields (for editors/agents to know the shape), and defaultContent (used to
# scaffold a new instance so a freshly added block already looks complete).
BLOCK_MANIFEST = [
    {
        "type": "hero",
        "label": "Hero",
        "category": "header",
        "description": "Top-of-page headline with optional badge/eyebrow, subhead, and up to two CTAs.",
        "variants": ["split", "centered", "fullbleed"],
        "fields": [
            {"key": "badge", "type": "text", "label": "Badge pill (optional)"},
            {"key": "kicker", "type": "text", "label": "Eyebrow (shown if no badge)"},
            {"key": "headline", "type": "text", "label": "Headline"},
            {"key": "headlineAccent", "type": "text", "label": "Accent line (gradient)"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "cta", "type": "cta", "label": "Primary button"},
            {"key": "secondaryCta", "type": "cta", "label": "Secondary button"},
        ],
        "defaultContent": {
            "kicker": "Your eyebrow",
            "headline": "A clear, benefit-led headline",
            "headlineAccent": "",
            "subhead": "One or two sentences that explain the offer and invite the next step.",
            "cta": {"label": "Get started", "href": "/contact"},
            "secondaryCta": {"label": "Learn more", "href": "/blog"},
        },
    },
    {
        "type": "stats",
        "label": "Stats / KPIs",
        "category": "social-proof",
        "description": "A row of metric value + label pairs.",
        "variants": ["default"],
        "fields": [
            {"key": "items", "type": "list", "label": "Stats",
             "item": [{"key": "value", "type": "text"}, {"key": "label", "type": "text"}]},
        ],
        "defaultContent": {"items": [
            {"value": "99%", "label": "Uptime"},
            {"value": "24/7", "label": "Support"},
            {"value": "10k+", "label": "Users"},
            {"value": "4.9", "label": "Rating"},
        ]},
    },
    {
        "type": "logos",
        "label": "Logo / trust strip",
        "category": "social-proof",
        "description": "A heading plus a row of text chips (partners, tech, press).",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "items", "type": "list", "label": "Chips", "item": [{"key": "label", "type": "text"}]},
        ],
        "defaultContent": {"heading": "Trusted by", "items": [
            {"label": "Acme"}, {"label": "Globex"}, {"label": "Initech"}, {"label": "Umbrella"},
        ]},
    },
    {
        "type": "features",
        "label": "Features",
        "category": "content",
        "description": "Icon + title + body, as cards or as minimal columns.",
        "variants": ["cards", "minimal"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Features",
             "item": [{"key": "icon", "type": "icon"}, {"key": "title", "type": "text"}, {"key": "body", "type": "textarea"}]},
        ],
        "defaultContent": {"heading": "What you get", "subhead": "", "items": [
            {"icon": "sparkles", "title": "Feature one", "body": "A short benefit-led description."},
            {"icon": "shield", "title": "Feature two", "body": "A short benefit-led description."},
            {"icon": "gauge", "title": "Feature three", "body": "A short benefit-led description."},
        ]},
    },
    {
        "type": "problem",
        "label": "Problem / pain points",
        "category": "content",
        "description": "Accent-toned cards naming the pains your offer removes.",
        "variants": ["cards"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Problems",
             "item": [{"key": "icon", "type": "icon"}, {"key": "title", "type": "text"}, {"key": "body", "type": "textarea"}]},
        ],
        "defaultContent": {"heading": "Sound familiar?", "subhead": "", "items": [
            {"icon": "layers", "title": "Problem one", "body": "Describe the pain."},
            {"icon": "gauge", "title": "Problem two", "body": "Describe the pain."},
            {"icon": "shield", "title": "Problem three", "body": "Describe the pain."},
        ]},
    },
    {
        "type": "comparison",
        "label": "Comparison (us vs. them)",
        "category": "content",
        "description": "Two columns; the right one is highlighted as the better choice.",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "left", "type": "column", "label": "Left column",
             "shape": [{"key": "title", "type": "text"}, {"key": "items", "type": "list", "item": [{"key": "_", "type": "text"}]}]},
            {"key": "right", "type": "column", "label": "Right column (highlighted)",
             "shape": [{"key": "title", "type": "text"}, {"key": "items", "type": "list", "item": [{"key": "_", "type": "text"}]}]},
        ],
        "defaultContent": {
            "heading": "Why choose us",
            "left": {"title": "The usual way", "items": ["Downside one", "Downside two", "Downside three"]},
            "right": {"title": "Our way", "items": ["Upside one", "Upside two", "Upside three"]},
        },
    },
    {
        "type": "testimonials",
        "label": "Testimonials",
        "category": "social-proof",
        "description": "Quote cards with author and role.",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "items", "type": "list", "label": "Quotes",
             "item": [{"key": "quote", "type": "textarea"}, {"key": "author", "type": "text"}, {"key": "role", "type": "text"}]},
        ],
        "defaultContent": {"heading": "What people say", "items": [
            {"quote": "A short, specific, credible quote.", "author": "A. Customer", "role": "Title, Company"},
            {"quote": "A short, specific, credible quote.", "author": "B. Customer", "role": "Title, Company"},
            {"quote": "A short, specific, credible quote.", "author": "C. Customer", "role": "Title, Company"},
        ]},
    },
    {
        "type": "pricing",
        "label": "Pricing tiers",
        "category": "conversion",
        "description": "Tier cards with price, features, and a CTA; one can be featured.",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Tiers",
             "item": [{"key": "name", "type": "text"}, {"key": "price", "type": "text"}, {"key": "period", "type": "text"},
                      {"key": "features", "type": "list", "item": [{"key": "_", "type": "text"}]},
                      {"key": "featured", "type": "bool"}, {"key": "cta", "type": "cta"}]},
        ],
        "defaultContent": {"heading": "Pricing", "subhead": "", "items": [
            {"name": "Starter", "price": "$0", "period": "/forever", "features": ["Feature", "Feature"], "cta": {"label": "Get started", "href": "/contact"}},
            {"name": "Pro", "price": "$99", "period": "/mo", "features": ["Everything in Starter", "More"], "featured": True, "cta": {"label": "Choose Pro", "href": "/contact"}},
            {"name": "Enterprise", "price": "Custom", "period": "", "features": ["Everything in Pro", "More"], "cta": {"label": "Contact us", "href": "/contact"}},
        ]},
    },
    {
        "type": "faq",
        "label": "FAQ",
        "category": "content",
        "description": "Accordion of question/answer pairs.",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "items", "type": "list", "label": "Q&A",
             "item": [{"key": "q", "type": "text"}, {"key": "a", "type": "textarea"}]},
        ],
        "defaultContent": {"heading": "Questions", "items": [
            {"q": "A common question?", "a": "A clear, reassuring answer."},
            {"q": "Another question?", "a": "A clear, reassuring answer."},
        ]},
    },
    {
        "type": "cta",
        "label": "Call to action",
        "category": "conversion",
        "description": "A full-width banner with a headline and a button.",
        "variants": ["banner"],
        "fields": [
            {"key": "headline", "type": "text", "label": "Headline"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "cta", "type": "cta", "label": "Button"},
        ],
        "defaultContent": {"headline": "Ready to get started?", "subhead": "", "cta": {"label": "Get in touch", "href": "/contact"}},
    },
    {
        # The "capture" target — one flexible, token-driven block that can express
        # most section layouts the fixed blocks don't cover (e.g. rebuilt from a
        # screenshot). It reads only design tokens, so it auto-harmonizes; the
        # frontend SectionRenderer ('section') must mirror these field names.
        "type": "section",
        "label": "Custom section (flexible)",
        "category": "custom",
        "description": (
            "Flexible token-driven section for layouts the fixed blocks don't cover "
            "(e.g. captured from a screenshot). Pick a variant (grid/split/stack/banner), "
            "set layout.columns 1-4, layout.align left|center, layout.media none|left|right|top, "
            "layout.tone plain|tint|inverse. Each item has a 'kind': feature/stat/quote/step/media/text/button. "
            "Never copy a source's exact colors — colors come from the site's tokens."
        ),
        "variants": ["grid", "split", "stack", "banner"],
        "fields": [
            {"key": "eyebrow", "type": "text", "label": "Eyebrow (optional)"},
            {"key": "heading", "type": "text", "label": "Heading (optional)"},
            {"key": "subhead", "type": "textarea", "label": "Subhead (optional)"},
            {"key": "layout", "type": "object", "label": "Layout", "shape": [
                {"key": "columns", "type": "number", "label": "Columns 1-4"},
                {"key": "align", "type": "enum", "options": ["left", "center"]},
                {"key": "media", "type": "enum", "options": ["none", "left", "right", "top"]},
                {"key": "tone", "type": "enum", "options": ["plain", "tint", "inverse"]},
            ]},
            {"key": "items", "type": "list", "label": "Items", "item": [
                {"key": "kind", "type": "enum", "options": ["feature", "stat", "quote", "step", "media", "text", "button"]},
                {"key": "icon", "type": "icon"}, {"key": "title", "type": "text"}, {"key": "body", "type": "textarea"},
                {"key": "value", "type": "text"}, {"key": "label", "type": "text"},
                {"key": "quote", "type": "textarea"}, {"key": "author", "type": "text"}, {"key": "role", "type": "text"},
                {"key": "image", "type": "text"}, {"key": "href", "type": "text"},
            ]},
            {"key": "cta", "type": "cta", "label": "Footer button (optional)"},
        ],
        "defaultContent": {
            "eyebrow": "", "heading": "A flexible section", "subhead": "",
            "layout": {"columns": 3, "align": "center", "media": "none", "tone": "plain"},
            "items": [
                {"kind": "feature", "icon": "sparkles", "title": "Item one", "body": "Describe it."},
                {"kind": "feature", "icon": "shield", "title": "Item two", "body": "Describe it."},
                {"kind": "feature", "icon": "gauge", "title": "Item three", "body": "Describe it."},
            ],
            "cta": {"label": "", "href": ""},
        },
    },
    {
        "type": "steps",
        "label": "Steps / process",
        "category": "content",
        "description": "Numbered how-it-works steps — icon + title + body, connected in order.",
        "variants": ["default"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Steps",
             "item": [{"key": "icon", "type": "icon"}, {"key": "title", "type": "text"}, {"key": "body", "type": "textarea"}]},
        ],
        "defaultContent": {"heading": "How it works", "subhead": "", "items": [
            {"icon": "sparkles", "title": "Step one", "body": "What happens first."},
            {"icon": "gauge", "title": "Step two", "body": "Then this."},
            {"icon": "shield", "title": "Step three", "body": "And you're done."},
        ]},
    },
    {
        "type": "gallery",
        "label": "Image gallery",
        "category": "media",
        "description": "A responsive grid of images. Use self-hosted URLs (/api/media/<file>) or any public image URL; optional caption per image.",
        "variants": ["grid"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Images",
             "item": [{"key": "image", "type": "text"}, {"key": "caption", "type": "text"}]},
        ],
        "defaultContent": {"heading": "Gallery", "subhead": "", "items": [
            {"image": "", "caption": "Caption one"}, {"image": "", "caption": "Caption two"}, {"image": "", "caption": "Caption three"},
        ]},
    },
    {
        "type": "team",
        "label": "Team",
        "category": "social-proof",
        "description": "Team member cards — name, role, optional photo (image URL) and short bio.",
        "variants": ["cards"],
        "fields": [
            {"key": "heading", "type": "text", "label": "Heading"},
            {"key": "subhead", "type": "textarea", "label": "Subhead"},
            {"key": "items", "type": "list", "label": "Members",
             "item": [{"key": "image", "type": "text"}, {"key": "name", "type": "text"}, {"key": "role", "type": "text"}, {"key": "body", "type": "textarea"}]},
        ],
        "defaultContent": {"heading": "Meet the team", "subhead": "", "items": [
            {"image": "", "name": "Alex Kim", "role": "Founder", "body": "Leads the work and keeps it honest."},
            {"image": "", "name": "Sam Lee", "role": "Design", "body": "Makes everything look the part."},
            {"image": "", "name": "Jo Ray", "role": "Engineering", "body": "Builds it fast and solid."},
        ]},
    },
    {
        "type": "banner",
        "label": "Highlight banner",
        "category": "conversion",
        "description": "A slim highlight strip — an icon, a short message, and an optional button. Good for announcements or offers.",
        "variants": ["default", "tint"],
        "fields": [
            {"key": "icon", "type": "icon", "label": "Icon"},
            {"key": "text", "type": "text", "label": "Message"},
            {"key": "cta", "type": "cta", "label": "Button (optional)"},
        ],
        "defaultContent": {"icon": "sparkles", "text": "Now in beta — try it free this month.", "cta": {"label": "Learn more", "href": "/contact"}},
    },
]

_BY_TYPE = {b["type"]: b for b in BLOCK_MANIFEST}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def manifest() -> list:
    """The full block catalog (deep-copied), plus the icon vocabulary."""
    return deepcopy(BLOCK_MANIFEST)


def block_types() -> list:
    return list(_BY_TYPE.keys())


def block_spec(block_type: str) -> Optional[dict]:
    return _BY_TYPE.get(block_type)


def new_block_id() -> str:
    return "b_" + uuid.uuid4().hex[:8]


def ensure_ids(sections: list) -> bool:
    """Backfill stable ids on any blocks that lack one (legacy data).
    Returns True if anything changed (so the caller can persist)."""
    changed = False
    for block in sections or []:
        if isinstance(block, dict) and not block.get("id"):
            block["id"] = new_block_id()
            changed = True
    return changed


def _validate_variant(block_type: str, variant: Optional[str]) -> Optional[str]:
    spec = _BY_TYPE.get(block_type)
    variants = (spec or {}).get("variants") or []
    if variant is None:
        return variants[0] if variants else None
    if variants and variant not in variants:
        raise BlockError(
            f"Unknown variant '{variant}' for block '{block_type}'. Allowed: {', '.join(variants)}."
        )
    return variant


def make_block(block_type: str, variant: Optional[str] = None, content: Optional[dict] = None) -> dict:
    """Scaffold a complete new block instance from the manifest defaults."""
    spec = _BY_TYPE.get(block_type)
    if not spec:
        raise BlockError(
            f"Unknown block type '{block_type}'. Known types: {', '.join(_BY_TYPE)}."
        )
    resolved_variant = _validate_variant(block_type, variant)
    block = {"id": new_block_id(), "type": block_type}
    if resolved_variant:
        block["variant"] = resolved_variant
    base_content = deepcopy(spec.get("defaultContent", {}))
    block["content"] = _deep_merge(base_content, content) if content else base_content
    return block


def find_index(sections: list, block_id: str) -> int:
    for i, block in enumerate(sections or []):
        if isinstance(block, dict) and block.get("id") == block_id:
            return i
    return -1


def _require_index(sections: list, block_id: str) -> int:
    idx = find_index(sections, block_id)
    if idx < 0:
        raise BlockError(f"No block with id '{block_id}' on this page.")
    return idx


def resolve_position(sections: list, position) -> int:
    """Translate a position spec into an insert index.
    Accepts: None/"end", "start", an int index, or "after:<id>"/"before:<id>"."""
    n = len(sections)
    if position is None or position == "end":
        return n
    if position == "start":
        return 0
    if isinstance(position, bool):  # guard: bool is an int subclass
        raise BlockError(f"Invalid position '{position}'.")
    if isinstance(position, int):
        return max(0, min(position, n))
    if isinstance(position, str) and ":" in position:
        kind, _, ref = position.partition(":")
        idx = find_index(sections, ref)
        if idx < 0:
            raise BlockError(f"Position references unknown block id '{ref}'.")
        if kind == "before":
            return idx
        if kind == "after":
            return idx + 1
    raise BlockError("Invalid position. Use 'start', 'end', an index, or 'after:<id>' / 'before:<id>'.")


def add_block(sections: list, block_type: str, variant: Optional[str] = None,
              content: Optional[dict] = None, position="end") -> dict:
    block = make_block(block_type, variant, content)
    sections.insert(resolve_position(sections, position), block)
    return block


def update_block(sections: list, block_id: str, variant: Optional[str] = None,
                 content: Optional[dict] = None, replace_content: bool = False) -> dict:
    block = sections[_require_index(sections, block_id)]
    if variant is not None:
        block["variant"] = _validate_variant(block["type"], variant)
    if content is not None:
        if replace_content:
            block["content"] = deepcopy(content)
        else:
            block["content"] = _deep_merge(block.get("content") or {}, content)
    return block


def move_block(sections: list, block_id: str, position) -> dict:
    block = sections.pop(_require_index(sections, block_id))
    sections.insert(resolve_position(sections, position), block)
    return block


def duplicate_block(sections: list, block_id: str) -> dict:
    idx = _require_index(sections, block_id)
    clone = deepcopy(sections[idx])
    clone["id"] = new_block_id()
    sections.insert(idx + 1, clone)
    return clone


def remove_block(sections: list, block_id: str) -> dict:
    return sections.pop(_require_index(sections, block_id))


VALID_OPS = ("add", "update", "move", "duplicate", "remove")


def apply_op(sections: list, op: dict) -> dict:
    """Apply a single batch operation in place; return the affected block.
    Raises BlockError (with a machine-readable message) on any problem so the
    caller can roll back / report failedAt. Used by the batch endpoint."""
    if not isinstance(op, dict):
        raise BlockError("Each op must be an object with an 'op' field.")
    kind = (op.get("op") or "").strip().lower()
    if kind == "add":
        return add_block(sections, op.get("type"), op.get("variant"), op.get("content"), op.get("position", "end"))
    if kind == "update":
        return update_block(sections, op.get("id"), op.get("variant"), op.get("content"), bool(op.get("replaceContent", False)))
    if kind == "move":
        return move_block(sections, op.get("id"), op.get("position", "end"))
    if kind == "duplicate":
        return duplicate_block(sections, op.get("id"))
    if kind == "remove":
        return remove_block(sections, op.get("id"))
    raise BlockError(f"Unknown op '{op.get('op')}'. Valid: {', '.join(VALID_OPS)}.")


def _block_title(block: dict) -> str:
    c = block.get("content") or {}
    return c.get("heading") or c.get("headline") or c.get("title") or ""


def summarize(sections: list) -> list:
    """Compact listing for an agent: id, type, variant, a human title, item count."""
    out = []
    for block in sections or []:
        if not isinstance(block, dict):
            continue
        content = block.get("content") or {}
        out.append({
            "id": block.get("id"),
            "type": block.get("type"),
            "variant": block.get("variant"),
            "title": _block_title(block),
            "items": len(content["items"]) if isinstance(content.get("items"), list) else None,
        })
    return out


# ---------------------------------------------------------------------------
# Page templates — the block library organized *by page*. Each common page is a
# recipe of blocks in a sensible order; POST /admin/pages {template:"<name>"}
# scaffolds a full page from one. (The home page = the active design's sections.)
# ---------------------------------------------------------------------------
PAGE_TEMPLATES = {
    "home": {"label": "Home / landing",
        "blurb": "Full landing: open -> prove -> explain -> convert.",
        "blocks": [("hero", "centered", None), ("stats", None, None), ("logos", None, None),
                   ("features", "cards", None), ("steps", None, None), ("comparison", None, None),
                   ("cta", "banner", None)]},
    "about": {"label": "About",
        "blurb": "Who you are, the team, and what you stand for.",
        "blocks": [("hero", "centered", {"headline": "About us", "headlineAccent": "", "subhead": "Who we are and what we believe."}),
                   ("section", "stack", {"heading": "Our story", "items": [
                       {"kind": "text", "title": "How we started", "body": "Share the origin and the why."},
                       {"kind": "text", "title": "What drives us", "body": "The values and the work you care about."}]}),
                   ("stats", None, None), ("team", None, None),
                   ("cta", "banner", {"headline": "Want to work with us?"})]},
    "services": {"label": "Services",
        "blurb": "What you offer, how it works, what it costs.",
        "blocks": [("hero", "centered", {"headline": "What we do", "headlineAccent": "", "subhead": "Clear services, clearly explained."}),
                   ("features", "cards", {"heading": "Services"}), ("steps", None, {"heading": "How we work"}),
                   ("pricing", None, None), ("faq", None, None), ("cta", "banner", None)]},
    "solutions": {"label": "Solutions",
        "blurb": "Problem-first: the pain, your answer, the proof.",
        "blocks": [("hero", "centered", {"headline": "Solutions", "headlineAccent": "", "subhead": "The problems we solve."}),
                   ("problem", None, None), ("features", "cards", {"heading": "How we help"}),
                   ("steps", None, None), ("testimonials", None, None), ("cta", "banner", None)]},
    "pricing": {"label": "Pricing",
        "blurb": "Tiers, comparison, and an FAQ to close.",
        "blocks": [("hero", "centered", {"headline": "Pricing", "headlineAccent": "", "subhead": "Simple, transparent plans."}),
                   ("pricing", None, None), ("comparison", None, None), ("faq", None, None), ("cta", "banner", None)]},
    "landing": {"label": "Campaign landing",
        "blurb": "Focused single-offer landing page.",
        "blocks": [("hero", "fullbleed", None), ("features", "minimal", None),
                   ("testimonials", None, None), ("pricing", None, None), ("cta", "banner", None)]},
    "restaurant": {"label": "Restaurant / café",
        "blurb": "Appetite-first: hero, what you're known for, gallery, reviews, reserve.",
        "blocks": [("hero", "fullbleed", {"headline": "Good food,", "headlineAccent": "made with care.", "subhead": "A warm room, a short menu, done well."}),
                   ("features", "cards", {"heading": "What we're known for"}),
                   ("gallery", None, {"heading": "A look inside"}),
                   ("testimonials", None, {"heading": "What guests say"}),
                   ("banner", "tint", {"text": "Walk-ins welcome · Open Tue–Sun"}),
                   ("cta", "banner", {"headline": "Book a table", "cta": {"label": "Reserve", "href": "/contact"}})]},
    "clinic": {"label": "Clinic / healthcare",
        "blurb": "Trust-first: services, how to book, the team, FAQ.",
        "blocks": [("hero", "split", {"headline": "Care you can trust", "subhead": "Calm, attentive treatment for you and your family."}),
                   ("features", "cards", {"heading": "Our services"}),
                   ("steps", None, {"heading": "How to book"}),
                   ("team", None, {"heading": "Meet the team"}),
                   ("faq", None, None),
                   ("cta", "banner", {"headline": "Book an appointment", "cta": {"label": "Get in touch", "href": "/contact"}})]},
    "law": {"label": "Law firm / advisory",
        "blurb": "Authority-first: practice areas, track record, testimonials.",
        "blocks": [("hero", "split", {"headline": "Counsel you can rely on", "subhead": "Clear advice and steady representation when it matters."}),
                   ("features", "cards", {"heading": "Practice areas"}),
                   ("stats", None, None),
                   ("testimonials", None, {"heading": "Client outcomes"}),
                   ("faq", None, None),
                   ("cta", "banner", {"headline": "Request a consultation", "cta": {"label": "Contact us", "href": "/contact"}})]},
}


def page_template(name: str) -> Optional[dict]:
    return PAGE_TEMPLATES.get((name or "").strip().lower())


def build_page_template(name: str) -> Optional[list]:
    """Fresh sections list scaffolded from a page template, or None if unknown."""
    tpl = page_template(name)
    if not tpl:
        return None
    return [make_block(bt, variant, overrides) for (bt, variant, overrides) in tpl["blocks"]]


def list_page_templates() -> list:
    return [{"name": k, "label": v["label"], "blurb": v.get("blurb", ""),
             "sections": [b[0] for b in v["blocks"]]} for k, v in PAGE_TEMPLATES.items()]
