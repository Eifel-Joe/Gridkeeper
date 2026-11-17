"""
p292 (r28_insert_check l3, 17.11.2026): importing a part file made Fusion write a folder _XRef_ with copies of the
files beside it, in the add-in's own folder. The parts are imported from a copy in a temporary folder that goes away
afterwards, with what Fusion wrote there.
"""

import os

import pytest

from tests.test_joint_origin_layout import _load

tempCopy = _load("tempCopy")


def _source(tmp_path):
    folder = tmp_path / "resources"
    folder.mkdir()
    path = folder / "hinge.f3d"
    path.write_bytes(b"part")
    return folder, path


def test_the_part_is_used_from_a_copy_elsewhere_and_its_folder_gets_nothing(tmp_path):
    folder, path = _source(tmp_path)
    seen = []

    def use(copy):
        seen.append(copy)
        assert os.path.dirname(copy) != str(folder)
        assert open(copy, "rb").read() == b"part"
        os.makedirs(os.path.join(os.path.dirname(copy), "_XRef_"))
        return "imported"

    assert tempCopy.withTempCopy(str(path), use) == "imported"
    assert os.path.basename(seen[0]) == "hinge.f3d"
    assert sorted(os.listdir(folder)) == ["hinge.f3d"]
    assert not os.path.exists(os.path.dirname(seen[0]))


def test_the_copy_goes_away_when_the_import_fails(tmp_path):
    _, path = _source(tmp_path)
    seen = []

    def use(copy):
        seen.append(copy)
        raise RuntimeError("import failed")

    with pytest.raises(RuntimeError):
        tempCopy.withTempCopy(str(path), use)
    assert not os.path.exists(os.path.dirname(seen[0]))
