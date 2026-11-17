"""
Tests for the update check (p310): which GitHub release is newer than the running add-in, its short info, and when to
check. Fusion-free, see lib/updateCheck.py
"""

import datetime
import importlib.util
import json
import os


def _load(name):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(project_root, "lib", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


updateCheck = _load("updateCheck")


def release(tag, draft=False, prerelease=False, asset=True, body="Notes"):
    version = tag.split("-v")[-1]
    assets = []
    if asset:
        assets.append({
            "name": f"Gridkeeper-v{version}.zip",
            "browser_download_url": f"https://github.com/Eifel-Joe/Gridkeeper/releases/download/{tag}/Gridkeeper-v{version}.zip",
            "size": 1234,
            "digest": "sha256:abc",
        })
        assets.append({"name": "other.txt", "browser_download_url": "https://x/other.txt", "size": 1})
    return {
        "tag_name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "html_url": f"https://github.com/Eifel-Joe/Gridkeeper/releases/tag/{tag}",
        "body": body,
        "assets": assets,
    }


# versions

def test_parse_version():
    assert updateCheck.parseVersion("1.0.0") == (1, 0, 0)
    assert updateCheck.parseVersion("12.3.40") == (12, 3, 40)
    for text in ["1.0", "v1.0.0", "", "1.0.0.0", "1.0.0-beta", None]:
        assert updateCheck.parseVersion(text) is None


def test_tag_version_only_gridkeeper_tags():
    assert updateCheck.tagVersion("gridkeeper-v1.1.0") == (1, 1, 0)
    for tag in ["v2.4.2.0", "v1.0.0", "gridkeeper-v1.0", "gridkeeper-v1.0.0-beta", "Gridkeeper-v1.0.0", ""]:
        assert updateCheck.tagVersion(tag) is None


# newest release

def test_newest_ignores_original_tags():
    releases = [release("v9.4.2.0"), release("gridkeeper-v1.1.0"), release("gridkeeper-v1.0.0")]
    newest = updateCheck.newestRelease(releases, (1, 0, 0))
    assert newest.tag == "gridkeeper-v1.1.0"
    assert newest.version == (1, 1, 0)
    assert newest.versionText == "1.1.0"
    assert newest.pageUrl == "https://github.com/Eifel-Joe/Gridkeeper/releases/tag/gridkeeper-v1.1.0"
    assert newest.assetUrl.endswith("/gridkeeper-v1.1.0/Gridkeeper-v1.1.0.zip")
    assert newest.assetSize == 1234
    assert newest.assetDigest == "sha256:abc"


def test_numeric_not_text():
    releases = [release("gridkeeper-v1.9.0"), release("gridkeeper-v1.10.0")]
    assert updateCheck.newestRelease(releases, (1, 0, 0)).tag == "gridkeeper-v1.10.0"


def test_skips_draft_and_prerelease():
    releases = [release("gridkeeper-v2.0.0", draft=True), release("gridkeeper-v1.5.0", prerelease=True), release("gridkeeper-v1.1.0")]
    assert updateCheck.newestRelease(releases, (1, 0, 0)).tag == "gridkeeper-v1.1.0"


def test_none_when_not_newer():
    releases = [release("gridkeeper-v1.1.0"), release("gridkeeper-v1.0.0")]
    assert updateCheck.newestRelease(releases, (1, 1, 0)) is None
    assert updateCheck.newestRelease(releases, (2, 0, 0)) is None
    assert updateCheck.newestRelease([], (1, 0, 0)) is None


def test_missing_asset_keeps_release_without_url():
    newest = updateCheck.newestRelease([release("gridkeeper-v1.1.0", asset=False)], (1, 0, 0))
    assert newest.tag == "gridkeeper-v1.1.0"
    assert newest.assetUrl is None
    assert newest.assetSize is None
    assert newest.assetDigest is None


def test_odd_entries_are_skipped():
    releases = [None, "x", {"tag_name": None}, {"tag_name": "gridkeeper-v1.2.0", "html_url": "https://x"}, release("gridkeeper-v1.1.0")]
    newest = updateCheck.newestRelease(releases, (1, 0, 0))
    # an entry without assets and body still counts, it only can't be installed
    assert newest.tag == "gridkeeper-v1.2.0"
    assert newest.assetUrl is None
    assert newest.summary == ""


# short info

def test_summary_first_paragraph_plain():
    body = "The first **Gridkeeper**, see [docs](https://x) and `code`.\r\n\r\nMore"
    assert updateCheck.summary(body) == "The first Gridkeeper, see docs and code."


def test_summary_joins_lines_of_the_paragraph():
    assert updateCheck.summary("Line one\r\nline two\r\n\r\nNext") == "Line one line two"


def test_summary_skips_leading_heading_and_blank_lines():
    assert updateCheck.summary("\n\n## What's new\n\nBoxes after Pred.") == "Boxes after Pred."


def test_summary_drops_heading_lines_not_the_paragraph():
    assert updateCheck.summary("## What's new\n- Boxes after Pred\n- Magnet size") == "- Boxes after Pred - Magnet size"


def test_only_github_links():
    entry = release("gridkeeper-v1.1.0")
    entry["html_url"] = "javascript:alert(1)"
    entry["assets"][0]["browser_download_url"] = "http://evil.example/Gridkeeper-v1.1.0.zip"
    newest = updateCheck.newestRelease([entry], (1, 0, 0))
    assert newest.pageUrl == ""
    assert newest.assetUrl is None


def test_summary_cut():
    text = updateCheck.summary("a" * 400)
    assert len(text) == 300
    assert text.endswith("…")


def test_summary_empty():
    assert updateCheck.summary(None) == ""
    assert updateCheck.summary("") == ""
    assert updateCheck.summary("\r\n\r\n") == ""


# when to check

def test_due_once_a_day():
    today = datetime.date(2026, 11, 17)
    assert not updateCheck.isDue({"checkAtStartup": True, "lastCheck": "2026-11-17"}, today)
    assert updateCheck.isDue({"checkAtStartup": True, "lastCheck": "2026-11-16"}, today)
    assert updateCheck.isDue({"checkAtStartup": True}, today)
    assert updateCheck.isDue({"checkAtStartup": True, "lastCheck": "garbage"}, today)
    assert not updateCheck.isDue({"checkAtStartup": False}, today)


def test_settings_defaults_and_round_trip(tmp_path):
    path = str(tmp_path / "updateConfig" / "update.json")
    assert updateCheck.readSettings(path) == {"checkAtStartup": True}
    assert updateCheck.writeSettings(path, {"checkAtStartup": False, "lastCheck": "2026-11-17"})
    assert updateCheck.readSettings(path) == {"checkAtStartup": False, "lastCheck": "2026-11-17"}


def test_settings_broken_file_defaults(tmp_path):
    path = tmp_path / "update.json"
    for text in ["not json", "[1, 2]", '{"checkAtStartup": "yes"}']:
        path.write_text(text)
        assert updateCheck.readSettings(str(path))["checkAtStartup"] is True


def test_manifest_version(tmp_path):
    (tmp_path / "Gridkeeper.manifest").write_text('{\n\t"type":\t"addin",\n\t"version":\t"1.0.0",\n\t"runOnStartup":\ttrue\n}')
    assert updateCheck.manifestVersion(str(tmp_path)) == (1, 0, 0)


def test_manifest_version_unreadable(tmp_path):
    assert updateCheck.manifestVersion(str(tmp_path)) is None
    (tmp_path / "Gridkeeper.manifest").write_text('{"version": "1.0"}')
    assert updateCheck.manifestVersion(str(tmp_path)) is None


def test_manifest_version_of_the_repo():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(project_root, "Gridkeeper.manifest"), encoding="utf-8") as file:
        expected = updateCheck.parseVersion(json.load(file)["version"])
    assert expected is not None
    assert updateCheck.manifestVersion(project_root) == expected


