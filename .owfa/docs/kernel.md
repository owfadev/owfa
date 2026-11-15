# The Kernel

> Reader: anyone — human or agent — who needs to understand the kernel's mechanics precisely: what `.owfa/scripts/owfa_kernel.py` enforces, projects, and refuses, and where each rule lives in the source. The script itself is authoritative; where this page and the source disagree, the source prevails. Every mechanism below cites the function, check, or constant that implements it (re-verified against the v0.4.8 kernel, 3056 lines) — citations name code identifiers, not line numbers, so they do not drift as the file grows. First written 2026-11-15, absorbing the kernel half of the former `mechanics.md`.

## 1. What the kernel is

The kernel is a **single Python file**, `.owfa/scripts/owfa_kernel.py`, importable and runnable with **Python 3.9+ and the standard library only** — module-level imports are `ast / importlib / os / re / shutil / sys / types` (`owfa_kernel.py`); networking (`urllib`) and process execution (`subprocess`) are imported lazily inside the functions that need them (`owfa_kernel.py`). No third-party dependency, no interpreter beyond CPython. This is a deployment guarantee: any machine that can run the installer's post-install steps can run the kernel.

Its charter is stated in the module docstring: deterministic structural operations go to the script, semantic judgment goes to the LLM; and the script **touches only four places** — plugin directories in and out, the AGENTS.md injection-region marker blocks, the registry plugin section, and the `.agents/skills/` command copies. Protocol artifacts, reserved sections, and handwritten regions are never touched (`owfa_kernel.py`).

The subcommand surface has converged to two groups:

- **7 convergence subcommands** — `ls / validate / audit / inject / registry / deploy / all` (`owfa_kernel.py`, dispatch in `main`)
- **8 package-lifecycle subcommands** — `plan / install / uninstall / list-remote / migrate / upgrade / pkg / residual` (`owfa_kernel.py`, dispatch in `main`)

One auxiliary read-only view completes the surface: `provides` — an offline, disk-read-only report of every installed package's capability provides and the satisfaction status of every needs declaration (`do_provides`).

One **global flag** precedes the subcommand dispatch: `--root <path>` (consumed by `_take_root` before any subcommand is parsed). It re-derives every ROOT-based path constant (`_apply_root`) so a kernel file living anywhere can operate on another workspace tree — this is exactly how the user-level channel serves a workspace: the kernel under `$OWFA_HOME/kernel/<ver>/` runs with `--root` pinned to the workspace, while the workspace's own `.owfa/scripts/owfa_kernel.py` is a thin deprecated host forwarder that execs it (see [deployment.md](deployment.md)).

**Protocol independence.** The kernel knows packages, plugin manifests, dependency graphs, capabilities, and projections — nothing else. It does not know any content protocol: what a "page" should contain, what territories exist, what derived artifacts a workspace keeps — none of it is kernel vocabulary. The cleanest proof is the v0.4.2 ownership split: `pipeline.py` (the data-area derived-layer tool of the vault-wiki protocol, e.g. index/tags/hot/log rebuilding) **left the framework tree for the protocol's suite package** — since suite 0.1.1 it ships at the package root of owfa-personal, and a workspace with the personal suite installed runs it at the instance path `.owfa/plugins/domains/personal/pipeline.py`. The kernel never calls it in any form. Where the pipeline actually lives depends on the channel (verified against 0.4.8 installs): the legacy `init` payload still carries a deprecated framework-tree copy at `.owfa/scripts/pipeline.py` (a compatibility shim for reverse-order upgrades, retiring in 0.5.0); the user-level channel plants no pipeline shim at all — `--user-level` writes only the kernel forwarder under `.owfa/scripts/`. Either way, a workspace without the personal suite package still has a deprecated-but-working framework-tree copy on the legacy channel — while the user-level channel ships no pipeline at all, so a user-level workspace without the suite has no pipeline anywhere. Where the kernel is Protocol-agnostic by design, the protocol owns everything the kernel deliberately does not interpret.

## 2. The package model

Since v0.4, plugins travel with **packages**. The install unit is the directory: one package = one directory under `.owfa/plugins/domains/<pkg>/` containing a `PKG.yaml` (`load_packages`; install destination in `do_install`). Directory boundary == package boundary; the layout walker also tolerates the legacy flat and `core/` layouts (`_plugin_dirs`). One plugin belongs to at most one package — a member declared by two PKGs is an error (`load_packages`).

