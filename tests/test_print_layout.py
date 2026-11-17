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
    # Jörg 17.11.2026: "Flush kommt auf die Schrift alle anderen auf die Unterseite, wie sie auch eingebaut werden."
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
    (placements, tooLarge, _) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == []
    assert {p.plate for p in placements} == {0}
    assert_spaced(footprints, placements, 5)


def test_what_does_not_fit_goes_on_the_next_plate():
    footprints = [(200, 200), (200, 200), (30, 30)]
    (placements, tooLarge, _) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == []
    assert placements[0].plate != placements[1].plate
    assert max(p.plate for p in placements) == 1
    assert_spaced(footprints, placements, 5)


def test_a_part_that_only_fits_across_is_turned():
    footprints = [(100, 300)]
    (placements, tooLarge, _) = printLayout.arrange(footprints, (350, 200), spacing=5, purge=0)
    assert tooLarge == []
    assert placements[0].turned
    assert_spaced(footprints, placements, 5, (350, 200))


def test_a_part_larger_than_the_bed_gets_a_plate_of_its_own_and_is_named():
    footprints = [(30, 30), (300, 300), (30, 30)]
    (placements, tooLarge, _) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert tooLarge == [1]
    assert placements[1].plate not in (placements[0].plate, placements[2].plate)


def test_the_purge_corner_back_right_stays_free_on_every_plate():
    footprints = [(40, 40)] * 40
    spacing, purge = 5, 50
    (placements, _, _) = printLayout.arrange(footprints, BED, spacing=spacing, purge=purge)
    assert max(p.plate for p in placements) >= 1
    corner = (BED[0] - spacing - purge, BED[1] - spacing - purge, BED[0] - spacing, BED[1] - spacing)
    for (f, p) in zip(footprints, placements):
        assert not overlap(rect(f, p), corner, spacing - 1e-9)
    assert_spaced(footprints, placements, spacing)


def test_without_a_purge_area_the_corner_is_used():
    footprints = [(40, 40)] * 25
    (placements, _, _) = printLayout.arrange(footprints, BED, spacing=5, purge=0)
    assert {p.plate for p in placements} == {0}


def test_a_single_part_lies_in_the_middle_of_the_bed():
    (placements, _, _) = printLayout.arrange([(84, 42)], BED, spacing=5, purge=0)
    (x0, y0, x1, y1) = rect((84, 42), placements[0])
    assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_single_part_keeps_clear_of_the_purge_corner():
    # in the middle it would reach into the corner, 38 to 218 against 201
    (placements, tooLarge, noPurge) = printLayout.arrange([(180, 180)], BED, spacing=5, purge=50)
    corner = (256 - 55, 256 - 55, 251, 251)
    assert tooLarge == [] and noPurge == []
    assert not overlap(rect((180, 180), placements[0]), corner, 5 - 1e-9)


def test_a_part_that_fits_the_bed_but_not_beside_the_purge_corner_is_named_apart():
    # review r29-export: it isn't larger than the bed, the message must not say so
    (placements, tooLarge, noPurge) = printLayout.arrange([(30, 30), (230, 230)], BED, spacing=5, purge=50)
    assert tooLarge == []
    assert noPurge == [1]
    assert placements[1].plate != placements[0].plate


def test_a_part_turns_when_only_the_purge_corner_is_in_the_way():
    # review r29-export: 200 x 150 on 250 x 210 doesn't fit beside the corner unturned, 150 x 200 does
    footprints = [(200, 150), (20, 20)]
    (placements, tooLarge, noPurge) = printLayout.arrange(footprints, (250, 210), spacing=5, purge=50)
    assert tooLarge == [] and noPurge == []
    assert placements[0].turned and placements[0].plate == 0
    corner = (250 - 55, 210 - 55, 245, 205)
    assert not overlap(rect(footprints[0], placements[0]), corner, 5 - 1e-9)


def test_a_purge_square_larger_than_the_bed_keeps_every_part_on_one_plate_without_it():
    (placements, tooLarge, noPurge) = printLayout.arrange([(20, 20), (20, 20)], (100, 100), spacing=5, purge=200)
    assert tooLarge == []
    assert sorted(noPurge) == [0, 1] or {p.plate for p in placements} == {0}


# ---------------------------------------------------------------------------
# layOut: groups of meshes onto the plates, Bambu's plate grid
# ---------------------------------------------------------------------------

