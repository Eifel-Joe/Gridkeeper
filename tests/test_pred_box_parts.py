"""
Tests for the small parts of the storage box after Pred (round 28, p261): which parts the set holds, how many of each,
and the names of their joints and of the joint origins on the box (plan 2026-11-17-runde-28, decisions 3 and 4; spec:
"4 Riegel, 2 vorn und je einer seitlich hinten", "Griff mit 2 Haltestiften", "Scharniere in Druckposition").
"""

import os

import pytest

from tests.test_joint_origin_layout import _load

parts = _load("predBoxParts")


def test_the_set_holds_preds_small_parts():
    assert [(part.role, part.count) for part in parts.PARTS] == [("Latch", 4), ("Handle", 1), ("Handle pin", 2), ("Hinge", 2)]


def test_no_part_comes_from_a_file_any_more():
    """Round 29: every part is drawn in code, the part files of round 28 are gone with the import"""
    import dataclasses
    assert "file" not in {field.name for field in dataclasses.fields(parts.Part)}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.isdir(os.path.join(root, "resources", "predBox"))


def test_every_part_is_jointed_the_hinges_beside_the_box():
    """Jörg 17.11.2026 ("Ja, beides" to Vorschlag J): the hinges are jointed too, in their print position beside the box"""
    jointed = {part.role: part.seats for part in parts.PARTS}
    assert jointed == {
        "Latch": ["Latch front left", "Latch front right", "Latch left", "Latch right"],
        "Handle": ["Handle"],
        "Handle pin": ["Handle pin left", "Handle pin right"],
        "Hinge": ["Hinge 1", "Hinge 2"],
    }


# Jörg 17.11.2026: "alle drei zum auswählen ist besser", M3x30 the default
def test_the_three_hinge_variants():
    assert parts.HINGES == ("M3x30", "Pinned", "Plain")
    assert parts.DEFAULT_HINGE == "M3x30"


def test_every_hinge_variant_has_the_same_parts_an_unknown_one_none():
    for hinge in parts.HINGES:
        assert parts.partsFor(hinge) == parts.PARTS
    with pytest.raises(ValueError):
        parts.partsFor("Hinge_X")


def test_every_jointed_part_has_a_seat_per_occurrence():
    for part in parts.PARTS:
        assert len(part.seats) == part.count


def test_seat_joint_origin_names():
    assert parts.seatJointOriginName("Latch left") == "Latch left joint origin"
    assert parts.SEAT_NAMES == ["Latch front left", "Latch front right", "Latch left", "Latch right", "Handle",
                                "Handle pin left", "Handle pin right", "Hinge 1", "Hinge 2"]



# Round 29 (Jörg 17.11.2026: "Wir zeichnen die Teile im Code."): parts are drawn in the box command, no file is
# imported; on the integration branch a part comes in once its generator is there (Jörg: "So wie eine Sitzung fertig
# ist, kann ja sofort ein Testlauf mit Klicktest durchgeführt werden."), the others stay out

def test_only_parts_with_a_generator_are_built():
    assert parts.partsToDraw("M3x30", drawn=[]) == []
    assert [p.role for p in parts.partsToDraw("M3x30", drawn=["Handle"])] == ["Handle"]
    assert [p.role for p in parts.partsToDraw("Plain", drawn=["Hinge", "Latch"])] == ["Latch", "Hinge"]


def test_the_drawn_roles_are_roles_of_the_set():
    assert set(parts.DRAWN_ROLES) <= {part.role for part in parts.PARTS}
    assert parts.partsToDraw("M3x30") == parts.partsToDraw("M3x30", drawn=parts.DRAWN_ROLES)


def test_the_drawn_parts_so_far():
    """Round 29: the pin passed its Fusion check first (r29_pin_check, concept test passed with 2e16a78), then the
    handle (r29_handle_check), the latch (r29_latch_build)"""
    assert parts.DRAWN_ROLES == ["Latch", "Handle", "Handle pin", "Hinge"]