`PKG.yaml` is parsed by a purpose-built minimal parser (scalars, flow lists, block dict-lists, one nested mapping of lists — `parse_pkg`). The full field-by-field reference, suite vs domain-family semantics, and authoring guidance live in [packages.md](packages.md); this section fixes only what the kernel mechanically reads:

| Field | Kernel use | Source |
|---|---|---|
| `id` | must equal the directory name (`load_packages`) | |
| `kind` | `suite` (rootless: no family root, no closure laws) vs `domain-family` (default); presence/compat/flat-graph/id laws apply to both (`package_shape_issues`); `protocol` adds the step2 shape laws and — since 0.4.6 — the R11 two-state ABI qualification ([abi.md](abi.md)) | |
| `version` | A.B.C; compared against INDEX rows at install (`do_install`) and `upgrade` | |
| `compat` | `>= X.Y` or `>= X.Y.Z` floor checked against `.owfa/VERSION` (`compat_floor`: two segments = minor-line floor — every X.Y.z passes; three segments = patch floor — X.Y.Z+ or higher minor) | |
| `members` | the plugin roster; subset installs must stay dependency-closed (`package_shape_issues`) | |
| `skeleton` | instance directories install mkdirs mechanically — the kernel hardcodes no layout; path-escape guard included (`do_install`) | |
| `connectors` | in-repo directories copied to `connectors/` at install (`do_install`), removed at uninstall (`do_uninstall`) | |
| `needs` / `provides` | package-scale capabilities (section 3) | |
| `uninstall` | `anchors` (residual-scan surfaces, section 7), `retains` / `credentials` / `processes` (teardown disclosures printed at uninstall) | |
| `menu` / `disclosure` / `migrations/` | consumed by `plan` (`do_plan`) and the migration staging of section 7 | |

At the plugin level, every manifest carries seven required keys — `id / version / depends / updated / attachment / fields / inject` (`REQUIRED_KEYS`) plus the optional keys (`commands`, `usage`, `checks`, `bridge`, `inject_tier`, `usage_routes`, `transports`). The kernel requires `attachment` and `fields` to be **present** but does not interpret their entries: what an attachment claim means over the instance's data model is protocol semantics; the kernel's authority over plugin content is mechanical, not editorial.

### 2.1 The plugin ontology — owner's final ruling (2026-11-15)

Entry-level definition of what a plugin **is**, ruled by the owner on 2026-11-15. It is an entry above the mechanism sections: nothing below is revised — the R1–R10 lines (enumerated in [packages.md § kind: protocol](packages.md)), the ABI, and the package/capability machinery stand exactly as written.

