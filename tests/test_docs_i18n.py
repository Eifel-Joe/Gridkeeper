"""
The German docs (round 60): every page has a German twin page.de.md, built by mkdocs-static-i18n under /de/. A picture
with a German version name.de.png is published as /de/assets/.../name.png. Markdown pictures are found by the plugin
(the German version, else the English one), raw HTML (the <picture> of the animations) is not: a German page points one
folder higher for the English picture, to /assets/..., and to /de/assets/... where the German version exists.
"""

import os
import posixpath
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
# maintainers' list of pictures, not a page of the site (mkdocs.yml exclude_docs)
NOT_PAGES = {"assets/images/NEEDED.md"}
RAW_REFERENCE = re.compile(r'(?:src|srcset)="([^"]+)"')
MARKDOWN_PICTURE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')


def _pages():
    pages = []
    for (folder, _, names) in os.walk(DOCS):
        for name in names:
            path = os.path.relpath(os.path.join(folder, name), DOCS).replace(os.sep, "/")
            if name.endswith(".md") and not name.endswith(".de.md") and path not in NOT_PAGES:
                pages.append(path)
    return sorted(pages)


PAGES = _pages()


def _germanPages():
    return [page[:-3] + ".de.md" for page in PAGES if os.path.exists(os.path.join(DOCS, page[:-3] + ".de.md"))]


def _url(page: str, german: bool) -> str:
    """The folder the built page is served from, use_directory_urls: bins/size.md is /bins/size/, index.md is /"""
    path = page[:-6] if page.endswith(".de.md") else page[:-3]
    folder = "/" + (posixpath.dirname(path) if path.endswith("index") else path)
    return ("/de" if german else "") + folder.rstrip("/") + "/"


def _localized(path: str) -> str:
    (stem, extension) = posixpath.splitext(path)
    return f"{stem}.de{extension}"


@pytest.mark.parametrize("page", PAGES)
def test_every_page_has_a_german_twin(page):
    assert os.path.exists(os.path.join(DOCS, page[:-3] + ".de.md")), f"{page} has no German page"


@pytest.mark.parametrize("page", _germanPages())
def test_raw_html_pictures_of_german_pages_are_found(page):
    with open(os.path.join(DOCS, page), encoding="utf-8") as file:
        text = file.read()
    base = _url(page, german=True)
    for reference in RAW_REFERENCE.findall(text):
        if "://" in reference:
            continue
        target = posixpath.normpath(posixpath.join(base, reference))
        if target.startswith("/de/"):
            source = _localized(target[len("/de/"):])
            assert os.path.exists(os.path.join(DOCS, source)), (
                f"{page}: {reference} needs the German {source}, else point one folder higher to the English one")
        else:
            assert os.path.exists(os.path.join(DOCS, target.lstrip("/"))), f"{page}: {reference} not found"
            assert not os.path.exists(os.path.join(DOCS, _localized(target.lstrip("/")))), (
                f"{page}: {reference} has a German version, point to it under /de/")


@pytest.mark.parametrize("page", _germanPages())
def test_markdown_pictures_of_german_pages_exist(page):
    with open(os.path.join(DOCS, page), encoding="utf-8") as file:
        text = file.read()
    for reference in MARKDOWN_PICTURE.findall(text):
        if "://" in reference:
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(page), reference))
        assert os.path.exists(os.path.join(DOCS, target)), f"{page}: {reference} not found"


ANCHOR_LINK = re.compile(r'\]\(([^)\s#]*)#([\w-]+)\)')
HEADING = re.compile(r'^#{1,6}\s+(.*?)\s*$', re.MULTILINE)
EXPLICIT_ID = re.compile(r'\{[^}]*#([\w-]+)[^}]*\}|\bid="([\w-]+)"')


def _slug(text: str) -> str:
    """Python-Markdown's toc slugify, as mkdocs makes heading ids"""
    import unicodedata
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def _ids(page: str) -> set[str]:
    with open(os.path.join(DOCS, page), encoding="utf-8") as file:
        text = file.read()
    ids = {first or second for (first, second) in EXPLICIT_ID.findall(text)}
    for heading in HEADING.findall(text):
        if "{" not in heading:
            ids.add(_slug(re.sub(r"[*_`]|\[([^\]]*)\]\([^)]*\)", r"\1", heading)))
    return ids


@pytest.mark.parametrize("page", _germanPages())
def test_anchor_links_of_german_pages_lead_to_a_heading(page):
    """A German heading keeps the English id ({ #id }) where other pages link to it"""
    with open(os.path.join(DOCS, page), encoding="utf-8") as file:
        text = file.read()
    for (path, anchor) in ANCHOR_LINK.findall(text):
        if "://" in path:
            continue
        english = posixpath.normpath(posixpath.join(posixpath.dirname(page), path)) if path else page[:-6] + ".md"
        german = english[:-3] + ".de.md"
        target = german if os.path.exists(os.path.join(DOCS, german)) else english
        assert anchor in _ids(target), f"{page}: #{anchor} isn't a heading of {target}"


def test_german_pictures_have_an_english_original():
    """name.de.png only beside name.png, so English pages never miss a picture"""
    for (folder, _, names) in os.walk(os.path.join(DOCS, "assets")):
        for name in names:
            match = re.match(r"(.+)\.de(\.\w+)$", name)
            if match:
                assert os.path.exists(os.path.join(folder, match.group(1) + match.group(2))), name
