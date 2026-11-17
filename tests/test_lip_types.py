"""
Upstream round 17.11. (p13): the lip types of GridfinityGenerator (Le0Michine) and how our dividers raised into the lip
follow them. See dev-notes/specs/2026-11-17-upstream-lippentypen.md
"""

import importlib
import os
import sys
import types

import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "gridfinityUtilsLipTypes"


def _load_lip_input():
    # the module imports its siblings relatively, so it's loaded as part of a package over lib/gridfinityUtils. It and
    # Dim annotate with adsk.core types, which only need to exist while loading: they're taken out again, so other
    # tests still put in their own fakes
    core = sys.modules["adsk.core"]
    added = [name for name in ("Base", "ValueInput", "Point3D") if not hasattr(core, name)]
    for name in added:
        setattr(core, name, type(name, (), {}))
    try:
        if PACKAGE not in sys.modules:
            package = types.ModuleType(PACKAGE)
            package.__path__ = [os.path.join(PROJECT_ROOT, "lib", "gridfinityUtils")]
            sys.modules[PACKAGE] = package
        return importlib.import_module(f"{PACKAGE}.binBodyLipGeneratorInput")
    finally:
        for name in added:
            delattr(core, name)


lipInput = _load_lip_input()


def test_light_is_the_default_lip_and_keeps_its_top_trimmed():
    lip = lipInput.BinBodyLipGeneratorInput()
    assert lip.lipType == lipInput.LIP_TYPE_LIGHT
    assert lip.topTrimHeight == pytest.approx(0.06)
    assert lipInput.lipTopTrimHeight(True) == pytest.approx(0.06)
    assert lipInput.lipTopTrimHeight(False) == 0


def test_only_the_full_lip_socket_narrows_at_its_bottom():
    assert lipInput.lipSocketHasBottomChamfer(lipInput.LIP_TYPE_FULL) is True
    assert lipInput.lipSocketHasBottomChamfer(lipInput.LIP_TYPE_LIGHT) is False


def _source(*path):
    with open(os.path.join(PROJECT_ROOT, *path), encoding="utf-8") as file:
        return file.read()


def test_lip_socket_and_stacked_foot_cutters_share_the_chamfer_rule():
    # the lip cutout of a plain bin and the feet cut out of raised dividers follow the same profile, so the ridge of a
    # divider meets the lip around it (spec: own addition)
    source = _source("lib", "gridfinityUtils", "binBodyLipGenerator.py")
    assert "hasBottomChamfer = input.lipType == LIP_TYPE_FULL" not in source
    assert "hasBottomChamfer = False" not in source
    assert source.count("lipCutoutInput.hasBottomChamfer = lipSocketHasBottomChamfer(input.lipType)") == 2


def test_raised_dividers_pass_the_lip_type_to_their_foot_cutters():
    source = _source("lib", "gridfinityUtils", "binBodyGenerator.py")
    start = source.index("lipInput = BinBodyLipGeneratorInput()")
    block = source[start:source.index("createGridfinityBinBodyLip(lipInput", start)]
    assert "lipInput.lipType = input.lipType" in block


def test_raised_dividers_reach_the_top_of_an_untrimmed_lip_too():
    # with Trim lip top off the lip stands 0.6 mm higher, the dividers go up to its top all the same (review finding)
    source = _source("lib", "gridfinityUtils", "binBodyGenerator.py")
    start = source.index("def createRaisedDividers(")
    body = source[start:source.index("\ndef ", start + 1)]
    assert "const.BIN_LIP_TOP_RECESS_HEIGHT" not in body
    assert "- lipInput.topTrimHeight" in body
