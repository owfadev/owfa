# The Kernel

> Reader: anyone — human or agent — who needs to understand the kernel's mechanics precisely: what `.owfa/scripts/owfa_kernel.py` enforces, projects, and refuses, and where each rule lives in the source. The script itself is authoritative; where this page and the source disagree, the source prevails. Every mechanism below carries its source line references (against the v0.4.2 kernel, 2335 lines). First written 2026-11-15, absorbing the kernel half of the former `mechanics.md`.

## 1. What the kernel is

The kernel is a **single Python file**, `.owfa/scripts/owfa_kernel.py`, importable and runnable with **Python 3.9+ and the standard library only** — module-level imports are `ast / importlib / os / re / shutil / sys / types` (`owfa_kernel.py:131-137`); networking (`urllib`) and process execution (`subprocess`) are imported lazily inside the functions that need them (`owfa_kernel.py:1205`, `1253-1254`). No third-party dependency, no interpreter beyond CPython. This is a deployment guarantee: any machine that can run the installer's post-install steps can run the kernel.

Its charter is stated in the module docstring: deterministic structural operations go to the script, semantic judgment goes to the LLM; and the script **touches only four places** — plugin directories in and out, the AGENTS.md injection-region marker blocks, the registry plugin section, and the `.agents/skills/` command copies. Protocol artifacts, reserved sections, and handwritten regions are never touched (`owfa_kernel.py:5-9`).

The subcommand surface has converged to two groups:

- **7 convergence subcommands** — `ls / validate / audit / inject / registry / deploy / all` (`owfa_kernel.py:12-18`, dispatch `2277-2330`)
- **8 package-lifecycle subcommands** — `plan / install / uninstall / list-remote / migrate / upgrade / pkg / residual` (`owfa_kernel.py:19-27`, dispatch `2205-2270`)

One auxiliary read-only view completes the surface: `provides` — an offline, disk-read-only report of every installed package's capability provides and the satisfaction status of every needs declaration (`owfa_kernel.py:26`, `1677-1704`).

**Protocol independence.** The kernel knows packages, plugin manifests, dependency graphs, capabilities, and projections — nothing else. It does not know any content protocol: what a "page" should contain, what territories exist, what derived artifacts a workspace keeps — none of it is kernel vocabulary. The cleanest proof is the v0.4.2 ownership split: `pipeline.py` (the data-area derived-layer tool of the vault-wiki protocol, e.g. index/tags/hot/log rebuilding) **left the framework tree for the protocol's suite package** — since suite 0.1.1 it ships at the package root of owfa-personal (instance path `.owfa/plugins/domains/personal/pipeline.py`), and the framework-tree copy is a one-version deprecation shim that retires in 0.5.0; the kernel never calls it (shim header, `.owfa/scripts/pipeline.py:3-6`). Where the kernel is Protocol-agnostic by design, the protocol owns everything the kernel deliberately does not interpret.

## 2. The package model

Since v0.4, plugins travel with **packages**. The install unit is the directory: one package = one directory under `.owfa/plugins/domains/<pkg>/` containing a `PKG.yaml` (`load_packages`, `owfa_kernel.py:877-893`; install destination `1454`). Directory boundary == package boundary; the layout walker also tolerates the legacy flat and `core/` layouts (`_plugin_dirs`, `252-273`). One plugin belongs to at most one package — a member declared by two PKGs is an error (`936-939`).

`PKG.yaml` is parsed by a purpose-built minimal parser (scalars, flow lists, block dict-lists, one nested mapping of lists — `parse_pkg`, `817-874`). The full field-by-field reference, suite vs domain-family semantics, and authoring guidance live in [packages.md](packages.md); this section fixes only what the kernel mechanically reads:

