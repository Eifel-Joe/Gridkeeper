"""
Round 47 (p591): latch, hinge and handle pin are drawn once per Fusion session and every box gets copies of their
bodies (spec dev-notes/specs/2026-11-19-r47-box-small-parts.md, requirement 1); the handle keeps its width parameter
and is drawn in each set.
"""

import sys
import types

import pytest

from tests.test_joint_origin_layout import _load

cache = _load("predPartCache")


def test_latch_hinge_and_pin_are_copied_the_handle_is_drawn():
    assert cache.COPIED_ROLES == ("Latch", "Handle pin", "Hinge")
    assert "Handle" not in cache.COPIED_ROLES


def test_only_the_hinge_key_carries_the_variant():
    assert cache.cacheKey("Hinge", "M3x30") != cache.cacheKey("Hinge", "Pinned")
    assert cache.cacheKey("Latch", "M3x30") == cache.cacheKey("Latch", "Plain")
    assert cache.cacheKey("Handle pin", "M3x30") == cache.cacheKey("Handle pin", "Pinned")
    assert cache.cacheKey("Latch", "M3x30") != cache.cacheKey("Handle pin", "M3x30")


def test_a_part_is_drawn_once_and_kept():
    parts = cache.PartCache()
    calls = []

    def draw():
        calls.append(1)
        return [("Latch", "body")]

    first = parts.bodies(cache.cacheKey("Latch", "M3x30"), draw)
    again = parts.bodies(cache.cacheKey("Latch", "Plain"), draw)
    assert first == again == [("Latch", "body")]
    assert len(calls) == 1


def test_each_hinge_variant_is_drawn_once():
    parts = cache.PartCache()
    drawn = []
    for hinge in ("M3x30", "Pinned", "M3x30", "Pinned"):
        parts.bodies(cache.cacheKey("Hinge", hinge), lambda hinge=hinge: drawn.append(hinge) or [(hinge, hinge)])
    assert drawn == ["M3x30", "Pinned"]


def test_a_failed_drawing_keeps_nothing_and_the_next_box_tries_again():
    parts = cache.PartCache()

    def fails():
        raise RuntimeError("no scratch")

    with pytest.raises(RuntimeError):
        parts.bodies(cache.cacheKey("Latch", "M3x30"), fails)
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "body")]) == [("Latch", "body")]


def test_a_drawing_without_bodies_is_not_kept():
    parts = cache.PartCache()
    with pytest.raises(ValueError):
        parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [])
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "body")]) == [("Latch", "body")]


def test_clear_forgets_every_part():
    parts = cache.PartCache()
    parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "old")])
    parts.clear()
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "new")]) == [("Latch", "new")]


def test_the_session_has_one_cache():
    assert isinstance(cache.SESSION, cache.PartCache)


# round 49 (p610): a store on disk behind the session's memory

class FakeStore:
    def __init__(self, files=None, failLoad=False, failSave=False):
        self.files = dict(files or {})
        self.saved = []
        self.failLoad = failLoad
        self.failSave = failSave

    def load(self, key):
        if self.failLoad:
            raise OSError("unreadable")
        return self.files.get(key)

    def discard(self, key):
        self.discarded = getattr(self, "discarded", []) + [key]
        self.files.pop(key, None)

    def save(self, key, kept):
        if self.failSave:
            raise OSError("disk full")
        self.saved.append(key)
        self.files[key] = list(kept)


def test_a_part_on_disk_is_read_not_drawn():
    store = FakeStore({cache.cacheKey("Latch", "M3x30"): [("Latch", "from file")]})
    parts = cache.PartCache(store=lambda: store)
    drawn = []
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: drawn.append(1) or [("Latch", "drawn")]) == [("Latch", "from file")]
    assert drawn == [] and store.saved == []


def test_a_drawn_part_is_written_and_kept_in_memory():
    store = FakeStore()
    parts = cache.PartCache(store=lambda: store)
    key = cache.cacheKey("Hinge", "Pinned")
    parts.bodies(key, lambda: [("Hinge top", "drawn")])
    store.files.clear()
    assert parts.bodies(key, lambda: [("Hinge top", "again")]) == [("Hinge top", "drawn")]
    assert store.saved == [key]


def test_store_failures_draw_and_build_anyway():
    logged = []
    for store in (FakeStore(failLoad=True), FakeStore(failSave=True)):
        parts = cache.PartCache(store=lambda store=store: store, log=logged.append)
        assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "drawn")]) == [("Latch", "drawn")]
    assert any("unreadable" in line for line in logged) and any("disk full" in line for line in logged)


def test_a_store_that_cannot_be_set_up_leaves_the_session_cache():
    logged = []

    def noStore():
        raise RuntimeError("no manifest")

    parts = cache.PartCache(store=noStore, log=logged.append)
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "drawn")]) == [("Latch", "drawn")]
    assert parts.bodies(cache.cacheKey("Handle pin", "M3x30"), lambda: [("Handle pin", "drawn")]) == [("Handle pin", "drawn")]
    assert len([line for line in logged if "no manifest" in line]) == 1


def test_an_empty_read_is_drawn():
    store = FakeStore({cache.cacheKey("Latch", "M3x30"): []})
    parts = cache.PartCache(store=lambda: store)
    assert parts.bodies(cache.cacheKey("Latch", "M3x30"), lambda: [("Latch", "drawn")]) == [("Latch", "drawn")]


def test_the_session_cache_keeps_parts_on_disk():
    assert cache.SESSION._store is not None


def test_forget_drops_the_part_from_memory_and_disk():
    """Review round 49: a file that reads but cannot be copied must be drawn and written anew, not kept for good"""
    store = FakeStore({cache.cacheKey("Latch", "M3x30"): [("Latch", "unusable")]})
    parts = cache.PartCache(store=lambda: store)
    key = cache.cacheKey("Latch", "M3x30")
    assert parts.bodies(key, lambda: [("Latch", "drawn")]) == [("Latch", "unusable")]
    parts.forget(key)
    assert store.discarded == [key]
    assert parts.bodies(key, lambda: [("Latch", "drawn")]) == [("Latch", "drawn")]
    assert store.files[key] == [("Latch", "drawn")]


def test_forget_never_fails():
    logged = []

    class Refuses(FakeStore):
        def discard(self, key):
            raise OSError("in use")

    parts = cache.PartCache(store=lambda: Refuses(), log=logged.append)
    parts.forget(cache.cacheKey("Latch", "M3x30"))
    assert any("in use" in line for line in logged)


def test_the_session_key_is_taken_when_the_module_loads(monkeypatch):
    """Review round 49: code checked out while Fusion runs must not be keyed with the code that is loaded"""
    package = cache.__name__.rsplit(".", 1)[0]
    partFile = sys.modules[package + ".predPartFile"]
    # commonUtils needs the add-in's config, not in this test package: its log only
    monkeypatch.setitem(sys.modules, package + ".commonUtils", types.SimpleNamespace(fileLog=print))
    loaded = cache._SESSION_KEY
    assert loaded == partFile.sessionKey()
    original = partFile.codeStamp
    partFile.codeStamp = lambda folder: "checked0out0"
    try:
        assert (cache._sessionStore().version, cache._sessionStore().stamp) == loaded
    finally:
        partFile.codeStamp = original
