# owfa-personal

**OWFA personal suite** — the default **protocol package** (the first `kind: protocol` package, `protocol: vaultwiki`, `provides: vaultwiki.org.v1` since framework 0.4.3): the 21 members (calendar, cron, device, domain, hot, index, instance-git, language, link, log, mapping, notes, sessions, structure, tag, tmp, todo, trust, user-profile, vault, wiki) that give an OWFA instance its wiki container, notes/sessions native zones, vault proxy layer, derived projections (index/tags/hot/log) and the personal time/task territories. Since framework v0.4 these ship as an independent package instead of riding in `.owfa/plugins/core/`; `owfa init` installs it by default, so a fresh instance starts with the vaultwiki protocol's self-sufficient baseline. The package carries no connectors — everything runs on the framework kernel ([owfa](https://github.com/owfadev/owfa)), which owns the plugin mechanics (manifests, projections, lifecycle); see [PKG.yaml](PKG.yaml) for members/compat and the framework's packages doc for the mechanism.

## Documentation

| Document | What it covers |
|---|---|
| [docs/protocol.md](docs/protocol.md) | The default protocol in full: lineage, the three-layer model, slot shapes, vocabulary, the derived machine, member roster, switching paths (中文版：[docs/zh/protocol.md](docs/zh/protocol.md)) |
| [docs/usage.md](docs/usage.md) | The three working loops: vault stewardship, course study, collaborative development (中文版：[docs/zh/usage.md](docs/zh/usage.md)) |

## Machinery

`pipeline.py` lives at the package root (since 0.1.1): the derived-layer post-write pipeline (index / tags / hot / log / verify) is suite machinery — the kernel never calls it. Instance path: `.owfa/plugins/domains/personal/pipeline.py`; the framework tree keeps a deprecated host copy until 0.5.0.
