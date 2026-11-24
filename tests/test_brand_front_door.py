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
# Agent setup verified against the corestory CLI (v0.1.0-rc1 / main 2026-11-16):
# `corestory mcp` serves the directory it starts in and has no --path/--no-watch.
require('"args": ["mcp"]')
require('cwd = "/absolute/path/to/your-repo"')
require("${workspaceFolder}")
require("corestory setup")
for dead in ("--path", "--no-watch", "corestory refine", "store.db"):
    assert dead not in PAGE, f"stale CLI instruction on page: {dead}"
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

# The container preview is not public: no links point to it, and its URL is a noindex placeholder
assert 'href="container/"' not in PAGE, "front door links to the unpublished container page"
assert "container/" not in (ROOT / "llms.txt").read_text(), "llms.txt points to the container page"
assert "container/" not in (ROOT / "sitemap.xml").read_text(), "sitemap lists the container page"
CONTAINER_PAGE = (ROOT / "container" / "index.html").read_text()
require('<meta name="robots" content="noindex">', CONTAINER_PAGE)
for leaked in ["CoreStory-Frontier", "ghcr.io", "docker build", "plot-container"]:
    assert leaked not in CONTAINER_PAGE, f"container placeholder exposes internal detail: {leaked}"

# Social/SEO metadata: absolute OG image that exists in the repo, large Twitter card, JSON-LD.
require('<meta property="og:image" content="https://get.corestory.ai/assets/social/og-get-corestory-v2.png">')
require('<meta name="twitter:card" content="summary_large_image">')
require('"@type": "SoftwareApplication"')
assert (ROOT / "assets/social/og-get-corestory-v2.png").exists(), "OG image file missing"
assert (ROOT / "apple-touch-icon.png").exists(), "apple-touch-icon missing"

# Claude Code plugin (agent-skills#5 fixed its MCP args; verified install from GitHub 2026-11-16).
require("claude plugin install corestory-local@corestory")

# Agent install path: hero prompt, agent instructions, and the honest setup caveat.
require("Install CoreStory from get.corestory.ai")
require("You accept the terms and add your model key")
LLMS = (ROOT / "llms.txt").read_text()
for value in ("corestory setup", "Do not accept the terms on the user's behalf", "x86_64-unknown-linux-musl", '"args":["mcp"]'):
    assert value in LLMS, f"llms.txt missing: {value}"
for dead in ("--path", "--no-watch"):
    assert dead not in LLMS, f"llms.txt has stale flag {dead}"

# Download clicks also go to CoreStory's PostHog (anonymous, no cookies), so clicks
# by people can be told apart from GitHub's raw download count.
require('event: "get/download-clicked"')
require('"https://telemetry.corestory.ai/i/v0/e/"')
require("$process_person_profile = false")
