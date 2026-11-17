"""
Tests for lib/printLayout.py (round r29-export, spec dev-notes/specs/2026-11-17-r29-export-drucklage.md): how each part
is turned into its print orientation, how the parts are spread over the print bed and further plates, with spacing
and the purge tower's corner kept free.
"""

import math
import os
import importlib.util
import pytest


def _load(name):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


threeMf = _load("threeMf")
printLayout = _load("printLayout")


def box(name, x0, y0, z0, sx, sy, sz):
    vertices = [(x0 + dx * sx, y0 + dy * sy, z0 + dz * sz) for dz in (0, 1) for dy in (0, 1) for dx in (0, 1)]
    triangles = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    return threeMf.MeshObject(name, vertices, triangles)


def extent(vertices):
    return tuple(max(v[axis] for v in vertices) - min(v[axis] for v in vertices) for axis in range(3))


def bounds(vertices):
    return tuple((min(v[axis] for v in vertices), max(v[axis] for v in vertices)) for axis in range(3))


# ---------------------------------------------------------------------------
# printRotation: the rule of each role, in the part's own frame
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role, body", [
    (None, "Bin 2x3"),
    (None, "Baseplate 4x4"),
    ("Box", "Base"),
    ("Lid", "Lid"),
    ("Latch", "Latch"),
    ("Handle pin", "Handle pin"),
    ("Hinge", "BottomHingePart_M3x30"),
    ("Hinge", "TopHingePart_M3x30"),
    ("Hinge", "BottomHingePart"),
    ("Hinge", "TopHingePart"),
])
def test_parts_already_in_print_orientation_stay(role, body):
    assert printLayout.printRotation(role, body, None) == printLayout.ROTATE_NONE


def test_the_handle_lies_flat():
    assert printLayout.printRotation("Handle", "Handle", None) == printLayout.ROTATE_X_PLUS_90


def test_the_pinned_hinges_pin_lies_on_its_flat():
    assert printLayout.printRotation("Hinge", "Hinge pin", None) == printLayout.ROTATE_X_MINUS_90


def test_a_flush_label_lies_on_its_text():
    # Nutzer 17.11.2026: "Flush kommt auf die Schrift alle anderen auf die Unterseite, wie sie auch eingebaut werden."
    assert printLayout.printRotation(None, "Label", "Flush") == printLayout.ROTATE_X_180


@pytest.mark.parametrize("surface", ["Embossed", "Debossed"])
def test_other_labels_lie_on_their_underside(surface):
    assert printLayout.printRotation(None, "Label", surface) == printLayout.ROTATE_NONE


def test_turning_by_plus_90_about_x_brings_minus_y_down():
    # a handle-like bar 10 x 20 x 30, its -y face (y = 0) must end up lowest
    vertices = box("bar", 0, 0, 0, 10, 20, 30).vertices
    turned = printLayout.rotated(vertices, printLayout.ROTATE_X_PLUS_90)
    assert extent(turned) == pytest.approx((10, 30, 20))
    lowest = min(z for (_, _, z) in turned)
    assert [v for (v, t) in zip(vertices, turned) if t[2] == pytest.approx(lowest)] == [v for v in vertices if v[1] == 0]


def test_turning_by_minus_90_about_x_brings_plus_y_down():
    vertices = box("pin", 0, 0, 0, 10, 20, 30).vertices
    turned = printLayout.rotated(vertices, printLayout.ROTATE_X_MINUS_90)
    lowest = min(z for (_, _, z) in turned)
    assert [v for (v, t) in zip(vertices, turned) if t[2] == pytest.approx(lowest)] == [v for v in vertices if v[1] == 20]


def test_turning_by_180_about_x_turns_upside_down():
    vertices = box("label", 0, 0, 0, 10, 20, 3).vertices
    turned = printLayout.rotated(vertices, printLayout.ROTATE_X_180)
    assert extent(turned) == pytest.approx((10, 20, 3))
    lowest = min(z for (_, _, z) in turned)
    assert [v for (v, t) in zip(vertices, turned) if t[2] == pytest.approx(lowest)] == [v for v in vertices if v[2] == 3]


