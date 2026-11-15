"""
Tests for the joint origins of bin feet and baseplate sockets (round 15, p170): one point per cell, named by its cell,
at the cell's center as dims that follow the grid parameters, all at one height.
"""

import os
import sys
import importlib.util


def _load(name):
    core = sys.modules["adsk.core"]
    added = [typeName for typeName in ("Base", "ValueInput") if not hasattr(core, typeName)]
    for typeName in added:
        setattr(core, typeName, type(typeName, (), {}))
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder = os.path.join(project_root, "lib", "gridfinityUtils")
        package = "jointOriginLayoutTestPackage"
        if package not in sys.modules:
            packageSpec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
            packageModule = importlib.util.module_from_spec(packageSpec)
            packageModule.__path__ = [folder]
            sys.modules[package] = packageModule
        spec = importlib.util.spec_from_file_location(f"{package}.{name}", os.path.join(folder, f"{name}.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        for typeName in added:
            delattr(core, typeName)


layout = _load("jointOriginLayout")
dim = sys.modules["jointOriginLayoutTestPackage.dim"]
Dim = dim.Dim


def test_names_and_order_follow_the_cells():
    centers = [(0, 0, Dim.length(2.1), Dim.length(2.1)), (1, 0, Dim.length(6.3), Dim.length(2.1)), (0, 1, Dim.length(2.1), Dim.length(6.3))]
    points = layout.cellJointOriginPoints(centers, "Foot joint origin", Dim.length(-0.5))
    assert [point[0] for point in points] == ["Foot joint origin 1-1", "Foot joint origin 2-1", "Foot joint origin 1-2"]


def test_dims_and_height_pass_through():
    x = Dim(6.3, "gfBin1_baseWidth * 1.5", dim.DimKind.EXPRESSION, True)
    z = Dim.length(-0.5)
    [(_, pointX, pointY, pointZ)] = layout.cellJointOriginPoints([(1, 0, x, Dim.length(2.1))], "Socket joint origin", z)
    assert pointX is x and pointX.isExpression
    assert pointY.value == 2.1
    assert pointZ is z
