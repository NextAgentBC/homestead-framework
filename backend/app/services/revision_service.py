"""Surface revision history — snapshot before each change so edits are undoable.

A "surface" is an editable thing:
  • "home"          — the active design profile's section list
  • "page:<slug>"   — a content page's sections
  • "design"        — the whole active design profile (tokens + voice + sections),
                      captured on a theme switch / token change

Every compose mutation and design change records the **prior** state here, so
the operator (or the assistant) can undo the last change or jump back to a kept point — no
redeploy. History is capped per (surface, locale) so it can't grow without bound.

This module owns persistence only; the admin routes decide *what* to snapshot and
how to write a snapshot back onto its surface.
"""
from __future__ import annotations

from flask import current_app

from ..extensions import db
from ..models import Revision

DEFAULT_CAP = 50


def _cap() -> int:
    try:
        return int(current_app.config.get("REVISION_HISTORY", DEFAULT_CAP))
    except (RuntimeError, TypeError, ValueError):
        return DEFAULT_CAP


def record(surface: str, locale, kind: str, snapshot, label: str = "") -> Revision:
    """Push a prior-state snapshot for a surface, then prune old history. The row
    is flushed (not committed) so it joins the caller's transaction — the snapshot
    and the change it precedes are saved (or rolled back) together."""
    rev = Revision(
        surface=surface,
        locale=(locale or ""),
        kind=kind,
        snapshot=snapshot,
        label=(label or "")[:255],
    )
    db.session.add(rev)
    db.session.flush()
    _prune(surface, locale or "")
    return rev


def _prune(surface: str, locale: str) -> None:
    """Delete snapshots beyond the cap for this (surface, locale), oldest first."""
    extra = (
        Revision.query
        .filter_by(surface=surface, locale=locale)
        .order_by(Revision.id.desc())
        .offset(_cap())
        .all()
    )
    for rev in extra:
        db.session.delete(rev)


def history(surface=None, locale=None, limit: int = 50):
    """Snapshots newest-first. With no surface → recent across all surfaces; with a
    surface and locale → just that one editable surface."""
    q = Revision.query
    if surface is not None:
        q = q.filter_by(surface=surface)
        if locale is not None:
            q = q.filter_by(locale=(locale or ""))
    return q.order_by(Revision.id.desc()).limit(max(1, min(int(limit), 200))).all()


def latest(surface: str, locale):
    return (
        Revision.query
        .filter_by(surface=surface, locale=(locale or ""))
        .order_by(Revision.id.desc())
        .first()
    )
