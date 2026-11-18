from contextlib import contextmanager

# The names a build asks for its components (round 44, p570). Fusion counts a name still taken up: a bin rebuilt while
# the old one is still there asked for "Gridfinity bin 1x1x3" and got "... (1)". A rebuild records what was asked for,
# see rebuildUtils.dropComponentCounters: a name that differs from it by a counter is Fusion's, one asked for with an
# "(n)" of its own (from a label text) stays. No Fusion import, so it can be unit tested.

_recorded: list | None = None


def name(component, requested: str):
    """Names the component, recorded while a rebuild builds"""
    component.name = requested
    if _recorded is not None:
        _recorded.append((component, requested))


@contextmanager
def recording():
    """The (component, requested name) pairs named inside, the recording ends even when the build fails"""
    global _recorded
    named = []
    _recorded = named
    try:
        yield named
    finally:
        _recorded = None
