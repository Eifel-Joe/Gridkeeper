"""
Upstream's tab top offset (c2e12c0, round 38) in the fork's own code: the raised dividers and the Cullenect sockets
were placed by the fixed 0.5 mm the offset replaced, they follow the offset so they still meet the lowered dividers
and tabs. binBodyGenerator and binBuilder need Fusion to load, so the tests read their source, the geometry is
checked in Fusion.
"""

import ast
import os
import re

from lib import defaultSettings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_BODY_GENERATOR = os.path.join(ROOT, "lib", "gridfinityUtils", "binBodyGenerator.py")
BIN_BUILDER = os.path.join(ROOT, "commands", "commandCreateBin", "binBuilder.py")
# other tests put a stub of const in sys.modules, the value is read from the source
CONST = os.path.join(ROOT, "lib", "gridfinityUtils", "const.py")


def _text(path):
    return open(path, encoding="utf-8").read()


def _function(path, name):
    tree = ast.parse(_text(path))
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_every_tab_top_clearance_takes_the_offset():
    """A call with the label style alone is the fixed 0.5 mm, a Cullenect socket would stay up while the tab goes down"""
    for path in (BIN_BODY_GENERATOR, BIN_BUILDER):
        calls = re.findall(r"tabTopClearance\(([^()]*)\)", _text(path))
        assert calls, path
        assert [call for call in calls if "," not in call and not call.startswith("labelStyle: str")] == [], path


def test_raised_dividers_start_at_the_lowered_divider_top():
    """The raised dividers stand on the dividers lowered by the offset (round 38) and end at the lip's top, trimmed or
    not, see createRaisedDividers"""
    arguments = [argument.arg for argument in _function(BIN_BODY_GENERATOR, "createRaisedDividers").args.args]
    assert "topOffset" in arguments
    body = ast.unparse(_function(BIN_BODY_GENERATOR, "createRaisedDividers"))
    assert "BIN_TAB_TOP_CLEARANCE" not in body
    assert "binBodyTotalHeight - Dim.length(topOffset)" in body
    assert "topZ = binBodyTotalHeight + Dim.length(const.BIN_LIP_EXTRA_HEIGHT - lipInput.topTrimHeight)" in body


def test_the_default_offset_is_the_old_clearance():
    """Bins of the default settings keep their shape"""
    assert re.search(r"^BIN_TAB_TOP_CLEARANCE = 0\.05$", _text(CONST), re.MULTILINE)
    assert defaultSettings.BIN["tabTopOffset"] == 0.5


def test_ridges_reach_the_outer_walls_up_to_a_hair_under_their_outer_face():
    """Round 50: a ridge ending half a wall short of a scoop wall's cavity, or at a wall's middle, left a gap to the
    thinner top of the lip (shown by the divider gap check); it ends RIDGE_WALL_MARGIN in from the outer face"""
    body = ast.unparse(_function(BIN_BODY_GENERATOR, "createRaisedDividers"))
    assert "RIDGE_WALL_MARGIN" in body
    assert "runTrims" not in body


def test_labels_sit_at_the_back_wall_also_in_front_of_a_raised_divider():
    """Round 50, decided: nothing overhangs a compartment from a raised divider, its tab and label sit at the
    compartment's back as at a wall"""
    body = ast.unparse(_function(BIN_BODY_GENERATOR, "createGridfinityBinBody"))
    assert "compartmentY + compartmentLength," in body
    assert "behindTab" not in body
    assert "ridgeSides" not in body
