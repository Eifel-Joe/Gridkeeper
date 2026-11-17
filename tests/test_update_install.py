"""
Tests for installing an update (p310): the release ZIP is downloaded and checked, unpacked, the user's files carried
over, and the add-in folder swapped with a way back on every failure. Fusion-free, see lib/updateInstall.py
"""

import datetime
import hashlib
import importlib.util
import io
import json
import os
import zipfile

import pytest


def _load(name):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(project_root, "lib", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


updateInstall = _load("updateInstall")
UpdateError = updateInstall.UpdateError


def manifest(version):
    return json.dumps({"type": "addin", "version": version}).encode()


def zipBytes(entries: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for (name, data) in entries.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def releaseEntries(version="1.1.0", extra=None):
    entries = {
        "Gridkeeper/Gridkeeper.manifest": manifest(version),
        "Gridkeeper/Gridkeeper.py": b"# new\n",
        "Gridkeeper/lib/new.py": b"# new module\n",
        "Gridkeeper/lib/symbols/hardware/nut.svg": b"<svg/>",
    }
    entries.update(extra or {})
    return entries


def writeZip(tmp_path, entries, name="Gridkeeper-v1.1.0.zip"):
    path = tmp_path / name
    path.write_bytes(zipBytes(entries))
    return str(path)


def digestOf(path):
    with open(path, "rb") as file:
        return "sha256:" + hashlib.sha256(file.read()).hexdigest()


# checking the ZIP

def test_verify_ok(tmp_path):
    # 7-Zip in release.yml writes folder entries too
    path = writeZip(tmp_path, releaseEntries(extra={"Gridkeeper/": b"", "Gridkeeper/lib/": b""}))
    updateInstall.verifyZip(path, (1, 1, 0), digestOf(path), os.path.getsize(path))


def test_wrong_digest(tmp_path):
    path = writeZip(tmp_path, releaseEntries())
    with pytest.raises(UpdateError, match="checksum"):
        updateInstall.verifyZip(path, (1, 1, 0), "sha256:" + "0" * 64, None)


def test_unknown_digest_kind_falls_back_to_size(tmp_path):
    path = writeZip(tmp_path, releaseEntries())
    updateInstall.verifyZip(path, (1, 1, 0), "md5:abc", os.path.getsize(path))
    with pytest.raises(UpdateError):
        updateInstall.verifyZip(path, (1, 1, 0), "md5:abc", None)


def test_no_digest_size_must_match(tmp_path):
    path = writeZip(tmp_path, releaseEntries())
    updateInstall.verifyZip(path, (1, 1, 0), None, os.path.getsize(path))
    with pytest.raises(UpdateError, match="size"):
        updateInstall.verifyZip(path, (1, 1, 0), None, os.path.getsize(path) + 1)
    with pytest.raises(UpdateError):
        updateInstall.verifyZip(path, (1, 1, 0), None, None)


def test_not_a_zip(tmp_path):
    path = tmp_path / "x.zip"
    path.write_bytes(b"not a zip")
    with pytest.raises(UpdateError):
        updateInstall.verifyZip(str(path), (1, 1, 0), digestOf(path), None)


@pytest.mark.parametrize("name", [
    "Gridkeeper/../evil.py",
    "/Gridkeeper/abs.py",
    "Gridkeeper\\..\\evil.py",
    "C:/Gridkeeper/x.py",
    "Gridkeeper/C:/x.py",
    "Other/x.py",
    "top.txt",
])
def test_rejects_unsafe_or_foreign_paths(tmp_path, name):
    path = writeZip(tmp_path, releaseEntries(extra={name: b"x"}))
    with pytest.raises(UpdateError):
        updateInstall.verifyZip(path, (1, 1, 0), digestOf(path), None)


def test_rejects_wrong_manifest_version(tmp_path):
    path = writeZip(tmp_path, releaseEntries(version="1.0.9"))
    with pytest.raises(UpdateError, match="1.0.9"):
        updateInstall.verifyZip(path, (1, 1, 0), digestOf(path), None)


def test_rejects_missing_manifest_or_py(tmp_path):
    for missing in ["Gridkeeper/Gridkeeper.manifest", "Gridkeeper/Gridkeeper.py"]:
        entries = releaseEntries()
        del entries[missing]
        path = writeZip(tmp_path, entries)
        with pytest.raises(UpdateError):
            updateInstall.verifyZip(path, (1, 1, 0), digestOf(path), None)


def test_rejects_too_big_uncompressed(tmp_path):
    path = writeZip(tmp_path, releaseEntries(extra={"Gridkeeper/big.bin": b"0" * 5000}))
    with pytest.raises(UpdateError, match="large"):
        updateInstall.verifyZip(path, (1, 1, 0), digestOf(path), None, maxUnpacked=4000)


# downloading

class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fakeUrlopen(payload=b"", error=None, calls=None):
    def urlopen(request, timeout=None):
        if calls is not None:
            calls.append((request, timeout))
        if error is not None:
            raise error
        return FakeResponse(payload)
    return urlopen


def test_download(tmp_path):
    calls = []
    target = str(tmp_path / "a.zip")
    updateInstall.download("https://x/a.zip", target, urlopen=fakeUrlopen(b"abc", calls=calls))
    assert open(target, "rb").read() == b"abc"
    (request, timeout) = calls[0]
    assert timeout == 60
    assert dict(request.header_items()) == {"User-agent": "Gridkeeper-update-check"}


def test_download_bad_url(tmp_path):
    # urlopen isn't reached, the request itself refuses it
    with pytest.raises(UpdateError, match="download"):
        updateInstall.download("not a url", str(tmp_path / "a.zip"))


def test_download_reports_progress(tmp_path):
    seen = []
    updateInstall.download("https://x/a.zip", str(tmp_path / "a.zip"), urlopen=fakeUrlopen(b"0" * 150000), progress=seen.append)
    assert seen[-1] == 150000
    assert seen == sorted(seen)
    assert len(seen) >= 2


def test_download_stops_over_limit(tmp_path):
    target = str(tmp_path / "a.zip")
    with pytest.raises(UpdateError, match="large"):
        updateInstall.download("https://x/a.zip", target, urlopen=fakeUrlopen(b"0" * 100), limit=50)


def test_download_error(tmp_path):
    with pytest.raises(UpdateError, match="download"):
        updateInstall.download("https://x/a.zip", str(tmp_path / "a.zip"), urlopen=fakeUrlopen(error=OSError("offline")))


def test_extract(tmp_path):
    path = writeZip(tmp_path, releaseEntries())
    folder = updateInstall.extract(path, str(tmp_path / "new"))
    assert folder == str(tmp_path / "new" / "Gridkeeper")
    assert open(os.path.join(folder, "Gridkeeper.py"), "rb").read() == b"# new\n"


# git checkouts

def test_git_dir_and_file(tmp_path):
    assert not updateInstall.isGitCheckout(str(tmp_path))
    (tmp_path / ".git").mkdir()
    assert updateInstall.isGitCheckout(str(tmp_path))
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    # a git worktree has a .git file pointing to the repository
    (worktree / ".git").write_text("gitdir: D:/repo/.git/worktrees/x")
    assert updateInstall.isGitCheckout(str(worktree))


# swapping the add-in folder

def tree(folder) -> dict:
    """relative path -> content of every file below folder"""
    files = {}
    for (root, _, names) in os.walk(folder):
        for name in names:
            path = os.path.join(root, name)
            with open(path, "rb") as file:
                files[os.path.relpath(path, folder).replace(os.sep, "/")] = file.read()
    return files


def makeTree(folder, files: dict):
    for (name, data) in files.items():
        path = os.path.join(folder, *name.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(data)
    return str(folder)


OLD = {
    "Gridkeeper.manifest": manifest("1.0.0"),
    "Gridkeeper.py": b"# old\n",
    "lib/gone.py": b"# removed in the new version\n",
    "lib/__pycache__/gone.cpython-314.pyc": b"pyc",
    "lib/symbols/hardware/nut.svg": b"<svg old/>",
    "lib/symbols/hardware/my.svg": b"<svg mine/>",
    "commands/commandCreateBin/commandConfig/defaults.json": b"{}",
    "commands/commandCreateBin/commandConfig/config.ini": b"[UI]",
    "updateConfig/update.json": b'{"checkAtStartup": false}',
}
NEW = {
    "Gridkeeper.manifest": manifest("1.1.0"),
    "Gridkeeper.py": b"# new\n",
    "lib/new.py": b"# new module\n",
    "lib/symbols/hardware/nut.svg": b"<svg new/>",
}


def test_carries_user_files(tmp_path):
    old = makeTree(tmp_path / "old", OLD)
    new = makeTree(tmp_path / "new", NEW)
    carried = updateInstall.carryOver(old, new)
    assert sorted(carried) == [
        "commands/commandCreateBin/commandConfig/config.ini",
        "commands/commandCreateBin/commandConfig/defaults.json",
        "lib/symbols/hardware/my.svg",
        "updateConfig/update.json",
    ]
    result = tree(new)
    assert result["lib/symbols/hardware/my.svg"] == b"<svg mine/>"
    # the new version's files win, code and caches of the old one stay behind
    assert result["lib/symbols/hardware/nut.svg"] == b"<svg new/>"
    assert result["Gridkeeper.py"] == b"# new\n"
    assert "lib/gone.py" not in result
    assert not any("__pycache__" in name for name in result)


def setUpSwap(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    new = makeTree(tmp_path / "addins" / ".gridkeeper-update" / "new" / "Gridkeeper", {**NEW, "updateConfig/update.json": b"{}"})
    backup = str(tmp_path / "addins" / ".gridkeeper-update" / "backup-1" / "Gridkeeper")
    os.makedirs(os.path.dirname(backup))
    return (addin, new, backup)


def test_swap_renames(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    expected = tree(new)
    assert updateInstall.swap(addin, new, backup) == "renamed"
    assert tree(addin) == expected
    assert tree(backup) == OLD


def failingAt(calls: list, failAt: int, real):
    """real, but raising PermissionError on its failAt-th call (1-based)"""
    def call(*args, **kwargs):
        calls.append(args)
        if len(calls) == failAt:
            raise PermissionError("in use")
        return real(*args, **kwargs)
    return call


def test_second_rename_fails_restores(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    with pytest.raises(UpdateError):
        updateInstall.swap(addin, new, backup, rename=failingAt([], 2, os.replace))
    assert tree(addin) == OLD


def test_first_rename_fails_copies(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    expected = tree(new)
    assert updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace)) == "copied"
    # old code files the new version doesn't have are gone as after a rename
    assert tree(addin) == expected
    # the backup is the whole old folder
    assert tree(backup) == OLD


def test_backup_copy_fails_nothing_changes(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    import shutil

    def copyFile(source, target, *args, **kwargs):
        # the backup copy breaks after a few files
        if os.path.normpath(target).startswith(os.path.normpath(backup)) and len(os.listdir(os.path.dirname(target))) >= 1:
            raise PermissionError("disk full")
        return shutil.copy2(source, target, *args, **kwargs)

    with pytest.raises(UpdateError):
        updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace), copyFile=copyFile)
    assert tree(addin) == OLD
    # no half backup is left
    assert not os.path.exists(backup)


def test_copy_fails_restores(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    import shutil
    fromNew = []

    def copyFile(source, target, *args, **kwargs):
        # copying the new version over the add-in folder breaks after two files
        if os.path.normpath(source).startswith(os.path.normpath(new)):
            fromNew.append(source)
            if len(fromNew) == 3:
                raise PermissionError("in use")
        return shutil.copy2(source, target, *args, **kwargs)

    with pytest.raises(UpdateError):
        updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace), copyFile=copyFile)
    assert tree(addin) == OLD


def test_swap_fails_without_way_back_names_backup(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    calls = []

    def rename(source, target):
        calls.append(source)
        if len(calls) >= 2:
            raise PermissionError("in use")
        return os.replace(source, target)

    with pytest.raises(UpdateError) as info:
        updateInstall.swap(addin, new, backup, rename=rename)
    assert backup in str(info.value)


# the whole update

class Release:
    def __init__(self, version, assetUrl, assetSize, assetDigest):
        self.version = version
        self.assetUrl = assetUrl
        self.assetSize = assetSize
        self.assetDigest = assetDigest


def releaseFor(payload, digest=True):
    return Release((1, 1, 0), "https://x/Gridkeeper-v1.1.0.zip", len(payload),
                   "sha256:" + hashlib.sha256(payload).hexdigest() if digest else None)


def test_install_end_to_end(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    way = updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload),
                                now=lambda: datetime.datetime(2026, 11, 17, 12, 0, 0))
    assert way == "renamed"
    result = tree(addin)
    assert result["Gridkeeper.py"] == b"# new\n"
    assert result["updateConfig/update.json"] == b'{"checkAtStartup": false}'
    assert result["commands/commandCreateBin/commandConfig/defaults.json"] == b"{}"
    work = tmp_path / "addins" / ".gridkeeper-update"
    # only the backup is left
    assert sorted(os.listdir(work)) == ["backup-20261117-120000"]
    assert tree(work / "backup-20261117-120000" / "Gridkeeper") == OLD


def test_install_twice_same_second(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    now = lambda: datetime.datetime(2026, 11, 17, 12, 0, 0)
    updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload), now=now)
    updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload), now=now)
    assert tree(addin)["Gridkeeper.py"] == b"# new\n"


