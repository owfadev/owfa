---
name: query
owner: framework
consumes: [log]
description: "Retrieve from the wiki and answer synthetically: hot cache → index → grep → read pages, producing answers with wikilink citations. Triggers on: query, what do you know about, what is, explain, find in wiki, 检索."
---

# query: retrieval

Read-mostly; the only write action is one log line (a read signal). Layered progression — the cheapest goes first.

## Scope

Read: hot, index, tags, pages
Write: log (one line only, type "query")

## Read Order

1. wiki/hot.md (recent context, cheapest)
2. wiki/index.md / wiki/tags.md (directory and tag indexes)
3. grep (path / title / body keywords)
4. Read specific pages to confirm (≤3-5 pages per query)

## Answer Rules

- Output language takes the default key of the language declaration page `wiki/language.md` (a missing page or missing key falls back to the session language); page names are preserved as wikilinks
- Cite sources inline
- Explicitly flag contradictions with existing repository content

## Not For

- Do not read the repository for general programming questions (training data already covers them)
- Do not read the repository for content already in the conversation or project files

## Wrap-up

- Write one log line (a read signal — this is how read popularity becomes measurable): see the log block of the injection region for how to call it
- A log line is a data-zone change: commit immediately per the commit discipline (`检索: <topic>`, see `.owfa/protocol/actions.md`); do not batch up

## Injected Section (plugin usage blocks)

> This region is a owfa-kernel projection: consumes pulls merged with usage_routes source-side routing; disclosure order = owner first, routed blocks in the middle, pulled blocks last (rebuilt by inject / all); handwritten content does not belong here — to change the write-side contract, edit PLUGIN.yaml.

<!-- cmd-inject:start -->
<!-- usage:log -->
- Writing lines (mechanical, automatic): `python .owfa/scripts/pipeline.py log <type> "<one sentence>" [--domain <domain>]` (type value set in the log block of the AGENTS injection region; domain tag = domain-plugin name such as bb/lark/vault, mandatory for in-domain transactions, omitted for framework and native transactions); rolling window and archiving are performed by the script
<!-- /usage:log -->
<!-- cmd-inject:end -->
