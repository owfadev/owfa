# payloads/personal/ — the embedded blessed suite copy

Embedded copy of the **personal suite** package (source: `owfadev/owfa-personal`,
synced by `scripts/sync-blessed.sh` before each release). `owfa init` installs this
copy via `kernel install --path payloads/personal` — the default bootstrap stays
100% offline. See the channel repository's own docs for the package's members,
skeleton and teardown anchors (PKG.yaml).
