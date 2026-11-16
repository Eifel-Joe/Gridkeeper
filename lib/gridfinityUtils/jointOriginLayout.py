from .dim import Dim

# Joint origins at the cells of bin feet and baseplate sockets (round 15, p170). They used to share one sketch with
# reference dimensions and stayed put when the grid parameters changed; now each is a point of its own built by
# baseGenerator.createPointJointOrigins, which drives its dims. Names stay as they were, joints made on them keep them


def cellJointOriginPoints(centers: list[tuple[int, int, Dim, Dim]], name: str, z: Dim) -> list[tuple[str, Dim, Dim, Dim]]:
    """The name, x, y and z of a joint origin at each cell center, named by its column and row from 1"""
    return [(f'{name} {column + 1}-{row + 1}', x, y, z) for (column, row, x, y) in centers]