# what the dialogs say

def test_dialog_html_update():
    newest = updateCheck.newestRelease([release("gridkeeper-v1.1.0", body="Boxes & <b>lids</b>.")], (1, 0, 0))
    text = updateCheck.dialogHtml(newest, (1, 0, 0), gitCheckout=False)
    assert "Gridkeeper 1.1.0 is available (you have 1.0.0)." in text
    assert '<a href="https://github.com/Eifel-Joe/Gridkeeper/releases/tag/gridkeeper-v1.1.0">Release notes</a>' in text
    # the release text is the release author's, shown as text
    assert "Boxes &amp; &lt;b&gt;lids&lt;/b&gt;." in text
    assert "git checkout" not in text


def test_dialog_html_git_checkout():
    newest = updateCheck.newestRelease([release("gridkeeper-v1.1.0")], (1, 0, 0))
    text = updateCheck.dialogHtml(newest, (1, 0, 0), gitCheckout=True)
    assert "This add-in runs from a git checkout, update it with git." in text
    assert "Release notes" in text


def test_dialog_html_without_zip():
    newest = updateCheck.newestRelease([release("gridkeeper-v1.1.0", asset=False)], (1, 0, 0))
    text = updateCheck.dialogHtml(newest, (1, 0, 0), gitCheckout=False)
    assert "has no ZIP file" in text