| Field | Kernel use | Source |
|---|---|---|
| `id` | must equal the directory name (`889-890`) | |
| `kind` | `suite` (rootless: no family root, no closure laws) vs `domain-family` (default); presence/compat/flat-graph/id laws apply to both (`916-979`) | |
| `version` | A.B.C; compared against INDEX rows at install (`1421-1424`) and `upgrade` | |
| `compat` | `>= X.Y` floor checked against `.owfa/VERSION` (`framework_version`, `896-908`; check `973-979`, install `1409-1414`) | |
| `members` | the plugin roster; subset installs must stay dependency-closed (`948-969`) | |
| `skeleton` | instance directories install mkdirs mechanically — the kernel hardcodes no layout; path-escape guard included (`1559-1564`) | |
| `connectors` | in-repo directories copied to `connectors/` at install (`1510-1519`), removed at uninstall (`1616-1627`) | |
| `needs` / `provides` | package-scale capabilities (section 3) | |
| `uninstall` | `anchors` (residual-scan surfaces, section 7), `retains` / `credentials` / `processes` (teardown disclosures printed at uninstall, `1664-1670`) | |
| `menu` / `disclosure` / `migrations/` | consumed by `plan` (`2123-2161`) and the migration staging of section 7 | |

At the plugin level, every manifest carries seven required keys — `id / version / depends / updated / attachment / fields / inject` (`REQUIRED_KEYS`, `155`) plus the optional keys (`commands`, `usage`, `checks`, `bridge`, `inject_tier`, `usage_routes`, `transports`). The kernel requires `attachment` and `fields` to be **present** but does not interpret their entries: what an attachment claim means over the instance's data model is protocol semantics; the kernel's authority over plugin content is mechanical, not editorial.

## 3. The capability engine

Since v0.4, packages declare capabilities in PKG.yaml — `needs: [ … ]` / `provides: [ … ]` — deliberately package-scale; plugin-level declarations are unsupported by design (`owfa_kernel.py:982-984`). (What member-level capabilities would mean in a multi-protocol world is a step-2 design question, out of scope here.) The kernel enforces four laws:

- **Grammar**: `^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$` (`CAPABILITY_RE`, `991`; checks `1016-1025`). The `owfa.*` namespace is framework-owned; any other capability's first name segment must equal the declaring package id (`1023-1024`) — the kernel checks grammar, the registry review gate polices `owfa.*` grants.
- **Exact-name matching**: a need is satisfied only by a provides of the very same name; a v2 provider leaves a v1 need unsatisfied, reported distinctly from a wholly missing capability (`_cap_base` version-variant test, `1011-1013`, `1059-1063`).
- **Exclusive slots**: at most one installed package may provide a given capability; a second provider is an error (`1045-1047`).
- **Trust-gated satisfaction**: only provides from trusted packages — `framework-bundled` or `reviewed-3rd-party` per the registry INDEX row (`TRUSTED_PROVIDERS`, `995`) — satisfy needs. An exact-name provider at unverified trust is a **soft refusal**: overridable with `--yes`, and the override is journaled (`1052-1057`, `1493-1502`). Grammar, exclusive-slot, missing, and version failures refuse outright — no override.

Convergence points: **install** runs the check as a preflight over the *prospective* package graph — installed provides, minus the replaced edition's old provides on the upgrade path, plus the incoming edition's — before any file or projection changes (`1460-1502`; the prospective board rationale, `1776-1783`). **validate** runs the same laws over the full installed graph as errors, downgraded to warnings in single-package `--scope` mode (`validate_capabilities`, `1071-1091`; dispatch `2299-2301`). **Uninstall is deliberately not a convergence point**: removing the last provider of a needed capability leaves a red validate while the uninstall itself succeeds — the intentional asymmetry (`1655-1658`).

The kernel journal (`.owfa/kernel-journal.log`) records every mechanical operation — install, uninstall, upgrade, trust overrides, sweeps, migration clears — one line per op, last 500 lines kept (`JOURNAL`, `152`; `_journal`, `1863-1871`).

## 4. The dependency graph and injection order

`depends` declares behavioral or semantic dependencies. validate checks existence (`440-446`) and acyclicity via DFS three-color marking (`447-464`).

