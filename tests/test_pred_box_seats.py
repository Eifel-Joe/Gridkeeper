"""
Where the small parts of the storage box after Pred sit (round 28, p261, plan task 3): the seats as formulas on the box
measures, checked against Pred's file at 5 x 4 x 6 and 7 x 5 x 10 (fusion-auftraege/r28_tmp/pred_parts.json, mm, world
frame of Pred's box: outer corner at x = y = 0, z = 0 on the top of the bottom plate).
"""

import pytest

from tests.test_joint_origin_layout import _load

predBox = _load("predBox")
seats = _load("predBoxSeats")
parts = _load("predBoxParts")
Dim, DimKind = predBox.Dim, predBox.DimKind


def _dims(gridX, gridY, heightU):
    return predBox.PredBoxDims(
        Dim(gridX, "gfBox1_baseWidth", DimKind.EXPRESSION),
        Dim(gridY, "gfBox1_baseLength", DimKind.EXPRESSION),
        Dim(heightU, "gfBox1_heightU", DimKind.EXPRESSION),
    )


# pred_parts.json, mm
LATCH_ORIGIN = {(5, 4, 6): (31.0, 0.25, 52.15), (7, 5, 10): (31.0, 0.25, 80.15)}
LATCH_X_AXIS = (-1.0, 0.0, 0.0)
LATCH_Z_AXIS = (0.0, 1.0, 0.0)
PIN_BOX = {(5, 4, 6): ((58.05, 1.2, 23.4), (77.75, 6.3, 27.25)), (7, 5, 10): ((92.8, 1.2, 37.4), (112.5, 6.3, 41.25))}
HANDLE_BOX = {(5, 4, 6): ((65.5, 0.25, -1.8), (164.5, 7.25, 28.2)), (7, 5, 10): ((100.25, 0.25, 12.2), (213.75, 7.25, 42.2))}
SIZES = [(5, 4, 6), (7, 5, 10)]


def _byName(size):
    return {seat.name: seat for seat in seats.seats(_dims(*size))}


def _mm(seat):
    return tuple(round(v.value * 10, 4) for v in (seat.x, seat.y, seat.z))


def test_a_seat_for_every_jointed_part():
    assert [seat.name for seat in seats.seats(_dims(5, 4, 6))] == parts.SEAT_NAMES


@pytest.mark.parametrize("size", SIZES)
def test_the_front_left_latch_sits_where_preds_latch_does(size):
    seat = _byName(size)["Latch front left"]
    assert _mm(seat) == pytest.approx(LATCH_ORIGIN[size], abs=0.01)
    assert seat.xAxis == LATCH_X_AXIS and seat.zAxis == LATCH_Z_AXIS


@pytest.mark.parametrize("size", SIZES)
def test_the_other_latches_follow_the_walls(size):
    d = _dims(*size)
    W, L = d.outerWidth.value * 10, d.outerLength.value * 10
    top = LATCH_ORIGIN[size][2]
    by = _byName(size)
    assert _mm(by["Latch front right"]) == pytest.approx((W - 31.0, 0.25, top), abs=0.01)
    assert _mm(by["Latch left"]) == pytest.approx((0.25, L - 31.0, top), abs=0.01)
    assert _mm(by["Latch right"]) == pytest.approx((W - 0.25, L - 31.0, top), abs=0.01)
    # each latch lies flat on its wall, outside up: its z into the box, its y (z x x) straight up
    for name, z in (("Latch front right", (0, 1, 0)), ("Latch left", (1, 0, 0)), ("Latch right", (-1, 0, 0))):
        seat = by[name]
        assert seat.zAxis == z
        assert seats.yAxis(seat) == (0, 0, 1)


def _local(box, seat):
    """A box in world mm into the seat's frame, for seats turned only about z"""
    origin = _mm(seat)
    corners = []
    for point in box:
        d = [p - o for p, o in zip(point, origin)]
        x = d[0] * seat.xAxis[0] + d[1] * seat.xAxis[1]
        y = d[0] * seats.yAxis(seat)[0] + d[1] * seats.yAxis(seat)[1]
        corners.append((x, y, d[2]))
    return tuple(tuple(round(min(c[i] for c in corners), 4) for i in range(3))), \
        tuple(tuple(round(max(c[i] for c in corners), 4) for i in range(3)))


