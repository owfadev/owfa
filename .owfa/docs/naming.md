# The name

> **OWFA — One Workspace For All (agents).**
> Public framework: **OWFA Core** (proposed; `vault-wiki` retires from the public surface) · installer: **OWFA CLI** · GitHub: **owfadev** · npm: `owfa` (application pending) or `owfadev` (fallback).

This page exists because a name is a contract with the people who type it. It records what the words commit to, which layers must not be collapsed, where the name actually resolves, and what happens if a registry refuses the string.

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
| Framework | **OWFA Core** (proposed) | `.owfa/` + `.agents/skills/` | the body that is installed into a workspace |
| Installer | **OWFA CLI** | `bin/owfa.js` (npm package) | fetch the tree, `init`, `upgrade`, `doctor`, `add` |
| Engine | **kernel** | `.owfa/scripts/owfa_kernel.py` | validate / inject / registry / deploy / install mechanics |
| Plugin tier | **core** | `.owfa/plugins/core/` | the 21 framework plugins |
| Extension | **package** | `.owfa/plugins/domains/<pkg>/` | domain families (cuhksz, lark, email, bili, project…) |
| Unit | **instance** | the user's directory | a deployed workspace |

The call chain is the reason the names must stay distinct:

```
npx owfa init
  └─ bin/owfa.js            CLI: fetch payload, copy trees, write AGENTS.md, call the engine
       └─ kernel             validate → inject → registry → deploy
            └─ core plugins  the structural contracts projected into AGENTS.md
```

Two rules fall out:

- **CLI ≠ kernel.** The CLI is replaceable delivery (npm today, pipx or curl tomorrow); the kernel is deterministic mechanics with a fixed contract. Renaming the kernel to "OWFA CLI" would collapse the two and make the npm channel appear to own semantics it does not own.
- **`core` is the plugin tier.** If the framework is publicly called *OWFA Core*, do **not** also name the repository `core`: one word, two referents. The repo is `owfadev/owfa` for now; if it ever splits, `owfadev/core` (framework body) and `owfadev/cli` (installer) can take the word, and only then does `core` mean the repo.

`vault-wiki` is retired from the public surface: public copy says OWFA (or OWFA Core), the repo target is `owfadev/owfa`. The old string survives in history, old links and technical identifiers; there is no big-bang rename of the kernel, plugin directories or package IDs.

## Two names, two jobs

| Name | Job | Where it appears |
|---|---|---|
| `vault-wiki` | historical / technical alias — what the code was called | old links, commit history, registry rows until the move |
| OWFA / OWFA Core | public name — what the project is | README first line, npm page, docs |
| `owfadev` | namespace — where the name resolves | GitHub org, npm fallback package |

A name that exists only in slides is a slogan; a name that resolves in a package manager is an address. The address layer is the one that has to be settled mechanically, not rhetorically.

## Namespaces — the actual collision

- **GitHub `owfa` is taken** by an unrelated, dormant organization ("One Web For All", 0 public repos). We do not claim it, link it, or wait for it.
- **GitHub `owfadev` is available** (checked 2026-10-25). It is the project's org target. The repository target is `owfadev/owfa`; the current `AIE3905-Wuwa/vault-wiki` stays in place until the org exists and the team agrees to the move. A move is a migration either way: transfer the repo into a new org, or rename the current org (`AIE3905-Wuwa` is project-only — 9 repos, 3 members — so renaming is viable if the course no longer depends on the name). Both paths need the same URL/registry sweep; renaming releases the old org name and 404s the old org profile/API, while transferring leaves the course org intact. **Update 2026-10-26: the team agreed — direct org rename (plan B) to `owfadev` with the repository renamed to `owfa`; execution follows `migration.md`.**
- **npm `owfa` is frozen.** `npm view owfa` returns 404, but 404 means "no published package", **not** "publishable": npm holds the name back under its similarity policy (too close to `ow` / `ora`; reported by the maintainer when publishing). The only path is an application to npm support.
- **The fallback is `owfadev`** — it returns 404 on npm (no published package, no freeze reported; unlike `owfa`, confirm at the first publish), matching the GitHub org. The package can expose both bins (`owfa` and `owfadev`), so `npx owfadev init` works today and `owfa init` works after a global install. If the application is granted, `owfa` becomes the primary package; `owfadev` stays as an alias or is deprecated, never deleted.

A 404 is not a claim. A frozen name is claimed by an application **plus** a working fallback, not by announcing the command early.

## Sequence — why GitHub first

1. **Create `owfadev` and move the repo** (`owfadev/owfa`), update metadata and links. This is the public home a reviewer can inspect.
2. **Apply to npm** with the org, the repo, the docs and the fallback as evidence that this is a project, not a typo-squat.
3. **Publish the fallback first if the application is slow**; switch the primary package to `owfa` if and when it is granted. The brand never blocks on the registry string.

The order is not bureaucratic: npm support evaluates a project by its public home, and a repo that is about to move is weak evidence. Settle the home, then ask for the address.

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

3. **"The GitHub org is taken and npm froze the name, so the name is not ours."**
   The brand and the address are separate. The org target `owfadev` is ours; the npm fallback `owfadev` is publishable; `owfa` is an application, not a dependency. If the string is denied, the project still ships, and the README says which command works.

4. **"Then rename the repo and all packages."**
   No. The repo target is `owfadev/owfa`; package IDs, plugin directories and the kernel stay as they are. `core` stays the plugin tier. This is the `ripgrep`/`rg` pattern at the namespace level.

5. **"It is still just a slogan."**
   It is a CLI with a working fallback channel; the command runs under `owfadev` even before `owfa` is granted. That is the difference between a position paper and a channel.

## Where the name is enforced

- `package.json` — `"name": "owfa"` (target) with `"bin": { "owfa": "bin/owfa.js" }`; the fallback is the same file with `"name": "owfadev"` and bins `owfa` + `owfadev`
- `README.md` — first line, the *Name* section, and the install note (never announce a command the registry does not serve)
- `templates/AGENTS.template.md` — the identity paragraph a new instance starts from
- `.owfa/docs/distribution.md` — the channel's version invariant, fallback and release runbook
- `scripts/verify-release.js` — the release gate (name/bin agreement, version rides `.owfa/VERSION`, tag matches)

Update 2026-10-26: the repository itself is renamed to `owfa` (`owfadev/owfa`), and the public copy uses OWFA / OWFA Core; `vault-wiki` survives only in history and old links. Nothing in the kernel, plugin IDs, or registry depends on the brand.
