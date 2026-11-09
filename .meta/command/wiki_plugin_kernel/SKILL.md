---
name: wiki_plugin_kernel
owner: framework
description: "Kernel and mechanics reference: the projector's subcommands (7 convergence — ls/validate/audit/inject/registry/deploy/all — plus 8 package-lifecycle: plan/install/uninstall/list-remote/migrate/upgrade/pkg/residual) + a full account of the plugin mechanics — manifest / dependencies / the three projections / command binding / bridge rules / layering principles (a bb-domain worked example). Triggers on: 插件内核, wiki_plugin_kernel, kernel, 注入块更新, 投影重建, 插件机制, 更新注入."
---

# wiki_plugin_kernel: kernel and mechanics reference

`python .meta/scripts/wiki_plugin_kernel.py <subcommand>` — the framework side's only projector: PLUGIN.yaml is the body; the AGENTS.md injection region, the check check blocks, the command usage blocks, the registry plugin section, and the command and connector skill copies are all its projections. Idempotent, runnable at any time; drift is fixed on the run. This skill also serves as the **mechanics master outline**: a deployed instance carrying only the AGENTS.md injection region + skill copies is self-sufficient; this file is the authoritative home of the mechanics on the deployment side.

## Subcommands

| Subcommand | Purpose | Disk writes |
|---|---|---|
| `ls` | plugin list + dependencies + driven commands | none |
| `validate` | compliance checks: manifest fields, acyclic dependencies, owner×commands bidirectional consistency, consumes present with usage, usage_routes targets present and not duplicating consumes, bridge rules; exit code 1 on error | none |
| `audit` | attached audit: executes each plugin's `scripts/check.py` on discovery, read-only report (may take a plugin id to check just one) | none |
| `inject` | rebuilds the three projections: the AGENTS injection region + the check check blocks + the command usage blocks | AGENTS.md, command SKILL.md files containing injection regions |
| `registry` | rebuilds the registry.yaml plugin section (from each manifest's `fields`) | registry.yaml |
| `deploy` | syncs skill masters (`.meta/command/*/` commands + `connectors/*/` connectors) → `.agents/skills/` copies; orphan copies are reported only (deletion belongs to the human) | copies |
| `all` | validate + inject + registry + deploy in one step | all of the above |

Package lifecycle (full wizard protocol and judgment rules: `.meta/command/plugin/SKILL.md`):

| Subcommand | Purpose | Disk writes |
|---|---|---|
| `plan <pkg>` | dependency plan for a package about to land | none |
| `install <pkg> [--yes] [--without ...]` | fetch from registry or path → `domains/<pkg>/`; owner/repo specs need `--yes` (unknown trust); stages pending migrations | package dir, projections, migrations staging |
| `uninstall <pkg> [--yes]` | remove package + projections; stages teardown (x->0) when declared | inverse of install |
| `list-remote` | registry catalog (INDEX.yaml): packages, versions, compat floors | none |
| `migrate [<pkg>] [--clear] [--force]` | pending semantic migrations: status / clear (verify- and residual-gated, use-and-delete) | migrations staging |
| `upgrade [<pkg>]` | compare versions against the registry; apply via silent reinstall | as install |
| `pkg` | installed packages: members, versions, connectors | none |
| `residual <pkg>` | anchor-surface reference scan (the default teardown gate) | none |

The kernel journal (`.meta/kernel-journal.log`, rolling cap of 500 lines, git-tracked) records the mechanical chain — install / warn+ / clear / uninstall / sweep; mechanical facts only, semantic narrative stays in the instance wiki's log.

## Typical scenarios

- **PLUGIN.yaml changed** (inject / checks / usage / fields / version): `python .meta/scripts/wiki_plugin_kernel.py all` — the daily standard action; one command converges everything; if validate fails it blocks — fix and rerun
- **Only refreshing injection blocks**: `inject` suffices, but note it modifies the `.meta/command/` masters; copies sync only via `deploy` — hence always use `all` in daily work
- **Quick health check**: `validate` (structure) + `audit` (attached audit); a full audit (including semantic items) goes through the check command
- **(Un)installing plugins**: the semantic flow (decisions, directory archiving, log line) goes through the plugin command; the mechanical steps inside it are exactly this CLI's `validate` / `all` / `audit`
- **Connector skill changed** (`connectors/*/SKILL.md` master): run `deploy` (or `all`) to sync copies — connector skills never enter `.meta/command/` (the command family is pure wiki operation)

## Plugin shape

- **One plugin, one directory** (`.meta/plugins/<id>/`): `PLUGIN.yaml` (the manifest, the machine-readable body) + `PLUGIN.md` (pure documentation: design summary (why / family position / key rulings and rejected alternatives) / Structure / Invariants / Changelog — **design rationale and per-plugin details belong here**; mechanics commonalities belong to this reference) + optional `scripts/check.py` (attached audit)
- **Manifest keys**: seven required keys `id / version / depends / updated / attachment / fields / inject`; optional `commands` (command names this plugin drives), `usage` (write-side contract list — the third projection source), `checks` (check-rule list — the check projection source), `bridge` (bridge declaration, see bridge rules), `inject_tier` (injection tier, see tier law below)
- **attachment** = declares territory and borrow-read relationships (who owns which paths, who read-only consumes whose pages); **fields** = owned page fields (enter the registry, the global vocabulary); **inject** = the plugin's disclosure, one line (the full-disclosure home in the manifest either way; known to the agent the moment it enters the repository when tier is full, read on demand when tier is member)
- **Attached-audit contract**: `scripts/check.py` defines `check(ctx)` returning `[{level, message}]`; read-only with zero side effects; fixes belong to commands/humans; an AST static check validates the contract's shape

## Dependency mechanics

- `depends` declares behavioral or semantic dependencies (e.g. a bridging piece depends on the concept plugins on both ends); validate checks existence and acyclicity (DFS)
- **Domain plugins** = those whose depends chain reaches `domain`; those directly depending on domain are **domain bases** (vault / lark / project / email / bb). In-domain plugins belong to the domain transitively and need not connect to domain directly
- **Injection order = dependency topology (the depended-on injected first) + alphabetical within a batch** — consumer-side plugins are injected after the producers' disclosures are present (e.g. bb-track before bb-teach / bb-quiz); there is no layering concept
- A domain must be discoverable within the wiki (declaration page or injection line); domain plugins create no root container — course/in-domain artifacts live in the domain territory (both sides `<term>/<course>/` isomorphic), with the general-purpose container (vault) or pointers as the default posture

## Tier law (issue #12 layer discipline)

- **`inject_tier: full | member`** (optional, default full): **full** projects into the AGENTS.md injection region; **member** exits it — exposure rides on the family root's roster line (every member named with id + one phrase), the skill catalog (trigger-surface awareness), and L-layer reads (the manifest `inject` field stays the full-disclosure home either way)
- Validate requires a member to reach a **full-tier domain root** through depends (family membership, else it exits into invisibility)
- The projected plugin blocks carry a **byte budget** (16 KiB, derived from the smallest mainstream whole-file AGENTS.md cap minus handwritten allowance): over-budget is a validate error — compress pointer lines or re-tier domain members; the A layer holds pointers and red lines only, never procedures or formats (content contract in `protocol/experiments.md`)
- Each full-tier `inject` line has a **pointer-density guideline** (256 B, `INJECT_LINE_GUIDE`, issue #49): a longer line is a validate warning, never an error — write path + read/write trigger + the one easy-to-break invariant + a pointer to PLUGIN.md; detail moves to PLUGIN.md / usage / skills

## Command-plugin binding

- **owner × commands bidirectional declaration**: the command SKILL.md frontmatter `owner: <plugin id>` (or `framework`, explicitly ownerless), the plugin manifest `commands: [command name]`; a one-sided declaration on either side is an error
- **consumes (pull side)**: the command frontmatter `consumes: [plugin list]` — the destination declares which plugins' usage to pull; mandatory for owner-driven commands and must include all owners
- **usage_routes (source-side routing)**: the plugin manifest `usage_routes: [command name list]` — additional commands the usage lands in; installing a plugin lands its projections without touching the destination command (the push side of "presence means registration"); validate checks that targets are present, that routed plugins carry usage, and that duplication with consumes is an error
- **Disclosure order**: owner blocks first (consumes order), routed blocks in the middle (dependency topology plus alphabetical), the rest of consumes last — this is a presentation order, not an execution order
- First case: bb-teach and bb-quiz each declare `usage_routes: [bb-track]` — the cognition hub automatically aggregates the collection channels' usage; the bb-track command's consumes keeps only its own and tools; `ls` prints the usage routing table (those without a landing point are marked as contract-document surfaces)
- The **disclosure at the point of consumption** principle: the authoritative source of integration formats is usage (reaching commands via projection), not plugin prose — see the last item of the bridge rules

## Projection mechanics (three projections, one source)

- **The manifest is the only text source**; the kernel mechanically projects into three places, all idempotently rebuilt and auto-synced on (un)install:
  1. **The AGENTS.md injection region** (`wiki-inject:start/end` marker blocks) ← the `inject` line — constitutional level, one block per full-tier plugin (member tier exits, see the tier law)
  2. **The check check blocks** (`check-inject:start/end` inside the check command) ← the `checks` list — semantic-item check rules
  3. **The command usage blocks** (`cmd-inject:start/end` inside each command) ← the `usage` list in consumes order — write-side contracts
- A fourth mechanical projection: the **registry.yaml plugin section** ← `fields` (the global field vocabulary); a fifth: the **skill copies** (deploy)
- Handwritten and mechanical regions are strictly separated: hand-editing inside marker blocks is forbidden (a rebuild overwrites); body text outside blocks belongs to humans; changing a contract = edit the manifest → converge with `all` — **there is no second source of truth**

## Bridge rules (constitutional principle 11)

- **Global plugins** (cross-cutting services and destinations: trust / log / todo / calendar / notes / user-profile…) may declare **bridges** — manifest `bridge: 必依|按需` (must-attach|on-demand); **domain plugins** may not hold bridges (any plugin whose depends chain reaches domain — holding one is an error)
- **必依 (must-attach) bridges**: every domain base must carry the corresponding depends edge; a missing edge is an error (the topological-completeness invariant — e.g. the log must-attach bridge guarantees that anything a domain produces leaves a trace); **按需 (on-demand) bridges**: absence is tolerated (consumers skip without error, e.g. the user-profile cognition bridge)
- **Division of labor between bridges and cmd-inject** (ruled 2026-10-04): bridges hold **validation and declaration** (who may attach, cardinality, completeness checks, absence tolerance); disclosure distribution belongs to projection (the authoritative source of integration-format details = usage, arriving at the point of consumption via cmd-inject, zero retrieval cost) — the bridge section (PLUGIN.md) recedes into elaboration and holds no format authority. The kernel of a bridge that cmd-inject cannot replace: the must-attach completeness check is a topological constraint that consumes cannot express; and cross-territory writes (todo/calendar/notes derivations) happen during every command execution, with no single-point command container to mount them in

## Layering principles (in-domain example: the bb four-piece family)

- **The material layer is in bb/ (the outer workspace), the archive layer in wiki/ (the inner territory)**: process artifacts (fetches, human notes, ai notes, exam grading) live in the material layer; settled conclusions (cognition readings, projection pages) live in the archive layer — "bb/ notes/: human-primary with ai cohabiting" and "user.md as a domain-native page" are instances of this layering
- A domain's growth path: **the domain contract's six questions** (external territory / landing strategy / identity proof / wiki territory / write model / trust model) → the domain base establishes the territory (e.g. bb v0.7: both sides isomorphic + notes/ cohabitation) → the in-domain plugin family (bb-map projection rules, bb-track cognition profile) → consumer-side collection channels (bb-teach / bb-quiz: zero-territory workflow pieces whose usage mounts on the hub command via consumes) — **consumer-side plugins can take the thinnest form** (zero owned fields, contributing only usage and check rules)
- A data-flow loop example: teach explains → ai notes land in notes/ (weak evidence) → track consumes and converges → quiz generates questions with reference → grading flows back into the evidence stream (machine evidence) — the three stages of material production, archive refinement, and collection write-back each belong to their own piece

## Boundaries

- The script touches only four sites: plugin directories in/out, injection-region marker blocks, the registry plugin section, and the skill deployment copies; the protocol / reserved sections and the AGENTS.md handwritten region are never touched
- Pure standard library, zero dependencies (Python 3); English output
- The data-zone derived layer (`wiki/index.md`, `tags.md`, `hot.md`, `log.md`) is not this CLI's business — that is `pipeline.py` (`index` / `tags` / `hot` / `log` / `verify`), invoked by the post-write pipelines of map / save

## Parameters

- Subcommand (see the table above); `audit` may take a plugin id
