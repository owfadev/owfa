# Deployment

> Reader: anyone installing OWFA into a directory (an Obsidian vault, a notes folder, any workspace), or the agent doing it for you. This is the full guide — components, channels, first run, packages, upgrades, troubleshooting. The five-minute path is [quickstart.md](quickstart.md); the channel's design and release record is [distribution.md](distribution.md).

## 1. What gets installed

OWFA has three layers, and only one of them is "installed":

| Layer | What it is | Where it lives | Installed? |
|---|---|---|---|
| **OWFA CLI** | the installer / upgrader (`init`, `upgrade`, `doctor`, `add`, `list`, `pkg`) | npm package, run via `npx` or a global install | no — it stays outside the workspace |
| **OWFA Core** | the framework body: plugins, commands, protocols, kernel, skill copies | `.owfa/` + `.agents/skills/` | yes — copied into the workspace |
| **kernel** | the deterministic Python engine (`validate`, `inject`, `registry`, `deploy`, `install`) | `.owfa/scripts/owfa_kernel.py` | no — it ships **inside** Core; there is no separate kernel install |
| **packages** | optional domain extensions (course, lark, email, bili, project…) | `.owfa/plugins/domains/<pkg>/` | on demand |
| **instance** | the workspace you own: `vault/`, `wiki/`, `AGENTS.md`, the framework body | your directory | — |

The call chain is one direction:

```
OWFA CLI  →  copies OWFA Core  →  runs the kernel  →  kernel converges Core + packages
```

A deployed workspace looks like this:

```
my-workspace/
├── AGENTS.md                  # identity/layout (yours) + injection region (kernel-managed)
├── vault/                     # real assets, any format
├── wiki/                      # the markdown world
│   ├── notes/  sessions/  vault/
│   └── index.md  tags.md  hot.md  log.md   # derived, rebuilt by the pipeline
├── .owfa/                     # OWFA Core
│   ├── VERSION                # framework anchor (0.3)
│   ├── scripts/               # kernel + pipeline + wikilib
│   ├── plugins/core/          # 21 framework plugins
│   ├── plugins/domains/       # installed packages (empty until you add one)
│   ├── command/               # command masters
│   └── docs/                  # this guide and friends
└── .agents/skills/            # deployed command/connector skill copies
```

The kernel is **not** a service, a daemon, or a pip package. It is a pure-stdlib Python script that the CLI (and the agent) invoke on demand. Python 3.9+ is the only runtime requirement for Core.

## 2. Prerequisites

| Item | Requirement | Needed for |
|---|---|---|
| Python | **3.9+**, pure standard library | Core and the kernel |
| Node | **16.7+** | the npm channel only (the CLI is Node) |
| agent | a coding assistant that reads `AGENTS.md` and `.agents/skills/` (e.g. ZCode, Claude Code, Cursor, dsh) | daily use |
| git | recommended | instance snapshots and upgrade rollback |
| Obsidian | optional | viewing the wiki; never required |

The framework itself has zero package-manager dependencies: no `pip install`, no Python venv, no npm dependencies in the tarball. `npm` is a delivery vehicle, not a runtime.

## 3. Choose a channel

All channels deploy the same Core tree; pick by environment, not by feature.

| Channel | Command | Status |
|---|---|---|
| npm, target name | `npx owfa init my-workspace` | **name application pending** (npm froze `owfa` as too similar to `ow`/`ora`) |
| npm, fallback name | `npx owfadev init my-workspace` | same CLI, bins `owfa` + `owfadev`; to be published if the name is not granted |
| git, clone-as-instance | `git clone https://github.com/owfadev/owfa.git my-workspace` | works today |
| git, embed into an existing vault | clone the template elsewhere, copy `.owfa/` + `.agents/skills/` | works today |
| template + instance (developers) | a template clone + a separate instance | see [CONTRIBUTING.md](../../CONTRIBUTING.md) |

> Until the npm name is served by the registry, the git channel is the working path. Do not treat `npx owfa` as live before `npm view owfa version` returns a version.
>
> The org rename executed 2026-10-26 (`AIE3905-Wuwa` → `owfadev`, `vault-wiki` → `owfa`); old repository URLs redirect, old org/API paths 404.

## 4. Install

### 4.1 npm channel — one command

