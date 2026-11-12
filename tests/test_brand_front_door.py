#!/usr/bin/env python3
"""Validate the public distribution front door's branded, safe contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "index.html").read_text()


def require(value: str) -> None:
    assert value in PAGE, f"missing required page content: {value}"


require('data-theme="dark"')
require('data-expression="control-room"')
require('data-audience="builder"')
require('assets/brand/dist/tokens.css')
require('assets/brand/design-system/assets/Logos/CoreStory-Logo-Rev-Gold-RGB.svg')
require('Code Intelligence for agents')
require('Agent Skills catalog')
require('https://get.corestory.ai/.well-known/agent-skills/index.json')
require('https://github.com/CoreStoryAI/agent-skills')
require('https://github.com/CoreStory-Frontier/dist')
require('Signed public releases are not available yet.')

for asset in [
    "assets/brand/dist/tokens.css",
    "assets/brand/design-system/assets/Logos/CoreStory-Logo-Rev-Gold-RGB.svg",
    "assets/brand/design-system/fonts/Roboto-Regular.ttf",
    "assets/brand/design-system/fonts/RobotoCondensed-Bold.ttf",
]:
    assert (ROOT / asset).is_file(), f"missing vendored brand asset: {asset}"

assert 'CoreStoryAI/corestory' not in PAGE, "former release repository remains canonical"

CSS = (ROOT / "site.css").read_text()
assert 'prefers-reduced-motion' in CSS, "missing reduced-motion support"
assert ':focus-visible' in CSS, "missing visible keyboard focus"
