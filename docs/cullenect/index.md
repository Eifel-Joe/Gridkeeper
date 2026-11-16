# Cullenect labels

[Cullenect](https://github.com/CullenJWebb/Cullenect-Labels) by CullenJWebb is a system of exchangeable labels: a
thin insert with text and a symbol clicks into a pocket of the bin's label tab and is swapped when the contents
change. Gridkeeper builds both halves:

- **the pockets**, as the label style *Cullenect* of a bin's label tab, see [Pockets in bins](pockets.md);
- **the inserts**, with the command **Gridkeeper label**, see [Label inserts](inserts.md), with screw and hardware
  [symbols](symbols.md).

The sizes follow Cullenect's own OpenSCAD code, so Gridkeeper inserts fit Cullenect pockets and the other way round:

| | Size |
|---|---|
| Insert width | base width × units − 6 mm, e.g. 36 mm for 1U, 78 mm for 2U with 42 mm units |
| Insert height | 11 mm |
| Insert thickness | 1.2 mm |
| Pocket | 1.2 mm deep, larger than the insert by the socket play (0.3 mm) in width and height, with latch ribs along both long sides |

![A bin with three compartments, each with a Cullenect pocket and an insert in red, blue and black, the black one lifted out of its pocket](../assets/images/cullenect-overview.png)

To relabel a bin, print a new insert and press it into the pocket, the latch holds it. Text and symbol are bodies of
their own, ready for a second filament, see [Colors and multicolor printing](../working/colors.md).