def test_install_bad_download_leaves_addin(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    release = Release((1, 1, 0), "https://x/Gridkeeper-v1.1.0.zip", None, "sha256:" + "0" * 64)
    with pytest.raises(UpdateError):
        updateInstall.install(release, addin, urlopen=fakeUrlopen(payload))
    assert tree(addin) == OLD
    assert os.listdir(tmp_path / "addins" / ".gridkeeper-update") == []


def test_install_unexpected_error_is_update_error(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)

    def urlopen(request, timeout=None):
        raise RuntimeError("something nobody thought of")

    with pytest.raises(UpdateError):
        updateInstall.install(Release((1, 1, 0), "https://x/Gridkeeper-v1.1.0.zip", 1, None), addin, urlopen=urlopen)
    with pytest.raises(UpdateError):
        updateInstall.install(Release((1, 1, 0), "not a url", 1, None), addin)
    assert tree(addin) == OLD


def test_install_clears_leftovers_of_a_broken_run(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    makeTree(tmp_path / "addins" / ".gridkeeper-update" / "new" / "Gridkeeper", {"stale.py": b"x"})
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload))
    assert "stale.py" not in tree(addin)


def test_refuses_git_dir_and_file(tmp_path):
    for (name, make) in [("clone", lambda p: p.mkdir()), ("worktree", lambda p: p.write_text("gitdir: x"))]:
        addin = makeTree(tmp_path / name / "Gridkeeper", OLD)
        make(tmp_path / name / "Gridkeeper" / ".git")
        before = tree(addin)
        asked = []
        with pytest.raises(UpdateError, match="git"):
            updateInstall.install(Release((1, 1, 0), "https://x", 1, None), addin, urlopen=fakeUrlopen(b"", calls=asked))
        assert tree(addin) == before
        assert asked == []


