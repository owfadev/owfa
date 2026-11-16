# The Default Protocol

> Reader: anyone who uses this suite — the vault owner, agents working in an OWFA instance, and anyone who wants to understand this way of organizing information well enough to write a second protocol. This is the full charter of the default protocol as it exists today. Facts live here as implemented; nothing on this page is a promise about future syntax.

## Lineage

**llmwiki → vault-wiki → the OWFA default protocol.** The idea of organizing an agent-worked information repository as a wiki over a plain-file vault was born as llmwiki, took shape as the vault-wiki framework (2026-08 the personal vault founded; 09-08 the plugin prototype landed), and since OWFA v0.4 ships as this package — the **personal** suite, the first and currently the only implementation of that organization principle.

One terminology note before anything else: since framework 0.4.3 the kernel recognizes `kind: protocol` (with the `protocol:` field and an org-capability declaration), and this package declares it: `protocol: vaultwiki`, `provides: vaultwiki.org.v1` — the first protocol package. The protocol ABI is shipped machinery since 0.1.3: the package-root `proto_query.py` serves four semantics — `list`, `get`, `search`, `recent` — over the wiki face; the normative detail lives in [docs/abi.md](abi.md), and conformance tests in [tests/](../tests/). What this document describes is what the 21 members plus `pipeline.py` actually implement.

## What the Protocol Is

The protocol is three things at once:

1. **Information-shaping rules** — where information of each kind lands, in what shape, under whose write model. The vault/wiki split, territory syntax, page types, link grammar, red lines.
2. **A self-sufficient baseline** — with zero additional packages installed, the workspace is complete: map, save, query, and check all work. Domains (cuhksz, lark, email, bili, …) are add-ons that build on this baseline structure, not prerequisites for it.
3. **A service surface** — cross-cutting services every member uses: the derived layer (index, tags, hot, log), retrieval conventions, distillation zones (notes, sessions), the check rule set, and the ABI face.

The **ABI face is the whole `wiki/`** — the add-on domain territories are included (bili/lark/cuhksz page types are served like any other page), `wiki/tmp/` is excluded (tmp's invisible-to-the-derived-layer semantics carry over to the ABI). Pages are addressed by wiki-relative path (the full-name grammar of the `[[...]]` link syntax); see [docs/abi.md](abi.md) for the normative detail. Bridges consume this face **read-only** — a foreign workspace never writes through the ABI.

### Protocol vs. Domain vs. Kernel — three tests

A domain's internal rules can look deceptively protocol-like (a course domain's four-bucket layout is a miniature organization law). Three tests separate them:

| Test | Protocol | In-domain rules |
|---|---|---|
| **Whom does it bind?** | Everything in the workspace, including each domain's inner territory grammar | Only its own members and data |
| **Can it be removed?** | Remove it and the workspace is no longer this workspace | Uninstall the domain; the workspace is unharmed |
| **Does it provide cross-cutting services?** | Derived layer, retrieval, check rules, distillation zones — shared by all | No; domain derivations land through the protocol's services (conclusions enter notes via bridges, retrieved via the protocol's index) |