```bash
npx owfa init my-workspace          # target; once the name is granted
# or, while the name is pending:
npx owfadev init my-workspace       # fallback package, same CLI
cd my-workspace
npx owfa doctor                     # target: python, framework, markers, kernel validate
npx owfadev doctor                  # fallback: same check through the fallback package
```

**Command forms.** `npx <package> <verb>` needs no global install. A global install (`npm i -g owfa` or `npm i -g owfadev`) puts **both** `owfa` and `owfadev` on `PATH`. The rest of this guide writes `owfa <verb>` for the CLI and `kernel …` for the Python engine; substitute `npx owfa` / `npx owfadev` if you are not installing globally.

`init` performs the five manual steps below:

1. copies `.owfa/` and `.agents/skills/` from the tarball;
2. creates `vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`;
3. writes `AGENTS.md` from the seed, or appends **only the injection region** to an existing one (the handwritten part is preserved; half-present markers are refused);
4. runs `python .owfa/scripts/owfa_kernel.py all` (validate → inject → registry → deploy);
5. optionally installs packages (`--packages cuhksz,lark`), stopping at the first package that stages a semantic migration.

Useful flags:

- `--name NAME` — the workspace name written into the AGENTS seed;
- `--packages a,b` — install packages from the registry during init;
- `--force` — re-copy the framework trees over an existing instance, preserving the kernel's migration ledger, journal and registry cache. Instance data (`vault/`, `wiki/`) is never touched.

If the directory already contains `.owfa/`, `init` refuses; use `owfa upgrade` (or `--force` deliberately).

### 4.2 git channel — the five manual steps

**Clone-as-instance** (the clone *is* your workspace):

```bash
git clone https://github.com/owfadev/owfa.git my-workspace
cd my-workspace
# own the history if you do not want the framework's:
rm -rf .git && git init
```

**Embed into an existing vault**: clone the template somewhere else, then copy the two trees into the target root:

```bash
cp -R /path/to/owfa/.owfa          /path/to/my-workspace/
cp -R /path/to/owfa/.agents/skills /path/to/my-workspace/.agents/
```

Then, at the workspace root:

1. **Write `AGENTS.md`** — one identity paragraph, one layout paragraph, and the injection markers verbatim from [agents-example.md](agents-example.md). If an `AGENTS.md` already exists, paste in only the marker block (or let `owfa init` append it).
2. **Create the four directories**: `vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`. Derived pages build themselves.
3. **Converge**:

```bash
python .owfa/scripts/owfa_kernel.py all
```

Expected: all core plugins validate, package rosters reconcile, the injection region is rebuilt, command copies are in sync.

### 4.3 "Installing the kernel"

There is nothing separate to install. The kernel is the file `.owfa/scripts/owfa_kernel.py` inside Core; Python 3.9+ runs it. Verify it:

```bash
python3 .owfa/scripts/owfa_kernel.py validate   # structural check, read-only
python3 .owfa/scripts/owfa_kernel.py ls         # 21 core plugins
python3 .owfa/scripts/owfa_kernel.py pkg        # installed packages + core remainder
```

On Windows, `python` may be `py -3`; the CLI probes `python3`, `python`, then `py -3`. Set `OWFA_PYTHON=/path/to/python3` to override. If the kernel is missing, the Core copy is incomplete — recopy the tree, do not "pip install" anything.

## 5. First run

```bash
cd my-workspace
git init && git add -A && git commit -m "init: OWFA workspace"   # recommended
```

1. Put any file into `vault/` — `memo.txt`, a PDF, an image.
2. Open an agent session at the workspace root and say **map**.
3. The agent writes `wiki/vault/memo.txt.md` (SHA-256 + metadata), then the pipeline builds `wiki/index.md`, directory indexes, `tags.md`, `hot.md`, `log.md`.
4. Say **check** — a green audit means the deployment is sound.

The injection region in `AGENTS.md` now contains one block per full-tier plugin; the agent reads it as the structural contract. Everything outside the markers is yours.

## 6. How to use it

Open the agent at the workspace root; it reads `AGENTS.md` and `.agents/skills/`. Daily commands are natural language:

| You say | What happens |
|---|---|
| map | register a vault asset as a wiki proxy page (hash, metadata, links) |
| save | distill the current conversation into a native note |
| query | answer from hot cache → index → grep, with wikilink citations |
| check | repository health audit (structure + semantic checks) |
| plugin | install / uninstall / list structural plugins |
| profile | maintain the user cognition profile |
| teach / quiz / cognition profile | course-learning family (needs a course domain, e.g. cuhksz) |
| kernel reference | kernel usage and mechanics |