def test_every_group_stands_on_its_plate_inside_the_bed():
    groups = [[box("a", 500, 500, -20, 84, 84, 30)], [box("b", -300, 10, 7, 42, 42, 10)]]
    (laid, plates, tooLarge, noPurge, _) = printLayout.layOut(groups, BED, spacing=5, purge=0)
    assert plates == 1 and tooLarge == [] and noPurge == []
    for (plate, meshObject) in laid:
        ((x0, x1), (y0, y1), (z0, _)) = bounds(meshObject.vertices)
        assert plate == 0
        assert z0 == pytest.approx(0)
        assert 5 - 1e-9 <= x0 and x1 <= 251 + 1e-9 and 5 - 1e-9 <= y0 and y1 <= 251 + 1e-9


def plate_bounds(laid, plate):
    vertices = [v for (p, m) in laid if p == plate for v in m.vertices]
    return bounds(vertices)


def test_each_plates_parts_are_centered_on_the_bed():
    # Bambu Studio and PrusaSlicer move the parts of a 3MF not made by them to the middle of the bed as one group
    # (Plater.cpp center_instances_around_point), centered already they stay where the layout put them
    groups = [[box(f"p{i}", 0, 0, 0, 60, 40, 10)] for i in range(5)]
    (laid, plates, _, _, _) = printLayout.layOut(groups, BED, spacing=5, purge=0)
    for plate in range(plates):
        ((x0, x1), (y0, y1), _) = plate_bounds(laid, plate)
        assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_the_purge_corner_is_free_after_centering():
    groups = [[box(f"p{i}", 0, 0, 0, 50, 50, 10)] for i in range(7)]
    (laid, plates, _, noPurge, _) = printLayout.layOut(groups, BED, spacing=5, purge=50)
    assert noPurge == []
    corner = (256 - 55, 256 - 55, 251, 251)
    for (plate, meshObject) in laid:
        ((x0, x1), (y0, y1), _) = bounds(meshObject.vertices)
        assert not overlap((x0, y0, x1, y1), corner, 5 - 1e-9), meshObject.name
    for plate in range(plates):
        ((x0, x1), (y0, y1), _) = plate_bounds(laid, plate)
        assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_plate_whose_centered_part_takes_the_corner_is_named():
    # a large part alone lies in the middle of the bed in the slicer, whatever the layout says
    (laid, plates, tooLarge, noPurge, _) = printLayout.layOut([[box("big", 0, 0, 0, 230, 230, 10)]], BED, spacing=5, purge=50)
    assert tooLarge == [] and noPurge == [0]


def test_the_halves_of_a_hinge_keep_their_place_to_each_other():
    bottom = box("BottomHingePart", 0, 0, 0, 30, 10, 31.6)
    top = box("TopHingePart", 0, 12, 0, 30, 10, 31.6)
    (laid, _, _, _, _) = printLayout.layOut([[bottom, top], [box("x", 0, 0, 0, 60, 60, 5)]], BED, spacing=5, purge=0)
    placed = {meshObject.name: meshObject for (_, meshObject) in laid}
    delta = [tuple(b - a for (a, b) in zip(p, q)) for (p, q) in zip(bottom.vertices, placed["BottomHingePart"].vertices)]
    delta += [tuple(b - a for (a, b) in zip(p, q)) for (p, q) in zip(top.vertices, placed["TopHingePart"].vertices)]
    for d in delta:
        assert d == pytest.approx(delta[0])


def test_what_does_not_fit_lies_on_a_second_plate_of_its_own_coordinates():
    groups = [[box("a", 0, 0, 0, 200, 200, 10)], [box("b", 0, 0, 0, 200, 200, 10)]]
    (laid, plates, _, _, _) = printLayout.layOut(groups, BED, spacing=5, purge=0)
    assert plates == 2
    assert sorted(plate for (plate, _) in laid) == [0, 1]
    for plate in (0, 1):
        ((x0, x1), (y0, y1), _) = plate_bounds(laid, plate)
        assert 5 - 1e-9 <= x0 and x1 <= 251 + 1e-9 and 5 - 1e-9 <= y0 and y1 <= 251 + 1e-9


def test_a_turned_group_is_turned_about_z_whole():
    groups = [[box("long", 0, 0, 0, 100, 300, 10)]]
    (laid, _, tooLarge, _, _) = printLayout.layOut(groups, (350, 200), spacing=5, purge=0)
    assert tooLarge == []
    (_, meshObject) = laid[0]
    assert extent(meshObject.vertices)[:2] == pytest.approx((300, 100))