def test_refuses_release_without_zip(tmp_path):
    addin = makeTree(tmp_path / "Gridkeeper", OLD)
    with pytest.raises(UpdateError):
        updateInstall.install(Release((1, 1, 0), None, None, None), addin, urlopen=fakeUrlopen(b""))


def test_cleanup_keeps_newest_backup(tmp_path):
    addin = makeTree(tmp_path / "Gridkeeper", OLD)
    work = tmp_path / ".gridkeeper-update"
    for name in ["backup-20261101-080000", "backup-20261117-120000", "backup-20261110-090000"]:
        makeTree(work / name / "Gridkeeper", {"x": b"x"})
    makeTree(work / "new" / "Gridkeeper", {"x": b"x"})
    (work / "Gridkeeper-v1.1.0.zip").write_bytes(b"zip")
    updateInstall.cleanupBackups(addin)
    # new/ and the ZIP may belong to an update running right now, install clears them itself (review finding 4)
    assert sorted(os.listdir(work)) == ["Gridkeeper-v1.1.0.zip", "backup-20261117-120000", "new"]


def test_cleanup_orders_backups_of_one_second_by_number(tmp_path):
    addin = makeTree(tmp_path / "Gridkeeper", OLD)
    work = tmp_path / ".gridkeeper-update"
    for name in ["backup-20261117-120000", "backup-20261117-120000-2", "backup-20261117-120000-10"]:
        makeTree(work / name / "Gridkeeper", {"x": b"x"})
    updateInstall.cleanupBackups(addin)
    assert os.listdir(work) == ["backup-20261117-120000-10"]


