"""
Round 49 (p610): the box's latch, handle pin and hinge are kept on disk as well, as .smt with their names in a .json,
in the add-in's partCache folder (spec dev-notes/specs/2026-11-19-r49-small-parts-file.md). Fusion's export and import
come in as io, here fakes that write the body names into the file.
"""

import json
import os

import pytest

from tests.test_joint_origin_layout import _load

partFile = _load("predPartFile")
cache = _load("predPartCache")


class FakeIo:
    """Writes the 'bodies' (strings here) as json into the .smt, reads them back the same way"""

    def __init__(self):
        self.exported = []
        self.imported = []

    def export(self, bodies, path):
        self.exported.append(path)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(list(bodies), file)

    def load(self, path):
        self.imported.append(path)
        with open(path, encoding="utf-8") as file:
            return json.load(file)


def _store(tmp_path, io=None, logged=None, version="1.1.0", stamp="abc123def456"):
    folder = tmp_path / "partCache"
    return partFile.PartFile(str(folder), version, stamp, io or FakeIo(), (logged if logged is not None else []).append)


LATCH = cache.cacheKey("Latch", "M3x30")
HINGE = cache.cacheKey("Hinge", "Pinned")


# file names and the code stamp

def test_file_stem_carries_version_code_role_and_hinge():
    assert partFile.fileStem("1.1.0", "abc123def456", LATCH) == "1.1.0-abc123def456-Latch"
    assert partFile.fileStem("1.1.0", "abc123def456", HINGE) == "1.1.0-abc123def456-Hinge-Pinned"
    assert partFile.fileStem("1.1.0", "abc", cache.cacheKey("Handle pin", "Plain")) == "1.1.0-abc-Handle_pin"


def _tree(tmp_path, files):
    for (name, text) in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return str(tmp_path)


def test_code_stamp_is_12_hex_digits_and_stable(tmp_path):
    folder = _tree(tmp_path, {"a.py": "x = 1", "b.json": "{}"})
    stamp = partFile.codeStamp(folder)
    assert len(stamp) == 12 and int(stamp, 16) >= 0
    assert partFile.codeStamp(folder) == stamp


def test_code_stamp_changes_with_a_files_content(tmp_path):
    folder = _tree(tmp_path, {"a.py": "x = 1", "b.json": "{}"})
    before = partFile.codeStamp(folder)
    (tmp_path / "b.json").write_text('{"edge": 2}', encoding="utf-8")
    assert partFile.codeStamp(folder) != before


def test_code_stamp_changes_when_a_file_is_renamed(tmp_path):
    folder = _tree(tmp_path, {"a.py": "x = 1"})
    before = partFile.codeStamp(folder)
    os.rename(tmp_path / "a.py", tmp_path / "c.py")
    assert partFile.codeStamp(folder) != before


def test_code_stamp_ignores_other_files_and_pycache(tmp_path):
    folder = _tree(tmp_path, {"a.py": "x = 1"})
    before = partFile.codeStamp(folder)
    _tree(tmp_path, {"notes.txt": "x", "__pycache__/a.json": "{}", "__pycache__/a.cpython.pyc": "x"})
    assert partFile.codeStamp(folder) == before


def test_code_stamp_does_not_hang_on_line_endings(tmp_path):
    """git on Windows checks out CRLF, CI and a release zip may have LF: the same code, the same key"""
    lf = partFile.codeStamp(_tree(tmp_path / "lf", {"a.py": "x = 1\ny = 2\n"}))
    (tmp_path / "crlf").mkdir()
    (tmp_path / "crlf" / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
    assert partFile.codeStamp(str(tmp_path / "crlf")) == lf


# saving and loading

def test_saved_parts_load_with_their_names_in_order(tmp_path):
    store = _store(tmp_path)
    kept = [("Hinge top", "body 1"), ("Hinge bottom", "body 2"), ("Hinge pin", "body 3")]
    store.save(HINGE, kept)
    assert store.load(HINGE) == kept
    files = sorted(os.listdir(tmp_path / "partCache"))
    assert files == ["1.1.0-abc123def456-Hinge-Pinned.json", "1.1.0-abc123def456-Hinge-Pinned.smt"]


def test_missing_file_loads_nothing(tmp_path):
    assert _store(tmp_path).load(LATCH) is None


def test_another_version_or_code_does_not_read_the_file(tmp_path):
    _store(tmp_path).save(LATCH, [("Latch", "old")])
    assert _store(tmp_path, version="1.2.0").load(LATCH) is None
    assert _store(tmp_path, stamp="000000000000").load(LATCH) is None


@pytest.mark.parametrize("names", ["not json", "{}", '["Latch", 3]', "[]", '"Latch"'])
def test_broken_names_load_nothing(tmp_path, names):
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "body")])
    (tmp_path / "partCache" / "1.1.0-abc123def456-Latch.json").write_text(names, encoding="utf-8")
    assert store.load(LATCH) is None


def test_missing_smt_loads_nothing(tmp_path):
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "body")])
    os.remove(tmp_path / "partCache" / "1.1.0-abc123def456-Latch.smt")
    assert store.load(LATCH) is None


def test_unreadable_smt_loads_nothing_and_is_logged(tmp_path):
    logged = []

    class Broken(FakeIo):
        def load(self, path):
            raise RuntimeError("3 : not an smt file")

    store = _store(tmp_path, io=Broken(), logged=logged)
    store.save(LATCH, [("Latch", "body")])
    assert store.load(LATCH) is None
    assert any("not an smt file" in line for line in logged)


