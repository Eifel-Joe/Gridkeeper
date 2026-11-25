"""
Round 58: the palette's GIFs are the docs' animations of dev-notes/tools/anim/anims.json, made by compose.py, and the
Python for the tools is found without a venv of its own (commands/commandModelScreenshots/screenshotTools.py).
"""

import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _module():
    path = os.path.join(ROOT, "commands", "commandModelScreenshots", "screenshotTools.py")
    spec = importlib.util.spec_from_file_location("screenshotTools", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = _module()
VENV = (".venv", "Scripts", "python.exe") if sys.platform == "win32" else (".venv", "bin", "python")


def test_the_main_checkout_of_a_worktree(tmp_path):
    main = tmp_path / "Gridkeeper"
    worktree = main / ".claude" / "worktrees" / "r58"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {main / '.git' / 'worktrees' / 'r58'}\n")
    assert tools.mainCheckout(str(worktree)) == str(main)
    # a checkout of its own has a .git folder
    (main / ".git").mkdir()
    assert tools.mainCheckout(str(main)) is None


def test_the_python_is_the_checkouts_venv_then_the_main_checkouts_then_the_computers(tmp_path):
    root = str(tmp_path / "wt")
    main = str(tmp_path / "main")
    own = os.path.join(root, "tools", "screenshots", *VENV)
    mains = os.path.join(main, "tools", "screenshots", *VENV)
    system = [["py", "-3"], ["python"]]

    def find(existing, runnable):
        return tools.findPython(root, ["PIL"], main=main, system=system,
                                exists=lambda path: path in existing, canRun=lambda command, modules: command in runnable)

    assert find({own, mains}, [[own], [mains], ["py", "-3"]]) == [own]
    assert find({mains}, [[mains], ["py", "-3"]]) == [mains]
    # a venv without the modules is passed over
    assert find({own}, [["python"]]) == ["python"]
    assert find(set(), []) is None


def test_a_python_runs_without_fusions_own_variables():
    environment = tools.toolEnvironment({"PYTHONHOME": "fusion", "PYTHONPATH": "fusion", "PATH": "p"})
    assert environment == {"PATH": "p"}


def test_the_gif_rows_are_the_animations_of_anims_json(tmp_path):
    anim = tmp_path / "anim"
    (anim / "raw" / "bin-lip").mkdir(parents=True)
    (anim / "anims.json").write_text(json.dumps({"bin-lip": [{"caption": "Light"}, {"caption": "Full"}]}))
    for picture in ["1-model.png", "1-dialog.png", "2-dialog.png"]:
        (anim / "raw" / "bin-lip" / picture).write_bytes(b"png")
    gifs = tmp_path / "gif"
    gifs.mkdir()
    rows = tools.gifRows(str(anim), str(gifs))
    assert [row["name"] for row in rows] == ["bin-lip"]
    assert rows[0]["description"] == "Light · Full"
    assert rows[0]["missing"] == ["2-model.png"]
    assert rows[0]["files"] == {"model-light": None, "model-dark": None}


def test_compose_is_run_for_one_animation():
    assert tools.composeCommand(["python"], "/repo", "bin-lip") == [
        "python", os.path.join("/repo", "dev-notes", "tools", "anim", "compose.py"), "bin-lip"]


def test_compose_names_the_gifs_it_wrote():
    # the palette takes a line ending in .gif named after the animation as made, see entry.runTool
    with open(os.path.join(ROOT, "dev-notes", "tools", "anim", "compose.py"), encoding="utf-8") as file:
        source = file.read()
    assert "print(os.path.join(OUT, f'{name}-{theme}.gif'))" in source


def test_a_state_can_name_its_own_dialog_picture(tmp_path):
    # review round 58: compose.py takes a state's "dialog" (bin-solid-tool reuses 2-dialog.png), the row does too
    anim = tmp_path / "anim"
    (anim / "raw" / "tool").mkdir(parents=True)
    (anim / "anims.json").write_text(json.dumps({"tool": [{"caption": "A"}, {"caption": "B", "dialog": "1-dialog.png"}]}))
    for picture in ["1-model.png", "1-dialog.png", "2-model.png"]:
        (anim / "raw" / "tool" / picture).write_bytes(b"png")
    (row,) = tools.gifRows(str(anim), str(tmp_path))
    assert row["missing"] == []


def test_a_relative_gitdir_is_read_from_the_worktree(tmp_path):
    main = tmp_path / "Gridkeeper"
    worktree = main / ".claude" / "worktrees" / "r58"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: ../../../.git/worktrees/r58\n")
    assert tools.mainCheckout(str(worktree)) == str(main)
