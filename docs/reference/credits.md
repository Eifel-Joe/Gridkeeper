# Credits and license

Gridkeeper is our further development of GridfinityGenerator. It stands on the work of:

| Who | What | License |
|---|---|---|
| **Le0Michine** (Lev Mishin) | [FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator), the add-in Gridkeeper is built on; its history and authorship are kept in the repository | CC BY-NC-SA 4.0 |
| **CullenJWebb** | [Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels): insert and pocket dimensions, the insert geometry and layout, the screw and hardware symbols | MIT |
| **ostat / Chris Heazlewood** | [gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad), reference for the Cullenect tab | used as a reference |
| **Pred** | [Gridfinity Storage Box v1.1 (parametric)](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric): size and shape of the storage box and its lid, rebuilt in code with changes noted on [Storage boxes](../boxes.md); its latches, handle, handle pins and hinges, drawn in code after Pred's file | CC BY-NC |
| **Zack Freedman** | [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8), the system itself | |

All pictures and animations of this documentation are Gridkeeper's own, made with Gridkeeper in Fusion; the
animations follow the layout of GridfinityGenerator's README animations (model, dialog, caption).

The set screw symbols are own work of Gridkeeper under MIT, using Cullenect's thread and driver shapes.

## License

Gridkeeper is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/),
like the GridfinityGenerator it is built on. The Cullenect symbols keep their MIT license, see `LICENSE-Cullenect` in
`lib/gridfinityUtils/cullenectIcons/`.
The storage box follows [Pred's parametric Gridfinity Storage Box v1.1](https://www.printables.com/model/543553-gridfinity-storage-box-by-pred-now-parametric) (CC BY-NC): Gridkeeper rebuilds its shape in code, with the changes noted on [Storage boxes](../boxes.md), and credits Pred for it; the rebuild is part of Gridkeeper under CC BY-NC-SA, Pred's own files stay under Pred's license.

## How it is made

Gridkeeper is vibe-coded: its code is written by an AI, Claude, under the lead of Eifel-Joe, who designs the features,
tests them in Fusion and prints the results. Every change is checked by automated tests, by shape tests in Fusion and
by clicking through the dialogs; prints follow. Still,
expect rough edges, and please
[report what you find](https://github.com/Eifel-Joe/Gridkeeper/issues).
