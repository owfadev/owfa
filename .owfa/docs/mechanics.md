# Mechanics in Detail

> Audience: members and contributors who will modify the framework. The authoritative source of mechanical rules is the kernel reference skill and the `.owfa/` source code. This document expands the master outline by one level — principles, instance walkthroughs, and hands-on procedures — without copying rule text; where it conflicts with the source, the source prevails. Written 2026-10-04.

## 0. One Source, Five Projections

Each plugin is one directory, living at `.owfa/plugins/<id>/`. `PLUGIN.yaml` is the machine-readable body — the manifest. From the manifest, the kernel script mechanically projects into five places:

| Projection | Landing point | Source key | Who reads it |
|---|---|---|---|
| AGENTS injection region | `<!-- plugin:<id> v<x> -->` marker block | `inject` | The agent of every session; constitution-level disclosure |
| check inspection block | the `check-inject` block inside the check command | `checks` | The check command; semantic items |
| command usage block | the `cmd-inject` block inside each command | `usage`, in consumes order | Command execution sites; write-side rules |
| registry plugin section | `.owfa/protocol/registry.yaml` | `fields` | Commands consulting the field vocabulary before writing pages |
| skill copy | `.agents/skills/<command>/` | command and connector masters | Deployment-side agents |

The key property is idempotent rebuilding. Hand-editing inside marker blocks is forbidden — a rebuild overwrites; prose outside the blocks belongs to humans. There is no second source of truth: changing a rule means changing the manifest, after which the single command `all` converges everything. The whole class of documentation-drift problems is eliminated wholesale — projections and the body cannot disagree, because they are not two separate things.

Walk through one real sample. In bb-quiz's manifest, `inject:` is a single one-line disclosure stating what the quiz self-test does and where its products land. After `all` runs, that line appears verbatim in the AGENTS injection region inside the `<!-- plugin:bb-quiz v0.2 -->` block. What agents read day to day is the projection; the manifest body is touched only when (un)installing plugins.

## 1. Plugin Shape

One plugin, one directory, three pieces:

- `PLUGIN.yaml` — the manifest, the body
- `PLUGIN.md` — pure documentation: design summary, Structure, Invariants, Changelog. The why of the design lives here; mechanical commonality belongs to the kernel reference
- `scripts/check.py` — optional attached audit. Defines `check(ctx)` returning `[{level, message}]`, read-only with zero side effects; the shape is statically validated via AST

Seven required manifest keys, illustrated with real values from bb-quiz v0.2:

| Key | Semantics | Instance |
|---|---|---|
| `id` / `version` / `updated` | Identity and version; advance along the changelog without skipping numbers | `bb-quiz` / `0.2` / `2026-10-04` |
| `depends` | Dependency list | `[bb-track, bb-map]` |
| `attachment` | Territory declaration: owning means writing, borrowing means read-only consumption | see below |
| `fields` | The plugin's own page fields; enter the registry's global vocabulary | `quiz`, the exam-paper block mapping |
| `inject` | The source of the injection-region line; constitution-level disclosure | see the AGENTS bb-quiz block |

Four optional keys. `commands` declares the commands this plugin drives; `usage` is the write-side rule list; `checks` is the inspection rules; `bridge` is the bridge declaration, which only global pieces may hold.

