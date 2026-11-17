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


def test_latches_handle_and_pins_are_jointed_hinges_lie_beside_the_box():
    jointed = {part.role: part.seats for part in parts.PARTS if part.seats}
    assert jointed == {
        "Latch": ["Latch front left", "Latch front right", "Latch left", "Latch right"],
        "Handle": ["Handle"],
        "Handle pin": ["Handle pin left", "Handle pin right"],
    }
    hinge = [part for part in parts.PARTS if part.role == "Hinge"][0]
    assert hinge.seats == [] and hinge.count == 2


def test_every_jointed_part_has_a_seat_per_occurrence():
    for part in parts.PARTS:
        assert len(part.seats) in (0, part.count)


def test_seat_joint_origin_names():
    assert parts.seatJointOriginName("Latch left") == "Latch left joint origin"
    assert parts.SEAT_NAMES == ["Latch front left", "Latch front right", "Latch left", "Latch right", "Handle",
                                "Handle pin left", "Handle pin right"]


def test_the_part_files_are_named_once():
    files = [part.file for part in parts.PARTS]
    assert len(files) == len(set(files))
