# trust: Trust Fields

## Design Summary

- **Why it exists**: knowledge ages — turn "is this piece of knowledge still trustworthy" from re-reading the full text into reading a field. A cross-cutting field plugin: four trust fields, claimed from the registry-reserved section, shared repository-wide; a mandatory bridge attached to all domain bases
- **Key rulings**:
  - Level derivation is never persisted: pure computation at read time — unverified, machine-confirmed, human-reviewed, stale. The regenerable zone does not create a second truth that would drift
  - All four fields optional: not written = unverified, blocking no read or write — trust is an enhancement, not a threshold
  - verified is append-only, never rewritten: events are history; appends are triggered by review actions, reviews are initiated by the user, agents never spontaneously; never fabricated to inflate the level
  - The semantics of stale_after is "if no one reviews after this point, it should be considered expired" — refreshing it is itself a renewal decision

## Structure

- `generated`: block-style mapping of `by` plus `at` — actor convention plus YYYY-MM-DD; who generated the page. map and save write it along the way when producing proxy pages and notes
- `verified`: event list; items single-line `by: <actor>, at: <date>`; appendable multiple times, i.e. the review history. Who may write: human review, and mechanical verification by agent or process such as hash recalculation
- `stale_after`: YYYY-MM-DD absolute moment; semantics "if no one reviews after this point, it should be considered expired"; refreshing it = a renewal decision
- `sources`: source list; items contain id, resource, credibility signals — author, usage_count, last_modified

## Example

```yaml
generated:
  by: agent/GLM-5.3
  at: 2026-09-12
verified:
  - "by: process:hash-recalc, at: 2026-09-12"
  - "by: human:Joss, at: 2026-09-12"
stale_after: 2026-12-31
sources:
  - id: fog-harbor-design-memo
    resource: vault/fog-harbor/design-memo.md
    author: human:Joss
    usage_count: 3
    last_modified: 2026-09-05
```

In the example above the level = human-reviewed, containing a human event; after 2026-12-31 reads show stale. All four fields are optional; usually only `generated` is written.

## Level Derivation

Computed at read time, never persisted:

- **unverified**: no verified records
- **machine-confirmed**: only agent or process events
- **human-reviewed**: contains a human event, the highest level
- **stale**: now not earlier than stale_after — independent of the levels above, overrides the display

Derivation must not generate derived pages: the regenerable zone does not create a second truth that would drift; consumers — query, check, viewer — compute per the table above on the fly.

## Invariants

- verified events are append-only, never rewritten; events are history; appends are triggered by review actions, never fabricated to inflate the level
- Level and stale judgments are pure comparisons, no hidden state
- All fields optional: not written = unverified, blocking no read or write

## Bridge: mandatory

Field bridge: the trust-field contract shared by all domain plugins across domains, constitution principle 11. Attachment cardinality **mandatory** — all domain bases, i.e. plugins directly depending on domain, must depend on this plugin; kernel validate verifies completeness. Format authority lives in this plugin's usage, projected to the consumption sites, per the division-of-labor ruling. This section details: domain pages may optionally carry the four trust fields; each domain self-declares its trust ceiling, e.g. machine-confirmed; level derivation is computed at read time, never persisted.

## Changelog

- 0.10 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.9 2026-10-02: global-domain batch one — established the mandatory bridge, i.e. the field bridge; domain bases must depend on it, kernel verifies completeness
- 0.8 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.7 2026-09-13: usage gained the verified production channel — reviews are initiated by the user, agents never append spontaneously; expert review: the input channel was idling
- 0.6 2026-09-13: injection source moved to the manifest — removed Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.5 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.4 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.3 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.2 2026-09-12: disclosure patch — inlined a full-shape example of the four fields; cold-start audit guess point: spec without instances
- 0.1 2026-09-11: established — claimed the four registry-reserved fields and backfilled the plugin section; level derivation never persisted; attached audit covers the field contract, the stale list, and trust-level counts