The daily loops — library keeping, course learning, collaborative development — are in [usage.md](usage.md). Mechanics are in [mechanics.md](mechanics.md); the kernel reference skill is authoritative for flags.

## 7. Packages — finding and installing

Core ships only the framework plugins. External systems arrive as **packages**: one directory `.owfa/plugins/domains/<pkg>/` with a `PKG.yaml` roster, plugin masters, commands and connectors.

### 7.1 Find what exists

Run these inside the instance:

```bash
owfa list                    # registry catalog: versions, compat floors, installed marks
owfa pkg                     # what is installed here: members, connectors, core remainder
# the same through the kernel:
python3 .owfa/scripts/owfa_kernel.py list-remote
python3 .owfa/scripts/owfa_kernel.py pkg
```

The registry is the GitHub index at `owfadev/registry`; before installing, it is also readable directly as `INDEX.yaml` in that repository. Each row shows the package version, the framework compat floor, the member plugins and the trust level.

### 7.2 Install a package

```bash
owfa add cuhksz              # wraps kernel install + convergence
# equivalent, and more explicit:
python3 .owfa/scripts/owfa_kernel.py install cuhksz --yes
```

This is also what the agent's **plugin** command does: you can ask the agent to install a package by name, and it drives the same kernel. The CLI is the human/script equivalent.

What lands: plugin masters under `.owfa/plugins/domains/<pkg>/`, command masters, in-repo connectors, skill copies, injection blocks, registry rows. Then the kernel converges. If the package declares a **first-run semantic migration** (root packages such as `project` do), the install stages it and `validate` stays red until an agent performs the semantic step:

```bash
python3 .owfa/scripts/owfa_kernel.py migrate <pkg>
# read the printed page, create the declaration/identity page, then:
python3 .owfa/scripts/owfa_kernel.py migrate <pkg> --clear
```

The CLI stops and reports this instead of pretending convergence. `owfa add` exits non-zero in that state.

Other forms:

- `kernel install <pkg>@<tag>` — pin a release tag;
- `kernel install <owner>/<repo> --yes` — an unindexed repository (trust: unknown; `--yes` is the trust gate);
- `kernel install <pkg> --path ./local-pkg` — a local package (channel C, no registry);
- `--without a,b` — subset grammar is reserved; v1 reports not-yet-open. Offline alternative: copy `domains/<pkg>/` into `.owfa/plugins/domains/` and rerun `all`.

Trust levels are visible in `owfa list`: `framework-bundled` and `reviewed-3rd-party` install without a prompt; anything else needs `--yes` and is reported as unknown.

### 7.3 Upgrade and uninstall packages

```bash
python3 .owfa/scripts/owfa_kernel.py upgrade            # reconciliation report (read-only)
python3 .owfa/scripts/owfa_kernel.py upgrade <pkg> --yes # silent reinstall, per package, never cascaded
python3 .owfa/scripts/owfa_kernel.py uninstall <pkg> --yes
```

- Package versions are release ordinals riding their own tags; member plugin versions do not lockstep.
- Upgrade stages semantic migrations when a version lands; clear them before the next mechanical action.
- Uninstall does the mechanical four-clear (masters, commands, connectors, skills) plus a residual scan; **data zones and credentials are never auto-deleted**. A declared teardown stages a semantic-deletion warning and a residual gate. See [packages.md](packages.md).

## 8. Upgrade the framework

### npm channel

```bash
npx owfa upgrade            # replace .owfa/ + .agents/skills/ with the channel's version
npx owfa upgrade --check    # read-only report
npx owfa upgrade --backup   # keep a copy under .owfa/backup/<version>-<timestamp>/
```

`upgrade` preserves the instance-local kernel state (`.owfa/migrations/pending.json`, `.owfa/kernel-journal.log`, `.owfa/registry-cache.yaml`), replaces local edits under the two framework trees (instance hotfixes belong in git), and reruns `all`. A pending semantic migration blocks convergence and is reported with the exact `migrate` command.

### git channel

Re-copy `.owfa/` and `.agents/skills/` from the new template revision (review the diff, do not blind-copy over pending migrations), then `kernel all`. The instance git snapshot is the rollback path.

