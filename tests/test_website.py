from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        if tag == "img" and values.get("src"):
            self.images.append(str(values["src"]))
        if tag == "script" and values.get("src"):
            self.scripts.append(str(values["src"]))
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.stylesheets.append(str(values["href"]))


def test_download_website_structure_and_assets():
    parser = PageParser()
    parser.feed((DOCS / "index.html").read_text(encoding="utf-8"))

    assert len(parser.ids) == len(set(parser.ids))
    assert {
        "version-label", "windows-download", "windows-zip-download",
        "mac-download", "mac-zip-download", "release-meta", "release-link",
    } <= set(parser.ids)
    assert parser.scripts == ["app.js"]
    assert parser.stylesheets == ["styles.css"]
    assert "app_icon.png" in parser.images
    assert all((DOCS / asset).is_file() for asset in parser.scripts + parser.stylesheets + parser.images)
    assert any(link.endswith("SimplyAbrechnung-Windows-Setup.exe") for link in parser.links)
    assert any(link.endswith("SimplyAbrechnung-macOS.pkg") for link in parser.links)


def test_release_script_updates_both_platform_downloads():
    script = (DOCS / "app.js").read_text(encoding="utf-8")
    assert "api.github.com/repos/${repository}/releases" in script
    assert "SimplyAbrechnung-Windows-Setup.exe" in script
    assert "SimplyAbrechnung-Windows.zip" in script
    assert "SimplyAbrechnung-macOS.pkg" in script
    assert "SimplyAbrechnung-macOS.zip" in script
    assert "browser_download_url" in script


def test_build_workflow_publishes_installers_and_zip_archives():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    for asset in [
        "SimplyAbrechnung-Windows-Setup.exe",
        "SimplyAbrechnung-Windows.zip",
        "SimplyAbrechnung-macOS.pkg",
        "SimplyAbrechnung-macOS.zip",
    ]:
        assert asset in workflow
    assert "Compress-Archive" in workflow
    assert "ditto -c -k --keepParent" in workflow
