"""
Tests for CommandUiState.
"""

import sys
import os

import pytest
import adsk.core as core
from FusionGridfinityGenerator.lib.ui.commandUiState import CommandUiState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_bool_input(input_id: str, value: bool) -> core.BoolValueCommandInput:
    return core.BoolValueCommandInput(input_id, value)


# ---------------------------------------------------------------------------
# CommandUiState basic behaviour
# ---------------------------------------------------------------------------

class TestCommandUiStateBasics:
    def test_init_and_get_state(self):
        state = CommandUiState("test")
        state.initValue("my_input", True, core.BoolValueCommandInput.classType())
        assert state.getState("my_input") is True

    def test_update_value_changes_state(self):
        state = CommandUiState("test")
        state.initValue("my_input", True, core.BoolValueCommandInput.classType())
        state.updateValue("my_input", False)
        assert state.getState("my_input") is False

    def test_on_input_update_syncs_bool(self):
        state = CommandUiState("test")
        inp = make_bool_input("flag", True)
        state.onInputUpdate(inp)
        assert state.getState("flag") is True

        inp.value = False
        state.onInputUpdate(inp)
        assert state.getState("flag") is False

    def test_float_spinner_keeps_half_values(self):
        state = CommandUiState("test")
        inp = core.FloatSpinnerCommandInput("size", 2.5)
        state.onInputUpdate(inp)
        assert state.getState("size") == 2.5

        state.updateValue("size", 3.5)
        assert inp.value == 3.5

    def test_remove_value(self):
        state = CommandUiState("test")
        state.initValue("my_input", 42, core.IntegerSpinnerCommandInput.classType())
        state.removeValue("my_input")
        assert "my_input" not in state.inputState

    def test_to_dict(self):
        state = CommandUiState("test")
        state.initValue("a", 1, core.IntegerSpinnerCommandInput.classType())
        state.initValue("b", "x", core.StringValueCommandInput.classType())
        d = state.toDict()
        assert d["a"]["value"] == 1
        assert d["b"]["value"] == "x"

    def test_to_dict_ignore_keys(self):
        state = CommandUiState("test")
        state.initValue("keep", 1, core.IntegerSpinnerCommandInput.classType())
        state.initValue("drop", 2, core.IntegerSpinnerCommandInput.classType())
        d = state.toDict(ignoreKeys=["drop"])
        assert "keep" in d
        assert "drop" not in d


# ---------------------------------------------------------------------------
# forceUIRefresh behaviour
# ---------------------------------------------------------------------------

class TestForceUIRefresh:
    def test_refresh_pushes_cached_value_to_control(self):
        """forceUIRefresh must restore the cached value back to the control."""
        state = CommandUiState("test")
        inp = make_bool_input("flag", False)
        state.initValue("flag", True, core.BoolValueCommandInput.classType())
        state.registerCommandInput(inp)

        # control is False, cache is True — refresh should set control → True
        state.forceUIRefresh()
        assert inp.value is True

    def test_refresh_does_not_crash_for_unregistered_input(self):
        """Inputs in the cache but not yet registered should be silently skipped."""
        state = CommandUiState("test")
        state.initValue("unregistered", 99, core.IntegerSpinnerCommandInput.classType())
        # Should not raise
        state.forceUIRefresh()


# ---------------------------------------------------------------------------
# The bug: stale cache after manual preview
# ---------------------------------------------------------------------------