A fifth optional key `inject_tier` (full|member, default full) carries the **tier law** (issue #12 layer discipline): member exits the AGENTS injection region — exposure rides on the family root's roster line, the skill catalog, and on-demand reads of the manifest, and validate requires a member to reach a full-tier domain root through depends. The projected region carries a byte budget (16 KiB), keeping the A layer pointer-dense: pointers and red lines, never procedures or formats (contract in `protocol/experiments.md`). Each full-tier inject line also has a 256 B pointer-density guideline (issue #49) — over it, validate warns: keep the line to path + read/write trigger + the one easy-to-break invariant + a pointer to PLUGIN.md.

attachment deserves a closer look. bb-quiz declares three entries:

- `bb/<term>/<course>/notes/testing/` is the exam-paper sub-region, owned by this plugin. Each test run adds a question set plus answers; grading is appended on the answer page
- `wiki/bb/<term>/<course>/user.md` is the cognition profile, owned by bb-track. This plugin reads it only; grading writes back through bb-track's write rules
- `courseware/` and `assessments/` belong to bb-map. This plugin reads them only, taking sm-N anchors, the terminology table, and known assignments

The first is ownership; the latter two are borrows: the territory belongs to another plugin, and write paths must pass through its rules. attachment is the framework's property registry. Who owns which paths, who read-only consumes whom — visible at a glance, mechanically checkable.

## 2. Dependencies and Injection Order

`depends` declares dependencies. validate checks two things: dependencies exist, and there are no cycles — cycles are detected via DFS.

A domain piece is any plugin whose depends chain reaches `domain`. Those connecting to domain directly are domain bases — the five pieces vault, lark, project, email, bb; pieces inside a domain belong to it transitively, without connecting directly. bb-quiz does not connect to domain directly: it arrives via `bb-quiz → bb-track → bb-map → bb → domain`, and is thus a domain piece.

Injection order = dependency topology plus alphabetical order within a batch: dependees are injected first; same-batch pieces sort by name. Look at the bb family's depends and the real order in the injection region:

| Plugin | depends | Effect |
|---|---|---|
| bb | `[domain, wiki, trust, log]` | Domain base, injected first within the family |
| bb-map | `[bb, wiki]` | Mapping law, after bb |
| bb-track | `[bb, bb-map, trust, wiki]` | Cognition profile, after bb-map |
| bb-quiz / bb-teach | `[bb-track, bb-map]` | Collection channels; same batch sorted by name — quiz before teach |

This guarantees one thing: when a consumer-side plugin is injected, the disclosures it consumes are already present. bb-teach's injection line says "discipline, see the bb-track block" — that block is necessarily above it. There is one more domain discipline: a domain must be discoverable inside the wiki, via declaration page or injection line; domain pieces create no root containers.

## 3. Projection Walkthrough

Suppose you want to add one discipline to bb-quiz's write-side rules — here is what happens:

1. Edit the `usage:` list in `.owfa/plugins/bb-quiz/PLUGIN.yaml` and add a line. While at it, bump `version` and refresh `updated`; add a line to PLUGIN.md's Changelog
2. Run `python .owfa/scripts/owfa_kernel.py all`. In sequence: validate goes first — failure blocks, fix and rerun; if the inject line changed too, the AGENTS injection region is rebuilt; the cmd-inject blocks of the two command SKILL masters bb-quiz and bb-track are rebuilt — the usage appears in every command whose consumes includes bb-quiz; the registry plugin section is rebuilt; skill copies are synced
3. Self-review the diff. Changes should land only in the manifest, the two command SKILL masters, and the `.agents/skills/` copies; if inject or fields changed, AGENTS and registry change as well. Any change beyond these is an anomaly
4. Commit in the format `plugin: bb-quiz …`; one commit does one thing

This is the everyday feel of "one source, five projections": you wrote one thing, and five places agree automatically.

## 4. Command Binding

owner and commands are mutual declarations. A command's SKILL.md frontmatter writes `owner: <plugin-id>`, or `framework` to mean explicitly ownerless; a plugin manifest writes `commands: [command names]`. A one-sided declaration on either side is a validate error — preventing unowned commands and plugins falsely claiming commands alike.

Usage lands on commands by two routes. **Pull side**: a command's frontmatter writes `consumes: [plugin list]`, declaring which plugins' usage it pulls; owner-driven commands must fill it in and include all owners. **Source-side routing**: a plugin manifest writes `usage_routes: [command name list]`, declaring which additional commands its usage lands on — installing the plugin lands the projection, with no need to edit destination commands. Presence-as-registration is honored on the push side: (un)installing a single file takes effect. validate checks that routing targets are present, that routing plugins carry usage, and that duplication with consumes is an error.

Disclosure order is presentation order: owner blocks first, in consumes order; routed blocks in the middle, in dependency topology plus alphabetical order; the remaining consumes bring up the rear.

First-case walkthrough: the bb-track command, this cognition hub. The bb-track command declares only `consumes: [bb-track, trust, log]`; bb-teach and bb-quiz each declare `usage_routes: [bb-track]` in their manifests. After `all`, the bb-track command's SKILL.md contains five `<!-- usage:<id> -->` sub-blocks: bb-track's own write rules, the full usage of the two collection channels bb-quiz and bb-teach, and the write-side rules of trust and log. The effect: any agent stepping into the bb-track command site gets — in one place, with zero retrieval — how teaching and quizzing are used, how grading flows back, and what to do after writes. To establish a third collection channel later, the new plugin only needs well-written usage plus a routing declaration; the projection arrives automatically and the hub command changes not one character.

Usage routing is inspectable at any time via `ls`: every plugin carrying usage lists the commands it lands on; those with no landing are marked as the contract-documentation surface — e.g. email's write-side contract, declared ahead of use.

## 5. The Bridge Law

Global pieces are cross-cutting services and destinations: trust, log, todo, calendar, notes, user-profile. They may declare bridges; a domain piece holding a bridge is an error.

A must-attach bridge is written in the manifest as `bridge: 必依`: every domain base must have a depends edge to the piece; a missing edge is a validate error. log is an instance — the `log` edge in bb's depends in the section 2 table is forced by the must-attach bridge: any domain's activity must leave a trace. This is a topology-completeness invariant, not a style suggestion.

An on-demand bridge is written as `bridge: 按需`: absence is tolerated. user-profile's cognition bridge is an instance — bb-track registers one line only if the profile is present when it creates the archive; if absent it skips, creating nothing on the profile's behalf and raising no error.

Why consumes cannot replace bridges — the 2026-10-04 ruling gives two hard reasons:

1. Must-attach completeness checking is a topological constraint. "All five domain bases, not one may lack an edge" is a global graph invariant; consumes is a single command's list and cannot express global completeness
2. Writes across territories happen in every command execution. todo derivation, calendar derivation, notes emergence — none of them pass through some single-point command container; there is nowhere to hang consumes

Division of labor: the bridge holds validation and declaration — who may attach, cardinality, completeness checking, absence tolerance; disclosure distribution belongs to projection — the authoritative source of the integration format is usage, arriving at consumption sites via cmd-inject.

## 6. The Derived Layer

The kernel governs the framework area — plugins and projections; pipeline governs the data area — wiki derived pages. The commands are `python .owfa/scripts/pipeline.py index / tags / hot / log / verify`:

- **index / tags**: directory indexes and the tag reverse index. Pure-function rebuilds that only aggregate, never inventing structure; when an index list overflows the window, split the subdirectory into its own index — the cure is more subdirectories, not editing the index
- **hot**: the recent-change hot cache. At most 25 entries, within 5 days, each entry under 200 characters; agents read it first on entering the vault
- **log**: run-log line writing and rolling archive. Window at most 100 entries; overflow is mechanically archived to `wiki/archive/<month>/log.md`
- **verify**: post-write consistency check. The post-write pipelines of commands like map and save end with it

Derived pages and projections are two applications of one philosophy: projections derive from manifests — no second source on the framework side; derived pages derive from vault content — no second source on the data side. Hand-editing a derived page is futile; the next rebuild overwrites it.

## 7. (Un)install Lifecycle

The semantic flow of (un)installing goes through the plugin command, where the agent does the semantic part; the mechanical steps are this CLI. Since the split (2026-10-12) **packages are the install unit and this lifecycle is kernel-driven** — the authoritative accounts live in [packages.md](packages.md) (package model, the migrations algebra, the uninstall contract) and in `.owfa/command/plugin/SKILL.md` (the wizard protocol). What follows is the historical per-plugin flow, retained for the record; the install steps still describe authoring a new plugin inside the framework repo.

Install, five steps: prepare the three pieces under `.owfa/plugins/<id>/`; `validate` — errors block; `all` — projections arrive; smoke test — `audit <id>`, plus a walk-through of the key flows per PLUGIN.md; log a plugin line.

Upgrade, three steps: edit the plugin, bump `version`, add a Changelog line; `all`; log line. Package-level upgrades (`kernel upgrade`) additionally stage semantic migrations — see packages.md.

Uninstall: superseded by the package-level `kernel uninstall <pkg> --yes` (four-clear + residual scan + teardown staging, see packages.md). The old per-plugin flow — `validate` blocks dependents → move the directory out (archived, physical deletion belongs to humans) → `all` — applied before packages existed.

Discipline: script errors always block, warnings only report; versions advance along the changelog — no pre-reserving or skipping numbers.

## 8. How Domains Grow

The framework sets no whitelist for information sources outside the wiki. Integration is answering the same contract, and growth follows the same path. Follow the bb family through — it is the most complete family.

### The Contract's Six Questions

Designing a domain is answering the questions one by one. The answers land in the domain base's territory declaration and injection line:

| Question | The bb family's answer |
|---|---|
| Where is the external territory | bb.cuhk.edu.cn, connector bb-cli purely read-only |
| Landing strategy | Isomorphic two sides: `bb/` workspace plus `wiki/bb/` territory |
| Identity proof | Term-name and course-code directories, plus machine ids in the bb block mapping |
| wiki-side territory | `wiki/bb/<term>/<course>/`, bb-map's four-bucket projection |
| Write model | Fetched artifacts append-only; notes/ human-led, ai products append-only without overwrite |
| Trust model | machine-confirmed ceiling; stale_after = fetch date + TTL |

### Three Write Models

Landing is essentially a write-model choice, with three archetypes:

- **Final-state asset → append-only store**. Once landed, the body no longer changes — e.g. vault assets, bb materialized courseware. The command side is append-only; deletion and modification belong to humans
- **Process container → full read-write**. The agent works inside it — e.g. `projects/`, ai products in bb notes/
- **Truth lives elsewhere → pointer**. The source changes and no local copy is needed — e.g. lark pointer pages, bb media defaulting to pointers. stale_after governs freshness; the agent is the synchronizer

### Projection Density

Projection density decreases as translation cost rises, in three grades. **Mirror**: a 1:1 proxy, e.g. mapping. **Pointer**: token plus url plus snapshot excerpts, e.g. lark. **Disclosure-only**: one injection line plus on-demand live pulls, e.g. email retrieval. The default posture is borrowing vault or pointers; self-standing containers are the exception — when: the write model forks, or the structure is rigidly dictated by the source. bb stands alone for its rigid two-sided structure.

### The Growth Path

After the contract: the **domain base** establishes the territory — bb is isomorphic two sides plus notes/ cohabitation; the **in-domain piece family** follows — bb-map's projection law, bb-track's cognition profile, shapes growing heavier; **consumer-side collection channels** close it out — bb-teach and bb-quiz, zero territory, pure workflow, usage hung on hub commands via source-side routing. The in-family dependency chain `bb-quiz → bb-track → bb-map → bb` is the mechanical expression of this path — see section 2.

### Material and Archives

A two-way split inside the domain. Process products live in the domain workspace: fetched artifacts, human notes, ai notes, exam papers and grading. Settled conclusions live in the wiki territory: projection pages, cognition readings. The wiki takes distillates, not process. This line is isomorphic to the global discipline, only landed inside the domain.

### Connectors

Connectors live in `connectors/` — the domain's deployment-side CLI de-facto interface plus usage disclosure: `connectors/<name>/SKILL.md` lands as the `.agents/skills/` copy via kernel `deploy`. The difference from commands: commands are pure wiki operations, masters in `.owfa/command/`; connectors are data-fetching channels to external systems — credentials stay on the local machine, never committed, never persisted to disk. Domain plugins declare territory and discipline; connectors provide the de-facto interface. Discipline and tooling are separate.

## 9. Scenario Quick Reference

| You want to | Action |
|---|---|
| Change write-side rules / inspection rules / the injection line | Edit the corresponding manifest key, run `all` |
| Attach a new plugin's usage to a command | That plugin's manifest writes `usage`; the command's frontmatter consumes adds the id; run `all` |
| Edit a connector skill | Edit the `connectors/*/SKILL.md` master, run `deploy` or `all` |
| Quick health check | `validate` plus `audit`; full audit via the check command |
| (Un)install a plugin | The plugin command does semantics, this CLI does mechanics |
| Rebuild data-area derived pages | `pipeline.py index` or `tags`; hot and log are maintained as writes happen |
| Integrate a new external source | Answer the contract's six questions, see section 8; write a connector; the plugin command installs the domain base and in-domain pieces |
