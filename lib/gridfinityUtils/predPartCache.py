"""
Round 47 (p591): the box's latch, hinge and handle pin, after Pred's parametric Gridfinity Storage Box v1.1
(https://www.printables.com/model/543553, CC BY-NC, by Pred), drawn once per Fusion session and kept as temporary
bodies; every box set gets copies of them (predBoxInsert.insertParts). Fusion-free: what is kept and when it is drawn.

Measured (fusion-auftraege/r47_mess.log): drawn in a document with boxes the three cost 27 s (first box) to 45 s (second
box), copied into a component as a base feature about 1 s each. Their measures hang on no box parameter (decided
19.11.2026: they need no parameters and no history); the handle follows the box width and is drawn in each set.
A dict in the add-in's memory, as long as this module is loaded: it is loaded and dropped together with the
generators, so what it keeps was always drawn by the generators that are loaded.

Round 49 (p610): behind the memory a store on disk (predPartFile), so the first box after Fusion starts reads the parts
instead of drawing them. Memory → file → drawing; a drawn part is written right away. The store never fails a box: a
part it cannot give is drawn, a failed write is only logged.
"""

# the roles kept and copied, in the order of predBoxParts.PARTS; the handle is drawn with its width expression
COPIED_ROLES = ('Latch', 'Handle pin', 'Hinge')


def cacheKey(role: str, hinge: str) -> tuple:
    """Only the hinge is drawn in the variant of the box's setting, the latch and the pin are the same in every box"""
    return (role, hinge) if role == 'Hinge' else (role,)


class PartCache:
    def __init__(self, store=None, log=print):
        """store: a function giving the store on disk (load(key), save(key, kept)), called once when first needed"""
        self._kept = {}
        self._store = store
        self._log = log
        self._opened = None

    def bodies(self, key: tuple, draw) -> list:
        """
        The kept [(name, temporary body)] of the part; on the first call for the key the store or else draw() gives
        them. A drawing that fails or gives no bodies keeps nothing, the next box tries again
        """
        if key not in self._kept:
            store = self._openStore()
            read = self._tryStore(lambda: store.load(key), 'read') if store else None
            if read:
                self._kept[key] = list(read)
            else:
                drawn = list(draw())
                if not drawn:
                    raise ValueError(f'{key}: drawn without bodies')
                self._kept[key] = drawn
                if store:
                    self._tryStore(lambda: store.save(key, drawn), 'written')
        return self._kept[key]

    def _openStore(self):
        """The store, set up on first need; one that cannot be set up is logged once and left out for the session"""
        if self._opened is None:
            self._opened = False
            if self._store is not None:
                try:
                    self._opened = self._store()
                except Exception as err:
                    self._log(f'small parts kept in memory only, no part files: {err}')
        return self._opened or None

    def _tryStore(self, action, what: str):
        try:
            return action()
        except Exception as err:
            self._log(f'part file not {what}: {err}')
            return None

    def clear(self):
        self._kept.clear()


def _sessionStore():
    from . import predPartFile
    return predPartFile.sessionStore()


def _sessionLog(message: str):
    from . import commonUtils
    commonUtils.fileLog(message)


# the one cache of the running add-in, with the add-in's partCache folder behind it
SESSION = PartCache(store=_sessionStore, log=_sessionLog)