def test_dialog_html_quotes_in_url():
    newest = updateCheck.Release((1, 1, 0), "gridkeeper-v1.1.0", 'https://x/"><script>', "", None, None, None)
    assert '"><script>' not in updateCheck.dialogHtml(newest, (1, 0, 0), gitCheckout=False)


def test_version_line():
    assert updateCheck.versionLine((1, 0, 0), (1, 0, 0)) == "Running Gridkeeper 1.0.0."
    assert updateCheck.versionLine((1, 0, 0), (1, 1, 0)) == (
        "Running Gridkeeper 1.0.0, installed 1.1.0. Restart Fusion to use 1.1.0.")
    assert updateCheck.versionLine(None, None) == "Running Gridkeeper, its version is unknown."


def test_success_text():
    newest = updateCheck.newestRelease([release("gridkeeper-v1.1.0")], (1, 0, 0))
    # spec E11.7; until Fusion restarts the old code runs with the new files on disk, it says so (review finding 5)
    assert updateCheck.successText(newest) == (
        "Gridkeeper 1.1.0 is installed. Restart Fusion to load it, until then the old version runs.")


# asking GitHub

import io
import socket
import urllib.error


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fakeUrlopen(payload=None, error=None, calls=None):
    def urlopen(request, timeout=None):
        if calls is not None:
            calls.append((request, timeout))
        if error is not None:
            raise error
        return FakeResponse(payload)
    return urlopen


def test_request_headers_only_neutral():
    calls = []
    logs = []
    result = updateCheck.fetchReleases(urlopen=fakeUrlopen(b"[]", calls=calls), log=logs.append)
    assert result == []
    (request, timeout) = calls[0]
    assert request.full_url == "https://api.github.com/repos/Eifel-Joe/Gridkeeper/releases?per_page=30"
    assert timeout == 10
    assert dict(request.header_items()) == {"User-agent": "Gridkeeper-update-check", "Accept": "application/vnd.github+json"}
    assert request.data is None


def test_fetch_errors_are_none():
    for error in [urllib.error.URLError("offline"), socket.timeout("slow"), TimeoutError("slow"),
                  urllib.error.HTTPError("https://x", 403, "rate limit", {}, None), ConnectionResetError()]:
        logs = []
        assert updateCheck.fetchReleases(urlopen=fakeUrlopen(error=error), log=logs.append) is None
        assert len(logs) == 1
    for payload in [b"not json", b'{"message": "Not Found"}', b"\xff\xfe"]:
        logs = []
        assert updateCheck.fetchReleases(urlopen=fakeUrlopen(payload), log=logs.append) is None
        assert len(logs) == 1


def test_fetch_limits_the_answer():
    logs = []
    assert updateCheck.fetchReleases(urlopen=fakeUrlopen(b"[" + b"1," * 3_000_000 + b"1]"), log=logs.append) is None
    assert len(logs) == 1


def test_fetch_bad_url_is_none():
    logs = []
    assert updateCheck.fetchReleases(url="not a url", log=logs.append) is None
    assert len(logs) == 1


def _addin(tmp_path, version="1.0.0"):
    (tmp_path / "Gridkeeper.manifest").write_text(json.dumps({"version": version}))
    return str(tmp_path)


def test_check_for_update(tmp_path):
    releases = [release("gridkeeper-v1.1.0"), release("gridkeeper-v1.0.0")]
    newest = updateCheck.checkForUpdate(_addin(tmp_path), fetch=lambda: releases, log=lambda m: None)
    assert newest.versionText == "1.1.0"
    assert updateCheck.checkForUpdate(_addin(tmp_path, "1.1.0"), fetch=lambda: releases, log=lambda m: None) is None


def test_check_offline_none(tmp_path):
    assert updateCheck.checkForUpdate(_addin(tmp_path), fetch=lambda: None, log=lambda m: None) is None


def test_check_unreadable_manifest_none(tmp_path):
    logs = []
    asked = []
    result = updateCheck.checkForUpdate(_addin(tmp_path, "dev"), fetch=lambda: asked.append(1) or [release("gridkeeper-v1.1.0")], log=logs.append)
    assert result is None
    # no question to GitHub without a version to compare with
    assert asked == []
    assert len(logs) == 1
