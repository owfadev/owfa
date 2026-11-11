# Quickstart

> The five-minute path. Full guide — components, channels, packages, upgrades, troubleshooting: [deployment.md](deployment.md). The channel's design and release record: [distribution.md](distribution.md).
> Status: npm `owfa` is under application (frozen on similarity grounds); until the registry serves it, the git channel works today. The fallback package `owfadev` carries the same CLI once published.

## 1. Prerequisites

- **Python 3.9+** — the framework and kernel are pure stdlib; no pip, no venv.
- **Node 16.7+** — only for the npm channel (the CLI is Node).
- **An agent** that reads `AGENTS.md` and `.agents/skills/` (ZCode, Claude Code, Cursor, dsh…).
- **git** recommended — instance snapshots and the upgrade rollback path.

## 2. One command (npm channel)

| Item | Requirement |
|---|---|
| Python | 3.9+, pure standard library, zero dependencies |
| agent | A coding assistant that can read AGENTS.md and `.agents/skills/`, e.g. ZCode |
| Obsidian | Optional, viewer only |

## Three postures

**0. One command (npm channel).** `npx owfa init <your-vault>` — fetches the framework, creates the directories, writes the AGENTS shell (or appends only the injection region to an existing one), and converges the projections. Then `cd <your-vault> && npx owfa doctor`. This is the same deployment as ①–⑤ below, mechanized; the manual steps remain the reference, the offline path and the developer path. Optional packages: `npx owfa init <dir> --packages cuhksz,lark`; later `npx owfa upgrade` replaces the framework trees and preserves the kernel's migration state. Details: [distribution.md](distribution.md).

The manual steps below serve A and B; posture 0 skips them.

**A. Just using it (clone-as-instance).** A clone of this repository *is* your instance: `git clone https://github.com/owfadev/owfa.git <your-vault>`, optionally `rm -rf <your-vault>/.git && git init` to own the history, then do steps ③–⑤ below (AGENTS.md shell, four directories, converge). Packages install on demand from the registry — `kernel install <pkg> --yes`. No development intent needed; you never touch the framework internals.

**B. Developing (template + instance).** Keep a clone of this repository as the *template* — development, experiments and upstream updates happen there, following [CONTRIBUTING.md](../../CONTRIBUTING.md). Separately deploy a real *instance* (your actual vault — posture A's steps, or the embedding steps below); when the template gains updates, review the diff and sync selectively into the instance, then converge — see the "Template + instance workflow" section of CONTRIBUTING.md. To develop is to run a real instance: the framework is validated in actual use, not in the abstract.

## Five deployment steps

**① Get the framework**: `git clone https://github.com/owfadev/owfa.git`, or download the ZIP and unzip it (the old personal-repo address redirects).

**② Copy two trees** to the target vault root: `.owfa/` and `.agents/skills/`. Plugin masters, command masters and copies, protocol artifacts, and mechanical scripts all live there. The clone ships **core 20 only** — no domain packages. Packages are added per need from the registry: `python3 .owfa/scripts/owfa_kernel.py install <pkg> --yes` (see [packages.md](packages.md)); offline alternative — copy a package's `domains/<pkg>/` directory in and rerun `all`.

**③ Write the target vault's AGENTS.md**: draft the shell yourself—one identity paragraph plus a layout description; copy the injection region marker block verbatim from [agents-example.md](agents-example.md), not a single character changed—from `<!-- wiki-inject:start -->` to `<!-- wiki-inject:end -->`—it is the sole source of the structural contract. If the target vault already has an AGENTS.md, paste in only the injection region block.

**④ Create four empty directories**: `vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`. Derived pages need no hand-creation—index, tags, hot, and log are built by the pipeline on first run; the root index's `format_version` is also rendered by the pipeline.

**⑤ Converge the projections**, run at the target vault root:

```
python .owfa/scripts/owfa_kernel.py all

The npm name `owfa` is under application (similarity freeze); until it is granted the fallback package serves the same CLI: `npx owfadev init my-workspace`, `npx owfadev doctor`, etc. — substitute `owfadev` for `owfa` in every command above.
```

`init` copies `.owfa/` + `.agents/skills/`, creates `vault/` and the three wiki directories, writes or appends `AGENTS.md`, and runs the kernel. Existing content is untouched. Optional packages: `npx owfa init my-workspace --packages cuhksz,lark`.

Already have a workspace? `init` refuses if `.owfa/` exists; use `npx owfa upgrade` (or `--force` to re-copy the framework trees).

## 3. Manual five steps (git or offline)

1. **Get the framework**: `git clone https://github.com/owfadev/owfa.git my-workspace` — a clone is a valid instance (the pre-rename `AIE3905-Wuwa/vault-wiki` URL redirects). To embed into an existing vault, clone the template elsewhere and copy `.owfa/` + `.agents/skills/` into the target root.
2. **Write `AGENTS.md`**: one identity paragraph, one layout paragraph, and the injection markers verbatim from [agents-example.md](agents-example.md). Existing `AGENTS.md`? Paste in only the marker block.
3. **Create four directories**: `vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`.
4. **Converge**:
   ```bash
   python .owfa/scripts/owfa_kernel.py all
   ```
5. **Verify**: drop a file into `vault/`, open an agent at the root, say "map", then "check".

There is no separate kernel install: the kernel is `.owfa/scripts/owfa_kernel.py` inside the tree; Python 3.9+ runs it. On Windows use `py -3` or set `OWFA_PYTHON`.

## 4. Next

```bash
owfa list                  # registry catalog: packages, versions, installed marks
owfa add cuhksz            # install a domain package (stops at a semantic migration if one is staged)
owfa pkg                   # what is installed here
owfa upgrade               # later: replace the framework trees, preserve instance state
```

These assume a global install (`npm i -g owfa` or `npm i -g owfadev`); without one, use `npx owfa …` / `npx owfadev …`.

- Package lifecycle, trust levels, offline installs, uninstall: [deployment.md](deployment.md#7-packages--finding-and-installing).
- Daily use: [usage.md](usage.md); mechanics: [mechanics.md](mechanics.md).
- Developing the framework itself: [CONTRIBUTING.md](../../CONTRIBUTING.md).
