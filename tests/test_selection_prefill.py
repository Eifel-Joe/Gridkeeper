"""
Tests for lib/ui/selectionPrefill.py (round 20, p220): an entity put into a selection input of a dialog. Fusion refused
the pocket of a rebuilt insert ("3 : invalid argument selection") and the label dialog stopped half built, OK built
nothing. A refused entity leaves the input empty and says so, the dialog goes on.
"""

import os
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("selectionPrefill", os.path.join(PROJECT_ROOT, "lib", "ui", "selectionPrefill.py"))
prefill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prefill)


class _Input:
    def __init__(self, error=None):
        self.error = error
        self.selected = []

    def addSelection(self, entity):
        if self.error is not None:
            raise self.error
        self.selected.append(entity)
        return True


def test_an_entity_fusion_takes_is_selected():
    selection = _Input()
    assert prefill.prefillSelection(selection, 'pocket') is None
    assert selection.selected == ['pocket']


def test_a_refused_entity_leaves_the_input_empty_and_says_why():
    selection = _Input(RuntimeError('3 : invalid argument selection'))
    note = prefill.prefillSelection(selection, 'pocket')
    assert selection.selected == []
    assert 'invalid argument selection' in note


def test_nothing_to_put_in_is_no_note():
    assert prefill.prefillSelection(_Input(), None) is None
