"""
Round 39, p530: a box rebuild broke off with "InternalValidationError : jointOcc" when a user joint on the old set was
moved over and further joints came later in the timeline (a second box's own joints): moving a joint rolls the marker
back before it, and reading the sides of the joints after it, now rolled back, raised (fusion-auftraege/r39_mess.log,
branch and master alike). The joints' sides are read in one go before anything is moved. Same pattern in
repointJoints (an insert's pocket joint in a rebuilt bin). Run on stand-ins, the functions loaded from rebuildUtils'
source as in test_box_rebuild_seats.
"""

import ast
import os
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")
SOURCE = open(REBUILD_UTILS, encoding="utf-8").read()
_ADSK = types.SimpleNamespace(fusion=types.SimpleNamespace(JointOrigin=types.SimpleNamespace(cast=lambda entity: entity)))


def _load(name):
    node = next(n for n in ast.parse(SOURCE).body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"adsk": _ADSK}
    exec(compile(ast.Module(body=[node], type_ignores=[]), REBUILD_UTILS, "exec"), namespace)
    return namespace[name]


class _Timeline:
    def __init__(self):
        self.marker = 100


class _Item:
    def __init__(self, timeline, index):
        self.timeline = timeline
        self.index = index

    def rollTo(self, before):
        self.timeline.marker = self.index if before else self.index + 1


class _Joint:
    """A joint whose sides can't be read once the marker is before it, as Fusion's"""

    def __init__(self, timeline, index, one, two, occurrenceOne=None, occurrenceTwo=None):
        self.timelineObject = _Item(timeline, index)
        self._values = {"geometryOrOriginOne": one, "geometryOrOriginTwo": two,
                        "occurrenceOne": occurrenceOne, "occurrenceTwo": occurrenceTwo}

    def __getattr__(self, name):
        values = self.__dict__["_values"]
        if name in values:
            item = self.__dict__["timelineObject"]
            if item.timeline.marker <= item.index:
                raise RuntimeError("2 : InternalValidationError : jointOcc")
            return values[name]
        raise AttributeError(name)


def test_the_sides_of_every_joint_are_read_before_any_is_moved():
    readJointEnds = _load("readJointEnds")
    timeline = _Timeline()
    first = _Joint(timeline, 5, "Latch joint origin", "Probe origin", "latchOcc", "probeOcc")
    later = _Joint(timeline, 9, "Box 2 seat", None, "box2Occ", None)
    ends = readJointEnds([first, later])
    # moving the first joint over rolls the marker before it; what was read about the later one stays at hand
    first.timelineObject.rollTo(True)
    (joint, item, sides) = ends[1]
    assert joint is later and item is later.timelineObject
    assert sides == [("geometryOrOriginOne", "Box 2 seat", "box2Occ", None, None)]
    (_, _, firstSides) = ends[0]
    assert firstSides == [
        ("geometryOrOriginOne", "Latch joint origin", "latchOcc", "Probe origin", "probeOcc"),
        ("geometryOrOriginTwo", "Probe origin", "probeOcc", "Latch joint origin", "latchOcc"),
    ]


def _function(name):
    node = next(n for n in ast.parse(SOURCE).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return node


def test_the_repointing_loops_read_no_joint_side_themselves():
    for name in ("repointJointsByName", "repointJoints"):
        function = _function(name)
        source = ast.unparse(function)
        assert "readJointEnds(" in source, name
        reads = [ast.unparse(n) for n in ast.walk(function)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "getattr"
                 and ast.unparse(n.args[0]) == "joint"]
        assert reads == [], (name, reads)
        attributes = [n.attr for n in ast.walk(function) if isinstance(n, ast.Attribute)
                      and n.attr in ("geometryOrOriginOne", "geometryOrOriginTwo", "occurrenceOne", "occurrenceTwo", "timelineObject")
                      and ast.unparse(n.value) == "joint"]
        assert attributes == [], (name, attributes)


def test_a_joint_is_rolled_to_before_its_label_and_cell_checks():
    """Review round 39: after an earlier joint was moved the marker stood before that one; the width check of a box
    label jointed later read the label's bodies rolled back, found no plate and re-jointed a label too wide for the box.
    The joint is rolled to first, everything before it is computed for the checks"""
    function = _function("repointJointsByName")
    tries = [n for n in ast.walk(function) if isinstance(n, ast.Try)]
    body = [ast.unparse(statement) for statement in tries[0].body]
    roll = next(i for (i, line) in enumerate(body) if line.startswith("item.rollTo(True)"))
    label = next(i for (i, line) in enumerate(body) if "LABEL_JOINT_ORIGIN" in line)
    assert roll < label
