# OWFA — One Workspace For All (agents)

> English | [简体中文](README.zh-CN.md)

**OWFA** is an open-source, ontology-based workspace framework for AI agents. A workspace is a directory you own that every agent re-enters instead of being re-introduced each session; the agent reads and writes with zero priors, everything stays local in plain files, and any harness that reads `AGENTS.md` and skills can run it.

A workspace's nature is decided by its **protocol**:

- **personal** (the default, `vaultwiki`) — the personal-information protocol: real assets in `vault/`, markdown knowledge in `wiki/`, with map / save / query / check commands. Its design descends from llm-wiki, so an existing workflow ports over at near-zero cost.
- **project** — for workspaces whose primary product *is* the project. Add the optional `owfadevelop` package to develop owfa itself.
- Anything else — protocols and domain packages (cuhksz, lark, email, bili, qq, …) install on demand from the [registry](https://github.com/owfadev/owfa-registry).

## Install

```bash
npx owfadev init my-workspace   # kernel + the default personal protocol; --core none = bare, --core <pkg-id> = another protocol
cd my-workspace
npx owfadev doctor              # health check
npx owfadev add cuhksz          # optional domain package
npx owfadev upgrade             # later: update the framework, instance data untouched
```

Prerequisites: Node 16.7+ (installer), Python 3.9+ pure stdlib (kernel), an agent that reads `AGENTS.md`; git recommended; Obsidian optional (viewer only). The npm package is `owfadev` — `npx owfa` does not work (name frozen by npm), see [naming](.owfa/docs/naming.md). `init` is additive: existing content is never touched.

First use: open an agent session at the workspace root, drop a file in and say "map".

## With the default personal protocol

- Drop assets into `vault/`, any format — **map** registers each with SHA-256 and a markdown proxy page; **query** answers with cited results (hot cache → index → grep → source); **check** audits health
- Conversations distill into native notes via **save**; a living user profile drives personalization; index, tags and the run log maintain themselves
- External sources attach as domains: cuhksz pulls courseware, assignments and grades; lark / email / bili / qq bring their platforms in as queryable territory — installed when needed, removable without data loss

Commands are tiered: **owfa-check / owfa-docs / owfa-kernel / owfa-plugin** are framework built-ins (every workspace, protocol-neutral); the rest ride with their protocol suite or package — a missing command means a missing layer.

## Core concepts

| Concept | Definition |
|---|---|
| workspace | the directory you own; every agent re-enters it as standing context |
| protocol | decides the workspace's nature — what its territories, pages and loops are (personal, project, …) |
| package | how any capability ships: protocol suites, domain adapters, tools — installed/removed whole, listed in the registry |
| kernel | the package machinery: manifests, dependency graph, projections, install/upgrade — knows no content protocol |
| SASU-L | the disclosure paradigm: the agent learns only via system prompt, AGENTS.md, Skills, user's words, loop |

## Layout

| Directory | Contents |
|------|------|
| `.owfa/` | the kernel tree: `owfa_kernel.py` (pure stdlib), `VERSION`, `protocol/`, `docs/`, `command/` (the 4 framework command masters) |
| `payloads/personal/` | embedded copy of the personal suite — what a default `init` installs offline |
| `.agents/skills/` | deployed copies of command & connector skills |
| `bin/` + `templates/` | the npm channel (`owfadev` CLI, AGENTS seed) |

Domain packages live in their own `owfa-*` repos under the [owfadev](https://github.com/owfadev) org; the registry's one-line PR is the human-review listing gate. Since 0.4.8 a **user-level kernel** channel exists (`init --user-level`, `adopt`) — kernel once per machine, workspaces marked and registered (see [deployment.md](.owfa/docs/deployment.md)).

## Contributing

The intended surface is packages: a connector skill, a domain package, or a core improvement — the three-path table and dev loop are in [`developer.md`](.owfa/docs/developer.md). Developing owfa itself works best in a project-protocol workspace with the `owfadevelop` package. Issues for bugs and behavior questions; framework PRs need one approving review (rules in [CONTRIBUTING.md](CONTRIBUTING.md)).

## Doc index

- [quickstart](.owfa/docs/quickstart.md) — five-minute path · [deployment](.owfa/docs/deployment.md) — components, channels, upgrades
- [packages](.owfa/docs/packages.md) — package mechanism · [developer](.owfa/docs/developer.md) — where a plugin lands · [releasing](.owfa/docs/releasing.md) — release runbook
- [kernel](.owfa/docs/kernel.md) — kernel mechanics · [naming](.owfa/docs/naming.md) — the name, layers, collision policy
- [personal protocol](https://github.com/owfadev/owfa-personal/blob/master/docs/protocol.md) — the default protocol's own charter

## License

MIT — see [LICENSE](LICENSE).
