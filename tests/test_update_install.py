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
