"""
The magnet size choice before the free "Magnet cutout depth" field of bins, baseplates and boxes (round 27, p263).
Decided 16.11.2026: adjustable magnet holes, 2.4 mm for 2 mm magnets and 3.4 mm for 3 mm magnets. The choice only writes
the depth field; settings keep the depth alone, the choice is read back from it, so older settings files with other
depths load unchanged. Fusion-free, cm.
"""

SIZE_6X2 = '6×2 mm (2.4 mm deep)'
SIZE_6X3 = '6×3 mm (3.4 mm deep)'
CUSTOM = 'Custom'
MAGNET_SIZES = [(SIZE_6X2, 0.24), (SIZE_6X3, 0.34)]

ALL_CHOICES = [SIZE_6X2, SIZE_6X3, CUSTOM]
# Decided 16.11.2026: box with 6x2 mm magnets only, 3.4 mm would break through Pred's 2.8 mm floor pad
BOX_CHOICES = [SIZE_6X2, CUSTOM]

_TOLERANCE = 1e-6


def choiceForDepth(depth: float, choices: list[str]) -> str:
    """The choice a depth (cm) shows, Custom when no offered size has it"""
    for name, sizeDepth in MAGNET_SIZES:
        if name in choices and abs(depth - sizeDepth) < _TOLERANCE:
            return name
    return CUSTOM


def depthForChoice(choice: str) -> float | None:
    """The depth (cm) a choice sets, none for Custom"""
    return next((depth for name, depth in MAGNET_SIZES if name == choice), None)
