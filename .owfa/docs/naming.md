# The name

> **OWFA — One Workspace For All (agents).**
> Public framework: **OWFA Core** · installer: **OWFA CLI** · GitHub: **owfadev/owfa** · npm: `owfadev` (bins `owfa` + `owfadev`).

This page exists because a name is a contract with the people who type it. It records what the words commit to, which layers must not be collapsed, and where the name actually resolves.

## The line

Use the expansion exactly as written. Do not expand it as *One Wiki For All* or *One Web For All* in any public text — the first is a different (smaller) claim, the second belongs to an unrelated GitHub organization. When the acronym has to stand alone, pair it with the parenthetical once per document, then use `OWFA`.

- 中文：**一个工作区，装下你所有的 agent。**
- 一句话：OWFA gives every agent you use one workspace to re-enter — your assets, your wiki, your instructions — instead of re-introducing yourself every session.
- Agent-facing: "This is an OWFA workspace: `vault/` holds real assets, `wiki/` holds the md world, `.owfa/` + `.agents/skills/` are the framework body. Read AGENTS.md, then work from the indexes."

## What each word commits to

**One** — one directory, one place a new session re-enters. Not one app that swallows every tool, and not one vendor account. The unit is a workspace the human owns and every agent reads.

**Workspace** — the outer object: `vault/` + `wiki/` + `AGENTS.md` + the framework body. The wiki is the *inner* markdown world; the workspace is what the user actually owns, moves, backs up, and points agents at. Naming the workspace rather than the wiki is deliberate: the contribution is the re-entry surface, not markdown as a format.

**For all (agents)** — all *your* agents: across harnesses (ZCode, Claude Code, Cursor, dsh…), across sessions, across time. It does **not** mean all people, all data, or a hosted service. The parenthetical is part of the name, not a footnote — it is what keeps the claim true. Humans stay the owner and the audit anchor; agents are the ones that re-enter with zero priors.

The name answers the project's actual starting pain: an agent that must be re-introduced every session. "One workspace for all agents" is that pain inverted.

## Layers — do not collapse them

| Layer | Name | Lives in | Job |
|---|---|---|---|
| Product | **OWFA** | README, npm page, docs | the brand |
| Framework | **OWFA Core** | `.owfa/` + `.agents/skills/` | the body that is installed into a workspace |
| Installer | **OWFA CLI** | `bin/owfa.js` (npm package `owfadev`) | fetch the tree; subcommands: `init / install-kernel / adopt / workspaces / upgrade / doctor / add / list / pkg / version` |
| Engine | **kernel** | `.owfa/scripts/owfa_kernel.py` | validate / inject / registry / deploy / install mechanics |
| Plugin tier | **core** | the owfa-personal suite package (embedded at `payloads/personal/` in the channel) | the 21 former framework plugins |
| Extension | **package** | `.owfa/plugins/domains/<pkg>/` | domain families (cuhksz, lark, email, bili, project…) |
| Unit | **instance** | the user's directory | a deployed workspace |

The call chain is the reason the names must stay distinct:

```
npx owfadev init
  └─ bin/owfa.js            CLI: fetch payload, copy trees, write AGENTS.md, call the engine
       └─ kernel             validate → inject → registry → deploy
            └─ core plugins  the structural contracts projected into AGENTS.md
```

Two rules fall out:

- **CLI ≠ kernel.** The CLI is replaceable delivery (npm today, pipx or curl tomorrow); the kernel is deterministic mechanics with a fixed contract. Renaming the kernel to "OWFA CLI" would collapse the two and make the npm channel appear to own semantics it does not own.
- **`core` is the plugin tier.** The framework is publicly called *OWFA Core*, and the repository is `owfadev/owfa` — one word, two referents is avoided by never naming a repository `core`. If the framework ever splits, `owfadev/core` (framework body) and `owfadev/cli` (installer) can take the word, and only then does `core` mean the repo.

`vault-wiki` is retired from the public surface: public copy says OWFA (or OWFA Core), the repo is `owfadev/owfa`. The old string survives in history, old links and technical identifiers; there is no big-bang rename of the kernel, plugin directories or package IDs.

## Two names, two jobs — the settled layout

| Name | Job | Where it appears |
|---|---|---|
| `vault-wiki` | historical / technical alias — what the code was called | old links, commit history |
| OWFA / OWFA Core | public name — what the project is | README first line, npm page, docs |
| `owfadev` | namespace — where the name resolves | GitHub org and npm package (dual bins `owfa` + `owfadev`) |
| `owfa` | the CLI bin name, and the repository name (`owfadev/owfa`) | `PATH` after a global install; the GitHub home |

A name that exists only in slides is a slogan; a name that resolves in a package manager is an address. The address layer had to be settled mechanically, not rhetorically — and it now is: `npx owfadev` is the command every install example uses.

## What OWFA is not

- Not a SaaS or hosted product; every workspace is local and the framework has no telemetry.
- Not "for all people" and not a claim of access to all data; the scope is *your* workspace and *your* agents.
- Not the GitHub org named `owfa`, and not affiliated with "One Web For All".
- Not a replacement for the kernel, the CLI, or the `core` plugin tier as separate concepts.

## Objections, answered

1. **"It overclaims — it sounds like a universal product."**
   The scope is bounded twice: *your* workspace, *your* agents. The docs never say all data or all people. A slogan fails when it cannot be falsified; this one has a mechanical test — install it and see whether a fresh agent re-enters without being re-introduced.

2. **"'Workspace' is vague; the thing is a wiki."**
   The wiki is the medium; the workspace is the owned unit of re-entry. The product's value is that a new session knows where to look, not that files end in `.md`.

3. **"Then rename the repo and all packages."**
   No. The repo is `owfadev/owfa`; package IDs, plugin directories and the kernel stay as they are. `core` stays the plugin tier. This is the `ripgrep`/`rg` pattern at the namespace level.

## Where the name is enforced

- `package.json` — `"name": "owfadev"` with `"bin": { "owfa": …, "owfadev": … }`
- `README.md` — first line, the *Name* section, and the install note (never announce a command the registry does not serve)
- `templates/AGENTS.template.md` — the identity paragraph a new instance starts from
- `.owfa/docs/releasing.md` — the channel's version invariant and release runbook
- `scripts/verify-release.js` — the release gate (name/bin agreement, version rides `.owfa/VERSION`, tag matches)

---

**Outcome note (2026-10-26):** the project moved into the **`owfadev`** organization (org renamed from `AIE3905-Wuwa`, repository renamed from `vault-wiki` to `owfa`). npm held `owfa` frozen under its similarity policy, and the settled answer is the package **`owfadev`** with dual bins `owfa` + `owfadev` — published with provenance (v0.4.0 and v0.4.1, both 2026-11-14). The name question is closed; this page keeps the rationale, not the chase.
