#!/usr/bin/env python3
"""Validate the public download page's contract."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "index.html").read_text()
CSS = (ROOT / "get.css").read_text()


def require(value: str, text: str = PAGE) -> None:
    assert value in text, f"missing required content: {value}"


# Identity, discovery and analytics
require('<link rel="canonical" href="https://get.corestory.ai/">')
require('assets/brand/design-system/assets/Logos/CoreStory-Logo-Rev-Gold-RGB.svg')
require('https://get.corestory.ai/.well-known/agent-skills/index.json')
require('https://github.com/CoreStoryAI/agent-skills')
require('href="container/"')
require("GTM-MVPGQKQ2")
require("googletagmanager.com/ns.html?id=GTM-MVPGQKQ2")

# Download block: one button per platform, each tagged for analytics
for os_name in ["mac", "linux", "windows"]:
    require(f'data-download-os="{os_name}"')
require("Windows: command-line tool")
require("Desktop app for Windows coming soon")
require('var RELEASE_REPO = "CoreStory-Frontier/release-dist";')
require("https://api.github.com/repos/")

# No hardcoded binaries: every download href in the markup is the release page
for href in re.findall(r'href="([^"]+)"', PAGE):
    assert not re.search(r"\.(dmg|deb|AppImage|exe|msi|tar\.gz)$", href), f"hardcoded binary link: {href}"

# Benchmark claims match the published wording
require("of the places business rules live in the code were covered")
require("of hard code changes that agents alone usually fail were fixed or flagged")
assert "were found</p>" not in PAGE, "98% claim must say covered, not found"
for number in ["40&ndash;74%", "98%", "17&ndash;35%"]:
    require(number)

# Setup content exists on the page, not as dead links
for anchor in ["requirements", "install", "connect"]:
    require(f'id="{anchor}"')
    require(f'href="#{anchor}"')
require("claude plugin install corestory-local@corestory")
require('"args": ["mcp", "--path", "/absolute/path/to/repo", "--no-watch"]')
assert "create your account" not in PAGE, "no account is created on first run"
assert "hosted models" not in PAGE, "no hosted models are offered"

# Skills count matches the catalog
import json
skills = json.loads((ROOT / ".well-known/agent-skills/index.json").read_text())["skills"]
require(f"{len(skills)} ready-made skills")

# Footer legal links
require('href="https://app.corestory.ai/privacy"')
require('href="https://app.corestory.ai/terms"')

# No third-party font requests; vendored fonts exist
assert "fonts.googleapis.com" not in PAGE + CSS, "third-party font request"
for asset in [
    "assets/brand/design-system/fonts/Roboto-Regular.ttf",
    "assets/brand/design-system/fonts/Roboto-Medium.ttf",
    "assets/brand/design-system/fonts/Roboto-Bold.ttf",
    "assets/brand/design-system/fonts/RobotoCondensed-Bold.ttf",
    "assets/brand/design-system/assets/Logos/CoreStory-Logo-Rev-Gold-RGB.svg",
]:
    assert (ROOT / asset).is_file(), f"missing vendored brand asset: {asset}"

# Accessibility basics
require("prefers-reduced-motion", CSS)
require(":focus-visible", CSS)
for img in re.findall(r"<img [^>]*>", PAGE):
    assert 'alt="' in img, f"image without alt text: {img}"

# The container preview page is unchanged and still honest about its status
CONTAINER_PAGE = (ROOT / "container" / "index.html").read_text()
for value in [
    "Plot container preview",
    "https://github.com/CoreStory-Frontier/plot-container-poc",
    "No public image has been released yet.",
]:
    assert value in CONTAINER_PAGE, f"missing container preview content: {value}"
assert "docker pull ghcr.io" not in CONTAINER_PAGE, "unreleased image is pullable"
