"""
Round 44 (p570): the names a build asks for its components, recorded while a rebuild builds, so the rebuild can tell
Fusion's counter ("Gridfinity bin 1x1x3 (1)") from a name asked for with an "(n)" of its own.
"""

import pytest

from tests.test_joint_origin_layout import _load

componentNames = _load("componentNames")


class _Component:
    name = ""


def test_naming_sets_the_name_and_records_it_while_recording():
    first = _Component()
    second = _Component()
    componentNames.name(first, "outside")
    with componentNames.recording() as named:
        componentNames.name(second, "B")
    assert first.name == "outside" and second.name == "B"
    assert named == [(second, "B")]


def test_nothing_is_recorded_outside_a_recording():
    with componentNames.recording() as named:
        pass
    componentNames.name(_Component(), "after")
    assert named == []


def test_a_failing_build_ends_the_recording():
    with pytest.raises(RuntimeError):
        with componentNames.recording():
            raise RuntimeError("build failed")
    with componentNames.recording() as named:
        pass
    componentNames.name(_Component(), "after")
    assert named == []
