# Packages

Reader: package authors, instance maintainers, and anyone who wants to know what `install` / `uninstall` actually do.

The package is the distribution and install unit. This page is the consolidated reference: package layout, every `PKG.yaml` field, suite vs domain-family semantics, the capability mechanism, install channels and trust, the install/uninstall/residual contract, versioning and tags, and the registry line format. The kernel (`.owfa/scripts/owfa_kernel.py`) and the `PKG.yaml` declarations are authoritative; this page explains the mechanism and the reasons. It absorbs the former `plugin-lifecycle.md` (the develop → publish → be found → install → update → uninstall arc) and the name-governance rules.

## Package layout: directory == package

The v0.4 framework tree ships **no plugins** — kernel, 6 framework command masters (`.owfa/command/`), protocol artifacts (`.owfa/protocol/`), and the embedded blessed suite copy at `payloads/personal/`. Connectors travel with their packages (cuhksz-cli in owfa-cuhksz, mail-cli in owfa-email, bili-cli in owfa-bili); their SKILL.md files land in `.agents/skills/` via kernel deploy.

In an instance, installed packages live under `.owfa/plugins/domains/` — one directory per package, the directory boundary == install unit:

```
.owfa/plugins/domains/
 ├── personal/    # the blessed suite (kind: suite) — installed by default init
 ├── cuhksz/      # PKG.yaml + plugin masters + connectors/cuhksz-cli
 ├── email/  bili/  project/  ...
```

## Command tiers — which commands come from where

| Tier | Commands | Present in |
|---|---|---|
| framework built-ins (`.owfa/command/`) | asset-read, owfa-check, owfa-docs, owfa-kernel, owfa-plugin, owfa-query | **every workspace, any protocol** — they answer "why does my project-protocol workspace have asset-read" |
| protocol suite | personal: owfa-map, owfa-save, owfa-profile · project: (none in the suite itself) | workspaces running that protocol |
| package commands | arrive with their package — e.g. owfa-develop ← the optional `owfadevelop` package; connector skills likewise ride with their packages | workspaces that installed the package |

Projections stay id-keyed and flat (`.owfa/command/`, `.agents/skills/`, the registry, the AGENTS injection region): packages regroup masters, not projections, so deploy/inject/registry needed no redesign.

| Package (repo) | Kind | Members | Connectors |
|---|---|---|---|
| framework (the channel tree) | — | none — kernel + framework commands only | — |
| personal (**owfadev/owfa-personal**) | suite | 21 plugins (the former core, incl. the vault/mapping/structure boot exception) + 3 own commands (owfa-map / owfa-save / owfa-profile) | — |
| owfa-cuhksz | domain-family | cuhksz · bb · bb-map · bb-track · bb-teach · bb-quiz · sis · registry | cuhksz-cli (aggregates bb\|sis) |
| owfa-lark / owfa-email / owfa-bili / owfa-project / owfa-github / owfa-diary / owfa-qq | domain-family | per their PKG.yaml | lark-cli / mail-cli / bili-cli / — / gh / — / qq-cli |

Why the vault exception matters: a naive "all domains are packages" split would ship the default domain out of the framework — but every instance boots on vault/mapping/structure before any other package exists. Since the v0.4 split these boot plugins ride as members of the embedded personal suite (exceptions declared, not shipped as framework files). The framework copy stays in sync via `scripts/sync-blessed.sh`, which pulls tag-mode `personal-v[0-9]*` releases from owfa-personal into `payloads/personal/`.

## PKG.yaml — every field

The blessed suite, verbatim (`payloads/personal/PKG.yaml`):

```yaml
schema_version: 1
id: personal
kind: suite
version: 0.1.0
compat: ">= 0.4"
members: [calendar, cron, device, domain, hot, index, instance-git, language, link, log, mapping, notes, sessions, structure, tag, tmp, todo, trust, user-profile, vault, wiki]
depends: [framework]
skeleton: [vault/, wiki/notes/, wiki/sessions/, wiki/vault/]
uninstall:
  anchors: [wiki/profile.md, wiki/language.md, wiki/calendar.md, wiki/todo.md, wiki/cron/]
  retains: [vault/, wiki/]
  credentials: []
  bridges: []
  processes: []
disclosure: "Purely local information organization (calendar / todo / notes / sessions / vault proxies / tags / index / logs / cron intents); no network services, no credentials, no external data sources — all content stays on this machine's repository."
```

