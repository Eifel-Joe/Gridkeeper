"""
Measures of the storage box after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred; rebuilt in code for Gridkeeper, round 27).

Fusion-free so pytest can check it. Values in cm (Fusion's internal unit). The box uses Pred's own frame: the outer
corner at x = y = 0, z = 0 on the top of the 2.8 mm bottom plate, so every value can be compared with Pred's file
(fusion-auftraege/r27_pred_walk.log). Measures that hang on Pred's Grid_X, Grid_Y or GridfinityUnit are dims on the
gfBox parameters, so Fusion follows a parameter change by itself.
"""

from .dim import Dim, DimKind  # noqa: F401  (DimKind for callers building parameter dims)

# Pred's fixed values, cm. Pred's user parameter names in the comments.
PRED = {
    'grid': 4.2,                 # 42 mm cells
    'margin': 1.0,               # 10 mm from the outer wall to the first cell
    'bottomThickness': 0.28,     # Extrude1, -2.8 mm
    'heightPerUnit': 0.7,        # GridfinityUnit * 7 mm
    'heightExtra': 1.02,         # + 10.2 mm (Extrude4)
    'lidHeight': 1.0,            # LidCutPlane 10 mm below the top
    'innerCutStart': 0.415,      # Extrude3 starts 4.65 - 0.5 mm above the floor plane
    'innerCutExtra': 0.08,       # Extrude3: - (4.65 - 0.5) + 0.2 + 4.75 mm
    'labelWidthMax': 8.5,        # LabelWidth
    'labelWidthTaken': 15.95,    # (14 + 7 + 20 + 15) * 2 + (3.75 + 7.5 + 12.5) * 2 mm
    'hingeSlotLength': 3.2,      # HingeSlotLength
    'hingeSlotFromBack': 0.3,    # HingeSlotFromBack
    'hingeSlotDepth': 0.9,       # HingeSlotDepth
    'hingeSlotWidth': 0.2,       # HingeSlotWidth
    'backCutoutMin': 6.5,        # BackCutouts: max(HingeSlotLength + 14 mm + 20 mm; 65 mm)
    'catchSlideTop': 0.6,        # Extrude14 starts 6 mm below the top
    'catchSlideLength': 4.3,     # Extrude14, 43 mm
    'catchSlideBottomRoom': 0.6, # at least 6 mm left below the slot (plan decision 1, Pred at height 6)
    'holderHalfHeight': 1.25,    # LabelAndHandleHolder d1770 = 25 mm, centred on the box middle
    'lowerGrooveTop': 0.82,      # SideGroove: the lower groove from 6.2 to 8.2 mm
    'magnetPadExtra': 0.075,     # Sketch21 d1789 = MagnetHoleDiameter / 2 + 0.75 mm
    'holderBlend': 0.375,        # Fillet10, the rounding of the handle holders
    'lidChamfer': 0.1,           # Chamfer11 and Chamfer12, the chamfers along the lid joint
}


class PredBoxDims:
    """All measures that follow the grid size and the height, from the three box parameters
    (grid counts and height units as unitless dims)"""

    def __init__(self, gridX: Dim, gridY: Dim, heightU: Dim):
        self.gridX = gridX
        self.gridY = gridY
        self.heightU = heightU
        grid = Dim.length(PRED['grid'])
        rim = Dim.length(2 * PRED['margin'])
        self.outerWidth = gridX * grid + rim
        self.outerLength = gridY * grid + rim
        self.bodyTop = heightU * Dim.length(PRED['heightPerUnit']) + Dim.length(PRED['heightExtra'])
        self.bottom = Dim.length(-PRED['bottomThickness'])
        self.lidCut = self.bodyTop - Dim.length(PRED['lidHeight'])
        self.midX = self.outerWidth / 2
        self.midY = self.outerLength / 2
        self.midZ = (self.bodyTop - Dim.length(PRED['bottomThickness'])) / 2
        self.innerCutStart = Dim.length(PRED['innerCutStart'])
        self.innerCutDepth = heightU * Dim.length(PRED['heightPerUnit']) + Dim.length(PRED['innerCutExtra'])
        self.labelWidth = Dim.min(gridX * grid + rim - Dim.length(PRED['labelWidthTaken']), Dim.length(PRED['labelWidthMax']))
        self.backCutoutWidth = Dim.length(max(PRED['hingeSlotLength'] + 3.4, PRED['backCutoutMin']))
        # the slot ends at least 6 mm above the bottom: top - 6 mm - length >= bottom + 6 mm
        self.catchSlideDepth = Dim.min(
            Dim.length(PRED['catchSlideLength']),
            self.bodyTop - Dim.length(round(PRED['catchSlideTop'] + PRED['catchSlideBottomRoom'] - PRED['bottomThickness'], 6)))
        self.holderBottom = self.midZ - Dim.length(PRED['holderHalfHeight'])
        # Nutzer 16.11.2026, "Rundung weglassen (2)": at height 5 the top rounding of the handle holders would reach past
        # the lid joint, there it is square (0.01 mm), from height 6 Pred's 3.75 mm. An expression, Fusion has no
        # parameter to switch a feature off: max(0.01 mm; min(3.75 mm; (height units - 5) * 1000 mm))
        self.holderTopBlend = Dim.max(Dim.length(0.001), Dim.min(
            Dim.length(PRED['holderBlend']), (heightU - Dim.number(5)) * Dim.length(100)))
        # Nutzer 16.11.2026, "Ja, 0,2 mm (a)": at height 5 the holders and the label rail end 0.25 mm under the lid
        # joint, the box's chamfer along the front middle recess there is 0.2 mm instead of Pred's 1 mm:
        # min(1 mm; 0.2 mm + (height units - 5) * 1000 mm)
        self.frontLidChamfer = Dim.min(Dim.length(PRED['lidChamfer']),
                                       Dim.length(0.02) + (heightU - Dim.number(5)) * Dim.length(100))

    def values(self) -> dict:
        """The plain numbers (cm) for edge selection and placement math"""
        return {name: value.value for name, value in vars(self).items() if isinstance(value, Dim)}


def stackingJointZ(dims: PredBoxDims):
    """Heights of the stacking joint origins: under the box and on top of the lid (before the stacking tabs)"""
    return dims.bottom, dims.bodyTop
