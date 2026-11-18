"""
Round 47 (p591): the box's latch, hinge and handle pin, after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred), drawn once per Fusion session and kept as temporary
bodies; every box set gets copies of them (predBoxInsert.insertParts). Fusion-free: what is kept and when it is drawn.

Measured (fusion-auftraege/r47_mess.log): drawn in a document with boxes the three cost 27 s (first box) to 45 s (second
box), copied into a component as a base feature about 1 s each. Their measures hang on no box parameter (decided
19.11.2026: they need no parameters and no history); the handle follows the box width and is drawn in each set.
A dict in the add-in's memory: an add-in reload starts it anew, so a changed generator is never served from it.
"""

# the roles kept and copied, in the order of predBoxParts.PARTS; the handle is drawn with its width expression
COPIED_ROLES = ('Latch', 'Handle pin', 'Hinge')


def cacheKey(role: str, hinge: str) -> tuple:
    """Only the hinge is drawn in the variant of the box's setting, the latch and the pin are the same in every box"""
    return (role, hinge) if role == 'Hinge' else (role,)


class PartCache:
    def __init__(self):
        self._kept = {}

    def bodies(self, key: tuple, draw) -> list:
        """
        The kept [(name, temporary body)] of the part; on the first call for the key draw() gives them. A drawing that
        fails or gives no bodies keeps nothing, the next box tries again
        """
        if key not in self._kept:
            drawn = list(draw())
            if not drawn:
                raise ValueError(f'{key}: drawn without bodies')
            self._kept[key] = drawn
        return self._kept[key]

    def clear(self):
        self._kept.clear()


# the one cache of the running add-in
SESSION = PartCache()