def test_a_body_count_other_than_the_names_loads_nothing(tmp_path):
    store = _store(tmp_path)
    store.save(HINGE, [("Hinge top", "1"), ("Hinge bottom", "2")])
    (tmp_path / "partCache" / "1.1.0-abc123def456-Hinge-Pinned.smt").write_text('["1"]', encoding="utf-8")
    assert store.load(HINGE) is None


def test_a_write_leaves_no_temporary_file(tmp_path):
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "body")])
    assert not [name for name in os.listdir(tmp_path / "partCache") if ".tmp" in name]


def test_the_temporary_smt_keeps_its_suffix(tmp_path):
    """Fusion's exportToFile picks the format by the file's suffix"""
    io = FakeIo()
    _store(tmp_path, io=io).save(LATCH, [("Latch", "body")])
    assert io.exported[0].endswith(".smt")


def test_a_failed_export_writes_no_names(tmp_path):
    """The .json is written last: without it nothing is read, so a half-written pair is never taken as whole"""

    class Broken(FakeIo):
        def export(self, bodies, path):
            raise RuntimeError("disk full")

    store = _store(tmp_path, io=Broken())
    with pytest.raises(RuntimeError):
        store.save(LATCH, [("Latch", "body")])
    assert not (tmp_path / "partCache" / "1.1.0-abc123def456-Latch.json").exists()
    assert store.load(LATCH) is None


def test_a_rewrite_replaces_the_old_pair(tmp_path):
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "old")])
    store.save(LATCH, [("Latch", "new")])
    assert store.load(LATCH) == [("Latch", "new")]


# clean-up

def test_clean_up_deletes_old_keys_of_the_own_kinds_only(tmp_path):
    folder = tmp_path / "partCache"
    folder.mkdir()
    for name in ("1.0.0-abc123def456-Latch.smt", "1.1.0-000000000000-Latch.json", "1.1.0-000000000000-Latch.smt.tmp", "1.1.0-000000000000-Hinge-Plain.tmp.smt",
                 "1.1.0-abc123def456-Hinge-Plain.tmp.smt",
                 "readme.txt", "1.1.0-abc123def456-Hinge-Pinned.smt"):
        (folder / name).write_text("x", encoding="utf-8")
    (folder / "sub").mkdir()
    (folder / "sub" / "1.0.0-abc-Latch.smt").write_text("x", encoding="utf-8")
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "body")])
    left = sorted(os.listdir(folder))
    # a temporary of the current key may be another Fusion's write in flight (review round 49): it stays
    assert left == ["1.1.0-abc123def456-Hinge-Pinned.smt", "1.1.0-abc123def456-Hinge-Plain.tmp.smt", "1.1.0-abc123def456-Latch.json",
                    "1.1.0-abc123def456-Latch.smt", "readme.txt", "sub"]
    assert (folder / "sub" / "1.0.0-abc-Latch.smt").exists()


def test_clean_up_touches_nothing_outside_the_folder(tmp_path):
    beside = tmp_path / "1.0.0-abc-Latch.smt"
    beside.write_text("x", encoding="utf-8")
    _store(tmp_path).save(LATCH, [("Latch", "body")])
    assert beside.exists()


def test_a_failed_clean_up_is_only_logged(tmp_path, monkeypatch):
    logged = []
    folder = tmp_path / "partCache"
    folder.mkdir()
    (folder / "1.0.0-abc-Latch.smt").write_text("x", encoding="utf-8")

    def refuse(path):
        raise PermissionError("in use")

    monkeypatch.setattr(partFile.os, "remove", refuse)
    store = _store(tmp_path, logged=logged)
    store.save(LATCH, [("Latch", "body")])
    assert store.load(LATCH) == [("Latch", "body")]
    assert any("in use" in line for line in logged)


# the add-in's store

def test_discard_deletes_the_pair_of_the_key_only(tmp_path):
    store = _store(tmp_path)
    store.save(LATCH, [("Latch", "body")])
    store.save(HINGE, [("Hinge top", "body")])
    store.discard(LATCH)
    assert store.load(LATCH) is None
    assert sorted(os.listdir(tmp_path / "partCache")) == ["1.1.0-abc123def456-Hinge-Pinned.json", "1.1.0-abc123def456-Hinge-Pinned.smt"]


def test_session_key_is_the_manifest_version_and_the_code_stamp():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "Gridkeeper.manifest"), encoding="utf-8") as file:
        version = json.load(file)["version"]
    assert partFile.sessionKey() == (version, partFile.codeStamp(os.path.join(root, "lib", "gridfinityUtils")))


def test_session_store_uses_the_key_it_is_given(tmp_path):
    store = partFile.sessionStore(("9.9.9", "000000000000"), log=lambda message: None)
    assert (store.version, store.stamp) == ("9.9.9", "000000000000")
    assert os.path.normcase(store.folder) == os.path.normcase(os.path.join(partFile.addinFolder(), "partCache"))


def test_the_folder_is_partcache_in_the_add_in_folder():
    assert partFile.FOLDER_NAME == "partCache"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.normcase(partFile.addinFolder()) == os.path.normcase(root)


def test_git_ignores_the_folder():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, ".gitignore"), encoding="utf-8") as file:
        assert "partCache" in [line.strip() for line in file]
