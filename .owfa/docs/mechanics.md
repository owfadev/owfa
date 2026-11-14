# Mechanics in Detail

> Reader: members and contributors who will modify the framework or author a package. The authoritative source of mechanical rules is the kernel (`.owfa/scripts/owfa_kernel.py`) and the manifests it reads. This document expands the master outline by one level — principles, instance walkthroughs, and hands-on procedures — without copying rule text; where it conflicts with the source, the source prevails. First written 2026-10-04; rewritten for the v0.4 package era 2026-11-14.

## 0. One Source, Five Projections

Since the v0.4 split, plugins travel with **packages**: the release tree ships no plugins at all (kernel, six framework command masters under `.owfa/command/`, protocol artifacts, and the embedded `payloads/personal/` suite copy). In an installed instance, plugin masters live at `.owfa/plugins/domains/<pkg>/<id>/` — the package is the distribution and install unit (`PKG.yaml`, `kind: suite | domain-family`), and the directory boundary == the tier boundary == the package boundary.

Whatever directory a plugin master sits in, `PLUGIN.yaml` remains the machine-readable body — the manifest. From the manifest, the kernel script mechanically projects into five places:

| Projection | Landing point | Source key | Who reads it |
|---|---|---|---|
| AGENTS injection region | `<!-- plugin:<id> v<x> -->` marker block | `inject` | The agent of every session; constitution-level disclosure |
| check inspection block | the `check-inject` block inside the owfa-check command | `checks` | The check command; semantic items |
| command usage block | the `cmd-inject` block inside each command | `usage`, in consumes order | Command execution sites; write-side rules |
| registry plugin section | `.owfa/protocol/registry.yaml` | `fields` | Commands consulting the field vocabulary before writing pages |
| skill copy | `.agents/skills/<command>/` | command and connector masters | Deployment-side agents |

The key property is idempotent rebuilding. Hand-editing inside marker blocks is forbidden — a rebuild overwrites; prose outside the blocks belongs to humans. There is no second source of truth: changing a rule means changing the manifest, after which the single command `all` converges everything. The whole class of documentation-drift problems is eliminated wholesale — projections and the body cannot disagree, because they are not two separate things.

Walk through one real sample. In the cuhksz domain base's manifest, `inject:` is a one-line disclosure stating the school domain's territory, connectors, and red lines. After `all` runs, that line appears verbatim in the AGENTS injection region inside the `<!-- plugin:cuhksz v0.3 -->` block. What agents read day to day is the projection; the manifest body is touched only when packages are (un)installed or upgraded.

## 1. Plugin Shape

One plugin, one directory, three pieces — now inside its package:

- `PLUGIN.yaml` — the manifest, the body
- `PLUGIN.md` — pure documentation: design summary, Structure, Invariants, Changelog. The why of the design lives here; mechanical commonality belongs to the kernel reference
- `scripts/check.py` — optional attached audit. Defines `check(ctx)` returning `[{level, message}]`, read-only with zero side effects; the shape is statically validated via AST

Seven required manifest keys, illustrated with real values from bb-quiz (v0.8, member of the owfa-cuhksz package at `.owfa/plugins/domains/cuhksz/bb-quiz/`):

| Key | Semantics | Instance |
|---|---|---|
| `id` / `version` / `updated` | Identity and version; advance along the changelog without skipping numbers | `bb-quiz` / `0.8` |
| `depends` | Dependency list | `[bb-track, bb-map]` |
| `attachment` | Territory declaration: owning means writing, borrowing means read-only consumption | see below |
| `fields` | The plugin's own page fields; enter the registry's global vocabulary | `quiz`, the exam-paper block mapping |
| `inject` | The source of the injection-region line; constitution-level disclosure | rides on the cuhksz family (member tier, see below) |

Four optional keys. `commands` declares the commands this plugin drives; `usage` is the write-side rule list; `checks` is the inspection rules; `bridge` is the bridge declaration, which only global pieces may hold.