def test_plate_file_names():
    assert printLayout.plateFileName("Gridkeeper parts", 0, 1) == "Gridkeeper parts"
    assert printLayout.plateFileName("Gridkeeper parts", 0, 3) == "Gridkeeper parts, plate 1"
    assert printLayout.plateFileName("Gridkeeper parts", 2, 3) == "Gridkeeper parts, plate 3"


def boxes_of(footprints):
    return [[box(f"p{i}", 0, 0, 0, w, d, 10)] for (i, (w, d)) in enumerate(footprints)]


@pytest.mark.parametrize("footprints", [
    [(210, 168), (126, 210), (168, 42), (168, 168), (84, 210)],
    [(168, 84), (168, 210), (42, 126), (210, 42), (210, 168)],
])
def test_growing_the_purge_square_never_makes_the_layout_worse(footprints):
    # review r29-export: the last attempt was taken, one with more plates and no fewer plates without a corner
    (placements, _, _) = printLayout.arrange(footprints, BED, 5, 50)
    first = max(p.plate for p in placements) + 1
    (_, plates, _, noPurge, _) = printLayout.layOut(boxes_of(footprints), BED, spacing=5, purge=50)
    assert plates <= first
    assert len(noPurge) <= first


def test_a_part_larger_than_the_bed_is_not_named_twice():
    (_, _, tooLarge, noPurge, _) = printLayout.layOut(boxes_of([(300, 300), (30, 30)]), BED, spacing=5, purge=50)
    assert tooLarge == [0]
    assert noPurge == []


def test_older_plate_files_of_the_same_name_are_known():
    names = ["Parts.3mf", "Parts, plate 1.3mf", "Parts, plate 12.3mf", "Parts, plate x.3mf", "Parts 2.3mf", "Other.3mf", "parts, PLATE 3.3MF"]
    assert [n for n in names if printLayout.isPlateFileOf(n, "Parts")] == ["Parts.3mf", "Parts, plate 1.3mf", "Parts, plate 12.3mf", "parts, PLATE 3.3MF"]


# ---------------------------------------------------------------------------
# Bambu click test 17.11.2026: the purge tower's spot (F2) and the excluded area of a Bambu Lab printer chosen (F1;
# Jörg: „Wenn wir den Drucker exakt vorgeben ist die Sperrzone nicht mehr Sache des Users.“)
# ---------------------------------------------------------------------------

X1_TOWER = (0.644, 0.977)


def test_the_purge_square_lies_where_the_slicer_puts_the_tower():
    # Bambu Studio: the tower's corner at 0.644 x 0.977 of the bed, kept on the bed between the spacing
    assert printLayout.purgeSquare(BED, 5, 50, X1_TOWER) == pytest.approx((164.864, 201, 214.864, 251))
    assert printLayout.purgeSquare(BED, 5, 50, (0.0, 1.0)) == pytest.approx((5, 201, 55, 251))
    assert printLayout.purgeSquare(BED, 5, 50, (1.0, 1.0)) == pytest.approx((201, 201, 251, 251))
    assert printLayout.purgeSquare(BED, 5, 0, (1.0, 1.0)) is None


def laid_boxes(laid):
    out = []
    for (plate, meshObject) in laid:
        ((x0, x1), (y0, y1), _) = bounds(meshObject.vertices)
        out.append((plate, meshObject.name, (x0, y0, x1, y1)))
    return out


@pytest.mark.parametrize("footprints", [
    [(40, 40)] * 12,
    [(84, 84), (42, 126), (126, 42), (36, 11), (36, 11), (83.5, 41.5)],
    [(99, 30), (13.3, 12.8), (5.1, 31.6), (19.7, 5.1), (19.7, 5.1), (23.6, 36.5), (23.6, 36.5), (23.6, 36.5), (23.6, 36.5)],
])
def test_parts_keep_clear_of_the_tower_spot_after_centering(footprints):
    (laid, plates, tooLarge, blocked, _) = printLayout.layOut(boxes_of(footprints), BED, 5, 50, X1_TOWER)
    assert blocked == []
    tower = printLayout.purgeSquare(BED, 5, 50, X1_TOWER)
    for (plate, name, box_) in laid_boxes(laid):
        assert not overlap(box_, tower, 5 - 1e-6), (name, box_)
    for plate in range(plates):
        ((x0, x1), (y0, y1), _) = plate_bounds(laid, plate)
        assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_shelf_skips_past_the_tower_spot():
    (placements, _, _) = printLayout.arrange([(30, 30)] * 12, BED, 5, 50, X1_TOWER)
    tower = printLayout.purgeSquare(BED, 5, 50, X1_TOWER)
    for p in placements:
        assert not overlap((p.x, p.y, p.x + 30, p.y + 30), tower, 5 - 1e-9)


