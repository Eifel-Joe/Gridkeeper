"""
Reading Fusion collections (a body's edges, faces) by index, Fusion-free so pytest can count the calls.

Iterating one (list(), a for loop) asks its length before every item: twice the calls, each one dearer the more the
document holds. 5270 edges took 6.7 s with list(), 3.1 s with item(i) over count (round 39, p296,
fusion-auftraege/r39_probe.log); a box build reads ~34 000 edges.
"""


def items(collection) -> list:
    """Every item of the collection, its count read once"""
    return [collection.item(index) for index in range(collection.count)]


def itemsOfAll(collections) -> list:
    """The items of several collections one after another"""
    return [item for collection in collections for item in items(collection)]
