# Small parts of the storage box after Pred

The parts the **Gridkeeper box** inserts with each box (round 28, p261). They are taken over from
[Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric)
by Pred, licensed **CC BY-NC**, and changed for Gridkeeper as noted below.

| File | Pred's part | Changed |
|---|---|---|
| `latch.f3d` | `Latch_Experimental` | A joint origin *Latch joint origin* at the seat added; shape, sketches and features as Pred's |
| `handlePin.f3d` | `HandlePin` | A joint origin *Handle pin joint origin* on the bolt axis added, with its fully constrained sketch *Seat* |

Each file was made by `fusion-auftraege/r28_extract.py` from Pred's file, read only: the part exported on its own,
inserted into a new design, the joint origin added, checked (every sketch fully constrained, no user parameters, the
volume Pred's within 0.001 mm³) and saved. Hinge and handle follow in round 28.

Credits: Pred (box and small parts, CC BY-NC), Le0Michine (FusionGridfinityGenerator, CC BY-NC-SA 4.0), Zack Freedman
(Gridfinity).
