"""
Tests for where a generator puts what it builds, by the design intent of the document.
"""

import os
import importlib.util


def _load():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("designIntent", os.path.join(project_root, "lib", "gridfinityUtils", "designIntent.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


intent = _load()


def test_values_are_fusions_design_intent_types():
    # adsk.fusion.DesignIntentTypes, read in Fusion 14.11.2026: Part 0, Assembly 1, Hybrid 2
    assert (intent.PART, intent.ASSEMBLY, intent.HYBRID) == (0, 1, 2)


def test_new_part_in_part_design_switches_to_hybrid_into_container():
    assert intent.structurePlan(intent.PART, True) == intent.StructurePlan(switchToHybrid=True, place=intent.PLACE_CONTAINER)


def test_new_part_in_hybrid_or_assembly_goes_into_container():
    for designIntent in (intent.HYBRID, intent.ASSEMBLY):
        assert intent.structurePlan(designIntent, True) == intent.StructurePlan(switchToHybrid=False, place=intent.PLACE_CONTAINER)


def test_preview_in_part_design_builds_root_bodies():
    assert intent.structurePlan(intent.PART, False) == intent.StructurePlan(switchToHybrid=False, place=intent.PLACE_ROOT_BODIES)


def test_preview_in_hybrid_goes_into_container():
    assert intent.structurePlan(intent.HYBRID, False) == intent.StructurePlan(switchToHybrid=False, place=intent.PLACE_CONTAINER)


def test_rebuild_of_old_root_bodies_stays_root_bodies():
    for designIntent in (intent.PART, intent.HYBRID):
        for mayChange in (True, False):
            assert intent.structurePlan(designIntent, mayChange, intent.REBUILD_OLD_BODIES) == intent.StructurePlan(switchToHybrid=False, place=intent.PLACE_ROOT_BODIES)


def test_rebuild_of_an_occurrence_keeps_its_parent():
    for designIntent in (intent.PART, intent.HYBRID):
        for mayChange in (True, False):
            assert intent.structurePlan(designIntent, mayChange, intent.REBUILD_OLD_OCCURRENCE) == intent.StructurePlan(switchToHybrid=False, place=intent.PLACE_OLD_PARENT)


# --- review of round 13: bins and baseplates switch a part design to hybrid too, they tell the user like the label
# command does (it can't be switched back)

import ast


def test_every_command_tells_about_the_switch_to_hybrid():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for command in ("commandCreateBin", "commandCreateBaseplate", "commandCreateLabel"):
        with open(os.path.join(project_root, "commands", command, "entry.py"), encoding="utf-8") as file:
            tree = ast.parse(file.read())
        execute = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "command_execute")
        assert "HYBRID_SWITCH_MESSAGE" in ast.unparse(execute), command


def test_hybrid_switch_message_names_the_part():
    assert "part design" in intent.hybridSwitchMessage("bin") and "bin" in intent.hybridSwitchMessage("bin")