# ---------------------------------------------------------------------------
# Jörg 17.11.2026: „Das Zubehör der Box sollte auf eine separate Platte. Eine Box müsste je nach Größe 3 Platten
# gesamt ergeben.“
# ---------------------------------------------------------------------------

def test_parts_of_different_kinds_never_share_a_plate():
    groups = boxes_of([(230, 188), (230, 188), (23.6, 36.5), (23.6, 36.5), (99, 30), (40, 40)])
    kinds = [("Box 1", "base"), ("Box 1", "lid"), ("Box 1", "parts"), ("Box 1", "parts"), ("Box 1", "parts"), None]
    (laid, plates, tooLarge, blocked, _) = printLayout.layOutKinds(groups, kinds, BED, 5, 0, X1_TOWER)
    plateOf = {meshObject.name: plate for (plate, meshObject) in laid}
    assert plates == 4
    assert len({plateOf["p0"], plateOf["p1"], plateOf["p2"], plateOf["p5"]}) == 4
    assert plateOf["p2"] == plateOf["p3"] == plateOf["p4"]
    for plate in range(plates):
        ((x0, x1), (y0, y1), _) = plate_bounds(laid, plate)
        assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_kind_too_many_for_one_plate_takes_more_in_a_row():
    groups = boxes_of([(200, 200), (200, 200), (30, 30)])
    kinds = [("Box 1", "parts"), ("Box 1", "parts"), None]
    (laid, plates, _, _, _) = printLayout.layOutKinds(groups, kinds, BED, 5, 0, X1_TOWER)
    plateOf = {meshObject.name: plate for (plate, meshObject) in laid}
    assert plates == 3
    assert sorted([plateOf["p0"], plateOf["p1"]]) == [0, 1] and plateOf["p2"] == 2


def test_kinds_report_their_too_large_parts_and_taken_plates_in_the_whole_numbering():
    groups = boxes_of([(30, 30), (300, 300), (230, 230)])
    kinds = [None, ("Box 1", "base"), ("Box 1", "lid")]
    (laid, plates, tooLarge, blocked, _) = printLayout.layOutKinds(groups, kinds, BED, 5, 50, X1_TOWER)
    plateOf = {meshObject.name: plate for (plate, meshObject) in laid}
    assert tooLarge == [1]
    assert blocked == [plateOf["p2"]]


X1_EXCLUDED = [(0, 0, 18, 28)]


@pytest.mark.parametrize("footprints", [
    [(40, 40)] * 12,
    [(84, 84), (42, 126), (126, 42), (36, 11), (36, 11), (83.5, 41.5)],
    [(230, 188)],
    [(99, 30), (13.3, 12.8), (5.1, 31.6), (19.7, 5.1), (19.7, 5.1), (23.6, 36.5), (23.6, 36.5), (23.6, 36.5), (23.6, 36.5)],
])
@pytest.mark.parametrize("purge", [0, 50])
def test_parts_keep_clear_of_the_excluded_area_after_centering(footprints, purge):
    # Bambu Studio warned: "Box 5×4×6 Base is too close to exclusion area, there may be collisions when printing"
    (laid, plates, _, taken, nearExcluded) = printLayout.layOut(boxes_of(footprints), BED, 5, purge, X1_TOWER, X1_EXCLUDED)
    assert nearExcluded == []
    for (_, name, box_) in laid_boxes(laid):
        assert not overlap(box_, X1_EXCLUDED[0], 5 - 1e-6), (name, box_)


def test_arrange_skips_an_excluded_area_along_the_shelf():
    (placements, _, _) = printLayout.arrange([(30, 30)] * 3, BED, 5, 0, excluded=X1_EXCLUDED)
    for p in placements:
        assert not overlap((p.x, p.y, p.x + 30, p.y + 30), X1_EXCLUDED[0], 5 - 1e-9)


