"""
buildBox returns the native bodies of box and lid, as binBuilder does (round 27). The bodies moveToComponent gives back
are seen through the Box and Lid occurrences: the snapshot tests found neither among the design's bodies ("loose body
Base, not part of what was built") nor their box tag on them ("Base isn't in the Text component of its part"),
fusion-auftraege r27_snap step 1, 17.11.2026. boxBuilder needs Fusion to load, so the test reads its source.
"""

import ast
import os

SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commands", "commandCreateBox", "boxBuilder.py")


def _function(name):
    tree = ast.parse(open(SOURCE, encoding="utf-8").read())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_build_box_returns_the_native_bodies():
    returns = [node for node in ast.walk(_function("_buildBox")) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    value = returns[0].value
    if isinstance(value, ast.BinOp):
        value = value.left
    assert isinstance(value, ast.List) and len(value.elts) == 2
    for element in value.elts:
        assert isinstance(element, ast.Call) and ast.unparse(element.func) == "rebuildUtils.nativeBody", ast.unparse(element)


def test_build_box_puts_joint_origins_at_the_small_parts_seats():
    """Round 28, plan task 5: the seats of latches, handle, pins and the chosen hinges become joint origins in the box"""
    source = ast.unparse(_function("_buildBox"))
    assert "createOffsetJointOrigins(predBoxSeats.seatJointOriginPoints(dims, state.hinge), boxComponent" in source


def test_build_box_inserts_the_small_parts_and_returns_their_bodies_after_box_and_lid():
    """Round 28, plan task 6 and decision 5: the parts come into the set, buildBox gives box and lid first"""
    source = ast.unparse(_function("_buildBox"))
    assert "predBoxInsert.insertParts(des, setOccurrence, boxOccurrence, dims, state.hinge, name, assembly.inContext)" in source
    returns = [node for node in ast.walk(_function("_buildBox")) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert ast.unparse(returns[0].value) == "[rebuildUtils.nativeBody(base), rebuildUtils.nativeBody(lid)] + partBodies"


def test_a_rebuild_pairs_box_and_lid_only():
    """rebuildUtils.bodyMap pairs old and new bodies only when there are as many; the old set's tagged bodies are box
    and lid, the small parts (round 28) aren't tagged, so the rebuild's build gives the tagged bodies only"""
    rebuild = _function("rebuildBox")
    build = next(node for node in ast.walk(rebuild) if isinstance(node, ast.FunctionDef) and node.name == "build")
    assert "tagUtils.readBodyTag" in ast.unparse(build)


def test_a_rebuild_renames_the_small_parts_too():
    """Review round 28: the new set's parts are inserted while the old set still has its components, Fusion names them
    "Latch (1)" and so on; _renameParts gave box and lid back their names only. It walks the set's components now"""
    source = ast.unparse(_function("_renameParts"))
    assert "childOccurrences" in source


def test_a_single_body_part_has_its_roles_name():
    """Review round 28: the handle pin's body is "Body1" from Pred's file; snapshots key bodies by name and export names
    files after them, so a part's only body is named after the part"""
    source = open(os.path.join(os.path.dirname(SOURCE), "..", "..", "lib", "gridfinityUtils", "predBoxInsert.py"), encoding="utf-8").read()
    assert "bRepBodies.count == 1" in source and ".name = part.role" in source


def test_a_box_of_bodies_in_the_root_gets_no_seats():
    """Review round 28: without components no part is inserted, so the seat joint origins would be clutter"""
    source = ast.unparse(_function("_buildBox"))
    seat = source.index("predBoxSeats.seatJointOriginPoints(dims, state.hinge)")
    guard = source.rfind("if boxOccurrence is not None", 0, seat)
    assert guard != -1 and source.count("\n", guard, seat) <= 1


INSERT = os.path.join(os.path.dirname(SOURCE), "..", "..", "lib", "gridfinityUtils", "predBoxInsert.py")


def test_the_hinges_are_jointed_like_the_other_parts_without_a_captured_position():
    """17.11.2026: loose hinges stayed behind when the set was stacked and their
    captured position stayed suppressed after a rebuild (r28_cmd l1/l2); every part is jointed now, none is placed"""
    source = open(INSERT, encoding="utf-8").read()
    assert "snapshots.add" not in source and "transform2" not in source and "placeAllInSet" not in source
    assert "predBoxParts.partsToDraw(hinge)" in source and "predBoxSeats.seats(dims, hinge)" in source
    assert "originConstructionPoint" in source


def test_the_parts_are_drawn_in_the_set_not_imported():
    """Round 29: importToTarget fails in a command with a dialog (fusion-auftraege/r28_cmdvariants.log); every part is
    drawn by its generator into a new component of the set, in the box command, so it lands in the set's group"""
    source = open(INSERT, encoding="utf-8").read()
    assert "importToTarget" not in source and "tempCopy" not in source and ".f3d" not in source
    assert "predBoxParts.partsToDraw(hinge)" in source and "occurrences.addNewComponent(" in source
    assert "drawPart(component, part, dims, hinge)" in source


def test_every_drawn_role_has_its_generator():
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    drawPart = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "drawPart"))
    parts = open(os.path.join(os.path.dirname(INSERT), "predBoxParts.py"), encoding="utf-8").read()
    drawn = ast.literal_eval(next(node.value for node in ast.parse(parts).body
                                  if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "DRAWN_ROLES"))
    for role in drawn:
        assert f"'{role}'" in drawPart, role


