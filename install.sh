#!/bin/sh
# Install the CoreStory command-line tool on macOS (Apple silicon) or Linux (x64).
#
#   curl -fsSL https://get.corestory.ai/install.sh | sh
#
# Downloads the newest release from github.com/CoreStory-Frontier/release-dist,
# checks its SHA-256, and puts `corestory` in ~/.local/bin (or $CORESTORY_INSTALL_DIR).
# It does not accept the terms of use or send telemetry: run `corestory setup` next.
set -eu

REPO="CoreStory-Frontier/release-dist"
RELEASES_URL="${CORESTORY_RELEASES_URL:-https://api.github.com/repos/$REPO/releases?per_page=10}"
INSTALL_DIR="${CORESTORY_INSTALL_DIR:-$HOME/.local/bin}"

say() { printf '%s\n' "$*"; }
fail() { printf 'corestory install: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "needs '$1', which isn't installed"; }

need curl
need tar
need uname

os=$(uname -s)
arch=$(uname -m)
case "$os/$arch" in
  Darwin/arm64)               target="aarch64-apple-darwin" ;;
  Linux/x86_64|Linux/amd64)   target="x86_64-unknown-linux-(musl|gnu)" ;;
  Darwin/x86_64)              fail "Intel Macs aren't supported yet (Apple silicon only). See https://get.corestory.ai" ;;
  MINGW*|MSYS*|CYGWIN*)       fail "on Windows, run in PowerShell: irm https://get.corestory.ai/install.ps1 | iex" ;;
  *)                          fail "$os $arch isn't supported yet. See https://get.corestory.ai" ;;
esac

if command -v sha256sum >/dev/null 2>&1; then sha() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
else fail "needs 'sha256sum' or 'shasum' to verify the download"; fi

tmp=$(mktemp -d 2>/dev/null || mktemp -d -t corestory)
trap 'rm -rf "$tmp"' EXIT INT TERM

# Newest non-draft release (pre-releases included). Parse the asset URLs without jq:
# every browser_download_url is on its own "key": "value" pair in the API's JSON.
curl -fsSL -H "Accept: application/vnd.github+json" "$RELEASES_URL" -o "$tmp/releases.json" \
  || fail "couldn't reach GitHub to find the latest release. Download by hand: https://github.com/$REPO/releases"
urls=$(tr ',' '\n' < "$tmp/releases.json" | sed -n 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
# The API lists releases newest first; draft releases have no public download URLs.
url=$(printf '%s\n' "$urls" | grep -E "/corestory-cli-[^/]*-${target}\.tar\.gz\$" | head -n 1 || true)
[ -n "$url" ] || fail "no command-line tool for $os $arch in the latest release. See https://github.com/$REPO/releases"
file=${url##*/}

say "Downloading $file"
curl -fSL --progress-bar "$url" -o "$tmp/$file" || fail "download failed: $url"
curl -fsSL "$url.sha256" -o "$tmp/$file.sha256" || fail "couldn't download the checksum: $url.sha256"

# The .sha256 file names a build path, so compare the hash field only.
want=$(cut -d' ' -f1 < "$tmp/$file.sha256")
got=$(sha "$tmp/$file")
[ -n "$want" ] && [ "$want" = "$got" ] || fail "checksum mismatch for $file (expected $want, got $got). Nothing was installed."

tar -xzf "$tmp/$file" -C "$tmp" bin/corestory || fail "couldn't unpack $file"
mkdir -p "$INSTALL_DIR"
# Install via a temp name + rename so an existing copy is replaced in one step.
cp "$tmp/bin/corestory" "$INSTALL_DIR/.corestory.new"
chmod 755 "$INSTALL_DIR/.corestory.new"
mv -f "$INSTALL_DIR/.corestory.new" "$INSTALL_DIR/corestory"

version=$("$INSTALL_DIR/corestory" --version 2>/dev/null || true)
say ""
say "Installed ${version:-corestory} to $INSTALL_DIR/corestory"

case ":$PATH:" in
  *":$INSTALL_DIR:"*) on_path=1 ;;
  *) on_path=0 ;;
esac
if [ "$on_path" = 0 ]; then
  case "${SHELL:-}" in
    */zsh)  rc="$HOME/.zshrc" ;;
    */bash) rc="$HOME/.bashrc" ;;
    *)      rc="your shell's startup file" ;;
  esac
  say ""
  say "$INSTALL_DIR isn't on your PATH. Add it with:"
  say "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> $rc"
  say "then open a new terminal."
fi

say ""
say "Next: run 'corestory setup' to accept the terms of use, choose telemetry and add a model key."
say "Setup guide: https://get.corestory.ai/#setup"
