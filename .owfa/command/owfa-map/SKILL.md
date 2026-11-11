---
name: owfa-map
owner: mapping
consumes: [mapping, trust, tag, index, hot, log]
description: "Map assets in vault/ into wiki proxy pages: SHA-256, mirror path, frontmatter, index/hot-cache/log linkage. Triggers on: map, 映射, process this source, add this to the wiki."
---

# owfa-map: mapping

Map assets in `vault/` into `wiki/vault/` proxy pages — mapping and understanding are decoupled: a pure registration action (registration fields, body scale, and other write-side contracts are in the injection region). It targets only assets already in vault and does no vault-side processing (organizing and polishing belong to vault governance, discussed separately).

## Scope

Write: mapping (proxy pages), log, hot, index
Read: registry (`.owfa/protocol/registry.yaml`, field and value-set anchor), tag (vocabulary `wiki/tags.md`), trust (generated), vault (originals)

## Steps

1. **Anchor (one-time read)**: read `.owfa/protocol/registry.yaml` and `wiki/tags.md` — value sets and the existing vocabulary are visible before writing
2. Read the target asset in vault/
3. Assemble the proxy-page draft per the write-side contracts in the injection region (mapping mirror and registration fields, trust generated, tag labeling); **present the mapping preview** (path / hash / description / tags) and wait for user confirmation
4. After confirmation, write the proxy page
5. **Post-write pipeline** (deterministic, mechanical and automatic, no prompting): execute each plugin's write calls in injection-region order, then finish with `python .owfa/scripts/pipeline.py verify` (post-write self-verification; on failure, go back and fix); then commit per the commit discipline (`映射: <asset name>`, see the vocabulary in `.owfa/protocol/actions.md`)
6. Report: path / hash / description / tags

## Prohibitions

- Never modify any vault/ file (the command side is append-only toward vault); other hard rules (hash always computed, body never a full copy, etc.) defer to the mapping block of the injection region

## Language

Output language takes the default key of the language declaration page `wiki/language.md` (a missing page or missing key falls back to the session language); proper nouns and paths keep their original form.

## Parameters

- Asset path (relative inside vault/); batching allowed

## Injected Section (plugin usage blocks)

> This region is a owfa-kernel projection: consumes pulls merged with usage_routes source-side routing; disclosure order = owner first, routed blocks in the middle, pulled blocks last (rebuilt by inject / all); handwritten content does not belong here — to change the write-side contract, edit PLUGIN.yaml.

<!-- cmd-inject:start -->
<!-- usage:mapping -->
- Mirror locating: proxy path = `wiki/vault/<original-path>.md` (original name + .md, prevents name collisions); md assets also get proxies, no exceptions
- Registration fields: `type: source` + `raw_file` (root-relative path) / `raw_sha256` (hexadecimal SHA-256, never skip the computation)
- Body starts with a one-line description, never copying the full original text; summary / structure extraction are optional enhancements; diary-type assets are registration-first, summaries not enforced
- URL-type assets: the proxy page carries `url` (vault field — source link, source preservation; required when placed via agent channels, optional for manual placement)
<!-- /usage:mapping -->

<!-- usage:trust -->
- When writing a page, write `generated` along the way (block style: `by: agent/<current-model>` / `at: <today>`)
- When a review action happens, append a `verified` event (single line `by: <actor>, at: <date>`), never fabricated to inflate the level
- Reviews are initiated by the user (triggered by human instruction); agents never append verified events on their own
<!-- /usage:trust -->

<!-- usage:tag -->
- Before writing, read `wiki/tags.md` and prefer reusing existing terms
- New-term conventions: primary language follows the language page's default key (absent → session language, preventing mixed Chinese-English fragmentation of the vocabulary); English lowercase kebab-case; hierarchy ≤2; ≤5 per page; restating type forbidden
<!-- /usage:tag -->

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