def test_the_left_pin_keeps_its_place_to_the_seat_at_both_sizes():
    small, large = (_local(PIN_BOX[size], _byName(size)["Handle pin left"]) for size in SIZES)
    assert small[0] + small[1] == pytest.approx(large[0] + large[1], abs=0.01)
    # the pin ends at the seat and lies centred on the bolt axis
    assert small[1][0] == pytest.approx(0, abs=0.01) and small[0][1] == pytest.approx(-small[1][1], abs=0.01)


def test_the_pins_lie_mirrored_across_the_box_middle():
    for size in SIZES:
        d = _dims(*size)
        by = _byName(size)
        left, right = by["Handle pin left"], by["Handle pin right"]
        assert (left.x + right.x).value == pytest.approx(2 * d.midX.value)
        assert (left.y.value, left.z.value) == pytest.approx((right.y.value, right.z.value))
        assert right.xAxis == (-left.xAxis[0], -left.xAxis[1], left.xAxis[2])


@pytest.mark.parametrize("size", SIZES)
def test_the_handle_seat_is_the_middle_of_preds_handle_on_the_pin_axis(size):
    seat = _byName(size)["Handle"]
    (x0, y0, z0), (x1, y1, z1) = HANDLE_BOX[size]
    pin = _byName(size)["Handle pin left"]
    assert _mm(seat)[0] == pytest.approx((x0 + x1) / 2, abs=0.01)
    assert _mm(seat)[1:] == pytest.approx(_mm(pin)[1:], abs=0.01)
    # the handle hangs from the pin axis the same way at both sizes
    assert (z0 - _mm(seat)[2], z1 - _mm(seat)[2]) == pytest.approx((-26.5, 3.5), abs=0.01)


def test_the_seats_follow_the_box_parameters():
    seat = _byName((5, 4, 6))["Latch front right"]
    assert "gfBox1_baseWidth" in seat.x.expression
    assert "gfBox1_heightU" in seat.z.expression


def test_each_seat_is_its_parts_first_seat_turned_about_z():
    """The box's joint origins stand upright, X along X (createPointJointOrigins); each part's joint turns it about z
    from the pose of its first seat, the one Pred's file shows"""
    by = _byName((5, 4, 6))
    turns = {name: seats.turnAboutZ(by[first], by[name]) for first, names in (
        ("Latch front left", ["Latch front left", "Latch front right", "Latch left", "Latch right"]),
        ("Handle pin left", ["Handle pin left", "Handle pin right"]),
        ("Handle", ["Handle"])) for name in names}
    assert turns == {"Latch front left": 0, "Latch front right": 0, "Latch left": -90, "Latch right": 90,
                     "Handle pin left": 0, "Handle pin right": 180, "Handle": 0}


# Nutzer 17.11.2026: "Der Griff bleibt bei Max. 113,5mm stehen. Breiter macht keinen Sinn." Pred's handle is the label
# width + 28.5 mm wide (pred_parts.json: 99 mm at 5 x 4 x 6, 113.5 mm at 7 x 5 x 10), the label width stops at 85 mm.
@pytest.mark.parametrize("gridX, width", [(4, 57.0), (5, 99.0), (6, 113.5), (7, 113.5)])
def test_the_handle_is_the_label_width_and_28_5_mm_wide(gridX, width):
    assert seats.handleWidth(_dims(gridX, 4, 6)).value * 10 == pytest.approx(width, abs=1e-6)


def test_the_handle_width_follows_the_box_width_parameter():
    assert "gfBox1_baseWidth" in seats.handleWidth(_dims(5, 4, 6)).expression


@pytest.mark.parametrize("size", SIZES)
def test_the_handle_width_is_preds(size):
    (x0, _, _), (x1, _, _) = HANDLE_BOX[size]
    assert seats.handleWidth(_dims(*size)).value * 10 == pytest.approx(x1 - x0, abs=0.01)


def test_the_box_gets_a_joint_origin_at_every_seat():
    """Task 5: the points for baseGenerator.createPointJointOrigins, named after predBoxParts.seatJointOriginName"""
    d = _dims(5, 4, 6)
    points = seats.seatJointOriginPoints(d)
    assert [name for (name, *_rest) in points] == [parts.seatJointOriginName(name) for name in parts.SEAT_NAMES]
    by = _byName((5, 4, 6))
    for (name, x, y, z), seatName in zip(points, parts.SEAT_NAMES):
        assert (x.value, y.value, z.value) == (by[seatName].x.value, by[seatName].y.value, by[seatName].z.value)