Framework versions are anchored by `.owfa/VERSION` (0.3); a target-side semantic migration can be staged by an upgrade, with the same tri-face warning and `kernel migrate` flow.

## 9. Uninstall

- **A package**: `kernel uninstall <pkg> --yes`; data zones stay, credentials are only reminded, never deleted.
- **The whole framework**: delete `.owfa/`, `.agents/skills/`, and the `AGENTS.md` injection region block. `vault/` and `wiki/` are yours; dispose of them as you see fit. Nothing else is installed.

## 10. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Python 3.9+ not found` | install Python 3, or set `OWFA_PYTHON`; the installer is Node-only, the runtime is Python |
| `already contains .owfa/` | it is an instance — `owfa upgrade`; `--force` re-copies the trees |
| `npx` runs an old version | `npx owfa@latest …`; npm caches by version range |
| `publish` / `npx` 403 on `owfa` | the name is frozen on similarity grounds; use the `owfadev` fallback or wait for the application |
| upgrade blocked by pending migrations | run `kernel migrate <pkg>`, perform the semantic step, then `--clear` |
| AGENTS markers missing | the AGENTS shell lost the `wiki-inject:start/end` pair; restore both, then `kernel all` |
| Windows: `python` opens the Store | install Python 3 and ensure `py -3` or `python3` works; `OWFA_PYTHON` overrides |
| kernel `list-remote` fails | network/raw access; the registry index is fetched from GitHub raw. The framework itself still works offline |

## 11. File map after install

| Path | Purpose | Safe to edit by hand? |
|---|---|---|
| `AGENTS.md` | identity/layout (yours) + injection region (kernel) | outside the markers, yes |
| `vault/` | real assets | yes — the human owns it |
| `wiki/` | markdown world, proxies, notes, sessions | yes, via commands; derived pages are rebuilt |
| `wiki/index.md`, `tags.md`, `hot.md`, `log.md` | derived layer | no — the pipeline rewrites them |
| `.owfa/plugins/` | Core plugins + installed packages | no — framework authoring |
| `.owfa/scripts/` | kernel, pipeline, wikilib | no — framework authoring |
| `.owfa/command/` | command masters | no |
| `.agents/skills/` | deployed skill copies | no — `kernel deploy` syncs them |
| `.owfa/migrations/` | staged semantic migrations + ledger | no — kernel zone |
| `projects/` | project containers (if the project package is installed) | yes — project-owned |

## 12. FAQ

- **Existing vault with content?** Additive: `init` creates/extends the framework trees, never touches your files. New assets go through `map`; whether to proxy old content is your decision, incrementally.
- **Can I use Obsidian?** Yes — it is a viewer. The framework writes plain markdown plus files; no plugin is required.
- **Can I copy the whole `.agents/` tree?** Yes; this repository's `.agents/` contains only `skills/`.
- **Windows?** Pure stdlib, no hardcoded paths; the CLI probes `py -3`. Git Bash or PowerShell both work.
- **Offline?** `npm pack` the CLI on a connected machine, copy the `.tgz`, `npm install -g ./owfa-x.y.z.tgz`, then `owfa init`. Packages can be copied as `domains/<pkg>/` and converged with `all`.
- **Multiple workspaces?** One instance per directory; they are independent. The CLI can init/upgrade any path.
- **Where do plugins come from?** The registry index; unindexed repos are installable with `--yes` (trust: unknown). See [packages.md](packages.md) for the package model and `PKG.yaml`.

## Appendix — command cheatsheet

| Goal | Command |
|---|---|
| Install (target name) | `npx owfa init <dir>` |
| Install (fallback name) | `npx owfadev init <dir>` |
| Health check | `npx owfa doctor <dir>` |
| Framework upgrade | `npx owfa upgrade <dir>` (or `--check` / `--backup`) |
| Package catalog | `owfa list` / `kernel list-remote` |
| Installed packages | `owfa pkg` / `kernel pkg` |
| Install a package | `owfa add <pkg>` / `kernel install <pkg> --yes` |
| Package upgrade | `kernel upgrade` (report) / `kernel upgrade <pkg> --yes` |
| Package uninstall | `kernel uninstall <pkg> --yes` |
| Pending migrations | `kernel migrate` / `kernel migrate <pkg> --clear` |
| Structural check | `kernel validate` |
| Full convergence | `kernel all` |
