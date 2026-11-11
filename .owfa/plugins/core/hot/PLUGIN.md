# hot: Hot Cache

## Design Summary

- **Why it exists**: the recent-change digest page — the lowest-cost entry for an agent entering the repository, read hot first then dig deeper as needed; opposite the index retrieval entry, hot is the entry to "now". Merely a cache: if lost, rebuildable from log and the repository
- **Key rulings**:
  - Hard-cap trio — 25 entries, 5 days, 200 characters per entry: parameters calibrated against the original repository's measurements — per-entry median 389 characters, maximum 4959, runaway proven; the mechanical authoritative source is pipeline.py
  - The evict-before-write duty: outside the window means delete; eviction and truncation are performed mechanically by the script, no asking — the cache does not bloat
  - The only derived page with hand-written links: broken links are checked but it is not an inbound-link source, per the link contract

## Structure

- Single file `wiki/hot.md`, organized in sections — Recent map, Recent save, Recent query, Recent check, etc.
- Entry: date plus wikilink plus a one-sentence essence, at most 200 characters, a hard cap

## Invariants

- Wholly regenerable: hot is merely a cache; if lost, rebuildable from log and the repository
- Rolling window: outside the window means delete; eviction and truncation are performed mechanically by the script, no asking

## Config

```yaml config
hot.max_entries: 25        # mechanical authoritative source in pipeline.py; the script source is the rule list
hot.max_days: 5
hot.max_entry_chars: 200   # parameters calibrated against the original repository's measurements: per-entry median 389 chars, max 4959, runaway proven
```

## Changelog

- 0.10 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.9 2026-09-13: usage's type parameter gained its value-set source — same as log, pointing to the log block of the AGENTS injection region
- 0.8 2026-09-13: injection source moved to the manifest — removed Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.7 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.6 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.5 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.4 2026-09-10: writing mechanized — via pipeline.py hot, eviction and truncation performed by the script; the authoritative source of parameters moved to the script source
- 0.3 2026-09-10: manifest gained layer: derived — layering established: derived layer, zero dependencies
- 0.2 2026-09-09: per-entry length cap of 200 characters, plus the evict-before-write duty written down
- 0.1 2026-09-08: converted from the original wiki hot structure