def test_install_waits_for_the_lock(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    asked = []
    with updateInstall.WORK_LOCK:
        with pytest.raises(UpdateError, match="tidying up"):
            updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload, calls=asked), lockTimeout=0.1)
    assert asked == []
    assert tree(addin) == OLD


def test_cleanup_waits_for_a_running_install(tmp_path):
    import threading
    addin = makeTree(tmp_path / "Gridkeeper", OLD)
    work = tmp_path / ".gridkeeper-update"
    for name in ["backup-20261101-080000", "backup-20261117-120000"]:
        makeTree(work / name / "Gridkeeper", {"x": b"x"})
    with updateInstall.WORK_LOCK:
        cleanup = threading.Thread(target=updateInstall.cleanupBackups, args=(addin,))
        cleanup.start()
        cleanup.join(0.3)
        # still waiting, nothing deleted while the lock is held
        assert cleanup.is_alive()
        assert len(os.listdir(work)) == 2
    cleanup.join(5)
    assert os.listdir(work) == ["backup-20261117-120000"]


def test_copy_path_keeps_new_files_whose_folder_differs_in_case(tmp_path):
    # Windows keeps the old folder's spelling when the new version is copied over it, prune must not take the new
    # version's files in it for leftovers (second review, finding 1)
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", {"Gridkeeper.py": b"# old\n", "lib/Symbols/Nut.svg": b"<svg old/>"})
    new = makeTree(tmp_path / "addins" / ".gridkeeper-update" / "new" / "Gridkeeper", {"Gridkeeper.py": b"# new\n", "lib/symbols/nut.svg": b"<svg new/>"})
    backup = str(tmp_path / "addins" / ".gridkeeper-update" / "backup-1" / "Gridkeeper")
    os.makedirs(os.path.dirname(backup))
    assert updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace)) == "copied"
    result = tree(addin)
    nuts = [content for (name, content) in result.items() if os.path.normcase(name) == os.path.normcase("lib/symbols/nut.svg")]
    assert nuts == [b"<svg new/>"]
    assert result["Gridkeeper.py"] == b"# new\n"


