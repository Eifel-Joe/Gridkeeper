"""
Tests for the name a joint made by a rebuild gets once the old part is gone (round 43, p430): Fusion counts a name
still taken up, the new joint of a bin rebuilt in its cell was "... in cell (1)" while the old one was still there.
"""

import pytest

from tests.test_joint_origin_layout import _load

jointNames = _load("jointNames")


@pytest.mark.parametrize(
    ("name", "taken", "expected"),
    [
        # the old joint is gone: the counter goes
        ("Gridfinity bin 1x1x3 in cell (1)", [], "Gridfinity bin 1x1x3 in cell"),
        ("Gridfinity label 1U M3x10 in pocket (2)", ["Starr1"], "Gridfinity label 1U M3x10 in pocket"),
        # another bin of the same name holds the base: its counter stays the lowest free one
        ("B in cell (1)", ["B in cell"], None),
        ("B in cell (3)", ["B in cell", "B in cell (1)"], "B in cell (2)"),
        ("B in cell (2)", ["B in cell"], "B in cell (1)"),
        # no counter, nothing to do
        ("B in cell", [], None),
        ("Probe (x)", [], None),
        ("(1)", [], None),
    ],
)
def test_freed_name(name, taken, expected):
    assert jointNames.freedName(name, taken) == expected
