"""
Round 47 (p591): latch, hinge and handle pin are drawn once per Fusion session and every box gets copies of their
bodies (spec dev-notes/specs/2026-11-19-r47-box-small-parts.md, requirement 1); the handle keeps its width parameter
and is drawn in each set.
"""

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