def test_copy_path_old_version_not_back_names_backup(tmp_path):
    (addin, new, backup) = setUpSwap(tmp_path)
    import shutil
    lockedSvg = os.path.normcase(os.path.join(addin, "lib", "symbols", "hardware", "nut.svg"))
    addinPy = os.path.normcase(os.path.join(addin, "Gridkeeper.py"))

    def copyFile(source, target, *args, **kwargs):
        # the forward copy breaks on the svg after Gridkeeper.py is already new, the way back can't write Gridkeeper.py
        if os.path.normcase(target) == lockedSvg:
            raise PermissionError("in use")
        if os.path.normcase(target) == addinPy and os.path.normcase(source).startswith(os.path.normcase(backup)):
            raise PermissionError("in use")
        return shutil.copy2(source, target, *args, **kwargs)

    with pytest.raises(UpdateError) as info:
        updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace), copyFile=copyFile)
    assert "not back" in str(info.value)
    assert backup in str(info.value)
    assert tree(backup) == OLD


def test_carry_over_ignores_case_of_the_new_version(tmp_path):
    old = makeTree(tmp_path / "old", {"lib/Symbols/Nut.svg": b"<svg old/>"})
    new = makeTree(tmp_path / "new", {"lib/symbols/nut.svg": b"<svg new/>"})
    assert updateInstall.carryOver(old, new) == []
    assert tree(new) == {"lib/symbols/nut.svg": b"<svg new/>"}


def test_copy_fails_both_ways_on_a_locked_file(tmp_path):
    # Windows: a file Fusion holds open can be neither overwritten nor written back, but it never changed
    (addin, new, backup) = setUpSwap(tmp_path)
    import shutil
    locked = os.path.normcase(os.path.join(addin, "lib", "symbols", "hardware", "nut.svg"))

    def copyFile(source, target, *args, **kwargs):
        if os.path.normcase(target) == locked:
            raise PermissionError("in use")
        return shutil.copy2(source, target, *args, **kwargs)

    with pytest.raises(UpdateError) as info:
        updateInstall.swap(addin, new, backup, rename=failingAt([], 1, os.replace), copyFile=copyFile)
    assert "The old version is back" in str(info.value)
    assert tree(addin) == OLD


def test_install_end_to_end_by_copy(tmp_path):
    addin = makeTree(tmp_path / "addins" / "Gridkeeper", OLD)
    payload = zipBytes({f"Gridkeeper/{name}": data for (name, data) in NEW.items()})
    way = updateInstall.install(releaseFor(payload), addin, urlopen=fakeUrlopen(payload), rename=failingAt([], 1, os.replace))
    assert way == "copied"
    result = tree(addin)
    assert result["Gridkeeper.py"] == b"# new\n"
    assert "lib/gone.py" not in result
    assert result["commands/commandCreateBin/commandConfig/defaults.json"] == b"{}"


def test_cleanup_without_work_folder(tmp_path):
    updateInstall.cleanupBackups(makeTree(tmp_path / "Gridkeeper", OLD))
