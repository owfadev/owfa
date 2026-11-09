# tag: Semantic Classification

## Design Summary

- **Why it exists**: semantic classification across all pages — a semantic index with zero infrastructure: the semantic work is done at write time, map and save tag along the way; retrieval only does mechanical matching
- **Key rulings**:
  - Division of labor between type and tags: type is a closed protocol enum, origin, for machines to read; tags are open semantic classification, for humans and agents to retrieve — the two axes never mix, restating type is forbidden
  - The vocabulary grows freely, governance is after-the-fact merging, no up-front control — consistent with "the architecture does not enumerate"
  - Lightweight discipline: the primary language follows the language page's default key (absent → session language, preventing mixed Chinese-English fragmentation of the vocabulary); English proper names in kebab-case; hierarchy `/`-separated up to two levels; at most 5 per page, a soft cap. The former "Chinese-primary" hardcoding was removed in the language-neutralization batch (2026-10-04) — Chinese was merely a development-phase instance fact of this project

## Structure

Owns the `tags` field conventions:

- YAML list; the primary language follows the language page's default key (absent → session language), English proper names keep their original form
- English tags use lowercase kebab-case, e.g. local-llm
- Hierarchy allows the `parent/child` form; depth at most 2
- At most 5 per page, a soft cap

## Invariants

- `type` is a closed protocol enum, origin, for machines to read; `tags` are open semantic classification, for humans and agents to retrieve; restating type semantics is forbidden
- The vocabulary grows freely; governance is after-the-fact merging, no up-front control

## Changelog

- 0.12 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.11 2026-10-04: language neutralization — "Chinese-primary" removed; the primary language follows the language page's default key (absent → session language); hierarchy wording changed to "≤2, `/` separated"; the English kebab-case word-shape rule kept (already neutral); same batch as the language v0.2 follow-up cleanup
- 0.10 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.9 2026-09-13: checks merged with executors unified as mechanically-confirmed items; expert review: two conflicting tellings versus actions.md
- 0.8 2026-09-13: injection source moved to the manifest — removed Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.7 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.6 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.5 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.4 2026-09-11: attached audit gained the hierarchy-depth check, parent/child at most 2, empty-segment warnings
- 0.3 2026-09-10: manifest gained layer: field — layering established: field layer, zero dependencies
- 0.2 2026-09-09: mechanical check items landed in the attached-audit script scripts/check.py; this file keeps the semantic items
- 0.1 2026-09-08: newly established, absorbing the original lint's near-duplicate check idea