Field by field (the personal line is the example throughout):

| Field | Meaning | personal value |
|---|---|---|
| `schema_version` | manifest format version (1) — versioned once, shared with the upcoming behavior contracts | `1` |
| `id` | package id; must equal the directory name and the registry key | `personal` |
| `kind` | `suite` \| `domain-family` (default when absent) | `suite` |
| `version` | the package's own `A.B.C` release semantics — rides the `<pkg>-vA.B.C` git tag, never lockstep with the framework and not tied to member versions | `0.1.0` |
| `compat` | framework version floor, machine-checked against `.owfa/VERSION` | `">= 0.4"` |
| `members` | the declared plugin roster; for domain-family it must equal the maximal family closure (see below) | 21 ids |
| `depends` | v1 flat graph — `[framework]`, no package-to-package edges | `[framework]` |
| `skeleton` | instance directories the package needs; install mkdirs them mechanically (the kernel hardcodes no layout — default init's four dirs come from this line) | `vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/` |
| `uninstall.anchors` | teardown anchor surfaces added to the kernel floor (the AGENTS.md handwritten region) for the residual scan; additive only, a directory anchor expands to the .md files inside it | `wiki/profile.md` … `wiki/cron/` |
| `uninstall.retains` | data zones never touched by the kernel — reported at uninstall, never deleted | `vault/`, `wiki/` |
| `uninstall.credentials` | credential locations — prompted, never auto-deleted | `[]` |
| `uninstall.bridges` | semantic registration points to check at teardown | `[]` |
| `uninstall.processes` | long-running executors to stop | `[]` |
| `needs` / `provides` | package-scale capabilities (plugin level deliberately unsupported) — see below | — (declares `provides: owfa.org.v1` in its registry row) |
| `disclosure` | the one-line privacy/behavior disclosure shown by `plan` before consent | the quoted line above |

Packages that ship connectors additionally declare a `connectors:` list (tri-state): in-repo (`name` + `path: connectors/<id>` — code ships with the package), external (`external: true` — declaration only), or system (`system: true` + `expect: ">= 2.0"` — a preinstalled binary, capability + version expectation, no code). Example from owfa-cuhksz: `cuhksz-cli` in-repo; owfa-lark: `lark-cli` external; `gh` system.

The `uninstall:` block is a **declaration, never executable hooks** — no third execution surface (after inject text and connectors) running at a privileged moment; deletion knowledge becomes reviewable data.

PKG.yaml is a **minimal YAML subset** — top-level scalars, `key: []`, block lists, one-level block mappings; anything richer is silently dropped, so keep declarations flat.

## kind: suite — rootless semantics

`kind: suite` declares a **rootless** package: N parallel members, no family root plugin and none required (the owfa-personal shape). Consequences:

- **no synthetic root** — the kernel does not invent a root plugin for the package;
- **no synthetic dependency edges** — members do not get edges to a phantom root; `depends` stays the flat v1 graph;
- the **family-root / closure laws do not apply**: the family closure method (members == closure of depends chains reaching the package root) is the **domain-family** invariant only. A suite's `members` roster is presence-checked (subset discipline) but not closure-diffed.

Absent `kind` = the classic domain-family behavior (default): the kernel computes the family closure and diffs it against `members` both ways — drift is a validate error. Why declare at all, when the closure is computable? Because the depends graph is live and a package is a versioned anchor: a closure-derived package would silently change contents as the graph evolves. The declared roster pins contents to the version.

Site side, v1 requires full presence — every member on disk; the subset grammar (`installed ⊆ members`, non-empty, dependency-closed, root mandatory for domain-family) is fixed so `--without` never breaks the validator: `kernel install <pkg> --without a,b` (and `owfa add <pkg> --without a,b`) installs a validated subset today — installed members get a `suite subset install` note in validate. Its promise is semantic — zero injection, zero skill surface, zero credentials — not physical.

## kind: protocol — the step2 shape rulings (R1–R11)

`kind: protocol` + `protocol: <id>` declared together make a **protocol package** — the holder of a workspace protocol. The shape rulings, in force since step2 (0.4.5/0.4.6; canonical text: step2-spec v2), enumerated once here because kernel.md and abi.md cite them by number:

| # | Ruling (validate-enforced unless noted) |
|---|---|
| R1 | `kind: protocol` ⇔ `protocol:` field present — the pair declares together or not at all |
| R2 | a protocol package provides exactly one `<protocol>.org.v<N>` org capability (ordinary capabilities allowed, prefix = protocol id or package id per R4) |
| R3 | a protocol package is rootless (inherits the full kind:suite discipline: no root, closure laws skipped, all members present) |
| R4 | capability prefix has two legal sources: package id or the package's `protocol:` id; protocol id must not be `owfa` (reserved) |
| R5 | uninstall: retains must cover every data skeleton dir (validate warns on uncovered); the "workspace is protocol-less — a shell" notice lands in uninstall output + doctor, not validate |
| R6 | all-or-nothing: `--without` or member-level-needs pruning touching a protocol member refuses the whole package (subset installs belong to domain families only) |
| R7 | members non-empty; protocol id collides with no installed package id and no other protocol id; protocol id ≠ owfa |
| R8 | org-capability evolution: exactly one `<proto>.org.v<N>` per protocol at any time (v1+v2 coexisting = error); upgrade = in-place replacement, no coexistence window |
| R9 | org capabilities (`*.org.v*`) are protocol-package-only: a non-protocol package providing any org capability is a validate error; one-workspace-one-protocol follows automatically |
| R10 | member-level needs are trust-gated (only trust ≥ reviewed provides satisfy; untrusted = unsatisfied → R6 semantics); grammar = CAPABILITY_RE; `owfa.*` reserved |
| R11 | the two-state ABI qualification line (enforced since 0.4.6; error in 0.5.0) — enumerated in [abi.md §4](abi.md) |

## Capabilities

Package-scale `needs` / `provides` (v0.4). The grammar, mechanically checked by `validate`:

```
<namespace>.<capability>.v<ordinal>     e.g. owfa.org.v1
^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$
```

- **Prefix must equal the declaring package id** — a non-`owfa.*` capability's first name segment must equal the package id (`validate` rejects anything else); non-declarer namespaces are refused.
- **`owfa.*` is framework-owned** — those names are defined only in the framework repository; the registry review gate polices ownership at index PR time. Framework-granted exceptions exist: personal's `owfa.org.v1`.
- **Exact-name matching** — `needs: owfa.org.v1` is satisfied only by `provides: owfa.org.v1`, never by a sibling capability or a different ordinal; a v2 provider leaves a v1 need unsatisfied (reported distinctly as a version mismatch).
- **Exclusive slot** — at most one installed provider per exact capability name; two installed packages providing the same name is a validate error.
- **Dual supply is legal across ordinals** — the same base capability at different ordinals (`x.cap.v1` and `x.cap.v2`) may coexist installed; exact-name matching keeps them distinct slots.
- **Trust-gated needs** — only provides at trust ≥ reviewed count (`framework-bundled`, `reviewed-3rd-party`); the **registry INDEX row is the trust source**, so `--path` and owner-repo direct installs (trust: unknown) leave their provides unverified and a need they cover stays red.
- **`--yes` overrides at install, journaled** — the override is recorded in the kernel journal; it does not rewrite trust.

Convergence points: install preflight (prospective set — upgrade boards installed − old + new provides), `validate` (full-graph error, `--scope` warning), `upgrade` (prospective). **Uninstall is deliberately not a point**: removing the last provider leaves a red `validate` while the uninstall itself succeeds (intentional asymmetry).

Name governance generally stops collisions at three mechanical layers: (1) plugin id — validate errors on duplicates and install preflight rejects an incoming member id already installed; (2) package id — the registry `INDEX.yaml` is keyed by package id, ownership decided at the index PR; (3) command names — owner × commands mutual declaration, bidirectionally checked, so two packages cannot silently ship the same command.

## Install channels and trust

| Channel | Form | Trust |
|---|---|---|
| A — registry | `kernel install <pkg>` (optionally `<pkg>@<tag>`) | from the index row: `framework-bundled` / `reviewed-3rd-party` install without a prompt; anything else needs `--yes` |
| B — unindexed repo | `kernel install <owner>/<repo> --yes` | unknown — `--yes` is the trust gate; the registry PR is how a package earns reviewed trust |
| C — local path | `kernel install <pkg> --path ./dir` | you reviewed it by hand; no registry involved |

Trust levels: `framework-bundled` / `reviewed-3rd-party` / `unknown`. The default init's offline step is channel C: `kernel install personal --path payloads/personal`.

Publishing (the package author's arc): author PKG.yaml → bump `version` → tag `<pkg>-vA.B.C` → open the one-line registry PR. The tag, the PKG version, and the registry row must agree — the kernel refuses drift at install/upgrade. The last two steps (tag, registry PR) are deliberately separate small PRs: the registry never freezes with the framework.

## Install / uninstall / residual — the contract

Subcommands (package lifecycle, 8 total incl. `migrate` — see [conversion.md](conversion.md)):

| Command | What it does |
|---|---|
| `plan <pkg>` | dependency disclosure before a package lands: trust level, package disclosure, baseline/optional members, connectors, suggested command. One-shot, never interactive — the *agent* runs the consent conversation; the kernel only discloses |
| `install <pkg>[@tag]` | resolve the registry index (members reconciled against PKG.yaml) → trust gate → clone → prospective manifest/budget preflight → copy masters/connectors/commands → converge |
| `uninstall <pkg> --yes` | mechanical four-clear (masters / commands / connectors / skills) + convergence + residual scan + retains/credentials reminders — data never touched |
| `residual <pkg>` | standalone residual scan: greps the anchor surfaces (AGENTS handwritten region + the package's `uninstall.anchors` pages — profile/language/calendar/todo/cron for the personal suite, per its PKG.yaml) for member references — word-boundary, deliberately broad; the kernel-managed injection region is skipped (cleaned mechanically) |
| `list-remote` | registry index table with installed marks |
| `upgrade` / `upgrade <pkg> --yes` | read-only reconciliation report; applying is a **silent reinstall** per package (never cascaded) — member deltas, changelog excerpts, chained migration staging |
| `pkg` | package inventory: members, connectors, plugins unclaimed by any package |

**Install failure handling.** Before copying, `install` stages the prospective masters in a temp directory with the actual install filter and checks manifest/dependency rules and the existing UTF-8 injection budget against the combined (installed + incoming) set; a rejection exits 1 **before** any file changes (a caller's `--path` source is retained; downloaded temp sources are discarded). After the copy, convergence runs; failure there is *not* transactional rollback — inspect, fix, `kernel validate`. A package declaring a first-run semantic migration installs mechanically but leaves `validate` red and a banner up until the semantic step is done and cleared (`kernel migrate <pkg> --clear`).

**Uninstall contract.** The kernel does the mechanical four-clear, then the residual scan output is the human-side cleanup list; the agent finishes the semantics per the declaration (credential reminders, process stops, bridge registration lines) behind a confirmation gate. **Data and credentials are never auto-deleted** — the freedom to delete belongs to the human; retained data zones lapse into the deprecated posture. A declared `teardown.md` (staged dormant at every install) flips to a pending warning at uninstall — semantic deletion debt with the same tri-face banner and a residual-gated `--clear`.

**Migrations: the algebra 0 → x → y → 0.** Semantic state changes ride declarations, not hooks: init (`migrations/init.md`, fresh install), migrate (`x-to-y.md`, frozen at release, staged when an upgrade crosses a B-line), teardown (`teardown.md`, staged dormant at every install, consumed at uninstall). The kernel stages them into `.owfa/migrations/<pkg>/` with a ledger (`pending.json`) and raises the tri-face warning (banner on every invocation · red validate · a kernel-managed AGENTS block) until cleared via the author's AST-gated `verify(ctx)` — read-only, stdlib-only — then deletes the files (use-and-delete). Sweep symmetry keeps the ledger honest without a cron: migrate-kind entries die with the package, teardown-kind with reinstall; the dormant PKG.yaml copy in staging doubles as a presence marker, so even a manual `rm -rf` of a package directory self-heals the full mechanical residue. The kernel journal (`.owfa/kernel-journal.log`, rolling 500 lines, git-tracked) records the mechanical chain — install / warn+ / clear / uninstall / sweep, and `--yes` trust overrides.

## Versions and tags

Versioning is five layers under one principle: a layer carries release semantics (`A.B.C`) only when a tag or the registry addresses it — the other layers are ordinals answering *how much has this changed*, not *which release is this*.

| Layer | Version | Semantics |
|---|---|---|
| framework / channel | `A.B.C` — `.owfa/VERSION` == `package.json` == tag `vA.B.C` == npm == GitHub release | **A** project status (`0` = alpha) · **B** architecture line · **C** in-line updates |
| packages | `A.B.C` | the domain's own release semantics, independent of the framework (never lockstep) — tags `<pkg>-vA.B.C`, registry rows, migrations |
| member plugins (and core plugins) | `X.Y` | organ revision ordinals — bump on contract or behavior change; no release granularity of their own, they ship with the package's `A.B.C` |
| connectors | repo-internal anchors | engineering changelog — never enters registry / tags / PKG semantics |

Package bump rules: **A** only at graduation (the owner's call; kernel-forced adaptation is not an A event — that coupling lives in `compat`); **B** = the domain contract changed (member roster, disclosure/manifest schema, data or page shape, trust model, compat floor) — the only carrier of semantic migrations, named by B-line pairs (`0.2-to-0.3`); **C** = in-architecture updates, never migrations — a change that moves data or page shape is B, not C. Changed tree ⇒ new number, always; C counts releases, not organ changes (three members changing is one C bump). Sync duties: `PKG.yaml` version == `<pkg>-v` tag == registry row, refused on drift at install/upgrade.

## Registry line format

The registry is **owfadev/owfa-registry** (a repository, not an org): `INDEX.yaml`, one line per package, keyed by package id — the human-review gate (inject text and connectors are the security faces, so an index row is earned, not claimed; the PR is also where trust is assigned). Fields per row:

- `repo` — `owner/name` (organization repos are all `owfa-*`)
- `version` — `A.B.C`, must equal the package's tag
- `compat` — framework floor
- `trust` — `framework-bundled` / `reviewed-3rd-party` (the capability trust source)
- `members` — the plugin roster ('/'-separated)
- `summary` — one line, written for agents (see [developer.md](developer.md) §Discovery)
- `needs` / `provides` — optional capability lists ('/'-separated, mirroring PKG.yaml for cross-package discovery)
- `commit` — optional SHA pin, the supply-chain content anchor: a clone whose HEAD ≠ pin is refused

INDEX-row strings split on `/` (a comma terminates the value in the INDEX line grammar and would silently truncate a list).

## Transport contracts (optional per plugin)

A domain may declare a connector-agnostic capability so any conforming transport can serve it:

```yaml
transports:
  contract: qq.transport.v1      # capability id (required)
  recommends: qq-cli             # default connector (optional)
  declaration: qq/policy.md      # wiki page whose frontmatter `transport:` marks an active third-party transport (optional)
  providers: qq-cli, napcat-bridge   # comma-separated scalar (nested block lists are silently dropped)
```

`validate` checks the block structurally and warns when a declared contract has neither the recommended connector installed nor the declaration page carrying `transport:`. Guarantee semantics: undeclared = guarantee absent — agent-side discipline is the floor, transport-side enforcement is hardening on top. Contract ids follow the capability grammar above.

## Appendix: decision ledger (entries still in force)

| # | Decision | One-line reason |
|---|---|---|
| D1 | declared roster + closure reconciliation (domain-family only) | live graph vs versioned anchor; drift → commit-time error; suites are presence-checked, not closure-diffed |
| D2 | package version ≠ member versions | distribution unit ≠ semantic unit; lockstep is a trap |
| D3 | scope/tolerant validate in the binding round | the split is only safe if repos can self-check without the full graph |
| D4 | instance-local packages live in `domains/` too | one semantic: package directory == install unit; zero-index private packages |
| D5 | subset grammar fixed, `--without` shipped open | validator format never breaks; subset is validated at install time |
| D6 | declarative uninstall, no hooks | third execution surface declined; deletion knowledge becomes reviewable data |
| D7 | migrations are declarations closing 0→x→y→0; teardown ships dormant with every install | semantic change rides reviewable files; the x→0 case must be declared *before* the package is gone |
| D8 | sweep symmetry + dormant PKG.yaml presence marker | ledger truth without a cron; manual `rm -rf` still self-heals (no hooks anywhere) |
| D9 | teardown gate = residual scan by default, author scripts optional | D6's no-hooks principle extended to deletion *verification* — zero-script packages still get a semantic gate |