**Injection order = dependency topology (dependees first) + alphabetical within a batch** (`ordered_plugins`, `174-191`). On cycles or dangling dependencies the projector falls back to alphabetical output so projections stay buildable while validate reports the error (`177-179`). The guarantee: when a consumer-side plugin is projected, the disclosures it consumes are already above it.

Two graph concepts the kernel hardcodes:

- **The `domain` concept plugin.** A plugin whose depends chain reaches `domain` is a domain piece; one depending on `domain` directly is a domain base (`reaches_domain`, `298-305`). This is a kernel graph notion — what a "domain" means over instance data is protocol semantics.
- **Bridges** (`bridge: 必依 | 按需`). Only global pieces (depends chain not reaching `domain`) may hold a bridge; a must-attach (必依) bridge requires **every** domain base to carry a depends edge to the piece — a topology-completeness invariant, not a style suggestion (`validate_bridges`, `551-567`).

**Tier law** (`inject_tier: full | member`, default full): a member-tier plugin exits the AGENTS.md injection region — its exposure rides on the family root's roster line, the skill catalog, and on-demand manifest reads. validate requires every member-tier plugin to reach a full-tier domain root through depends, else it exits into invisibility (`INJECT_TIERS`, `165`; `build_inject_blocks`, `371-381`; tier check, `419-429`).

**Byte budget**: the projected injection region carries a 16 KiB budget (`INJECT_BUDGET = 16 * 1024`, `168`); over-budget is a validate error that blocks mechanical actions (`430-434`). **Line guideline**: each full-tier inject line has a 256 B pointer-density guideline (`INJECT_LINE_GUIDE`, `171`) — over it, validate warns, never blocks (`435-438`): a line is a routing pointer (path + read/write trigger + the one easy-to-break invariant + a pointer to PLUGIN.md), detail lives in PLUGIN.md.

## 5. The projections: one source, five landings

From the manifests, the kernel mechanically projects to five places. All are idempotently rebuilt; hand-editing inside marker blocks is futile (a rebuild overwrites), prose outside them belongs to humans. There is no second source of truth: to change a rule, change the manifest, then `all` converges everything.

| Projection | Landing point | Source key | Source |
|---|---|---|---|
| AGENTS injection region | `wiki-inject:start/end` marker region in AGENTS.md, one `<!-- plugin:<id> v<x> -->` block per full-tier plugin | `inject` | `do_inject`, `613-633` |
| check inspection block | the `check-inject` block inside the check command master | `checks` | `do_check_inject`, `636-666` |
| command usage blocks | the `cmd-inject` block inside each command SKILL.md | `usage` | `do_cmd_inject`, `669-721` |
| registry plugin section | the `plugins:` section of `.owfa/protocol/registry.yaml` (reserved sections untouched) | `fields` | `do_registry`, `724-748` |
| skill copies | `.agents/skills/<name>/SKILL.md` synced from command and connector masters | masters | `do_deploy`, `751-780` |

Command binding underpins the third projection. `owner` and `commands` are **mutual declarations**: a command's SKILL.md frontmatter writes `owner: <plugin-id>` (or `framework` for explicitly ownerless); a plugin manifest writes `commands: [names]`. A one-sided declaration on either side is a validate error, as are missing owner, owner pointing at an uninstalled plugin, and `framework` combined with other owners (`validate_bindings`, `476-533`).

Usage reaches commands by two routes:

- **Pull side**: a command's frontmatter writes `consumes: [plugin ids]` — the write-side contract pull declaration; owner-driven commands must fill it in and include all owners (`492-507`).
- **Source-side routing**: a plugin manifest writes `usage_routes: [command names]` — installing the plugin lands the projection, no destination-command edit needed. Presence-as-registration on the push side. validate checks that routing targets exist, that routing plugins carry `usage`, and that a plugin both routed and consumed is a duplicate-routing error (`534-548`).

Disclosure order inside a cmd-inject region is presentation order: owner blocks first (consumes order), routed blocks in the middle (dependency topology plus alphabetical), remaining consumes last (`702-707`). `ls` renders the full usage-routing table — every plugin carrying usage lists its landing commands; no landing means the contract-documentation surface (`791-814`).