def test_a_part_that_cant_keep_clear_of_the_excluded_area_is_named_for_it_not_for_the_tower():
    # review r29-export: 214 x 214 fits no strip between the edges, centered it comes near the corner
    (_, plates, tooLarge, taken, nearExcluded) = printLayout.layOut(boxes_of([(214, 214)]), BED, 5, 0, X1_TOWER, X1_EXCLUDED)
    assert tooLarge == [] and taken == []
    assert nearExcluded == [0]


def test_box_lid_and_small_parts_keep_their_own_plates_clear_of_the_excluded_area():
    groups = boxes_of([(230, 188), (230, 188), (23.6, 36.5), (23.6, 36.5), (99, 30)])
    kinds = [("Box 1", "box"), ("Box 1", "lid"), ("Box 1", "parts"), ("Box 1", "parts"), ("Box 1", "parts")]
    (laid, plates, _, _, nearExcluded) = printLayout.layOutKinds(groups, kinds, BED, 5, 0, X1_TOWER, X1_EXCLUDED)
    assert plates == 3 and nearExcluded == []
    for (_, name, box_) in laid_boxes(laid):
        assert not overlap(box_, X1_EXCLUDED[0], 5 - 1e-6), (name, box_)


# ---------------------------------------------------------------------------
# Jörg 17.11.2026, his own test: „Was mir nicht gefällt ist, dass die Kleinteile über die volle Breite angelegt sind.
# Diese könnten kompakter verteilt sein. Das muss nicht alles nebeneinander liegen.“
# ---------------------------------------------------------------------------

SMALL_PARTS = [(99, 30), (13.3, 12.8), (13.3, 12.8), (5.1, 31.6), (5.1, 31.6), (19.7, 5.1), (19.7, 5.1),
               (23.6, 36.5), (23.6, 36.5), (23.6, 36.5), (23.6, 36.5)]


@pytest.mark.parametrize("tower, excluded", [((1.0, 1.0), []), (X1_TOWER, X1_EXCLUDED)])
@pytest.mark.parametrize("purge", [0, 50])
def test_small_parts_lie_as_a_compact_group_in_the_middle(tower, excluded, purge):
    (laid, plates, _, taken, nearExcluded) = printLayout.layOut(boxes_of(SMALL_PARTS), BED, 5, purge, tower, excluded)
    assert plates == 1 and taken == [] and nearExcluded == []
    ((x0, x1), (y0, y1), _) = plate_bounds(laid, 0)
    # about square, not a row over the whole bed
    assert x1 - x0 < 160
    assert 0.5 <= (x1 - x0) / (y1 - y0) <= 2
    assert ((x0 + x1) / 2, (y0 + y1) / 2) == pytest.approx((128, 128))


def test_a_row_is_never_narrower_than_the_widest_part():
    (laid, plates, _, _, _) = printLayout.layOut(boxes_of([(200, 20), (10, 10), (10, 10)]), BED, 5, 0)
    assert plates == 1
    ((x0, x1), _, _) = plate_bounds(laid, 0)
    assert x1 - x0 >= 200


@pytest.mark.parametrize("footprints", [
    [(84, 84)] * 6,
    [(126, 84), (84, 84), (42, 42), (42, 42), (168, 42), (84, 126)],
    [(210, 168), (126, 210), (168, 42), (168, 168), (84, 210)],
    [(40, 40)] * 30,
])
def test_compact_groups_never_take_more_plates_than_full_rows(footprints):
    (_, compact, _, _, _) = printLayout.layOut(boxes_of(footprints), BED, 5, 50, X1_TOWER, X1_EXCLUDED)
    (placements, _, _) = printLayout.arrange(footprints, BED, 5, 50, X1_TOWER, X1_EXCLUDED)
    assert compact <= max(p.plate for p in placements) + 1


def test_each_box_gets_a_small_parts_plate_of_its_own():
    # Jörg 17.11.2026: „Je Box eine Zubehörplatte passt.“
    groups = boxes_of([(23.6, 36.5), (99, 30), (23.6, 36.5), (99, 30)])
    kinds = [("Box 1", "parts"), ("Box 1", "parts"), ("Box 2", "parts"), ("Box 2", "parts")]
    (laid, plates, _, _, _) = printLayout.layOutKinds(groups, kinds, BED, 5, 0)
    plateOf = {meshObject.name: plate for (plate, meshObject) in laid}
    assert plates == 2
    assert plateOf["p0"] == plateOf["p1"] != plateOf["p2"] == plateOf["p3"]