def test_the_pin_is_drawn_by_its_generator():
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    drawPart = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "drawPart"))
    assert "predHandlePin.createHandlePin(component)" in drawPart


def test_the_handle_is_drawn_with_the_width_of_the_box():
    """The handle follows the label width by its expression on gfBoxN_baseWidth (predBoxSeats.handleHalfWidth)"""
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    drawPart = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "drawPart"))
    assert "predHandle.createHandle(component, predBoxSeats.handleHalfWidth(dims).expression)" in drawPart


def test_the_latch_is_drawn_by_its_generator():
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    drawPart = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "drawPart"))
    assert "predLatch.createLatch(component)" in drawPart


def test_the_hinge_is_drawn_in_the_chosen_variant_and_gets_its_joint_origin():
    """The hinges are drawn in the variant of the box's setting; they have no joint origin of their own, insertParts
    gives them one at the component's origin and joints them at Hinge 1/2 beside the box (round 28, Vorschlag J)"""
    source = open(INSERT, encoding="utf-8").read()
    tree = ast.parse(source)
    drawPart = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "drawPart"))
    assert "predHinge.createHinge(component, hinge)" in drawPart
    assert "addOriginJointOrigin(component, partJointOriginName(part.role))" in source


def test_every_small_part_body_gets_the_box_parts_appearance():
    """17.11.2026: latches, hinges, handle and pins in another color than box and lid; insertParts gives every body
    of every part the appearance, on create, rebuild and clone alike (all build through it)"""
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    insertParts = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "insertParts"))
    assert "appearanceUtils.boxPartsAppearance(des)" in insertParts
    assert "body.appearance = appearance" in insertParts


def test_a_missing_library_appearance_leaves_the_parts_uncoloured_but_builds_the_box():
    """Review round 29: without a library appearance to copy (appearanceUtils.AppearanceError) the box command failed,
    before round 29 a box needed no appearance; the parts are drawn without their colour then"""
    source = open(INSERT, encoding="utf-8").read()
    assert "except appearanceUtils.AppearanceError" in source


def test_build_box_always_puts_joint_origins_into_the_floor_cells():
    """Round 31, p312: a new bin can be jointed into a cell of the box floor, every box has them, whatever an older config says"""
    source = ast.unparse(_function("_buildBox"))
    assert "cellJointOriginPoints(centers, CELL_JOINT_ORIGIN" in source
    assert "state.hasJointOrigins" not in source


def test_a_preview_builds_box_and_lid_without_the_small_parts():
    """Round 36, p295: inserting the small parts made every preview slow; the preview (a build that may not change
    the document) shows box and lid, OK builds the whole set"""
    build = ast.unparse(_function("buildBox"))
    assert "_buildBox(des, state, settings, plan, parameterPrefix, occurrenceTransform, oldPlace, forOk=mayChangeDocument)" in build
    source = ast.unparse(_function("_buildBox"))
    assert "partBodies = predBoxInsert.insertParts(des, setOccurrence, boxOccurrence, dims, state.hinge, name, assembly.inContext) if boxOccurrence is not None and forOk else []" in source


def _callsUnderForOk(function, name):
    """(calls of name inside an `if forOk` block, all calls of name) in the function"""
    def calls(node):
        return [call for call in ast.walk(node) if isinstance(call, ast.Call) and ast.unparse(call.func).endswith(name)]
    guarded = [call for node in ast.walk(function) if isinstance(node, ast.If) and ast.unparse(node.test) == "forOk"
               for statement in node.body for call in calls(statement)]
    return (guarded, calls(function))


