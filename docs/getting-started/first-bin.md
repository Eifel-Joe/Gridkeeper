# First bin

A quick tour: a baseplate, a bin on it with a Cullenect label pocket, and an insert in the pocket.

1. **New design.** Start a new design in Fusion. Gridkeeper works in part and hybrid designs; a part design is
   switched to a hybrid design when the first model is built, Gridkeeper says so in a short message.
2. **Baseplate.** Open **Solid › Create › Gridkeeper baseplate**. Set *Sizing mode* to *Grid units*, *Plate width* 3
   and *Plate length* 2, click **OK**. The plate lands in the component *Grid*.
3. **Bin.** Open **Solid › Create › Gridkeeper bin**. Set *Bin width* 2, *Bin length* 1 and *Bin height* 4. In
   *Bin compartments › Label tab* tick *Add label tab (along bin width)*, set *Tab length* to 2 u and pick *Label style* **Cullenect**. The second row of the
   *Actual dimensions* table shows the pocket size, "Cullenect: 2U: pocket 78.3 mm, insert 78 mm". Click **OK**. The bin lands in
   *Bins*.
4. **Insert.** Open **Solid › Create › Gridkeeper label**. Keep *Width* on *Base units*, set *Width (u)* to 2, type `M3x10` in *Line 1*, keep the
   socket head screw. In *Pocket* click the joint origin in the middle of the bin's pocket. Click **OK**: the insert
   sits in the pocket, in the component *Label*.
5. **Print.** Export the bin and the insert, for example as 3MF. The insert's text is a body of its own, give it a
   second filament in the slicer, see [Colors and multicolor printing](../working/colors.md).

![The baseplate, the 2x1 bin with its Cullenect pocket and an M3x10 insert in the pocket](../assets/images/first-bin-result.png)

Later you can right-click any of them for **Gridkeeper settings**, **Gridkeeper rebuild** and **Gridkeeper clone**,
see [Settings, rebuild and clone](../working/settings-rebuild-clone.md).