class TestManualPreviewStateBug:
    """
    Bug: with automatic preview disabled, clicking "Update preview once" sets
    the BoolValueCommandInput to True.  command_preview generates the bin then
    sets the native control back to False — but without calling onInputUpdate,
    the cache retains True.  A subsequent refreshUi/forceUIRefresh pushes True
    back to the control, causing an unintended extra rebuild.

    Fix: call commandUIState.onInputUpdate(showPreviewManual) immediately after
    setting showPreviewManual.value = False in command_preview.
    """

    def _setup(self):
        """Return a (state, manual_input) pair in the post-click state."""
        state = CommandUiState("test")
        manual = make_bool_input("show_preview_manual", True)  # user clicked the button
        # Simulate onInputUpdate being called when the button was clicked
        state.onInputUpdate(manual)
        state.registerCommandInput(manual)
        return state, manual

    def test_without_fix_cache_is_stale(self):
        """
        Demonstrates the bug: if we skip onInputUpdate after clearing the
        control, forceUIRefresh restores True from the stale cache.
        """
        state, manual = self._setup()
        assert state.getState("show_preview_manual") is True  # cache is True

        # Simulate what command_preview does WITHOUT the fix:
        manual.value = False          # clear native control only
        # (no onInputUpdate call here — this is the unfixed path)

        # Any subsequent refreshUi calls forceUIRefresh, which pushes True back
        state.forceUIRefresh()
        assert manual.value is True, (
            "Without the fix, forceUIRefresh restores True from the stale cache"
        )

    def test_with_fix_cache_is_cleared(self):
        """
        The patched path: onInputUpdate after clearing the control keeps the
        cache in sync, so forceUIRefresh does NOT restore True.
        """
        state, manual = self._setup()
        assert state.getState("show_preview_manual") is True  # cache is True

        # Simulate what command_preview does WITH the fix:
        manual.value = False
        state.onInputUpdate(manual)   # THE FIX

        # Now cache is False — forceUIRefresh must leave the control at False
        state.forceUIRefresh()
        assert manual.value is False, (
            "With the fix, forceUIRefresh must not restore True from the cache"
        )

    def test_cache_state_is_false_after_fix(self):
        """The cache entry itself must be False after applying the fix."""
        state, manual = self._setup()
        manual.value = False
        state.onInputUpdate(manual)
        assert state.getState("show_preview_manual") is False

    def test_multiple_manual_clicks_each_resolve_cleanly(self):
        """
        A second manual preview request after the first one completes should
        produce exactly one rebuild and leave the cache clean again.
        """
        state, manual = self._setup()

        # First click — fix applied
        manual.value = False
        state.onInputUpdate(manual)
        state.forceUIRefresh()
        assert manual.value is False

        # Second click
        manual.value = True
        state.onInputUpdate(manual)
        assert state.getState("show_preview_manual") is True

        # Fix applied again
        manual.value = False
        state.onInputUpdate(manual)
        state.forceUIRefresh()
        assert manual.value is False

    def test_auto_preview_on_before_first_manual_click(self):
        """
        If automatic preview was enabled and the manual button was never
        clicked, the cache entry for show_preview_manual doesn't exist yet.
        onInputUpdate must create it (not crash) — this is why updateValue
        alone would not have been sufficient as the fix.
        """
        state = CommandUiState("test")
        # Auto-preview scenario: manual input was never registered in the cache
        assert "show_preview_manual" not in state.inputState

        manual = make_bool_input("show_preview_manual", False)
        # The fix calls onInputUpdate — must not raise even with no prior entry
        state.onInputUpdate(manual)
        assert state.getState("show_preview_manual") is False

    def test_update_value_raises_on_missing_key(self):
        """
        Confirms that updateValue would NOT be a safe fix — it silently skips
        missing keys, meaning the entry would never get created for the
        auto-preview-first scenario.  (The real problem was the stale cache
        when the entry DID exist, but this covers the secondary concern.)
        """
        state = CommandUiState("test")
        # updateValue on a non-existent key is a no-op — entry still absent
        state.updateValue("show_preview_manual", False)
        assert "show_preview_manual" not in state.inputState


class TestSavedDefaults:
    def test_missing_saved_value_falls_back_to_default(self):
        # defaults saved before the Cullenect socket offset existed don't have it
        state = CommandUiState("test")
        state.initValue("bin_tab_cullenect_offset", 0.03, core.ValueCommandInput.classType())
        state.initValue("bin_tab_width", 1.3, core.ValueCommandInput.classType())
        state.initValues({"bin_tab_width": {"id": "bin_tab_width", "value": 1.5, "type": core.ValueCommandInput.classType()}})
        assert state.getState("bin_tab_cullenect_offset") == 0.03
        assert state.getState("bin_tab_width") == 1.5