The kernel, in turn, owns the *mechanisms* (manifest syntax, projections, [package/capability engine](https://github.com/owfadev/owfa/blob/master/.owfa/docs/packages.md) / [kernel mechanics](https://github.com/owfadev/owfa/blob/master/.owfa/docs/kernel.md), check machinery) and is protocol-agnostic: it enforces whatever rules the installed packages declare. In one sentence — **the kernel is the machinery, the protocol is this workspace's law, a domain is a defined information kind with its own charter**.

## The Shape of the Slots

*Slots* — storage, retrieval, distillation, checking — are an understanding frame for reading this suite, not a declared syntax. Each protocol fills the same slots with its own shapes; here is how this one does.

### Storage

- **The vault/wiki split**. `vault/` holds real assets of any format — the landing repository for everything, append-only toward the agent (deleting and modifying belong to the human). `wiki/` holds the md world: territory pages, native writings, and derived projections. Everything is Markdown plus plain files; no tool-private formats; viewers (Obsidian, web UIs) are replaceable.
- **Territory syntax**. Every path under `wiki/` belongs to some plugin's territory: `wiki/notes/` (native notes), `wiki/sessions/` (session backbones), `wiki/vault/` (proxy mirror of `vault/`), `wiki/tmp/` (temporary zone, invisible to the derived layer), `wiki/cron/` (deferred triggers), domain territories (`wiki/<domain>/…`), and the single-page territories (`hot.md`, `log.md`, `index.md`, `tags.md`, `todo.md`, `profile.md`, `language.md`, `structure.md`, `calendar.md`).

### Retrieval

- `wiki/index.md` (plus subtree `index.md` on overflow) — every reachable page by full path, derived, never hand-edited.
- `wiki/tags.md` — the tag reverse index.
- Full-text grep across `wiki/` for everything else.
- **Hot cache** `wiki/hot.md` — the recent-change digest agents read first on entering: ≤25 entries, <5 days, ≤200 chars per entry.

### Distillation

- `wiki/notes/` — knowledge born in the wiki; commands append, never modify. `wiki/sessions/` — session backbone pages; high-value topics are promoted to notes with a back-link.
- **Bridges and back-links**: domain derivations must back-link their source; cross-territory conclusions travel over declared bridges (must-attach or on-demand), and the wiki takes distillates, not process.

### Checking

Each member carries its own rule set in `checks:` (see the roster below); attached audit scripts (`scripts/check.py`) run mechanically on audit discovery, semantic items run in the check command. The rule sets sum to the protocol's health surface: window bounds on hot/log, derived-page drift, link integrity, trust-field validity, territory placement, mirror diffs between `vault/` and `wiki/vault/`, and more — every member's PLUGIN.yaml lists its own items verbatim.

## Vocabulary

| Term | Meaning |
|---|---|
| **wiki** | The md world (`wiki/`): territory pages, native writings, derived projections |
| **vault** | The real-asset store (`vault/`), any format, agent-append-only |
| **domain** | A bounded source-of-truth region with an adapter contract; wiki recognizes inside vs. outside |
| **territory** | The slice of paths a plugin owns (owning means writing; borrowing means read-only consumption) |
| **derived layer** | Mechanically regenerated pages (index / tags / hot / log) — hand-editing is futile, the next rebuild overwrites |
| **page type** | The open `type` frontmatter vocabulary; structure is declared by each plugin, not enumerated by the protocol |
| **red lines** | Hard disciplines: append-only toward `vault/` and log/history; no hand-regeneration of derived pages; commands append to notes/sessions, never modify; instance data never enters git |

## The Derived Machine: pipeline.py

[pipeline.py](../pipeline.py) lives at the package root (since 0.1.1) — derived-layer machinery travels with the suite; the kernel never calls it. Instance path: `.owfa/plugins/domains/personal/pipeline.py` (the framework tree keeps a deprecated host copy until 0.5.0). Deterministic structural operations go to this script; semantic judgment goes to the LLM; commands end by invoking it instead of hand-writing derived pages.

| Command | Effect |
|---|---|
| `index` | Rebuild `wiki/**/index.md` (pure function, idempotent; deletes surplus indexes after offloading merges back) |
| `tags` | Rebuild `wiki/tags.md` (idempotent) |
| `hot <type> <one-liner>` | Evict out-of-window entries, then prepend one hot-cache entry |
| `log <type> <one-liner> [--domain <d>]` | Capacity-archive, then prepend one log line (domain tag optional) |
| `verify` | Post-write self-attestation: kernel audit + derived-area drift check |

Window parameters (the script source is the authoritative rule list): hot ≤ **25** entries / **5** days / **200** chars; log main file ≤ **100** entries (overflow archived by month to `wiki/archive/<month>/log.md`); a single index list ≤ **25** entries, overflow cured by splitting subdirectories into their own indexes. Concept pages = all `.md` under `wiki/`, excluding reserved names, root derived pages, `archive/` and `tmp/`.

## Member Roster

The 21 members (versions verbatim from each PLUGIN.yaml; the `personal` package, `kind: protocol` / `protocol: vaultwiki` — version and compat floor see [PKG.yaml](../PKG.yaml)):

| id | one line | version |
|---|---|---|
| calendar | Time territory: `wiki/calendar.md` source keys + month pages (`## Schedule` wholesale refresh, `## Manual Notes` append-only) | 0.5 |
| cron | Deferred triggers `wiki/cron/`, one page per task (`cron` block + append-only run notes) | 0.5 |
| device | Device profiles in `wiki/notes/`; `device` block + tool-environment registry; warranty-expiry audit | 0.5 |
| domain | Declares inner/outer: each domain's adapter contract; members inherit | 0.3 |
| hot | Recent-change digest `wiki/hot.md` (≤25 entries, <5 days, ≤200 chars); agents read it first on entering | 0.11 |
| index | Derived `wiki/index.md` (+ subtree indexes on overflow); rebuild via `pipeline.py index` | 0.15 |
| instance-git | Instance git as snapshot ledger of real use: agent commits at transaction close; credentials never tracked | 0.2 |
| language | Writing declaration `wiki/language.md`: language rules and unified terms, read before writing artifacts | 0.6 |
| link | Link syntax `[[full name]]` = path within `wiki/` minus `.md`; never truncate; broken/orphan grading | 0.15 |
| log | Run log `wiki/log.md`: prepend, never rewrite; written via `pipeline.py log`; >100 entries auto-archived | 0.17 |
| mapping | Proxy layer `wiki/vault/`: 1:1 mirror of `vault/`, pages carry `raw_file` / `raw_sha256` | 0.8 |
| notes | Native notes `wiki/notes/`: knowledge born in the wiki, open `type` vocabulary; commands append, never modify | 0.16 |
| sessions | Session backbones `wiki/sessions/` (`type: session`, `participants` required); promotion to notes with back-link | 0.11 |
| structure | Vault layout declaration `wiki/structure.md`; read before placing assets, sync after reorganizations | 0.5 |
| tag | Page `tags`: YAML list, ≤5 per page, hierarchy ≤2; open semantics, never restate `type` | 0.13 |
| tmp | Temporary zone `wiki/tmp/`: drafts and intermediates, no retention promise, invisible to the derived layer | 0.4 |
| todo | Temporary memory `wiki/todo.md`: read first at session start (before hot); entry = trigger + one sentence + by/at; settle with [x] + log line | 0.6 |
| trust | Trust fields (`generated`/`verified`/`stale_after`/`sources`); level is derived, never stored | 0.10 |
| user-profile | Continuing cognition of the user in `wiki/profile.md`; write only via the profile command; assertions carry evidence | 0.8 |
| vault | Default domain `vault/`: real assets, append-only toward the agent; landing repository for other domains | 0.7 |
| wiki | The wiki container `wiki/`: territory page shape, frontmatter constraints, derived projections | 0.8 |

The package also ships three commands of its own (`command/owfa-map`, `owfa-save`, `owfa-profile`) and declares its skeleton directories (`vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`).

## Switching Protocols

The protocol is a package, so leaving it is a package uninstall — and the uninstall contract keeps your data:

- **Data survives.** `uninstall.retains: [vault/, wiki/]` — real assets and the whole wiki world stay on disk untouched.
- **Anchors are respected.** The declared anchors (`wiki/profile.md`, `language.md`, `structure.md`, `calendar.md`, `todo.md`, `wiki/cron/`) are instance content the kernel refuses to sweep.
- Install the new protocol package the usual way (`kernel install <pkg>`), migrate what the new organization can digest, and go.
- **Reinstalling this suite revives the workspace**: the derived layer (`index`, `tags`) is mechanically rebuilt from the surviving pages — nothing in `wiki/` needed the suite to stay readable.
