# OWFA — One Workspace For All (agents)

> English | [简体中文](README.zh-CN.md)

> **OWFA** is the project; **OWFA Core** is the framework body (formerly `vault-wiki`); **OWFA CLI** is the installer. The public home is **[`owfadev/owfa`](https://github.com/owfadev/owfa)** — `github.com/owfa` is an unrelated organization. See [The name](#the-name).

**OWFA** (One Workspace For All agents) is an open-source agent workspace: out-of-the-box on first install, continuously maintainable over time, and pluginized end to end. One workspace — the directory you own, holding `vault/` (real assets), `wiki/` (md proxies and native notes) and `AGENTS.md` (the constitution) — is the standing context that every agent you use re-enters instead of being re-introduced each session. The agent reads and writes with zero priors per the SASU-L disclosure order; md plus plain files are the foundation, and Obsidian and friends are replaceable viewers. New capabilities land as packages — every package is listed in the registry through a human-review gate, so contributions are welcome: build a domain package for the sources you use and file a one-line PR to list it (see [Contributing](#contributing)).

> Status: **alpha** — capability-wise a prototype matured by real daily use; distribution-wise still young, with few outside users. **Current release: see [`owfa version`](https://www.npmjs.com/package/owfadev)** — the running version lives in `.owfa/VERSION` / the npm page, not in this sentence. v0.4 is the core split: the release tree ships the kernel plus the embedded **personal** suite (21 plugin members) only — domain packages (cuhksz, lark, email, bili, project, …) moved to their own `owfa-*` repos and install on demand from the [registry](https://github.com/owfadev/owfa-registry). The npm package is **`owfadev`** (the name `owfa` is frozen by npm's similarity policy; the package exposes both `owfa` and `owfadev` bins). `.owfa/VERSION` tracks the kernel contract, not product maturity.

## Why OWFA

Two conveniences, one principle.

**Stop hand-pointing.** Without a workspace, every session you re-explain: where the files are, what that course page means, which video you watched, what you decided last week. OWFA inverts this — information registers itself into the wiki (owfa-map, owfa-save, domain packages), and the agent goes and finds it. The value is convenience in the plainest sense: the pointing you used to do by hand becomes retrieval the agent does itself.

**Any harness, your context.** OWFA ships as AGENTS.md + skills, not as a service — so it is indifferent to which agent harness reads them. Run it in one harness today, switch tomorrow, or run two at once: the workspace, the memory and the plugins come with you. The package line makes this concrete: the `bili` package (with its autonomous agent member) turns Bilibili into a queryable archive — raised in one harness, it runs just as well in any other that reads AGENTS.md. You are renting a harness, not adopting a walled garden.

## The name

**OWFA — One Workspace For All (agents).** One workspace — the directory you own, holding `vault/`, `wiki/`, `AGENTS.md` and the framework body — that every agent you use re-enters instead of being re-introduced each session. *All* means all of *your* agents, not all people and not a hosted service; the human stays the owner and the audit anchor. `vault-wiki` retires from the public surface: public copy says **OWFA** (or **OWFA Core**), the GitHub home is **`owfadev/owfa`**, and the npm package is **`owfadev`** — npm froze `owfa` as too similar to `ow`/`ora`, so `npx owfa` does not work and every install example says `npx owfadev` (the package exposes the `owfa` bin once installed). Full rationale, layers and collision policy: [`.owfa/docs/naming.md`](.owfa/docs/naming.md).

## What it does

Let an AI coding agent run a "personal wiki" for you:

- Drop assets into `vault/`, any format — md, txt, csv, pdf, images. The **owfa-map** command registers each as an md proxy page under `wiki/vault/`, with SHA-256, metadata and links
- Insights and decisions from conversations are distilled by the **owfa-save** command into native notes under `wiki/notes/`; session backbone pages go to `wiki/sessions/`
- The **owfa-query** command reads the hot cache and indexes first, then answers with wikilink-cited results
- Index, tags, hot cache and the run log are all maintained automatically by the derived layer; the **owfa-check** command audits library health; the **owfa-plugin** command installs/uninstalls packages
- External sources attach as domains: lark and email land as pointers or archive pages; calendar manages the timeline; project manages project containers; cuhksz pulls courseware, assignments and grades via cuhksz-cli; bilibili answers on demand via bili-cli. Translation happens outside domains; inside the wiki everything interlinks
- The **owfa-profile** command maintains a living cognition file about the user: assertions carry evidence, preferences expire; read it before any personalization

## Core concepts

| Concept | Definition |
|---|---|
| wiki | the md world, the inner side of the inner/outer divide: per-domain projections + native notes + derived layer |
| domain | the adapter contract for an information source outside the wiki. vault is the default domain; lark, project, email, cuhksz, bili, github are domains too |
| vault | the default domain — the real-asset repository; command side append-only, deletion & editing belong to the human |
| SASU-L | the disclosure paradigm: the agent learns only via system prompt, AGENTS.md, Skills, user's words, loop |

## Layout

The v0.4 release tree (core split, option B) — no `.owfa/plugins/`, no `connectors/`:

| Directory | Contents |
|------|------|
| `.owfa/` | The kernel tree: `scripts/owfa_kernel.py` and `wikilib` — pure stdlib, zero deps (the pipeline is suite-owned since 0.1.1: it ships at the owfa-personal package root; the framework-tree copy is a deprecated shim, retiring in 0.5.0), `VERSION` (the framework anchor; package `compat` floors checked against it), `protocol/` (field registry, action discipline, disclosure paradigm), `docs/` (human docs — indexed below) |
| `.owfa/command/` | 6 framework command masters: asset-read / owfa-check / owfa-docs / owfa-kernel / owfa-plugin / owfa-query (suite-owned commands — owfa-map / owfa-save / owfa-profile — ride with the personal suite) |
| `payloads/personal/` | Embedded copy of the blessed **personal** suite (canonical repo: `owfadev/owfa-personal`; kept fresh by `scripts/sync-blessed.sh`). 21 plugin members + 3 suite commands; a default init installs it offline from this path |
| Packages | Domain packages live in their own org repos — `owfa-cuhksz` (cuhksz-cli aggregates bb\|sis), `owfa-lark`, `owfa-email` (mail-cli), `owfa-bili` (bili-cli), `owfa-project`, `owfa-github`, `owfa-diary`, `owfa-qq` — connectors ship with their packages; SKILL.md lands in `.agents/skills/` via kernel deploy. The index is the [registry](https://github.com/owfadev/owfa-registry) (`owfadev/owfa-registry`): one line per package, a human-reviewed PR is the listing gate; `kernel install`/`list-remote` resolve against it, unindexed repos install with `--yes` (trust: unknown) |
| `.agents/skills/` | Deployment copies of command & connector skills (framework commands at init; connector skills arrive with their packages) |
| `bin/` + `templates/` + `package.json` | The npm channel: the `owfa`/`owfadev` CLI, AGENTS seed, package manifest (`owfadev`, provenance enabled). `test/` and `scripts/` are development-only and never ship |

## Install

```bash
npx owfadev init my-workspace   # two-stage: kernel bootstrap, then offline install of the embedded personal suite
cd my-workspace
npx owfadev doctor              # python / framework / markers / kernel validate
npx owfadev list                # registry catalog
npx owfadev add cuhksz          # optional domain package
npx owfadev upgrade             # later: replace the framework trees, preserve instance state
```

The npm package is `owfadev` — `npx owfa` does not work (the name is frozen under npm's similarity policy). The package exposes both `owfa` and `owfadev` bins, so a global install gives you the `owfa` command. Prerequisites: Node 16.7+ for the installer, Python 3.9+ (pure stdlib) for the kernel; an agent environment that reads AGENTS.md and skills; git recommended; Obsidian optional, viewer only.

`init` is additive (existing content untouched; an existing `AGENTS.md` keeps its text and gains only the injection region). Upgrading from 0.3: `npx owfadev upgrade` walks the core-split conversion (attic rescue → staging → rootless personal suite). Framework upgrades replace `.owfa/` and `.agents/skills/` — instance data is never touched; the migration ledger, journal and registry cache are kept.

First use: open an agent session at the workspace root, drop a file into `vault/` and say "owfa-map" to the agent.

Since 0.4.8 there is also a **user-level kernel channel**: `owfa init --user-level` (or `owfa adopt` on an existing workspace) installs the kernel once under `$OWFA_HOME/kernel/<ver>/` instead of per-workspace, marks the workspace with `.owfa/WORKSPACE.yaml`, and registers it in a machine-wide workspace registry (`owfa workspaces list / rescan`). The full mechanics are in [deployment.md](.owfa/docs/deployment.md).

## Contributing

Contributions are welcome, and packages are the intended surface: a new capability is a new package, not a fork of the framework. Three paths, smallest first — a connector skill for a CLI you use, a domain package that adapts an external source to the wiki (see [`developer.md`](.owfa/docs/developer.md) for the three-path table and the dev loop), or an improvement to core. Domain packages self-host in their own `owfa-*` repos; listing is a one-line PR to the [registry](https://github.com/owfadev/owfa-registry), which is the human-review trust gate. Bug reports and behavior questions go through issues; the framework body itself takes PRs (1 approving review to merge, `enforce_admins` on; dev rules in [CONTRIBUTING.md](CONTRIBUTING.md)).

## Doc index

- [`.owfa/docs/quickstart.md`](.owfa/docs/quickstart.md) — five-minute path: one command or the manual steps, then first run
- [`.owfa/docs/deployment.md`](.owfa/docs/deployment.md) — deployment guide: components, channels, first run, packages, upgrades, troubleshooting
- [`.owfa/docs/packages.md`](.owfa/docs/packages.md) — package mechanism: layout, PKG.yaml, capability syntax, install channels, trust levels, uninstall contract
- [`.owfa/docs/developer.md`](.owfa/docs/developer.md) — developer guide: where a plugin lands (the three-path table), the dev loop, registration and discovery
- [`.owfa/docs/releasing.md`](.owfa/docs/releasing.md) — the npm channel and release runbook: pipeline, five-artifact version invariant, merge discipline
- [`.owfa/docs/conversion.md`](.owfa/docs/conversion.md) — 0.3→0.4 conversion and migrations: staging, resume caveats, the conversion algebra
- [`.owfa/docs/kernel.md`](.owfa/docs/kernel.md) — kernel mechanics: packages, capabilities, projections, budgets, lifecycle; read before touching the framework
- [default protocol docs](https://github.com/owfadev/owfa-personal/blob/master/docs/protocol.md) — the protocol this suite implements: lineage (llmwiki → vault-wiki → OWFA default), slots, vocabulary, member roster, and the three work loops
- [`.owfa/docs/naming.md`](.owfa/docs/naming.md) — the name: canonical expansion, what each word commits to, two names two jobs, collision policy

## License

MIT — see [LICENSE](LICENSE).
