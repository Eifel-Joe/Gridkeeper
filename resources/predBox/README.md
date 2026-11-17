# Small parts of the storage box after Pred

The parts the **Gridkeeper box** inserts with each box (round 28, p261). They are taken over from
[Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
by Pred, licensed **CC BY-NC**, and changed for Gridkeeper as noted below.

| File | Pred's part | Changed |
|---|---|---|
| `latch.f3d` | `Latch_Experimental` | A joint origin *Latch joint origin* at the seat added; shape, sketches and features as Pred's |
| `handlePin.f3d` | `HandlePin` | A joint origin *Handle pin joint origin* on the bolt axis added, with its fully constrained sketch *Seat* |
| `handle.f3d` | `Handle` | Built anew by `fusion-auftraege/r28_handle_build.py` after Pred's measures (profile, fillet r3.5, chamfer 1 mm, hole d3.5, mirrored), the half width as the one model parameter *HandleHalfWidth* in place of Pred's expression, and a joint origin *Handle joint origin*; volume Pred's at both half widths 49.5 and 56.75 mm (6136.8299 / 6818.3299 mm³) |
| `hinge.f3d` | `Hinge_M3x30` | Pred's parameter expressions (HingeSlot…, HingeTolerane) turned into their values (slot 32 × 9 × 2 mm, tolerance 0.15 mm), Pred's user parameters left out; the sketches *HingeTabDetails* and *Sketch3* fully constrained with dimensions at their present values. No joint origin: the hinges lie beside the box in their print position |
| `hingePlain.f3d` | `Hinge` | As `hinge.f3d` (Pred's parameter expressions turned into their values, user parameters left out, free sketch curves fixed with dimensions at their present values); Pred's HingeInnerDiameter 4 mm and HingeOuterDiameter 7 mm as values |
| `hingePinned.f3d` | `Hinge_Pined` | As `hinge.f3d`; with Pred's printed pin as a third body |

Each file was made by `fusion-auftraege/r28_extract.py` from Pred's file, read only: the part exported on its own,
inserted into a new design, the joint origin added, checked (every sketch fully constrained, no user parameters, the
volume Pred's within 0.001 mm³) and saved.

Credits: Pred (box and small parts, CC BY-NC), Le0Michine (FusionGridfinityGenerator, CC BY-NC-SA 4.0), Zack Freedman
(Gridfinity).
