# Symbols

The symbols of the label inserts are svg files drawn from Cullenect's own OpenSCAD code, in
`lib/gridfinityUtils/cullenectIcons/` of the add-in. The names and their order are Cullenect's.

![A sheet of inserts with different screw and hardware symbols](../assets/images/insert-symbols.png)

## Screws

With **Screw** ticked, the symbol is put together from:

| Part | Choices |
|---|---|
| **Head** | None, Socket, Countersunk, Round, Pan |
| **Shaft** | Machine, Tapping |
| **Threads** | Full, Partial |
| **Driver** | None, Slot, Phillips, Phillips Slot, Phillips Square, Torx/Star, Hex, Robertson/Square, Triangle |
| **Flange** | on or off |
| **Security pin** | on or off |

Each dropdown offers only what makes a symbol together with the choices above it; a choice that doesn't moves to the
first one that does. **Flange** and **Security pin** are locked where no symbol has them.

**Set screws:** head *None* with a *Slot*, *Hex* or *Torx/Star* driver is a set screw (grub screw), drawn as its thread
and, beside it, its end with the driver; *Machine* gives a flat end, *Tapping* a point. Set screws are 1 mm wider than
the other screws.

## Hardware

Pick **Hardware** instead of a screw: Washer, Locking Washer, Threaded Insert, Nut, Square Nut, Nylon Lock Nut, T-Nut
Side, T-Nut Top, Magnet, Crimp Ring (open, closed), Crimp Fork (open, closed), Crimp Spade (open, closed), Crimp
Receptacle (open, closed) and Crimp Butt Splice.

The hardware symbols are also offered as **Label icon** of normal bin labels, see [Label tab and labels](../bins/labels.md#icons).

## Your own symbols

A new svg file in `cullenectIcons/hardware/` shows up in the **Hardware** list, named after the file, after the
add-in is restarted. The svg's `width` and `height` set its size; a number without unit counts as CSS pixels, as in
the svg standard.