`all` is the convergence command: validate first — failure blocks — then inject, check-inject, cmd-inject, registry, deploy (`converge`, `1278-1304`; dispatch `2318-2330`). The same convergence runs automatically at the end of install and uninstall.

## 6. The check mechanism

The audit contract (attached audit, `scripts/check.py` per plugin, optional) is kernel-owned **mechanism**; what the rules check is protocol content. One sentence on the split: the kernel defines and enforces the contract's shape; the protocol defines the semantics of each rule.

- **Contract**: the script must define `check(ctx)` returning an issue list `[{level: error|warning|info, message}]`; `ctx.root` is the repository root, `ctx.pages` the instance's page corpus (path, frontmatter, body), shared across a single scan; read-only with zero side effects — repair belongs to commands and humans (`owfa_kernel.py:124-129`).
- **Static gate**: the shape is validated via AST without executing the file — syntax errors and a missing `check(ctx)` are validate errors (`409-418`).
- **Discovery execution**: `audit` runs each present check script in discovery style — a contract-compliant script present in a plugin directory is automatically listed, and moving the directory out on uninstall automatically delists it. Presence as registration, isomorphic to the injection region, but with no text splicing (`do_audit`, `570-610`). One plugin's script failing is reported as that plugin's error without taking down the others (`596-600`); a nonzero error count is the nonzero exit (`610`).

The kernel's own validate is the hard-structure layer (fields, graph, bindings, budget); attached audits are the semantic layer stacked on top.

## 7. Install/uninstall contract and the migration algebra

The process-level narrative (consent wizard, channels, publishing) lives in [packages.md](packages.md) and [deployment.md](deployment.md); this section fixes the mechanics.

**Install** (`do_install`, `1342-1581`) lands a package: capability preflight over the prospective graph (section 3 — hard failures refuse before anything changes, `1460-1502`); manifest-graph preflight of the staged masters against the installed set — duplicate plugin ids refuse (`_preflight_install`, `1307-1339`); masters copied to `.owfa/plugins/domains/<pkg>/` (`1507-1508`); in-repo connectors copied to `connectors/`, existing directories kept (`1510-1519`); package-borne command masters copied to `.owfa/command/`, existing files never overwritten, pruned members' commands ride out (`1520-1534`); PKG-declared `skeleton:` directories mkdir'd with a path-escape guard (`1559-1564`); migrations staged (below); projections converge via `all` (`1575`).

**Uninstall** (`do_uninstall`, `1584-1674`) requires `--yes` (`1589-1591`) and performs the mechanical **four-clear**: package-borne commands removed from `.owfa/command/` together with their skill copies (`1603-1615`); declared connectors removed from `connectors/` and `.agents/skills/` (`1616-1627`); the package directory itself (`1641`); empty container directories left no residue (`1671-1673`). Data zones are never touched. The PKG's teardown disclosures are printed, not executed: `retains` (never touched), `credentials` (stay on the machine, manual removal), `processes` (stop long-running executors if any) — `1664-1670`.

**Anchors and residual.** The residual-scan surface is the kernel floor (AGENTS.md — whose injection region is skipped; the handwritten region is never deleted) plus the additive union of every package's `uninstall.anchors`; a directory anchor expands to the `.md` files inside it (`_anchor_files`, `1109-1135`). `residual <pkg>` greps those surfaces for references to the package and its members outside the kernel-managed region — the default teardown gate (`_residual_hits`, `1138-1167`; `do_residual`, `1170-1186`). Declared anchors are never deleted by the kernel — at install it explicitly discloses them (`1571-1573`).

**Migration algebra.** Semantic migrations ride packages as `migrations/` declarations and are staged into the kernel zone (`.owfa/migrations/`, use-and-delete; `1906-1937`):