- **Motivation.** OWFA is plugin-based because information is infinite and infinitely malleable — and the plugins are made for the agent's convenience. A plugin is how one defined kind of information is packaged so the agent can carry it.
- **The four-part formula.** An owfa plugin (package) = **plugin documentation + exposure mechanism** (injection, skills, …) **+ an information-acquisition channel** (a connector, or the user's own input such as the vault) **+ an information-processing approach**. In essence, a plugin corresponds to one **defined kind of information**.
- **Territory is not in the formula.** A territory is the storage-form requirement of *some* information kinds — never a condition of plugin identity. The precedents already in the tree prove it: `trust` has no directory territory, and `bridge` at 0.3 ran with zero territory. A plugin owns a territory exactly when its information kind needs that storage form; that is storage, not identity.
- **Processing is protocol-constrained.** How information is processed is bound by the protocol, along a strength spectrum from weak to strong — `bridge` is the full-strength end, where the constraint hardens into the topology-completeness law (section 4).

### 2.2 The inhabited design space (evidence, 2026-11-16)

The formula is not aspirational — the installed base has filled it in five distinct shapes, each a way a defined information kind answers "acquired how, processed how":

| Shape | Members (live) | Acquisition | Processing | Note |
|---|---|---|---|---|
| Concept | trust · tag · link · language · hot · index · log · todo · tmp · domain | reads existing pages | declarative — the manifest fields ARE the species definition | no connector, often no territory; `trust` (no directory) and `domain` (whose information kind is the inner/outer distinction itself) are the limiting cases |
| Container | wiki · notes · sessions · vault · diary · structure · mapping | the user's own writing / landing | registration + derived layers | territory here is a genuine storage-form need, not identity |
| Connector domain | cuhksz · lark · email · bili · github | a connector CLI | adapter contract + trust ceiling | credentials stay outside the repo (red lines); cache territories are storage, not identity |
| Method | bridge · bb-map · bb-teach · bb-quiz | the bridge/ABI, mapped artifacts, cognition profiles | pure method, zero landing code | `bridge` is the formula's zero point — zero territory, zero fields, production-proven; bb-track is deliberately NOT here — it lands cognition readings on pages, which is processing with a territory, not pure method |
| Trusted autonomous agent | bili-pet | feed scoring + debrief | standing consent + write whitelist + ledger | the declared exception class, not an accident: consent quotas are part of the species definition |

Two precedents worth citing by name: **`trust` proves territory is not in the formula** (a full plugin with no directory), and **`bridge` proves the formula's minimum** (a species defined by documentation and method alone). A new plugin should be able to say which row it extends; a row that fits none is a design question, not a failure of the formula.

### 2.3 Documentation is the formula's first part — the single-source discipline

Because documentation is a functional component of a plugin (not commentary about it), it is governed like any information kind. The discipline, learned from the 2026-11-16 doc-debt sweep (dead paths pointing at a retired layout, release numbers pinned in three places, mirrored doc sets drifting):

- **One home per fact.** Every fact — a path, a version number, a command name, a ruling number — has exactly one canonical home (the manifest, the protocol law, `.owfa/VERSION`); every other mention is a pointer, never a copy. The R1–R11 table lives in packages.md alone; kernel.md and abi.md point at it.
- **Docs state what is, not what is planned.** A law page that denies its own machinery ("the ABI remains undecided" beside a shipped proto_query.py) is the worst-class defect; promises of future kernel behavior belong in issue trackers, not law documents.
- **Mechanical guards catch what semantic review misses.** Structural doc checks — referenced paths must exist on disk, pinned version literals must match `.owfa/VERSION`, en/zh heading sets must align, changelog top entry must equal the manifest version — are shape checks, fit for the kernel/CI; whether docs *tell the truth about behavior* stays with fresh-context review.

### 2.4 The kernel's own boundary under the ontology

The kernel owns mechanisms — manifest syntax, projections, the package/capability engine, check machinery — and **no information kind**. Framework commands are explicitly ownerless (`owner: framework`); the kernel is protocol-agnostic and enforces whatever rules the installed packages declare. Two consequences follow, both deliberate:

- The kernel does **not** enforce the ontology. `validate` checks shape (manifest compliance, graph laws); whether a plugin's four parts are actually present and truthful is a semantic question, gated by fresh-context review at the registry PR — the machine polices shape, humans and reviewers police meaning. A plugin with a missing acquisition channel passes validate; it should not pass review.
- The kernel's own docs obey the same single-source discipline as any plugin's (2.3). When this page and `owfa_kernel.py` disagree, the source prevails — and that is itself an instance of the rule that law documents describe machinery, never substitute for it.

## 3. The capability engine

Since v0.4, packages declare capabilities in PKG.yaml — `needs: [ … ]` / `provides: [ … ]` — deliberately package-scale; plugin-level declarations are unsupported by design (`owfa_kernel.py`). (What member-level capabilities would mean in a multi-protocol world is a step-2 design question, out of scope here.) The kernel enforces four laws:

- **Grammar**: `^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$` (`CAPABILITY_RE`; checks in `capability_grammar_issues`). The `owfa.*` namespace is framework-owned; any other capability's first name segment must equal the declaring package id (`capability_grammar_issues`) — the kernel checks grammar, the registry review gate polices `owfa.*` grants.
- **Exact-name matching**: a need is satisfied only by a provides of the very same name; a v2 provider leaves a v1 need unsatisfied, reported distinctly from a wholly missing capability (`_cap_base` version-variant test).
- **Exclusive slots**: at most one installed package may provide a given capability; a second provider is an error (`capability_issues`).
- **Trust-gated satisfaction**: only provides from trusted packages — `framework-bundled` or `reviewed-3rd-party` per the registry INDEX row (`TRUSTED_PROVIDERS`) — satisfy needs. An exact-name provider at unverified trust is a **soft refusal**: overridable with `--yes`, and the override is journaled (`capability_issues`, `do_install`). Grammar, exclusive-slot, missing, and version failures refuse outright — no override.

Convergence points: **install** runs the check as a preflight over the *prospective* package graph — installed provides, minus the replaced edition's old provides on the upgrade path, plus the incoming edition's — before any file or projection changes (`do_install`). **validate** runs the same laws over the full installed graph as errors, downgraded to warnings in single-package `--scope` mode (`validate_capabilities`; dispatch in `main`). **Uninstall is deliberately not a convergence point**: removing the last provider of a needed capability leaves a red validate while the uninstall itself succeeds — the intentional asymmetry (`do_uninstall`).

The kernel journal (`.owfa/kernel-journal.log`) records every mechanical operation — install, uninstall, upgrade, trust overrides, sweeps, migration clears — one line per op, last 500 lines kept (`JOURNAL`; `_journal`).

## 4. The dependency graph and injection order

`depends` declares behavioral or semantic dependencies. validate checks existence and acyclicity via DFS three-color marking (`validate`).

**Injection order = dependency topology (dependees first) + alphabetical within a batch** (`ordered_plugins`). On cycles or dangling dependencies the projector falls back to alphabetical output so projections stay buildable while validate reports the error (`ordered_plugins`). The guarantee: when a consumer-side plugin is projected, the disclosures it consumes are already above it.

Two graph concepts the kernel hardcodes:

- **The `domain` concept plugin.** A plugin whose depends chain reaches `domain` is a domain piece; one depending on `domain` directly is a domain base (`reaches_domain`). This is a kernel graph notion — what a "domain" means over instance data is protocol semantics.
- **Bridges** (`bridge: 必依 | 按需`). Only global pieces (depends chain not reaching `domain`) may hold a bridge; a must-attach (必依) bridge requires **every** domain base to carry a depends edge to the piece — a topology-completeness invariant, not a style suggestion (`validate_bridges`).

**Tier law** (`inject_tier: full | member`, default full): a member-tier plugin exits the AGENTS.md injection region — its exposure rides on the family root's roster line, the skill catalog, and on-demand manifest reads. validate requires every member-tier plugin to reach a full-tier domain root through depends, else it exits into invisibility (`INJECT_TIERS`; `build_inject_blocks`; tier check).

**Byte budget**: the projected injection region carries a 16 KiB budget (`INJECT_BUDGET = 16 * 1024`); over-budget is a validate error that blocks mechanical actions (`validate`). **Line guideline**: each full-tier inject line has a 256 B pointer-density guideline (`INJECT_LINE_GUIDE`) — over it, validate warns, never blocks (`validate`): a line is a routing pointer (path + read/write trigger + the one easy-to-break invariant + a pointer to PLUGIN.md), detail lives in PLUGIN.md.

## 5. The projections: one source, five landings

From the manifests, the kernel mechanically projects to five places. All are idempotently rebuilt; hand-editing inside marker blocks is futile (a rebuild overwrites), prose outside them belongs to humans. There is no second source of truth: to change a rule, change the manifest, then `all` converges everything.

| Projection | Landing point | Source key | Source |
|---|---|---|---|
| AGENTS injection region | `wiki-inject:start/end` marker region in AGENTS.md, one `<!-- plugin:<id> v<x> -->` block per full-tier plugin | `inject` | `do_inject` |
| check inspection block | the `check-inject` block inside the check command master | `checks` | `do_check_inject` |
| command usage blocks | the `cmd-inject` block inside each command SKILL.md | `usage` | `do_cmd_inject` |
| registry plugin section | the `plugins:` section of `.owfa/protocol/registry.yaml` (reserved sections untouched) | `fields` | `do_registry` |
| skill copies | `.agents/skills/<name>/SKILL.md` synced from command and connector masters | masters | `do_deploy` |

Command binding underpins the third projection. `owner` and `commands` are **mutual declarations**: a command's SKILL.md frontmatter writes `owner: <plugin-id>` (or `framework` for explicitly ownerless); a plugin manifest writes `commands: [names]`. A one-sided declaration on either side is a validate error, as are missing owner, owner pointing at an uninstalled plugin, and `framework` combined with other owners (`validate_bindings`).

Usage reaches commands by two routes:

- **Pull side**: a command's frontmatter writes `consumes: [plugin ids]` — the write-side contract pull declaration; owner-driven commands must fill it in and include all owners (`validate_bindings`).
- **Source-side routing**: a plugin manifest writes `usage_routes: [command names]` — installing the plugin lands the projection, no destination-command edit needed. Presence-as-registration on the push side. validate checks that routing targets exist, that routing plugins carry `usage`, and that a plugin both routed and consumed is a duplicate-routing error (`validate_bindings`).

Disclosure order inside a cmd-inject region is presentation order: owner blocks first (consumes order), routed blocks in the middle (dependency topology plus alphabetical), remaining consumes last (`do_cmd_inject`). `ls` renders the full usage-routing table — every plugin carrying usage lists its landing commands; no landing means the contract-documentation surface (`do_ls`).

`all` is the convergence command: validate first — failure blocks — then inject, check-inject, cmd-inject, registry, deploy (`converge`; dispatch in `main`). The same convergence runs automatically at the end of install and uninstall.

## 6. The check mechanism

The audit contract (attached audit, `scripts/check.py` per plugin, optional) is kernel-owned **mechanism**; what the rules check is protocol content. One sentence on the split: the kernel defines and enforces the contract's shape; the protocol defines the semantics of each rule.

- **Contract**: the script must define `check(ctx)` returning an issue list `[{level: error|warning|info, message}]`; `ctx.root` is the repository root, `ctx.pages` the instance's page corpus (path, frontmatter, body), shared across a single scan; read-only with zero side effects — repair belongs to commands and humans (`owfa_kernel.py`).
- **Static gate**: the shape is validated via AST without executing the file — syntax errors and a missing `check(ctx)` are validate errors (`validate`, AST gate).
- **Discovery execution**: `audit` runs each present check script in discovery style — a contract-compliant script present in a plugin directory is automatically listed, and moving the directory out on uninstall automatically delists it. Presence as registration, isomorphic to the injection region, but with no text splicing (`do_audit`). One plugin's script failing is reported as that plugin's error without taking down the others; a nonzero error count is the nonzero exit (`do_audit`).

The kernel's own validate is the hard-structure layer (fields, graph, bindings, budget); attached audits are the semantic layer stacked on top.

## 7. Install/uninstall contract and the migration algebra

The process-level narrative (consent wizard, channels, publishing) lives in [packages.md](packages.md) and [deployment.md](deployment.md); this section fixes the mechanics.

**Install** (`do_install`) lands a package: capability preflight over the prospective graph (section 3 — hard failures refuse before anything changes); manifest-graph preflight of the staged masters against the installed set — duplicate plugin ids refuse (`_preflight_install`); masters copied to `.owfa/plugins/domains/<pkg>/` (`do_install`); in-repo connectors copied to `connectors/`, existing directories kept (`do_install`); package-borne command masters copied to `.owfa/command/`, existing files never overwritten, pruned members' commands ride out (`do_install`); PKG-declared `skeleton:` directories mkdir'd with a path-escape guard (`do_install`); migrations staged (below); projections converge via `all` (`converge`).

**Uninstall** (`do_uninstall`) requires `--yes` and performs the mechanical **four-clear**: package-borne commands removed from `.owfa/command/` together with their skill copies (`do_uninstall`); declared connectors removed from `connectors/` and `.agents/skills/` (`do_uninstall`); the package directory itself (`do_uninstall`); empty container directories left no residue (`do_uninstall`). Data zones are never touched. The PKG's teardown disclosures are printed, not executed: `retains` (never touched), `credentials` (stay on the machine, manual removal), `processes` (stop long-running executors if any) — `do_uninstall`.

**Anchors and residual.** The residual-scan surface is the kernel floor (AGENTS.md — whose injection region is skipped; the handwritten region is never deleted) plus the additive union of every package's `uninstall.anchors`; a directory anchor expands to the `.md` files inside it (`_anchor_files`). `residual <pkg>` greps those surfaces for references to the package and its members outside the kernel-managed region — the default teardown gate (`_residual_hits`; `do_residual`). Declared anchors are never deleted by the kernel — at install it explicitly discloses them (`do_install`).

**Migration algebra.** Semantic migrations ride packages as `migrations/` declarations and are staged into the kernel zone (`.owfa/migrations/`, use-and-delete; `_stage_migrations`):

- **0 → x**: a first install stages `init.md` when present (`_stage_migrations`).
- **x → y**: an upgrade stages every declaration whose line falls in `[prev_line, new_line)` — same-line patch updates stage nothing (`_stage_migrations`); `upgrade <pkg> --yes` is the quiet mechanical reinstall (uninstall → install with the old PKG boarded as prospective context) that triggers staging.
- **x → 0**: an uninstall consumes the package's dormant `teardown.md/py` declaration — the pending teardown is registered in the ledger and the warning banner **before** removal (`do_uninstall`).
- Reinstall sweeps a pending teardown (the premise vanished with the package's return); uninstall sweeps migrate-kind state (it dies with the package); orphaned package state in the kernel zone self-heals on any kernel run (`main`).

Pending migrations are **tri-face visible**: the ledger (`pending.json`), an AGENTS banner block injected at the top of the injection region (`_banner_set`), and a standing validate error — mechanical blessing is withheld until cleared (`main`). `migrate <pkg>` prints the staged declarations; `--clear` is gated: an author-provided `verify(ctx)` script must pass (AST-gated: stdlib-adjacent, read-only — banned imports and write-mode `open` are refused; executed in-process over the installed subset); a teardown without a script clears only when the residual scan is clean (`do_migrate`); with no script and no residual gate, `--force` is the explicit human assertion (`do_migrate`). Cleared items are deleted — permanent invariants belong in `scripts/check.py`, not in migrations (the judgment split).

**The empty shell.** After uninstalling every package, the instance is exactly a kernel-only instance: `.owfa/scripts/` + the AGENTS.md seed, no plugins, no skeleton beyond what humans made — the same shape `init --core none` produces (see [deployment.md](deployment.md)). Uninstalling a protocol is not a special operation: it is the same `kernel uninstall` mechanism, with the protocol package's `retains` covering its data zones so nothing the human owns is touched.

## 8. Registry resolution

The registry is the owfadev/owfa-registry repository; its catalog is `INDEX.yaml`, **one line per package** — each line a human-review gate. Row fields: `repo / version / compat / trust / members / summary`, plus v0.4 fields `needs` / `provides` ('/'-separated lists, the members precedent) and an optional `commit` SHA pin (`owfa_kernel.py`).

**Resolution order** (`load_index`): a local `INDEX.yaml` at the instance root wins; else a cache at `.owfa/registry-cache.yaml` fresh within a 600 s TTL; else the remote master is fetched and cached; a stale cache is the offline fallback; read-only callers (`validate`, `provides`) never touch the network. Rows parse as `  pkg: {key: value, …}` — a minimal one-line grammar (`load_index`).

**Commit pin.** A row carrying `commit: <sha>` pins the expected HEAD: after the shallow clone, the actual HEAD SHA must equal the pin or the clone is refused — the supply-chain content anchor against tag/path drift between review and fetch (`_clone_package`).

**Three install channels** (`do_install`):

1. **Registry** — the package is looked up in INDEX.yaml; a trust level outside `framework-bundled / reviewed-3rd-party` is not auto-installable and requires explicit `--yes` (`do_install`). Index rows are cross-checked against PKG.yaml: member-roster drift and version drift both refuse (`do_install`).
2. **Direct** `owner/repo` or URL — unindexed, reachable by convention, `--yes` required, trust: unknown; the registry PR is how a package earns reviewed trust (`do_install`).
3. **Local** `--path <dir>` — for development and embedded copies; no trust context at all (`do_install`).

Trust levels: `framework-bundled` / `reviewed-3rd-party` / `unknown` — the INDEX row is the single trust source feeding the capability trust gate (section 3). `list-remote` renders the index table with installed marks (`do_list_remote`); `upgrade` (report mode) reconciles installed versions against the index and the framework anchor against the template remote (`do_upgrade`). Release discipline — PKG version bump → tag `<pkg>-vA.B.C` → registry row PR — is documented in [packages.md](packages.md); the mechanics of each step are here.
