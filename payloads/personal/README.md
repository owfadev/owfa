# payloads/personal/ — the embedded blessed suite copy

This directory is the tarball-embedded copy of the **personal suite** package
(external repo: `owfadev/owfa-personal`). It exists so that `owfa init` stays
100% offline for the default bootstrap: stage ① deploys the kernel payload,
stage ② installs this copy via `kernel install --path payloads/personal`
(local-path channel — no network, no trust gate bypass needed).

## Status: placeholder

Until the suite repo lands, this directory carries only this README and a
placeholder `PKG.yaml`. Channel behavior in that state:

- the channel still ships `.owfa/plugins/core/` (compat period) — init then
  skips stage ② entirely: the suite is already inside the framework tree;
- once the channel stops shipping core, init with an unpopulated embedded copy
  reports "no suite installed — this instance cannot install packages that
  depend on core capabilities until a suite is installed" (`--core none`
  requests that state explicitly; `--core <pkg-id>` installs from the registry).

## Syncing

Run `scripts/sync-blessed.sh` before cutting a release: it pulls the latest tag
of `owfadev/owfa-personal` into this directory (README.md is channel-owned and
is re-created after the sync). `scripts/verify-release.js` refuses to publish
without `payloads/personal/PKG.yaml`.

Expected final shape (what the suite repo must provide):

    payloads/personal/
      PKG.yaml      # id: personal, members: [...], skeleton: [...], uninstall.anchors: [...]
      <member>/     # one directory per plugin (PLUGIN.yaml + PLUGIN.md + files)
      connectors/   # optional
      command/      # optional