def test_no_turn_leaves_the_vertices():
    vertices = box("bin", 1, 2, 3, 10, 20, 30).vertices
    assert printLayout.rotated(vertices, printLayout.ROTATE_NONE) == vertices


def test_a_turn_keeps_the_triangles_facing_out():
    # rotations are proper, no mirror: the signed volume keeps its sign
    meshObject = box("bar", 0, 0, 0, 10, 20, 30)

    def volume(vertices):
        total = 0.0
        for (a, b, c) in meshObject.triangles:
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = vertices[a], vertices[b], vertices[c]
            total += ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)
        return total / 6

    for rotation in printLayout.ROTATIONS:
        assert volume(printLayout.rotated(meshObject.vertices, rotation)) == pytest.approx(volume(meshObject.vertices))


# ---------------------------------------------------------------------------
# arrange: footprints on the bed and further plates
# ---------------------------------------------------------------------------

BED = (256.0, 256.0)


def rect(footprint, placement):
    (w, d) = (footprint[1], footprint[0]) if placement.turned else footprint
    return (placement.x, placement.y, placement.x + w, placement.y + d)


def overlap(a, b, gap):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def assert_spaced(footprints, placements, spacing, bed=BED):
    rects = [rect(f, p) for (f, p) in zip(footprints, placements)]
    for (i, (a, p)) in enumerate(zip(rects, placements)):
        assert a[0] >= spacing - 1e-9 and a[1] >= spacing - 1e-9
        assert a[2] <= bed[0] - spacing + 1e-9 and a[3] <= bed[1] - spacing + 1e-9
        for (j, (b, q)) in enumerate(zip(rects, placements)):
            if j > i and p.plate == q.plate:
                assert not overlap(a, b, spacing - 1e-9), (i, j, a, b)


def test_parts_that_fit_share_one_plate_spaced_from_each_other_and_the_edge():
    footprints = [(84, 126), (84, 84), (42, 42), (126, 42)]
    (placements, tooLarge) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == []
    assert {p.plate for p in placements} == {0}
    assert_spaced(footprints, placements, 5)


def test_what_does_not_fit_goes_on_the_next_plate():
    footprints = [(200, 200), (200, 200), (30, 30)]
    (placements, tooLarge) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == []
    assert placements[0].plate != placements[1].plate
    assert max(p.plate for p in placements) == 1
    assert_spaced(footprints, placements, 5)


def test_a_part_that_only_fits_across_is_turned():
    footprints = [(100, 300)]
    (placements, tooLarge) = printLayout.arrange(footprints, (350, 200), spacing=5, purge=0)
    assert tooLarge == []
    assert placements[0].turned
    assert_spaced(footprints, placements, 5, (350, 200))


def test_a_part_larger_than_the_bed_gets_a_plate_of_its_own_and_is_named():
    footprints = [(30, 30), (300, 300), (30, 30)]
    (placements, tooLarge) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == [1]
    assert placements[1].plate not in (placements[0].plate, placements[2].plate)


def test_the_purge_corner_back_right_stays_free_on_every_plate():
    footprints = [(40, 40)] * 40
    spacing, purge = 5, 50
    (placements, _) = printLayout.arrange(footprints, BED, spacing=spacing, purge=purge)
    assert max(p.plate for p in placements) >= 1
    corner = (BED[0] - spacing - purge, BED[1] - spacing - purge, BED[0] - spacing, BED[1] - spacing)
    for (f, p) in zip(footprints, placements):
        assert not overlap(rect(f, p), corner, spacing - 1e-9)
    assert_spaced(footprints, placements, spacing)


def test_without_a_purge_area_the_corner_is_used():
    footprints = [(40, 40)] * 25
    (placements, _) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert {p.plate for p in placements} == {0}


def test_a_single_part_lies_in_the_middle_of_the_bed():
    (placements, _) = printLayout.arrange([(84, 42)], BED, spacing=5, purge=0)
    (x0, y0, x1, y1) = rect((84, 42), placements[0])
    assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_single_part_keeps_clear_of_the_purge_corner():
    # in the middle it would reach into the corner, 38 to 218 against 201
    (placements, tooLarge) = printLayout.arrange([(180, 180)], BED, spacing=5, purge=50)
    corner = (256 - 55, 256 - 55, 251, 251)
    assert tooLarge == []
    assert not overlap(rect((180, 180), placements[0]), corner, 5 - 1e-9)


