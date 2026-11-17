"""
The joint origin a label goes into stays shown (Nutzer 17.11.2026 after his test: "Allerdings darf er nicht ausgeblendet
werden."): Fusion turns off the light bulb of a joint origin a joint uses and doesn't turn it on again when the joint
goes. After a rebuild without the box the box's Label joint origin was hidden, picking it again meant finding it in
the browser. The same for an insert and its pocket. The builders turn it on again after the joint, a rebuild also the
one the old joint used. Fusion code, so its source is read; the helper itself runs on stand-ins.
"""

import ast
import os
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSEMBLY = os.path.join(ROOT, "lib", "assembly.py")
BOX_LABEL = os.path.join(ROOT, "commands", "commandCreateBoxLabel", "boxLabelBuilder.py")
INSERT = os.path.join(ROOT, "commands", "commandCreateLabel", "labelBuilder.py")


def _node(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _function(path, name):
    return ast.unparse(_node(path, name))


def _keepShown():
    """assembly.keepShown, run without Fusion"""
    logged = []
    namespace = {"commonUtils": types.SimpleNamespace(fileLog=logged.append), "adsk": types.SimpleNamespace(fusion=types.SimpleNamespace(JointOrigin=object))}
    exec(compile(ast.Module(body=[_node(ASSEMBLY, "keepShown")], type_ignores=[]), ASSEMBLY, "exec"), namespace)
    return (namespace["keepShown"], logged)


class _JointOrigin:
    def __init__(self, native=None, fails=False):
        self.nativeObject = native
        self.fails = fails
        self._bulb = False

    @property
    def name(self):
        return "Label joint origin"

    @property
    def isLightBulbOn(self):
        return self._bulb

    @isLightBulbOn.setter
    def isLightBulbOn(self, value):
        if self.fails:
            raise RuntimeError("refused")
        self._bulb = value


def test_the_helper_turns_on_the_proxy_and_its_native_joint_origin():
    (keepShown, _) = _keepShown()
    native = _JointOrigin()
    proxy = _JointOrigin(native)
    keepShown(proxy)
    assert proxy.isLightBulbOn and native.isLightBulbOn


def test_the_helper_takes_none_and_a_refusal_without_failing_the_build():
    (keepShown, logged) = _keepShown()
    keepShown(None)
    keepShown(_JointOrigin(fails=True))
    assert len(logged) == 1


def test_the_box_label_keeps_the_holder_shown_after_its_joint():
    source = _function(BOX_LABEL, "_buildBoxLabel")
    assert source.index("root.joints.add(jointInput)") < source.index("assembly.keepShown(box)")


def test_a_box_label_rebuild_shows_the_holder_it_leaves():
    source = _function(BOX_LABEL, "rebuildBoxLabel")
    assert "oldHolder = labelHolder(des, body)" in source
    assert "assembly.keepShown(oldHolder)" in source
    assert source.index("oldHolder = labelHolder(des, body)") < source.index("rebuildUtils.rebuild(")


def test_the_insert_keeps_its_pocket_shown_after_its_joint():
    source = _function(INSERT, "_buildLabel")
    assert source.index("root.joints.add(jointInput)") < source.index("assembly.keepShown(pocket)")


def test_an_insert_rebuild_shows_the_pocket_it_leaves():
    source = _function(INSERT, "rebuildLabel")
    assert "oldPocket = insertPocket(des, body)" in source
    assert "assembly.keepShown(oldPocket)" in source
    assert source.index("oldPocket = insertPocket(des, body)") < source.index("rebuildUtils.rebuild(")


# -- a box or bin rebuilt with a label or insert in it (Nutzer: "Noch schöner wäre natürlich, wenn bei Rebuild der Joint
# erhalten bliebe."): rebuildUtils moves the joint over to the new holder or pocket, that one stays shown too, and a
# label that no longer fits the new box's width is said in the note after the rebuild

REBUILD_UTILS = os.path.join(ROOT, "lib", "rebuildUtils.py")


def test_a_rebuilt_box_keeps_its_new_label_holder_shown():
    source = _function(REBUILD_UTILS, "repointJointsByName")
    assert source.index("setattr(joint, side, newJointOrigin)") < source.index("shown.append(newJointOrigin)")
    # with the timeline at its end again (review)
    assert source.index("design.timeline.moveToEnd()") < source.index("assembly.keepShown(jointOrigin)")
    assert "predBoxSeats.LABEL_JOINT_ORIGIN" in source


def test_a_rebuilt_box_says_when_its_label_no_longer_fits():
    assert "boxLabelConfig.widthNote(" in _function(REBUILD_UTILS, "repointJointsByName")


def test_a_rebuilt_bin_keeps_its_new_pocket_shown():
    source = _function(REBUILD_UTILS, "repointJoints")
    assert source.index("setattr(joint, side, newPocket.createForAssemblyContext(newOccurrence))") < source.index("assembly.keepShown(")


def test_a_refused_proxy_still_turns_on_its_native_joint_origin():
    (keepShown, logged) = _keepShown()
    native = _JointOrigin()
    keepShown(_JointOrigin(native, fails=True))
    assert native.isLightBulbOn and len(logged) == 1


def test_a_joint_origin_gone_invalid_doesnt_fail_the_build():
    class _Gone(_JointOrigin):
        @property
        def name(self):
            raise RuntimeError("invalid")
    (keepShown, logged) = _keepShown()
    gone = _Gone(fails=True)
    keepShown(gone)
    assert len(logged) == 1


def test_a_rebuild_into_another_holder_or_pocket_shows_it_with_the_timeline_at_its_end():
    # review: shown while the timeline was rolled back, the new holder or pocket might go off when the joint computes
    label = _function(BOX_LABEL, "rebuildBoxLabel")
    assert label.index("rebuildUtils.rebuild(") < label.index("assembly.keepShown(box)")
    insert = _function(INSERT, "rebuildLabel")
    assert insert.index("rebuildUtils.rebuild(") < insert.index("assembly.keepShown(pocket)")
