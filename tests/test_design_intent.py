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


def test_part_design_is_switched_to_hybrid_for_a_component_of_its_own():
    assert intent.componentPlan(intent.PART, mayChangeDocument=True) == intent.ComponentPlan(switchToHybrid=True, isComponent=True)


def test_preview_leaves_a_part_design_as_it_is_and_builds_into_the_root():
    assert intent.componentPlan(intent.PART, mayChangeDocument=False) == intent.ComponentPlan(switchToHybrid=False, isComponent=False)


def test_assembly_and_hybrid_take_a_component_as_they_are():
    for designIntent in (intent.ASSEMBLY, intent.HYBRID):
        for mayChange in (True, False):
            assert intent.componentPlan(designIntent, mayChangeDocument=mayChange) == intent.ComponentPlan(switchToHybrid=False, isComponent=True)


def test_values_are_fusions_design_intent_types():
    # adsk.fusion.DesignIntentTypes, read in Fusion 14.11.2026: Part 0, Assembly 1, Hybrid 2
    assert (intent.PART, intent.ASSEMBLY, intent.HYBRID) == (0, 1, 2)
