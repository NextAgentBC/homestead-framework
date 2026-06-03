"""Site-coherence audit — the machine-checkable "definition of done" for a
rebrand / translation pass. Scans every surface × locale and reports incoherence
so an agent (or the operator) can loop until it's clean instead of eyeballing.

A *surface* is the home (active design profile's sections) or a content Page.
The checks are deterministic and JSON-serializable:

  • structural_drift   — a non-default locale's section list has a different
                         block id/type/order than the base (the bug that made
                         the zh home a stale 7-block tech page vs an 8-block base)
  • missing_translation — a localizable string is absent in a locale or still
                         identical to the default-locale text (untranslated)
  • language_mismatch  — CJK text sitting in the default (latin) locale, or a
                         long non-default-zh string with no CJK at all (the
                         "English page showing Chinese / Chinese page in English")
  • industry_residue   — leftover framework/other-industry terms after a rebrand

Pure functions only — no Flask/DB imports — so it is unit-testable in isolation.
"""
from __future__ import annotations

import re

_CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
# Obvious leftovers from the framework / tech-demo that should not survive a
# rebrand into a real-business industry.
_RESIDUE = (
    "openclaw", "homestead", "website framework", "tech stack", "elementor",
    "design tokens", "saas", "oracle site",
)
# Content keys that hold URLs / icon names / machine values, not human copy.
_NON_TEXT_KEYS = {"image", "icon", "href", "imageFocal", "imageAlt", "id", "type", "variant"}
_MAX_PER_SURFACE = 25  # bound the report so one broken surface can't flood it


def _has_cjk(s: str) -> bool:
    return bool(_CJK.search(s or ""))


def _is_trivial(s: str) -> bool:
    """Strings that are legitimately identical across locales: prices, numbers,
    ratings, very short tokens, urls/paths."""
    s = (s or "").strip()
    if len(s) < 4:
        return True
    if s.startswith(("http://", "https://", "/", "#", "var(", "data:")):
        return True
    if not any(c.isalpha() or _has_cjk(c) for c in s):  # pure digits/symbols ($68, 4.9★, 1:1)
        return True
    return False


def _texts(content, _key: str = ""):
    """Yield (key, string) human-copy pairs from a block's content, skipping
    urls/icons and machine fields."""
    out = []

    def walk(v, key):
        if isinstance(v, str):
            if key not in _NON_TEXT_KEYS and v.strip():
                out.append((key, v))
        elif isinstance(v, dict):
            for k, vv in v.items():
                walk(vv, k)
        elif isinstance(v, list):
            for vv in v:
                walk(vv, key)

    walk(content, _key)
    return out


def _sig(sections):
    """Structural signature: ordered (id, type) pairs."""
    return [(b.get("id"), b.get("type")) for b in (sections or [])]


def _audit_surface(surface, default_locale, locales, latin_default, finding):
    name, kind = surface["name"], surface.get("kind", "page")
    base = surface.get("base") or {}
    base_sections = base.get("sections") or []
    base_text = base.get("text") or {}
    i18n = surface.get("i18n") or {}

    # base sections, indexed by id, with their text strings
    base_blocks = {b.get("id"): b for b in base_sections}

    # --- default-locale checks: wrong-language + residue ---------------------
    base_all_text = list(base_text.items())
    for b in base_sections:
        base_all_text += _texts(b.get("content") or {})
    for key, s in base_all_text:
        if latin_default and _has_cjk(s):
            finding(name, default_locale, "language_mismatch",
                    f"default-locale ({default_locale}) text is Chinese: “{s[:48]}”", key)
        low = s.lower()
        for term in _RESIDUE:
            if term in low:
                finding(name, default_locale, "industry_residue",
                        f"leftover term “{term}” in “{s[:48]}”", key)
                break

    # --- per non-default locale ---------------------------------------------
    for loc in locales:
        if loc == default_locale:
            continue
        tr = i18n.get(loc) or {}

        # sections structure + per-block translation
        if base_sections:
            tr_sections = tr.get("sections")
            if tr_sections is None:
                finding(name, loc, "missing_translation", "section content not translated for this locale")
            else:
                if _sig(tr_sections) != _sig(base_sections):
                    finding(name, loc, "structural_drift",
                            f"locale has {len(tr_sections)} blocks vs base {len(base_sections)} "
                            f"(ids/types/order differ) — translate in place, don't restructure")
                else:
                    tr_blocks = {b.get("id"): b for b in tr_sections}
                    for bid, bb in base_blocks.items():
                        base_fields = {k: v for k, v in _texts(bb.get("content") or {})}
                        tr_fields = {k: v for k, v in _texts((tr_blocks.get(bid) or {}).get("content") or {})}
                        for key, s in base_fields.items():
                            if _is_trivial(s):
                                continue
                            tv = tr_fields.get(key)
                            if not tv or tv == s:
                                finding(name, loc, "missing_translation",
                                        f"untranslated: “{s[:40]}”", f"{bid}.{key}")
                            elif loc.startswith("zh") and not _has_cjk(tv) and len(tv) > 8:
                                finding(name, loc, "language_mismatch",
                                        f"zh text has no Chinese: “{tv[:40]}”", f"{bid}.{key}")

        # page-level text fields (title / nav_label / body_markdown / meta)
        for key, s in base_text.items():
            if _is_trivial(s):
                continue
            tv = tr.get(key)
            if not tv or tv == s:
                finding(name, loc, "missing_translation", f"untranslated {key}: “{s[:40]}”", key)
            elif loc.startswith("zh") and not _has_cjk(tv) and len(tv) > 8:
                finding(name, loc, "language_mismatch", f"zh {key} has no Chinese: “{tv[:40]}”", key)


def run_audit(surfaces, default_locale, locales, industry=""):
    """Audit a list of surface dicts; return {ok, findings, summary}.

    Each surface: {name, kind, base:{sections:[...], text:{field:str}}, i18n:{loc:{sections,...}}}.
    """
    latin_default = not str(default_locale or "en").startswith("zh")
    findings = []
    per_surface = {}

    def finding(surface, locale, kind, detail, block_id=None):
        if per_surface.get(surface, 0) >= _MAX_PER_SURFACE:
            return
        per_surface[surface] = per_surface.get(surface, 0) + 1
        item = {"surface": surface, "locale": locale, "kind": kind, "detail": detail}
        if block_id:
            item["blockId"] = block_id
        findings.append(item)

    for s in surfaces:
        _audit_surface(s, default_locale, locales, latin_default, finding)

    by_kind = {}
    for f in findings:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    return {
        "ok": not findings,
        "industry": industry,
        "defaultLocale": default_locale,
        "locales": list(locales),
        "findings": findings,
        "summary": {"surfaces": len(surfaces), "findings": len(findings), "byKind": by_kind},
    }