def test_a_preview_makes_no_joint_origins_ok_makes_them_all():
    """Round 36, p296: the six joint origin calls (cells, stack, seats, lid) took 20-100 s, 75 s in a preview that is
    thrown away; nothing in the preview reads them (rebuildUtils.rebuild returns the preview's bodies as they are).
    OK (forOk, the default, also the snapshot tests') makes every one of them and the lid's joint"""
    function = _function("_buildBox")
    (guarded, every) = _callsUnderForOk(function, "createOffsetJointOrigins")
    assert len(every) == 6 and len(guarded) == len(every)
    (guarded, every) = _callsUnderForOk(function, "joints.add")
    assert len(every) == 1 and len(guarded) == 1
    assert "forOk: bool=True" in ast.unparse(function.args)


def test_the_preview_checkbox_says_the_small_parts_come_with_ok():
    entry = open(os.path.join(os.path.dirname(SOURCE), "entry.py"), encoding="utf-8").read()
    line = next(line for line in entry.splitlines() if "SHOW_PREVIEW_INPUT, tr('Show preview" in line)
    assert "box and lid" in line and "OK" in line, line


def _insertFunction(name):
    tree = ast.parse(open(INSERT, encoding="utf-8").read())
    return ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name))


def test_insert_parts_gets_each_parts_bodies_the_copy_way():
    """Round 47 (p591): insertParts asks partBodies, which copies latch, hinge and pin and draws the handle"""
    insertParts = _insertFunction("insertParts")
    assert "partBodies(setComponent, component, part, dims, hinge)" in insertParts
    assert "drawPart(" not in insertParts


def test_latch_hinge_and_pin_come_as_copies_of_the_session_cache():
    partBodies = _insertFunction("partBodies")
    assert "part.role not in predPartCache.COPIED_ROLES" in partBodies
    assert "key = predPartCache.cacheKey(part.role, hinge)" in partBodies
    assert "predPartCache.SESSION.bodies(key, " in partBodies
    assert "predPartCopies.keepDrawn(setComponent, lambda scratch: drawPart(scratch, part, dims, hinge))" in partBodies
    assert "predPartCopies.addCopies(component, kept)" in partBodies


def test_the_handle_is_drawn_in_its_component_as_before():
    partBodies = _insertFunction("partBodies")
    first = partBodies.index("part.role not in predPartCache.COPIED_ROLES")
    assert partBodies.index("return drawPart(component, part, dims, hinge)", first) > first


def test_a_failed_copy_draws_the_part_in_place_and_logs_why():
    """Spec requirement 4: the box is built either way"""
    partBodies = _insertFunction("partBodies")
    assert "except Exception as err" in partBodies
    handler = partBodies[partBodies.index("except Exception as err"):]
    assert "commonUtils.fileLog(" in handler and "drawPart(component, part, dims, hinge)" in handler


def test_a_failed_copy_forgets_the_kept_part():
    """Review round 49: kept bodies that cannot be copied (a broken part file) are drawn and written anew next time"""
    partBodies = _insertFunction("partBodies")
    handler = partBodies[partBodies.index("except Exception as err"):]
    assert "predPartCache.SESSION.forget(key)" in handler
    assert handler.index("predPartCache.SESSION.forget(key)") < handler.index("drawPart(component, part, dims, hinge)")


def test_a_copied_part_gets_its_joint_origin_by_the_generators_function():
    """Same names and places as a drawn part: joints, seats and the rebuild's moving of user joints (p293) by name"""
    jointOrigin = _insertFunction("addPartJointOrigin")
    assert "predLatch.addJointOrigin(component)" in jointOrigin
    assert "predHandlePin.addJointOrigin(component)" in jointOrigin
    assert "addPartJointOrigin(component, part.role)" in _insertFunction("partBodies")


def test_a_copy_fusion_left_behind_is_not_drawn_over():
    """Review round 47: drawing in place on top of a copy that could not be removed would double the part"""
    partBodies = _insertFunction("partBodies")
    assert partBodies.index("except predPartCopies.LeftBehind:") < partBodies.index("except Exception as err")
    handler = partBodies[partBodies.index("except predPartCopies.LeftBehind:"):partBodies.index("except Exception as err")]
    assert "raise" in handler and "drawPart" not in handler
