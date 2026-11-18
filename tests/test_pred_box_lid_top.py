"""
Round 30, p311: a closed lid leaves out the steps of the grid on its top (spec 2026-11-18-r30-lid-closed, way A). The
generator needs Fusion, so its source is read (ast); the shape is checked in Fusion (fusion-auftraege/r30_lid_check.py,
snapshot case box_5x4x6_lid_closed).
"""

import ast
import os

GENERATOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "gridfinityUtils", "predBoxGenerator.py")


def _tree():
    return ast.parse(open(GENERATOR, encoding="utf-8").read())


def _function(name, tree=None):
    tree = tree or _tree()
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)


def _guard(function, text):
    """The test of the innermost if around each top-level statement of the function, or of an if in it, whose source
    holds text; None where there is no if. Loops, with and try are not entered, a statement in one counts as a whole
    under the if around it (enough for floorGrid and createPredBox; it can only fail wrongly, never pass wrongly)"""
    found = []

    def visit(node, guard):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If):
                for statement in child.body:
                    visit_statement(statement, ast.unparse(child.test))
                for statement in child.orelse:
                    visit_statement(statement, guard)
            else:
                visit_statement(child, guard)

    def visit_statement(statement, guard):
        if isinstance(statement, ast.If):
            visit(ast.Module(body=[statement], type_ignores=[]), guard)
            return
        if isinstance(statement, ast.stmt) and text in ast.unparse(statement):
            found.append(guard)
        elif not isinstance(statement, ast.stmt):
            visit(statement, guard)
    for statement in function.body:
        visit_statement(statement, None)
    return found


def test_the_floor_grid_asks_which_steps_the_lid_gets():
    source = ast.unparse(_function("floorGrid"))
    assert "predBoxConfig.lidTopFeatures(self.options.lidTop)" in source


def test_sweep1_cuts_the_lid_only_for_the_grid():
    source = ast.unparse(_function("floorGrid"))
    assert "[self.base, self.lid] if lidTop.socketsInTop else [self.base]" in source


def test_the_hollow_seats_and_cell_ridges_only_for_the_grid():
    floorGrid = _function("floorGrid")
    assert _guard(floorGrid, "'Sweep4'") == ["lidTop.hollowSeats"]
    assert _guard(floorGrid, "name='Cell ridges'") == ["lidTop.cellRidges"]
    # Sweep2, the bin seats under the lid, for both
    assert _guard(floorGrid, "'Sweep2'") == [None]


def test_the_ridge_chamfer_only_for_the_grid():
    assert _guard(_function("createPredBox"), "'#85 Chamfer16'") == ["predBoxConfig.lidTopFeatures(options.lidTop).ridgeChamfer"]


def test_the_box_options_reach_the_generator_by_name():
    """Review R30: boxBuilder unpacked predBoxConfig.BoxOptions into PredBoxOptions by position; a field moved in one of
    them would hand a value to the wrong option, lidTop among them. By name, and with the same fields"""
    builder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "commandCreateBox", "boxBuilder.py")
    assert "PredBoxOptions(**predBoxConfig.boxOptions(state)._asdict())" in open(builder, encoding="utf-8").read()
    options = next(node for node in _tree().body if isinstance(node, ast.ClassDef) and node.name == "PredBoxOptions")
    fields = [statement.target.id for statement in options.body if isinstance(statement, ast.AnnAssign)]
    from tests.test_joint_origin_layout import _load
    assert list(_load("predBoxConfig").BoxOptions._fields) == fields