class TestCommandUiStateSetValue:
    def test_sets_the_state_without_touching_a_registered_input(self):
        state = CommandUiState("test")
        state.initValue("flag", True, core.BoolValueCommandInput.classType())
        inp = make_bool_input("flag", True)
        state.registerCommandInput(inp)
        state.setValue("flag", False)
        assert state.getState("flag") is False
        assert inp.value is True
        assert state.inputState["flag"].type == core.BoolValueCommandInput.classType()


# ---------------------------------------------------------------------------
# A typed length is shown formatted (round 41, p291)
# ---------------------------------------------------------------------------

class TestLengthFormatRequest:
    def _requests(self, monkeypatch):
        import sys
        expressionFormat = sys.modules["FusionGridfinityGenerator.lib.ui.expressionFormat"]
        requested = []
        monkeypatch.setattr(expressionFormat, "request", requested.append)
        return requested

    def test_a_length_input_is_formatted_after_the_change(self, monkeypatch):
        requested = self._requests(monkeypatch)
        state = CommandUiState("test")
        inp = core.ValueCommandInput("wall", 0.29, "mm")
        inp.expression = "2.9 mm"
        state.onInputUpdate(inp)
        assert requested == [inp]
        assert state.getState("wall") == 0.29

    @pytest.mark.parametrize("unit", ["deg", ""])
    def test_angles_and_inputs_without_unit_are_not(self, monkeypatch, unit):
        requested = self._requests(monkeypatch)
        state = CommandUiState("test")
        state.onInputUpdate(core.ValueCommandInput("angle", 45, unit))
        assert requested == []

    def test_spinners_are_not(self, monkeypatch):
        requested = self._requests(monkeypatch)
        state = CommandUiState("test")
        state.onInputUpdate(core.IntegerSpinnerCommandInput("count", 3))
        assert requested == []


def test_the_add_in_starts_and_stops_the_length_format():
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "__init__.py"), encoding="utf-8") as f:
        source = f.read()
    assert "from ..lib.ui import expressionFormat" in source
    start = source[source.index("def start():"):source.index("def stop():")]
    stop = source[source.index("def stop():"):]
    assert "expressionFormat.start()" in start
    assert "expressionFormat.stop()" in stop


# ---------------------------------------------------------------------------
# Round 41 click test: the bin dialog refreshes every input after each change. Setting a length input's value, even
# to the same value, made Fusion keep the typed text on screen while the API already had "1.50 mm", so the
# formatting found nothing to set.
# ---------------------------------------------------------------------------

class _CountingLength(core.ValueCommandInput):
    def __init__(self, input_id, value, unit_type="mm"):
        super().__init__(input_id, value, unit_type)
        self.valueSets = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self.valueSets = getattr(self, "valueSets", 0) + 1
        self._value = v


class TestRefreshLeavesUnchangedLengths:
    def test_a_length_with_the_state_value_is_not_set_again(self, monkeypatch):
        state = CommandUiState("test")
        inp = _CountingLength("wall", 0.15000000000000002)
        inp.expression = "1.5 mm"
        state.initValue("wall", 0.15, core.ValueCommandInput.classType())
        state.registerCommandInput(inp)
        inp.valueSets = 0
        state.forceUIRefresh()
        assert inp.valueSets == 0
        assert inp.expression == "1.5 mm"

    def test_a_length_with_another_value_is_set(self):
        state = CommandUiState("test")
        inp = _CountingLength("wall", 0.12)
        state.initValue("wall", 0.15, core.ValueCommandInput.classType())
        state.registerCommandInput(inp)
        inp.valueSets = 0
        state.forceUIRefresh()
        assert inp.valueSets == 1
        assert inp.value == 0.15
