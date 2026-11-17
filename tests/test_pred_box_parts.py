"""
Tests for the small parts of the storage box after Pred (round 28, p261): which parts the set holds, how many of each,
and the names of their joints and of the joint origins on the box (plan 2026-11-17-runde-28, decisions 3 and 4; spec:
"4 Riegel, 2 vorn und je einer seitlich hinten", "Griff mit 2 Haltestiften", "Scharniere in Druckposition").
"""

from tests.test_joint_origin_layout import _load

parts = _load("predBoxParts")


def test_the_set_holds_preds_small_parts():
    assert [(part.role, part.file, part.count) for part in parts.PARTS] == [
        ("Latch", "latch.f3d", 4),
        ("Handle", "handle.f3d", 1),
        ("Handle pin", "handlePin.f3d", 2),
        ("Hinge", "hinge.f3d", 2),
    ]


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
def test_the_three_hinge_variants_and_their_files():
    assert parts.HINGES == {"M3x30": "hinge.f3d", "Pinned": "hingePinned.f3d", "Plain": "hingePlain.f3d"}
    assert parts.DEFAULT_HINGE == "M3x30"


def test_the_chosen_hinge_is_the_hinge_part_the_rest_stays():
    chosen = parts.partsFor("Plain")
    assert [(part.role, part.file) for part in chosen] == [
        ("Latch", "latch.f3d"), ("Handle", "handle.f3d"), ("Handle pin", "handlePin.f3d"), ("Hinge", "hingePlain.f3d")]
    assert parts.partsFor(parts.DEFAULT_HINGE) == parts.PARTS


def test_every_jointed_part_has_a_seat_per_occurrence():
    for part in parts.PARTS:
        assert len(part.seats) == part.count


def test_seat_joint_origin_names():
    assert parts.seatJointOriginName("Latch left") == "Latch left joint origin"
    assert parts.SEAT_NAMES == ["Latch front left", "Latch front right", "Latch left", "Latch right", "Handle",
                                "Handle pin left", "Handle pin right", "Hinge 1", "Hinge 2"]


def test_the_part_files_are_named_once():
    files = [part.file for part in parts.PARTS]
    assert len(files) == len(set(files))


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
    handle (r29_handle_check)"""
    assert parts.DRAWN_ROLES == ["Handle", "Handle pin"]
