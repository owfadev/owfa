# Plugin Lifecycle

> The third-party developer's view of plugin governance: develop → publish → be found → install → update → uninstall, plus the name-governance rules that keep the ecosystem collision-free. Companion to [packages.md](packages.md) (the package model and its design decisions) and [developer.md](developer.md) (where a plugin lands); this page walks the whole arc from the outside in. **Draft** — scheduled for a dedicated pass in the v0.4.1 docs round; the kernel (`owfa_kernel.py`) and the `plugin` command skill are authoritative where this page and they disagree.

## 1. Develop

One plugin, one directory, three pieces:

- `PLUGIN.yaml` — the manifest, the machine-readable body
- `PLUGIN.md` — pure documentation: design summary, Structure, Invariants, Changelog
- `scripts/check.py` — optional attached audit; `check(ctx)` returning `[{level, message}]`, read-only, statically validated via AST

Seven required manifest keys: `id` / `version` (`X.Y` organ ordinal) / `updated` / `depends` / `attachment` (the territory ownership registry: owning vs borrowing) / `fields` / `inject` (the constitution-level disclosure line). Optional keys include `commands`, `usage`, `checks`, `bridge`, `inject_tier` (full|member), `usage_routes`, and the `transports` block (contract id grammar: see [packages.md](packages.md) §Transport contracts).

The manifest is a **minimal YAML subset** — top-level scalars, `key: []`, block lists, one-level block mappings; anything richer is silently dropped, so keep declarations flat.

**The validate gate**: `kernel validate` (or `validate --scope <pkg>` inside a package repo, where out-of-package dependencies degrade to warnings) checks manifest compliance, dependency existence and acyclicity, command bindings, the bridge law, and package reconciliation (`members` == family closure, both directions). Errors block; warnings report.

**One source, five projections**: from the manifest the kernel projects into the AGENTS injection region (`<!-- plugin:<id> v<x> -->` blocks), the check command's inspection blocks, command usage blocks, the registry's field vocabulary, and the `.agents/skills/` copies. Never hand-edit a projection — change the manifest, run `all`, everything converges. The projected region carries a byte budget (16 KiB) and each full-tier inject line a 256 B pointer-density guideline.

## 2. Publish

A plugin never ships bare — the **package is the distribution unit** (a lone plugin is a single-member package; 12 lines of PKG.yaml). Publishing is:

1. Author `PKG.yaml` — `id`, `version` (`A.B.C`, the domain's own release semantics, never lockstep with the framework), `compat` floor (checked against `.owfa/VERSION`), `members` roster, `connectors` (tri-state: in-repo path / external / system), `depends: [framework]`, and the declarative `uninstall:` block (retains / credentials / bridges / processes — declaration, never executable hooks).
2. Tag the release: `git tag <pkg>-vA.B.C` — the tag, the PKG version, and the registry row must agree; the kernel refuses drift at install/upgrade. The core suite follows the same rule with `personal-vA.B.C` tags (package **owfa-personal**).
3. Open a one-line PR to the [registry](https://github.com/owfadev/owfa-registry) (`INDEX.yaml`). This PR is the **human-review gate** — inject text and connectors are the security faces, so an index row is earned, not claimed. The PR is also where the trust level is assigned.

Bump rules in brief: **A** only at graduation; **B** = contract change (roster, schema, page shape, trust model — the only carrier of semantic migrations, named by B-line pairs like `0.2-to-0.3`); **C** = in-architecture updates, never migrations; changed tree ⇒ new number, always.

## 3. Be found

- `kernel list-remote` — the registry catalog: package versions, compat floors, member plugins, trust levels, installed marks.
- `kernel plan <pkg>` — the consent wizard's data source: trust level, package disclosure, baseline/optional members, connectors, suggested command. One-shot and never interactive — the *agent* runs the consent conversation; the kernel only discloses.

## 4. Install

Three channels:

| Channel | Form | Trust |
|---|---|---|
| A — registry | `kernel install <pkg>` (optionally `<pkg>@<tag>`) | from the index row: `framework-bundled` / `reviewed-3rd-party` install without a prompt; anything else needs `--yes` |
| B — unindexed repo | `kernel install <owner>/<repo> --yes` | unknown — `--yes` is the trust gate; the registry PR is how a package earns reviewed trust |
| C — local path | `kernel install <pkg> --path ./dir` | you reviewed it by hand; no registry involved |

Before copying anything, `install` **stages the prospective masters in a temp directory** with the actual install filter and runs manifest/dependency/budget preflight against the combined (installed + incoming) set — a rejection exits 1 before any file changes. After the copy, convergence (validate → inject → registry → deploy) runs; failure there is *not* transactional — inspect, fix, `kernel validate`. A package declaring a first-run semantic migration (`migrations/init.md`) installs mechanically but leaves `validate` red and a banner up until an agent performs the semantic step and clears it (`kernel migrate <pkg> --clear`).

## 5. Update

- `kernel upgrade` — read-only reconciliation report (local versions vs the index).
- `kernel upgrade <pkg> --yes` — **silent reinstall** per package, never cascaded: member deltas, changelog excerpts, and chained migration staging. Crossing a B-line stages the corresponding `x-to-y` migration declarations.
- The framework itself updates through its own channel — npm (`owfa upgrade`) or git re-copy — never through package upgrade.

## 6. Uninstall

`kernel uninstall <pkg> --yes` runs the mechanical **four-clear**: package directory (masters), commands owned by members (masters + skill copies), connectors, and projections (injection region and registry rebuild via convergence). Then:

- **residual scan** — the kernel greps the semantic anchor surfaces (handwritten AGENTS region, profile / language / calendar / todo / cron pages) for member references, word-boundary and deliberately broad; hits are the human-side cleanup list (the kernel-managed injection region is skipped — it is already cleaned mechanically).
- **reminders, never deletions** — `retains` zones and `credentials` are reported, never auto-deleted; **data zones and credentials are never touched by the kernel**, ever. The freedom to delete belongs to the human.
- A declared `teardown.md` (staged dormant at every install) flips to a pending warning at uninstall — semantic deletion debt with the same tri-face banner and a residual-gated `--clear`.

## 7. Name governance (three gates)

Collisions are stopped mechanically at three layers:

1. **Plugin id** — `validate` errors on a duplicate plugin id (two layouts declaring it) *and* on install-time duplicates (an incoming package whose member id is already installed is rejected at preflight).
2. **Package id** — the registry `INDEX.yaml` is keyed by package id; the index PR review is where ownership of a name is decided, before anything is installable by that name.
3. **Command names** — owner × commands mutual declaration: a command's `owner` frontmatter and a manifest's `commands` list must agree bidirectionally; one-sided claims, ownerless commands (missing `owner`), and framework combined with other owners are all validate errors. Two packages therefore cannot silently ship the same command name.

Transport/capability names follow the same philosophy: the contract id grammar (`<namespace>.<capability>.v<ordinal>`) namespaces every capability under its declaring package (or the framework-reserved `owfa.`), mechanically checked — see [packages.md](packages.md).
