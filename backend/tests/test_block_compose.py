"""Unit tests for the block composition engine (pure functions, no app/db)."""

import pytest

from app.services import block_service as bs


CORE_TYPES = ["hero", "stats", "logos", "features", "problem", "comparison",
              "testimonials", "pricing", "faq", "cta"]


def test_manifest_covers_core_types():
    types = bs.block_types()
    for t in CORE_TYPES:
        assert t in types
    # every block declares at least one variant and default content
    for spec in bs.manifest():
        assert spec["variants"]
        assert isinstance(spec.get("defaultContent"), dict)


def test_make_block_scaffolds_defaults_and_id():
    b = bs.make_block("pricing")
    assert b["type"] == "pricing"
    assert b["id"].startswith("b_")
    assert b["variant"] == "default"          # first variant is the default
    assert b["content"]["items"]              # scaffolded so it looks complete


def test_make_block_merges_overrides():
    b = bs.make_block("hero", "centered", {"headline": "Hi"})
    assert b["variant"] == "centered"
    assert b["content"]["headline"] == "Hi"
    assert "subhead" in b["content"]          # defaults preserved by deep-merge


def test_unknown_type_and_variant_raise_clear_errors():
    with pytest.raises(bs.BlockError) as e1:
        bs.make_block("nope")
    assert "Unknown block type" in str(e1.value)
    with pytest.raises(bs.BlockError) as e2:
        bs.make_block("hero", "spinny")
    assert "variant" in str(e2.value)


def test_add_block_positions():
    s = []
    a = bs.add_block(s, "hero")
    bs.add_block(s, "cta", position="start")
    c = bs.add_block(s, "faq", position=f"after:{a['id']}")
    assert [x["type"] for x in s] == ["cta", "hero", "faq"]
    assert s[2]["id"] == c["id"]


def test_update_merges_then_replaces():
    s = [bs.make_block("hero", "split")]
    bid = s[0]["id"]
    bs.update_block(s, bid, variant="centered", content={"headline": "Books you can trust"})
    assert s[0]["variant"] == "centered"
    assert s[0]["content"]["headline"] == "Books you can trust"
    assert "subhead" in s[0]["content"]       # merged, not replaced
    bs.update_block(s, bid, content={"headline": "Only"}, replace_content=True)
    assert s[0]["content"] == {"headline": "Only"}


def test_move_duplicate_remove():
    s = []
    a = bs.add_block(s, "hero")
    bs.add_block(s, "features")
    c = bs.add_block(s, "cta")
    bs.move_block(s, c["id"], "start")
    assert [x["type"] for x in s] == ["cta", "hero", "features"]
    dup = bs.duplicate_block(s, a["id"])
    assert dup["id"] != a["id"]
    assert [x["type"] for x in s] == ["cta", "hero", "hero", "features"]
    bs.remove_block(s, dup["id"])
    assert [x["type"] for x in s] == ["cta", "hero", "features"]


def test_unknown_id_raises_everywhere():
    s = [bs.make_block("hero")]
    for fn in (
        lambda: bs.update_block(s, "missing", content={}),
        lambda: bs.move_block(s, "missing", "end"),
        lambda: bs.remove_block(s, "missing"),
        lambda: bs.duplicate_block(s, "missing"),
    ):
        with pytest.raises(bs.BlockError):
            fn()


def test_bad_position_reference_raises():
    s = [bs.make_block("hero")]
    with pytest.raises(bs.BlockError):
        bs.add_block(s, "cta", position="after:does-not-exist")


def test_ensure_ids_backfills_and_is_idempotent():
    s = [{"type": "hero", "content": {}}, {"type": "cta", "content": {}}]
    assert bs.ensure_ids(s) is True
    assert all(b["id"].startswith("b_") for b in s)
    assert bs.ensure_ids(s) is False


def test_apply_op_dispatches_each_kind():
    s = []
    a = bs.apply_op(s, {"op": "add", "type": "hero", "position": "end"})
    assert s[0]["type"] == "hero"
    bs.apply_op(s, {"op": "add", "type": "cta", "position": "start"})
    bs.apply_op(s, {"op": "update", "id": a["id"], "content": {"headline": "Hi"}})
    assert next(b for b in s if b["id"] == a["id"])["content"]["headline"] == "Hi"
    bs.apply_op(s, {"op": "duplicate", "id": a["id"]})
    bs.apply_op(s, {"op": "move", "id": a["id"], "position": "end"})
    assert [b["type"] for b in s] == ["cta", "hero", "hero"]
    bs.apply_op(s, {"op": "remove", "id": s[-1]["id"]})
    assert len(s) == 2


def test_apply_op_unknown_op_raises():
    with pytest.raises(bs.BlockError) as e:
        bs.apply_op([], {"op": "frobnicate"})
    assert "Unknown op" in str(e.value)


def test_summarize_shape():
    s = [bs.make_block("hero", content={"headline": "Welcome"}), bs.make_block("features")]
    out = bs.summarize(s)
    assert out[0]["type"] == "hero" and out[0]["title"] == "Welcome"
    assert out[1]["type"] == "features" and out[1]["items"] == 3
    assert all("id" in row for row in out)
