# Known deviations from the Gridfinity specification

Gridkeeper builds bins and baseplates to the Gridfinity specification, with the following deliberate deviation.

## Stacking lip with a flat top

The stacking lip at the top of a bin is cut off **0.6 mm flat** instead of running out to a sharp edge: its top stands
**3.8 mm** above the wall instead of 4.4 mm (measured on a built bin).

- Wall height, stacking pitch and the seat of a stacked bin are as in the specification, so Gridkeeper bins stack on
  and under other Gridfinity bins.
- This is the same as in the original GridfinityGenerator, on purpose, see
  [Le0Michine/FusionGridfinityGenerator#176](https://github.com/Le0Michine/FusionGridfinityGenerator/issues/176):
  a sharp edge takes more filament and doesn't print cleanly, a flat top does.

![Section through the lip of a bin, the flat top 0.6 mm below where the sharp edge would be](../assets/images/lip-flat-top-section.png)
