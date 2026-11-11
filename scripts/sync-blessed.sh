#!/usr/bin/env bash
# Sync the blessed personal suite into payloads/personal/ from the latest tag of
# owfadev/owfa-personal. Run before cutting a release — scripts/verify-release.js
# refuses to publish without payloads/personal/PKG.yaml, and `owfa init` (default
# two-stage bootstrap) installs exactly this embedded copy, offline.
#
# README.md is channel-owned documentation: it is removed from the synced content
# and re-created here so the suite repo never has to carry it.
set -euo pipefail

REPO="owfadev/owfa-personal"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/payloads/personal"

TAG="$(git ls-remote --tags --sort=-v:refname "https://github.com/${REPO}.git" 'v*' 'v[0-9]*' 2>/dev/null \
  | awk '!/\^{}$/ && NR==1 {sub(/^refs\/tags\//, "", $2); print $2}')"
if [ -z "$TAG" ]; then
  echo "sync-blessed: no version tags found in $REPO (the suite repo must tag releases)" >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://github.com/${REPO}/archive/refs/tags/${TAG}.tar.gz" | tar -xz -C "$TMP" --strip-components=1

if [ ! -f "$TMP/PKG.yaml" ]; then
  echo "sync-blessed: $REPO@$TAG has no PKG.yaml at the repository root — not a package repo shape" >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
cp -r "$TMP"/. "$DEST"/
rm -f "$DEST/README.md"

cat > "$DEST/README.md" <<'EOF'
# payloads/personal/ — the embedded blessed suite copy

Embedded copy of the **personal suite** package (source: `owfadev/owfa-personal`,
synced by `scripts/sync-blessed.sh` before each release). `owfa init` installs this
copy via `kernel install --path payloads/personal` — the default bootstrap stays
100% offline. See the channel repository's own docs for the package's members,
skeleton and teardown anchors (PKG.yaml).
EOF

echo "sync-blessed: $REPO@$TAG -> payloads/personal/ ($(find "$DEST" -name PLUGIN.yaml | wc -l) plugin masters)"