def test_a_part_that_only_fits_without_the_purge_corner_is_named():
    (placements, tooLarge) = printLayout.arrange([(30, 30), (200, 200)], BED, spacing=5, purge=50)
    assert tooLarge == [1]
    assert placements[1].plate != placements[0].plate


# ---------------------------------------------------------------------------
# layOut: groups of meshes onto the plates, Bambu's plate grid
# ---------------------------------------------------------------------------

def test_plate_origins_follow_bambus_grid():
    # Bambu Studio PartPlate.cpp: columns ceil(sqrt(n)), a fifth of the plate between plates, rows towards -y
    assert printLayout.plateOrigin(0, 1, BED) == (0, 0)
    assert printLayout.plateOrigin(1, 2, BED) == pytest.approx((256 * 1.2, 0))
    assert printLayout.plateOrigin(2, 3, BED) == pytest.approx((0, -256 * 1.2))
    assert printLayout.plateOrigin(3, 5, BED) == pytest.approx((0, -256 * 1.2))
    assert printLayout.plateOrigin(4, 5, BED) == pytest.approx((256 * 1.2, -256 * 1.2))


def test_every_group_stands_on_the_plate_inside_its_place():
    groups = [[box("a", 500, 500, -20, 84, 84, 30)], [box("b", -300, 10, 7, 42, 42, 10)]]
    (laid, plates, tooLarge) = printLayout.layOut(groups, BED, spacing=5, purge=0)
    assert plates == 1 and tooLarge == []
    for (plate, meshObject) in laid:
        ((x0, x1), (y0, y1), (z0, _)) = bounds(meshObject.vertices)
        assert plate == 0
        assert z0 == pytest.approx(0)
        assert 5 - 1e-9 <= x0 and x1 <= 251 + 1e-9 and 5 - 1e-9 <= y0 and y1 <= 251 + 1e-9


def test_the_halves_of_a_hinge_keep_their_place_to_each_other():
    bottom = box("BottomHingePart", 0, 0, 0, 30, 10, 31.6)
    top = box("TopHingePart", 0, 12, 0, 30, 10, 31.6)
    (laid, _, _) = printLayout.layOut([[bottom, top], [box("x", 0, 0, 0, 60, 60, 5)]], BED, spacing=5, purge=0)
    placed = {meshObject.name: meshObject for (_, meshObject) in laid}
    delta = [tuple(b - a for (a, b) in zip(p, q)) for (p, q) in zip(bottom.vertices, placed["BottomHingePart"].vertices)]
    delta += [tuple(b - a for (a, b) in zip(p, q)) for (p, q) in zip(top.vertices, placed["TopHingePart"].vertices)]
    for d in delta:
        assert d == pytest.approx(delta[0])


def test_parts_of_the_second_plate_lie_on_bambus_second_plate():
    groups = [[box("a", 0, 0, 0, 200, 200, 10)], [box("b", 0, 0, 0, 200, 200, 10)]]
    (laid, plates, _) = printLayout.layOut(groups, BED, spacing=5, purge=0)
    assert plates == 2
    second = [meshObject for (plate, meshObject) in laid if plate == 1][0]
    ((x0, x1), (y0, y1), _) = bounds(second.vertices)
    (ox, oy) = printLayout.plateOrigin(1, 2, BED)
    assert ox + 5 - 1e-9 <= x0 and x1 <= ox + 251 + 1e-9
    assert oy + 5 - 1e-9 <= y0 and y1 <= oy + 251 + 1e-9


def test_a_turned_group_is_turned_about_z_whole():
    groups = [[box("long", 0, 0, 0, 100, 300, 10)]]
    (laid, _, tooLarge) = printLayout.layOut(groups, (350, 200), spacing=5, purge=0)
    assert tooLarge == []
    (_, meshObject) = laid[0]
    assert extent(meshObject.vertices)[:2] == pytest.approx((300, 100))
