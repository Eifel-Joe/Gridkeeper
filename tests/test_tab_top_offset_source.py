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
    """At least: a ridge reaches further down where its support needs it (round 50), see raisedDividers.ridgeBox"""
    arguments = [argument.arg for argument in _function(BIN_BODY_GENERATOR, "createRaisedDividers").args.args]
    assert "topOffset" in arguments
    body = ast.unparse(_function(BIN_BODY_GENERATOR, "createRaisedDividers"))
    assert "BIN_TAB_TOP_CLEARANCE" not in body
    assert "minDepth=topOffset" in body
    assert "bottomZ = binBodyTotalHeight - Dim.length(depth)" in body
    assert "height = depth + const.BIN_LIP_EXTRA_HEIGHT - lipInput.topTrimHeight" in body


def test_the_default_offset_is_the_old_clearance():
    """Bins of the default settings keep their shape"""
    assert re.search(r"^BIN_TAB_TOP_CLEARANCE = 0\.05$", _text(CONST), re.MULTILINE)
    assert defaultSettings.BIN["tabTopOffset"] == 0.5
