# Known deviations from the Gridfinity specification

Gridkeeper builds bins and baseplates to the Gridfinity specification, with the following deliberate deviation by default.

## Stacking lip with a flat top

The stacking lip at the top of a bin is cut off **0.6 mm flat** instead of running out to a sharp edge: its top stands
**3.8 mm** above the wall instead of 4.4 mm (measured on a built bin).

- Wall height, stacking pitch and the seat of a stacked bin are as in the specification, so Gridkeeper bins stack on
  and under other Gridfinity bins.
- This is the same as in the original GridfinityGenerator, on purpose, see
  [Le0Michine/FusionGridfinityGenerator#176](https://github.com/Le0Michine/FusionGridfinityGenerator/issues/176):
  a sharp edge takes more filament and doesn't print cleanly, a flat top does.
- It is the default only: **Trim lip top** off keeps the sharp edge, and **Lip type** *Full* builds the whole original
  profile with its inner tip, see [Lip types](../bins/body.md#lip-types).

![Section through the lip at the corner of a bin: the top of the lip is flat, not a sharp edge](../assets/images/lip-flat-top-section.png)