A fifth optional key `inject_tier` (full|member, default full) carries the **tier law** (issue #12 layer discipline): member exits the AGENTS injection region — exposure rides on the family root's roster line, the skill catalog, and on-demand reads of the manifest, and validate requires a member to reach a full-tier domain root through depends. In the cuhksz package every member but the domain base itself is member-tier: the bb family's disclosure is carried by the cuhksz roster line, not by five separate AGENTS blocks. The projected region carries a byte budget (16 KiB), keeping the A layer pointer-dense: pointers and red lines, never procedures or formats (contract in `protocol/experiments.md`). Each full-tier inject line also has a 256 B pointer-density guideline (issue #49) — over it, validate warns: keep the line to path + read/write trigger + the one easy-to-break invariant + a pointer to PLUGIN.md.

attachment deserves a closer look. bb-quiz declares three entries:

- `cuhksz/bb/<term>/<course>/notes/testing/` is the exam-paper sub-region, owned by this plugin. Each test run adds a question set plus answers; grading is appended on the answers page
- `wiki/cuhksz/bb/<term>/<course>/user.md` is the cognition profile, owned by bb-track. This plugin reads it only; grading writes back through bb-track's write rules
- `wiki/cuhksz/bb/<term>/<course>/courseware/` and `assessments/` belong to bb-map. This plugin reads them only, taking sm-N anchors, the terminology table, and known assignments

The first is ownership; the latter two are borrows: the territory belongs to another plugin, and write paths must pass through its rules. attachment is the framework's property registry. Who owns which paths, who read-only consumes whom — visible at a glance, mechanically checkable.

## 2. Dependencies and Injection Order

`depends` declares dependencies. validate checks two things: dependencies exist, and there are no cycles — cycles are detected via DFS.

A domain piece is any plugin whose depends chain reaches `domain`. Those connecting to domain directly are domain bases — the seven current bases: vault (a member of the embedded personal suite), lark, project, email, cuhksz, bili, github; pieces inside a domain belong to it transitively, without connecting directly. bb-quiz does not connect to domain directly: it arrives via `bb-quiz → bb-track → bb-map → bb → cuhksz → domain`, and is thus a domain piece. Within the cuhksz package, bb (and likewise sis and registry) carries a direct edge to both cuhksz and domain — in-domain governing members, each ruling a sub-territory under the domain base.

Injection order = dependency topology plus alphabetical order within a batch: dependees are injected first; same-batch pieces sort by name. Look at the cuhksz family's depends and the resulting order:

| Plugin | depends | Effect |
|---|---|---|
| cuhksz | `[domain, wiki, trust, log]` | Domain base, injected first; sole full-tier block in the family |
| bb | `[cuhksz, domain, wiki, trust, log]` | Course-ops sub-base, after cuhksz |
| bb-map | `[bb, wiki]` | Mapping law, after bb |
| bb-track | `[bb, bb-map, trust, wiki]` | Cognition profile, after bb-map |
| bb-quiz / bb-teach | `[bb-track, bb-map]` | Collection channels; same batch sorted by name — quiz before teach |

This guarantees one thing: when a consumer-side plugin is projected, the disclosures it consumes are already present. bb-teach's usage says "discipline, see the bb-track block" — that block is necessarily above it. There is one more domain discipline: a domain must be discoverable inside the wiki, via declaration page or injection line; domain pieces create no root containers.

## 3. Projection Walkthrough

Suppose you want to add one discipline to bb-quiz's write-side rules — here is what happens:

1. Edit the `usage:` list in `.owfa/plugins/domains/cuhksz/bb-quiz/PLUGIN.yaml` and add a line. While at it, bump `version` and refresh `updated`; add a line to PLUGIN.md's Changelog. (Upstream of this sits the package: the change is authored in the owfa-cuhksz repository, released by a PKG version bump + tag, and reaches instances via `kernel upgrade` — see [packages.md](packages.md))
2. Run `python .owfa/scripts/owfa_kernel.py all`. In sequence: validate goes first — failure blocks, fix and rerun; the cmd-inject blocks of the command masters bb-quiz and bb-track are rebuilt — the usage appears in every command whose consumes includes bb-quiz; the registry plugin section is rebuilt; skill copies are synced
3. Self-review the diff. Changes should land only in the manifest, the affected command masters, and the `.agents/skills/` copies; if inject or fields changed, AGENTS and registry change as well. Any change beyond these is an anomaly
4. Commit in the format `plugin: bb-quiz …`; one commit does one thing

This is the everyday feel of "one source, five projections": you wrote one thing, and five places agree automatically.

## 4. Command Binding

owner and commands are mutual declarations. A command's SKILL.md frontmatter writes `owner: <plugin-id>`, or `framework` to mean explicitly ownerless; a plugin manifest writes `commands: [command names]`. A one-sided declaration on either side is a validate error — preventing unowned commands and plugins falsely claiming commands alike.

Usage lands on commands by two routes. **Pull side**: a command's frontmatter writes `consumes: [plugin list]`, declaring which plugins' usage it pulls; owner-driven commands must fill it in and include all owners. **Source-side routing**: a plugin manifest writes `usage_routes: [command name list]`, declaring which additional commands its usage lands on — installing the plugin lands the projection, with no need to edit destination commands. Presence-as-registration is honored on the push side: (un)installing a single file takes effect. validate checks that routing targets are present, that routing plugins carry usage, and that duplication with consumes is an error.

Disclosure order is presentation order: owner blocks first, in consumes order; routed blocks in the middle, in dependency topology plus alphabetical order; the remaining consumes bring up the rear.

First-case walkthrough: the bb-track command, the cognition hub. The bb-track command declares only `consumes: [bb-track, trust, log]`; bb-teach and bb-quiz each declare `usage_routes: [bb-track]` in their manifests. After `all`, the bb-track command's SKILL.md contains five `<!-- usage:<id> -->` sub-blocks: bb-track's own write rules, the full usage of the two collection channels bb-quiz and bb-teach, and the write-side rules of trust and log. The effect: any agent stepping into the bb-track command site gets — in one place, with zero retrieval — how teaching and quizzing are used, how grading flows back, and what to do after writes. To establish a third collection channel later, the new plugin only needs well-written usage plus a routing declaration; the projection arrives automatically and the hub command changes not one character.

Usage routing is inspectable at any time via `ls`: every plugin carrying usage lists the commands it lands on; those with no landing are marked as the contract-documentation surface — e.g. email's write-side contract, declared ahead of use.

## 5. The Bridge Law

Global pieces are cross-cutting services and destinations: trust, log, todo, calendar, notes, user-profile. They may declare bridges; a domain piece holding a bridge is an error.

A must-attach bridge is written in the manifest as `bridge: 必依`: every domain base must have a depends edge to the piece; a missing edge is a validate error. log is an instance — the `log` edge in cuhksz's depends in the section 2 table is forced by the must-attach bridge: any domain's activity must leave a trace. This is a topology-completeness invariant, not a style suggestion.

An on-demand bridge is written as `bridge: 按需`: absence is tolerated. user-profile's cognition bridge is an instance — bb-track registers one line only if the profile is present when it creates the archive; if absent it skips, creating nothing on the profile's behalf and raising no error.

Why consumes cannot replace bridges — the 2026-10-04 ruling gives two hard reasons:

1. Must-attach completeness checking is a topological constraint. "Every domain base, not one may lack an edge" is a global graph invariant; consumes is a single command's list and cannot express global completeness
2. Writes across territories happen in every command execution. todo derivation, calendar derivation, notes emergence — none of them pass through some single-point command container; there is nowhere to hang consumes

Division of labor: the bridge holds validation and declaration — who may attach, cardinality, completeness checking, absence tolerance; disclosure distribution belongs to projection — the authoritative source of the integration format is usage, arriving at consumption sites via cmd-inject.

## 6. The Capability Mechanism

Since v0.4, packages declare capabilities in PKG.yaml — `needs: [ … ]` / `provides: [ … ]`, deliberately package-scale (a capability is never declared at plugin level). The kernel enforces:

- **Grammar**: `^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$` — e.g. `owfa.org.v1`. The `owfa.*` namespace is framework-owned (special grants aside); any other capability's first name segment must equal the declaring package id
- **Exact-name matching**: a need is satisfied only by a provides of the very same name — a v2 provider leaves a v1 need unsatisfied, reported distinctly from a wholly missing capability
- **Exclusive slots**: at most one installed package may provide a given capability; a second provider is a validate error
- **Trust-gated satisfaction**: only provides from trusted packages (framework-bundled, reviewed-3rd-party — the registry INDEX row is the trust source) satisfy needs; an exact-name provider at unverified trust is a soft refusal, overridable with `--yes` and then journaled. Grammar, exclusive-slot, missing, and version failures refuse outright — no override

At install time the check runs as a preflight over the prospective package graph, before any file or projection changes; at validate time the same laws run over the full graph (single-package `--scope` mode downgrades them to warnings). The capability model's design rationale lives in [packages.md](packages.md); this section only fixes the mechanics.

## 7. The Derived Layer

The kernel governs the mechanisms and projections — the plugin graph, manifest compliance, and everything derived from them (since the v0.4 split, plugin *content* travels with packages; the kernel's authority over it is mechanical, not editorial); pipeline governs the data area — wiki derived pages. The commands are `python .owfa/scripts/pipeline.py index / tags / hot / log / verify`:

- **index / tags**: directory indexes and the tag reverse index. Pure-function rebuilds that only aggregate, never inventing structure; when an index list overflows the window, split the subdirectory into its own index — the cure is more subdirectories, not editing the index
- **hot**: the recent-change hot cache. At most 25 entries, within 5 days, each entry under 200 characters; agents read it first on entering the vault
- **log**: run-log line writing and rolling archive. Window at most 100 entries; overflow is mechanically archived to `wiki/archive/<month>/log.md`
- **verify**: post-write consistency check. The post-write pipelines of commands like map and save end with it

Derived pages and projections are two applications of one philosophy: projections derive from manifests — no second source on the framework side; derived pages derive from vault content — no second source on the data side. Hand-editing a derived page is futile; the next rebuild overwrites it.

## 8. (Un)install Lifecycle

Since the split (2026-10-12) **packages are the install unit and the lifecycle is kernel-driven** — the authoritative account lives in [packages.md](packages.md) (package model, the migrations algebra, the uninstall contract) and in the owfa-plugin command skill (the wizard protocol). What follows here is the mechanics-level view.

`kernel install <pkg>` lands a package in five moves: capability preflight (section 6 — hard failures refuse before anything changes); plugin masters are copied to `.owfa/plugins/domains/<pkg>/`; connectors ride along into the instance's `connectors/`; package-borne command masters land in `.owfa/command/` (existing files are kept, never overwritten); the PKG-declared `skeleton:` directories are mkdir'd mechanically — the kernel hardcodes no instance layout. Projections then converge via `all`. Install channels: the registry, direct `owner/repo` (requires `--yes`, trust: unknown), or `--path` for local packages.

Uninstall is the package-level `kernel uninstall <pkg> --yes` (four-clear + residual scan + teardown staging — see packages.md). Upgrade stages semantic migrations on top of the re-install.

Authoring a new plugin today means authoring it inside a package repository: prepare the three pieces under the package tree, `validate`, `all`, smoke test (`audit <id>` plus a walk-through of the key flows per PLUGIN.md), log a line — then release through the package's version bump and registry row. Discipline throughout: script errors always block, warnings only report; versions advance along the changelog — no pre-reserving or skipping numbers.

## 9. How Domains Grow

The framework sets no whitelist for information sources outside the wiki. Integration is answering the same contract, and growth follows the same path. Follow the cuhksz package through — its bb family is the most complete in-tree example.

### The Contract's Six Questions

Designing a domain is answering the questions one by one. The answers land in the domain base's territory declaration and injection line:

| Question | The cuhksz domain's answer |
|---|---|
| Where is the external territory | The cuhk.edu.cn school-system family — bb course ops, sis student records, registry academic regulations; connector cuhksz-cli (aggregating bb and sis; the legacy bb-cli / sis-cli wrappers remain for compatibility), purely read-only |
| Landing strategy | Isomorphic two sides: the `cuhksz/` data zone plus the `wiki/cuhksz/` territory |
| Identity proof | The domain identity page `wiki/cuhksz/identity.md`; term-name and course-code directories plus machine ids in the bb block mapping |
| wiki-side territory | `wiki/cuhksz/bb/<term>/<course>/`, bb-map's four-bucket projection |
| Write model | Fetched artifacts append-only; notes/ human-led, ai products append-only without overwrite |
| Trust model | machine-confirmed ceiling; stale_after = fetch date + TTL |

### Three Write Models

Landing is essentially a write-model choice, with three archetypes:

- **Final-state asset → append-only store**. Once landed, the body no longer changes — e.g. vault assets, bb materialized courseware, sis transcript PDFs. The command side is append-only; deletion and modification belong to humans
- **Process container → full read-write**. The agent works inside it — e.g. `projects/`, ai products in bb notes/
- **Truth lives elsewhere → pointer**. The source changes and no local copy is needed — e.g. lark pointer pages, bb media defaulting to pointers. stale_after governs freshness; the agent is the synchronizer

### Projection Density

Projection density decreases as translation cost rises, in three grades. **Mirror**: a 1:1 proxy, e.g. mapping. **Pointer**: token plus url plus snapshot excerpts, e.g. lark. **Disclosure-only**: one injection line plus on-demand live pulls, e.g. email retrieval. The default posture is borrowing vault or pointers; self-standing containers are the exception — when: the write model forks, or the structure is rigidly dictated by the source. The cuhksz data zone stands alone for its rigid two-sided structure.

### The Growth Path

After the contract: the **domain base** establishes the territory — cuhksz is isomorphic two sides plus notes/ cohabitation, declared as one package; **in-domain governing members** follow — bb, sis, and registry, each ruling a sub-territory with a direct edge to both the base and domain; then the **in-domain piece family** — bb-map's projection law, bb-track's cognition profile, shapes growing heavier; **consumer-side collection channels** close it out — bb-teach and bb-quiz, zero territory, pure workflow, usage hung on hub commands via source-side routing. The in-family dependency chain `bb-quiz → bb-track → bb-map → bb → cuhksz` is the mechanical expression of this path — see section 2.

### Material and Archives

A two-way split inside the domain. Process products live in the domain workspace: fetched artifacts, human notes, ai notes, exam papers and grading. Settled conclusions live in the wiki territory: projection pages, cognition readings. The wiki takes distillates, not process. This line is isomorphic to the global discipline, only landed inside the domain.

### Connectors

Connectors ship with packages — each PKG.yaml declares its connectors (in-repo `path`, `external` maintained elsewhere, or `system` preinstalled binaries), and `kernel install` copies in-repo connector directories into the instance's `connectors/`. Each connector's `SKILL.md` then lands as the `.agents/skills/` copy via kernel `deploy`. The difference from commands: commands are pure wiki operations, masters in `.owfa/command/`; connectors are data-fetching channels to external systems — credentials stay on the local machine, never committed, never persisted to disk. Domain plugins declare territory and discipline; connectors provide the de-facto interface. Discipline and tooling are separate.

## 10. Scenario Quick Reference

| You want to | Action |
|---|---|
| Change write-side rules / inspection rules / the injection line | Edit the corresponding manifest key in `.owfa/plugins/domains/<pkg>/<id>/PLUGIN.yaml`, run `all` |
| Attach a new plugin's usage to a command | That plugin's manifest writes `usage`; the command's frontmatter consumes adds the id; run `all` |
| Edit a connector skill | Edit the `connectors/<name>/SKILL.md` master, run `deploy` or `all` |
| Quick health check | `validate` plus `audit`; full audit via the check command |
| (Un)install or upgrade a package | The owfa-plugin command does semantics, `kernel install / uninstall / upgrade` does mechanics — see [packages.md](packages.md) |
| Rebuild data-area derived pages | `pipeline.py index` or `tags`; hot and log are maintained as writes happen |
| Integrate a new external source | Answer the contract's six questions, see section 9; author a connector and a domain-family package; the owfa-plugin wizard walks the install |
