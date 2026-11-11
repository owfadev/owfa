---
name: save
owner: [notes, sessions]
consumes: [notes, sessions, trust, index, hot, log]
description: "Save the current conversation, answers, or insights as wiki native notes. Deduplicate before filing, infer type and title, chunk-extract long sessions, update index/log/hot cache. Triggers on: save this, /save, file this, save to wiki, 保存."
---

# save: capture

Good answers should not vanish in chat history. Save what was just discussed as permanent wiki pages. The wiki compounds through it — save often.

## Scope

Write: sessions (session backbone pages), notes (native notes), log, hot, index
Read: registry (`.owfa/protocol/registry.yaml`, field and value-set anchor), tag (vocabulary `wiki/tags.md`), trust (generated), index / hot (dedup prerequisites)

## Dedup Before Filing (required)

1. Read wiki/hot.md and wiki/index.md for recent context
2. Search existing pages by title and key concepts
3. A related page exists: never rewrite directly — show the differences and let the user adjudicate (append-style merging requires a user instruction and leaves traces, or the human edits by hand, or a new page is created); partial overlap: likewise, show the differences and let the user choose
4. Create a new page only after confirming none covers it

## Type and Destination

type / status value sets defer to the registry (a one-time read anchor; do not re-copy the table); ask only on genuine ambiguity. Destination splits by type: session goes to the long-sessions section below, other native types land in `wiki/notes/` (per-type destinations and contracts in the injection region); the source type is out of scope here — anything with a vault counterpart goes through map.

## Workflow

1. **Anchor (one-time read)**: read `.owfa/protocol/registry.yaml` and `wiki/tags.md` — type / status value sets and the existing vocabulary are visible before writing
2. Scan the conversation for high-value content (non-obvious insights, decisions with reasons, hard-won analyses, comparisons that will be cited again); skip mechanical Q&A / debugging processes / content already in the repository
3. Set the type (ask only on genuine ambiguity) and title (ask only on ambiguity or conflict)
4. Rewrite in declarative present tense: write knowledge, not dialogue
5. Create the page per the write-side contracts in the injection region (notes / sessions destinations and shapes, trust generated, tag labeling); the session type goes to the long-sessions section
6. Write wiki pages mentioned in the conversation into related with wikilinks
7. **Post-write pipeline** (deterministic, mechanical, automatic): execute each plugin's write calls in injection-region order, then finish with `python .owfa/scripts/pipeline.py verify` (post-write self-verification; on failure, go back and fix); then commit per the commit discipline (`保存: <page title>`, see `.owfa/protocol/actions.md`)
8. Report: `Saved as [[title]] in wiki/notes/` (session type: `... in wiki/sessions/`)

## Long Sessions (session backbone)

1. Split into 3-8 sections by topic (not by message count); merge and drop mechanical details
2. Create the session backbone page: destination, default naming, participants, backbone-page shape, and promotion rules in the sessions block of the injection region
3. Ask about the title only on genuine ambiguity

## Writing Rules

Declarative present tense; output language takes the default key of the language declaration page `wiki/language.md` (a missing page or missing key falls back to the session language); every concept / page mentioned gets a wikilink; a future session must be able to cold-read this page.

## Parameters

- `/save` saves the whole session; `/save <topic>` saves only that topic; `--force` skips confirmation (only when conflict-free)

## Injected Section (plugin usage blocks)

> This region is a owfa-kernel projection: consumes pulls merged with usage_routes source-side routing; disclosure order = owner first, routed blocks in the middle, pulled blocks last (rebuilt by inject / all); handwritten content does not belong here — to change the write-side contract, edit PLUGIN.yaml.

<!-- cmd-inject:start -->
<!-- usage:notes -->
- Landing spot `wiki/notes/<title>.md`, file name free (named by humans); type form vocabulary in registry (open, self-extended by instances), territory values do not land in this zone
- Append-only: commands never rewrite an existing note wholesale; updating = append-style merge under user instruction (trace left in the body) or manual human edits
<!-- /usage:notes -->

<!-- usage:sessions -->
- Landing spot `wiki/sessions/YYYY-MM-DD-<topic>.md` (default naming), type: session, participants required (actor list)
- Backbone page five-section shape: Core Conclusions / Decisions & Rationale / Non-obvious Insights / Open Questions / Related Pages (full-shape sample in the Example section of `.owfa/plugins/sessions/PLUGIN.md`)
- Standalone high-value topics promoted to `wiki/notes/` pages, the backbone page keeping a wikilink; dedupe before promotion
<!-- /usage:sessions -->

<!-- usage:language -->
- Register discipline: follow the language.register audience reading level when writing saved artifacts; absent register uses the program baseline (first/second-year undergraduates), while explicit user audience requirements and domain source-alignment rules take precedence
- When to read: read the declaration page before writing any artifact (wiki pages, documents, lecture distillates); page or key absent = follow the session language (conversation language is the output language); proper nouns, code, paths, commands, and file names always keep their original form (language neutrality, invariant under configuration) — the framework presets no specific language; Chinese is merely an instance fact of this project's development period (AGENTS principle 7)
- Term discipline: when writing hits a term, consult the `terms` mapping first — if tabled, follow the table; otherwise annotate the original in parentheses on first occurrence (e.g. '检索增强生成 (RAG)'), registering only after recurring hits (emergence-based); a registered entry = a single line original→translation, long notes (translation rationale, usage examples) go to the body distillation section
- Layering: a default baseline, not a mandate — the domain plugins' source-alignment discipline (exam language follows samples/course materials) takes precedence over this page; tag word forms belong to tag, forms of address and personal dynamic preferences belong to user-profile, in-domain term tables (the bb courseware glossary) are self-managed within the domain — none of these are restated on this page
- Maintenance: the `language` mapping is human-defined first, the agent may propose; the `terms` mapping may be registered by the agent but never overwrites human-defined entries (objections reported); the body distillation section is append-only
<!-- /usage:language -->

<!-- usage:trust -->
- When writing a page, write `generated` along the way (block style: `by: agent/<current-model>` / `at: <today>`)
- When a review action happens, append a `verified` event (single line `by: <actor>, at: <date>`), never fabricated to inflate the level
- Reviews are initiated by the user (triggered by human instruction); agents never append verified events on their own
<!-- /usage:trust -->

<!-- usage:index -->
- Post-write rebuild (mechanical, automatic): `python .owfa/scripts/pipeline.py index` (index — overflow-offloading scheme, including deletion of obsolete old indexes after merge-back) and the same script's `tags` (tag reverse index); LLMs never hand-write indexes
<!-- /usage:index -->

<!-- usage:hot -->
- Writing entries (mechanical, automatic): `python .owfa/scripts/pipeline.py hot <type> "<wikilink + one-sentence essence>"` (type value set same as log, see the log block of the AGENTS injection region); window eviction and truncation are performed by the script
<!-- /usage:hot -->

<!-- usage:log -->
- Writing lines (mechanical, automatic): `python .owfa/scripts/pipeline.py log <type> "<one sentence>" [--domain <domain>]` (type value set in the log block of the AGENTS injection region; domain tag = domain-plugin name such as bb/lark/vault, mandatory for in-domain transactions, omitted for framework and native transactions); rolling window and archiving are performed by the script
<!-- /usage:log -->
<!-- cmd-inject:end -->
