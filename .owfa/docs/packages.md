# Packages

> Design record of the split-improvement phase (2026-10-12 → 10-13: binding round issue #20, discovery/download/update, teardown). Mechanism and — more importantly — the reasons behind each decision. Authoritative mechanics live in the kernel (`owfa_kernel.py`) and in the `PKG.yaml` declarations; this page explains why they are shaped this way.

## Layout: directory == package

`.owfa/plugins/` is two-level:

```
.owfa/plugins/
├── core/            # 20 framework plugins (the two roots + cross-cutting pieces)
│   ├── wiki/ …
└── domains/         # one directory per package = the install unit
    ├── cuhksz/      #   PKG.yaml + 8 plugin masters
    ├── lark/        #   PKG.yaml + 4 plugin masters
    ├── email/  bili/  project/
```

The **directory boundary == tier boundary == package boundary** — the same structure fact expressed once. Projections stay id-keyed and flat (`.owfa/command/`, `.agents/skills/`, registry, the AGENTS injection region): packages regroup masters, not projections, so deploy/inject/registry needed no redesign.

| Unit | Members | Connectors | Depends |
|---|---|---|---|
| framework (core) | 20, incl. the explicit vault/mapping/structure exception — the default domain is constitutional infrastructure, the mapping proxy layer belongs to the wiki body | — | — |
| cuhksz | cuhksz · bb · bb-map · bb-track · bb-teach · bb-quiz · sis · registry | bb-cli, sis-cli | framework |
| lark | lark · lark-docs · lark-im · lark-calendar | lark-cli (external) | framework |
| email | email | mail-cli | framework |
| bili | bili | bili-cli | framework |
| project | project | — | framework |

Why the vault-exception matters: a naive "all domains are packages" split would ship the default domain out of the framework — but every instance boots on vault/mapping/structure before any package exists. Exceptions are declared, not discovered.

## PKG.yaml

```yaml
schema_version: 1
id: cuhksz
version: 0.1            # release ordinal, rides the git tag — NOT tied to member versions
compat: ">= 0.2"        # framework version floor, checked against .owfa/VERSION
members: [cuhksz, bb, bb-map, bb-quiz, bb-teach, bb-track, sis, registry]
connectors:             # tri-state:
  - name: bb-cli        #   in-repo: path (code ships with the package)
    path: connectors/bb-cli
  - name: lark-cli      #   external: maintained outside (declaration only)
    external: true
  - name: gh            #   system: a preinstalled binary (capability + version expectation, no code)
    system: true
    expect: ">= 2.0"
depends: [framework]    # v1 flat graph — no package-to-package edges
uninstall:              # declaration, never executable hooks
  retains: [wiki/cuhksz/, cuhksz/]       # data zones never touched by the kernel
  credentials: [~/.bb-cli/, ~/.sis-cli/] # prompted, never auto-deleted
  bridges: [profile#domain-cognition]    # semantic registration points to check
  processes: []                          # long-running executors to stop
```

## Invariants

**Authoring side (D1): `members` == the maximal family closure.** The kernel computes the closure (depends chains reaching the package root) and diffs it against the declaration both ways — drift is a validate error.

*Why declare at all, when the closure is computable?* Because **the depends graph is live and a package is a versioned anchor**. A closure-derived package would silently change contents as the graph evolves — the same tag would ship different things at different times. The declared roster pins contents to the version; reconciliation turns structural drift into a commit-time error instead of an install-time surprise. Redundant, but self-verifying — the third application of the owner×commands dual-declaration pattern.

**Site side (D5): v1 requires full presence** — every member on disk. The subset grammar is fixed now so it never breaks the validator later: `installed ⊆ members`, non-empty, dependency-closed, root mandatory. Prunability classes:

| Class | Example | Rule |
|---|---|---|
| leaf consumers | bb-teach, bb-quiz | freely prunable — nothing depends on them |
| structural members | bb, bb-map, bb-track | prunable only together with their dependents (the closure rule enforces it) |
| family root | cuhksz | never prunable — owns territory, identity page, roster line |
| connectors | bb-cli | prunable when no installed member consumes it |

`--without` is a reserved parameter (v1 reports not-yet-open). Its promise is semantic — zero injection, zero skill surface, zero credentials — not physical: a cached clone of reviewed code is not an exposure surface, so sparse download stays an optimization outside the contract. Family-root roster lines are capability catalogs; **skill presence is the call-time truth** (tolerant degradation, no dynamic reassembly of inject text).

## Versions (D2)

`.owfa/VERSION` anchors the framework (`0.2`, git tag `v0.2`); the kernel contract changes (manifest fields, projection rules) are what bump it. Package versions are release ordinals riding their own tags; **member plugins keep their own changelog versions and the two levels never lockstep** — a package is a distribution unit, not a semantic one.

## Kernel surface

| Command | What it does |
|---|---|
| `validate` | full graph + package reconciliation (closure diff, presence, flat graph, compat vs VERSION) |
| `validate --scope <pkg>` | single-package tolerant mode (D3): deps absent outside the package degrade to warnings — the CI shape for package repos post-split, run with a framework checkout alongside |
| `pkg` | package inventory: members, connectors, implicit core remainder |
| `residual <pkg>` | D6 residual scan: greps handwritten AGENTS region + profile/language/calendar/todo/cron anchors for member references (the kernel-managed injection region is skipped — it is cleaned mechanically) |
| `install <pkg>[@tag]` | resolve the [registry](https://github.com/owfadev/registry) index (members reconciled against PKG.yaml) → trust gate → clone → prospective manifest/budget preflight → copy masters/connectors/commands → converge. `install <owner/repo> --yes` installs an unindexed repository (trust: unknown); `--path <dir>` installs a local one (channel C) |
| `uninstall <pkg> --yes` | D6 four-clear (masters/commands/connectors/skills) + convergence + residual scan + retains/credentials reminders — data never touched |
| `list-remote` | index table with installed marks |
| `plan <pkg>` | dependency disclosure before a package lands |
| `migrate [<pkg>] [--clear] [--force]` | pending semantic migrations: status / clear (author verify + teardown residual gate; use-and-delete) — see [Migrations](#migrations-the-algebra-0--x--y--0) below |
| `upgrade` | reconciliation report (local vs index); applying runs a **silent reinstall** per package (never cascaded) — member deltas, changelog excerpts, chained migration staging |

*Why scope mode exists before the split:* after the split the framework repo and each package repo no longer contain the full graph — validate would be blind exactly where it matters most. Absence-tolerance turns "plugin missing" from an error into a listed warning, keeping every repo self-checkable.

### Install failure handling

Before copying into the instance, `install` stages the prospective masters in a temporary directory using the actual install filter (including `--without` and its dependent-member pruning). It combines them with installed manifests and checks manifest/dependency rules and the existing UTF-8 injection budget. A rejection returns exit 1 before changing package masters, commands, connectors, migration state, journal or projections. Registry lookup may still refresh its local index cache; downloaded temporary sources are discarded on preflight rejection, while a caller's `--path` source is retained.

After copying, full binding/bridge/package validation and projection/deployment still run. Failure returns exit 1 with an incomplete-state warning; later projection steps stop when a preceding step returns failure. This is **not transactional rollback**: errors discovered after preflight, filesystem failures, or concurrent changes can leave files behind. Inspect the reported errors and run `kernel validate` before recovery; a successful diagnostic does not itself repair missing projection markers. Pending semantic init migrations retain the existing behavior: mechanical install can return 0 while explicitly reporting pending work, and `validate` stays red until the migration is completed and cleared.

The 16 KiB limit and its calculation are unchanged (#48/#49). This does not make `upgrade` transactional: its existing uninstall/reinstall sequence can remove the old package before the install preflight runs. Uninstall's own return-code contract is unchanged.

Offline regression suite: `python -m unittest discover -s .owfa/tests -p test_install_preflight.py -v` (synthetic packages; no network or credentials).

## Uninstall contract (D6)

No executable uninstall hooks — that would be a **third execution surface** (after inject text and connectors), running at a privileged moment; the security model declines. Instead the package *declares* its deletion semantics (`uninstall:` above) and the flow is: kernel mechanical four-clear (directory / injection / registry / projections) → residual scan output → agent semantic finish per the declaration (credential reminders, process stops, bridge registration lines) behind a confirmation gate. **Data and credentials are never auto-deleted** — the freedom to delete belongs to the human; retained data zones lapse into the deprecated posture.

## Migrations: the algebra 0 → x → y → 0

Package state changes are **semantic migrations carried by declarations, not hooks**. Three kinds close the algebra:

| Kind | Files | Staged when | Lives until |
|---|---|---|---|
| init (0→x) | `migrations/init.md` (+ optional `init.py`) | fresh install | verify-clean `--clear` |
| migrate (x→y) | `migrations/x-to-y.md`, frozen at release | an upgrade landing that version | verify-clean `--clear` |
| teardown (x→0) | `migrations/teardown.md` | **every install, dormant**; consumed at uninstall | residual-clean `--clear` |

Mechanics: the kernel stages declarations into `.owfa/migrations/<pkg>/` (kernel zone — never inside the package dir), keeps a ledger (`pending.json`), and raises the **tri-face warning**: a banner on every kernel invocation · `validate` stays red — mechanical blessing is withheld until the semantic step is done · a kernel-managed block lands in the AGENTS injection region so every session sees it. Clearing runs the author's `verify(ctx)` — AST-gated (read-only, stdlib-only) — then deletes the staged files (**use-and-delete**: declarations are useful precisely once; assertions that hold forever belong in the package's `scripts/check.py` — the judgment split rule).

**Sweep symmetry** keeps the ledger honest without a cron: migrate-kind entries die with the package (uninstall sweeps them), teardown-kind entries die with reinstall (install sweeps them). The dormant `PKG.yaml` copy in the staging directory doubles as a **presence marker**: after a manual `rm -rf` of a package directory, the marker lets the kernel sweep the full mechanical residue — commands, connectors, skills, ledger, banner. Self-healing with no hooks.

**Teardown gate**: teardown declares semantic deletions; with no author script the kernel scans the anchor surfaces (the AGENTS handwritten region, profile / language / calendar / todo / cron pages — the kernel-managed injection region is skipped) for member references — word-boundary, deliberately broad: a layout line naming the territory, a cognition registration line, a calendar source key are all references the human side must finish deleting. Clean anchors clear; hits block `--clear` (override `--force`, on your own judgment). The kernel journal (`.owfa/kernel-journal.log`, rolling cap of 500 lines, git-tracked) records the mechanical chain — install / warn+ / clear / uninstall / sweep; mechanical facts only, semantic narrative stays in the instance wiki's log.

## Manifest schema

`schema_version: 1` on PLUGIN.yaml and PKG.yaml. One format migration shared with the upcoming behavior contracts (#34: owns/trigger/emits/never) — versioning the schema once avoids a second format churn when #34 lands.

## Decision ledger

| # | Decision | One-line reason |
|---|---|---|
| D1 | declared roster + closure reconciliation | live graph vs versioned anchor; drift → commit-time error |
| D2 | package version ≠ member versions | distribution unit ≠ semantic unit; lockstep is a trap |
| D3 | scope/tolerant validate in the binding round | the split is only safe if repos can self-check without the full graph |
| D4 | instance-local packages live in `domains/` too | one semantic: package directory == install unit; zero-index private packages |
| D5 | subset grammar fixed now, `--without` opens on demand | validator format never breaks; first real subset user triggers it |
| D6 | declarative uninstall, no hooks | third execution surface declined; deletion knowledge becomes reviewable data |
| D7 | migrations are declarations closing 0→x→y→0; teardown ships dormant with every install | semantic change rides reviewable files; the x→0 case must be declared *before* the package is gone |
| D8 | sweep symmetry + dormant PKG.yaml presence marker | ledger truth without a cron; manual `rm -rf` still self-heals (no hooks anywhere) |
| D9 | teardown gate = residual scan by default, author scripts optional | D6's no-hooks principle extended to deletion *verification* — zero-script packages still get a semantic gate |

## Transport contracts (transports block, optional per plugin)

A domain may declare a connector-agnostic capability so that any conforming
transport — the first-party connector, a third-party one, or a harness-native
channel — can serve it (work order #56, owfa#27):

```yaml
transports:
  contract: qq.transport.v1      # capability id (required)
  recommends: qq-cli             # default connector (optional; installed under connectors/<id>)
  declaration: qq/policy.md      # wiki page whose frontmatter `transport:` marks an active third-party transport (optional)
  providers:                     # known implementations — routing data, never enforcement
    - {id: qq-cli, harness: universal, guarantees: [allowlist-enforced, passive-only, openid-hashed]}
    - {id: napcat-bridge, harness: universal, guarantees: [active-send], trust: reviewed-3rd-party}
```

`validate` checks the block structurally and judges health mechanically: contract
declared but neither the recommended connector installed nor the declaration page
carrying a `transport:` field → warning (unhealthy-but-usable; the domain's skill
degrades to guidance). Guarantee semantics: **undeclared = guarantee absent** — the
agent-side discipline is the floor, transport-side enforcement is hardening on top.
Registry rows may mirror `provides:` / `harness:` for cross-package discovery.
