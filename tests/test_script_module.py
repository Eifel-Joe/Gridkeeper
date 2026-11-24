"""
Tests for registering the add-in as the module scripts in Fusion import.
"""

import os
import importlib.util
import types


def _load_script_module():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "scriptModule.py")
    spec = importlib.util.spec_from_file_location("scriptModule", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scriptModule = _load_script_module()


def addin():
    module = types.ModuleType("api")
    setattr(module, scriptModule.MARKER, True)
    return module


def test_the_addin_is_imported_by_its_short_name():
    modules = {}
    module = addin()
    assert scriptModule.register(module, modules)
    assert modules[scriptModule.MODULE_NAME] is module


def test_a_new_run_replaces_the_one_before():
    modules = {}
    (before, after) = (addin(), addin())
    scriptModule.register(before, modules)
    assert scriptModule.register(after, modules)
    assert modules[scriptModule.MODULE_NAME] is after


def test_another_module_of_the_name_is_left_alone():
    other = types.ModuleType(scriptModule.MODULE_NAME)
    modules = {scriptModule.MODULE_NAME: other}
    assert not scriptModule.register(addin(), modules)
    assert modules[scriptModule.MODULE_NAME] is other


def test_stopping_removes_only_the_module_registered():
    modules = {}
    (before, after) = (addin(), addin())
    scriptModule.register(before, modules)
    scriptModule.register(after, modules)
    scriptModule.unregister(before, modules)
    assert modules[scriptModule.MODULE_NAME] is after
    scriptModule.unregister(after, modules)
    assert scriptModule.MODULE_NAME not in modules


def test_gridkeeper_has_a_name_of_its_own():
    # GridfinityGenerator registers as gridfinity: both add-ins may run, a script knows which one it imports
    assert scriptModule.MODULE_NAME == "gridkeeper"
    assert scriptModule.MARKER == "IS_GRIDKEEPER"


def test_gridfinity_generators_module_is_never_taken_over():
    original = types.ModuleType("gridfinity")
    original.IS_GRIDFINITY_GENERATOR = True
    modules = {"gridfinity": original}
    assert scriptModule.register(addin(), modules)
    scriptModule.unregister(modules[scriptModule.MODULE_NAME], modules)
    assert modules == {"gridfinity": original}


def test_the_api_carries_the_marker_and_every_builder():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.py")
    source = open(path, encoding="utf-8").read()
    assert f"{scriptModule.MARKER} = True" in source
    assert "import gridkeeper" in source
    for builder in ("binBuilder", "baseplateBuilder", "boxBuilder", "boxLabelBuilder", "labelBuilder"):
        assert f" import {builder}" in source, builder