- **0 → x**: a first install stages `init.md` when present (`1912-1913`).
- **x → y**: an upgrade stages every declaration whose line falls in `[prev_line, new_line)` — same-line patch updates stage nothing (`1916-1922`); `upgrade <pkg> --yes` is the quiet mechanical reinstall (uninstall → install with the old PKG boarded as prospective context, `1776-1787`) that triggers staging.
- **x → 0**: an uninstall consumes the package's dormant `teardown.md/py` declaration — the pending teardown is registered in the ledger and the warning banner **before** removal (`1628-1640`).
- Reinstall sweeps a pending teardown (the premise vanished with the package's return, `1535-1541`); uninstall sweeps migrate-kind state (it dies with the package, `1642-1650`); orphaned package state in the kernel zone self-heals on any kernel run (`2217-2256`).

Pending migrations are **tri-face visible**: the ledger (`pending.json`), an AGENTS banner block injected at the top of the injection region (`_banner_set`, `1890-1903`), and a standing validate error — mechanical blessing is withheld until cleared (`2307-2308`). `migrate <pkg>` prints the staged declarations; `--clear` is gated: an author-provided `verify(ctx)` script must pass (AST-gated: stdlib-adjacent, read-only — banned imports and write-mode `open` are refused, `1940-1962`; executed in-process over the installed subset, `1965-1988`); a teardown without a script clears only when the residual scan is clean (`2062-2071`); with no script and no residual gate, `--force` is the explicit human assertion (`2072-2074`). Cleared items are deleted — permanent invariants belong in `scripts/check.py`, not in migrations (the judgment split, `2088`).

**The empty shell.** After uninstalling every package, the instance is exactly a kernel-only instance: `.owfa/scripts/` + the AGENTS.md seed, no plugins, no skeleton beyond what humans made — the same shape `init --core none` produces (see [deployment.md](deployment.md)). Uninstalling a protocol is not a special operation: it is the same `kernel uninstall` mechanism, with the protocol package's `retains` covering its data zones so nothing the human owns is touched.

## 8. Registry resolution

The registry is the owfadev/owfa-registry repository; its catalog is `INDEX.yaml`, **one line per package** — each line a human-review gate. Row fields: `repo / version / compat / trust / members / summary`, plus v0.4 fields `needs` / `provides` ('/'-separated lists, the members precedent) and an optional `commit` SHA pin (`owfa_kernel.py:1201-1204`).

**Resolution order** (`load_index`, `1196-1244`): a local `INDEX.yaml` at the instance root wins; else a cache at `.owfa/registry-cache.yaml` fresh within a 600 s TTL; else the remote master is fetched and cached; a stale cache is the offline fallback; read-only callers (`validate`, `provides`) never touch the network. Rows parse as `  pkg: {key: value, …}` — a minimal one-line grammar (`1238-1243`).

**Commit pin.** A row carrying `commit: <sha>` pins the expected HEAD: after the shallow clone, the actual HEAD SHA must equal the pin or the clone is refused — the supply-chain content anchor against tag/path drift between review and fetch (`_clone_package`, `1247-1275`).

**Three install channels** (`do_install`, `1342-1399`):

1. **Registry** — the package is looked up in INDEX.yaml; a trust level outside `framework-bundled / reviewed-3rd-party` is not auto-installable and requires explicit `--yes` (`1384-1399`). Index rows are cross-checked against PKG.yaml: member-roster drift and version drift both refuse (`1415-1424`).
2. **Direct** `owner/repo` or URL — unindexed, reachable by convention, `--yes` required, trust: unknown; the registry PR is how a package earns reviewed trust (`1371-1383`).
3. **Local** `--path <dir>` — for development and embedded copies; no trust context at all (`1366-1370`).

Trust levels: `framework-bundled` / `reviewed-3rd-party` / `unknown` — the INDEX row is the single trust source feeding the capability trust gate (section 3). `list-remote` renders the index table with installed marks (`1707-1721`); `upgrade` (report mode) reconciles installed versions against the index and the framework anchor against the template remote (`1810-1850`). Release discipline — PKG version bump → tag `<pkg>-vA.B.C` → registry row PR — is documented in [packages.md](packages.md); the mechanics of each step are here.
