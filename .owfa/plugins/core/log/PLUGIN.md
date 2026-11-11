# log: Run Log

## Design Summary

- **Why it exists**: the repository's operation journal — what was done to the repository and when. Opposite of hot: hot is the present that gets evicted, log is append-only never-deleted history. The mandatory bridge guarantees that anything any domain produces always leaves a trace — an instance of the topological-completeness invariant, see Section 5 of mechanics
- **Key rulings**:
  - Entries are append-only and never rewritten, prepended at the top: modifying a historical entry = error; archival moves don't change a single character of an entry
  - Rolling window rather than an infinite ledger: the main file holds at most 100 entries; overflow is mechanically archived, grouped by entry month, to `wiki/archive/<month>/log.md` — freshness and full history both served
  - Writing is mechanized: via `pipeline.py log`; capacity checks and archiving are performed by the script; the authoritative source of parameters is the script source
  - Domain tags, since 0.15: in-domain transaction entries carry `[domain]`; domainless transactions omit it — the journal becomes searchable by domain

## Structure

- Single file `wiki/log.md`; entries prepended at the top, newest on top
- Entry format: `- YYYY-MM-DD <type> [<domain>]: one-sentence summary`, may contain wikilinks; the domain tag is omissible, i.e. domainless transactions
- Type enum: map, save, query, check, plugin, todo, other; instances may extend

## Bridge: mandatory

Recording bridge: the operation-journal home shared by all domain plugins across domains, constitution principle 11. Attachment cardinality **mandatory** — all domain bases must depend on this plugin; kernel validate verifies completeness; the topology guarantees: anything a domain produces leaves a trace. Format authority lives in this plugin's usage, projected to the consumption sites, per the division-of-labor ruling. This section details: in-domain transaction entries carry the domain tag `[domain]`, e.g. `[bb]`; domainless transactions omit it; written via `pipeline.py log --domain`.

## Invariants

- Entries are append-only and never rewritten — the object of "append-only, never delete" is entry content, not the file's physical location; modifying a historical entry = error
- Every entry must carry a date, accurate to the day
- Archival moves don't change a single character of entry content

## Rolling

The main file is a rolling window, not an infinite ledger:

- Window of at most 100 entries, about 14k characters; the mechanical authoritative source is `pipeline.py`, this section is the semantic description
- On overflow the oldest segment is automatically moved, grouped by entry month, into `wiki/archive/YYYY-MM/log.md`; entry content unchanged by a single character, only moved. The archive file is the reserved name log.md of its directory — reserved-name files are not concept pages, naturally exempt from frontmatter
- The archive directory falls into the immutable zone; compression and consolidation still require human confirmation, see constitution principle 5

## Config

```yaml config
log.max_entries: 100     # main-file rolling window, entries
log.max_chars: 14000     # window character cap, approximate
```

## Changelog

- 0.16 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.15 2026-10-02: global-domain batch one — established the mandatory bridge, i.e. the recording bridge; domain bases must depend on it, kernel verifies completeness; entries gained the omissible `[domain]` tag; pipeline log gained the `--domain` parameter
- 0.13 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.12 2026-09-14: type value set extended with todo — the home of the todo plugin's task-settlement events; history goes to log, the todo page keeps only the active working set
- 0.11 2026-09-13: usage's type parameter gained its value-set source — the log block of the AGENTS injection region, removing cross-block guess points
- 0.10 2026-09-13: injection source moved to the manifest — removed Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.9 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.8 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.7 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.6 2026-09-11: the undated-entry check moved into the attached-audit script, main file and archive checked alike; the historical-modification audit kept as a semantic item, verifiable via git
- 0.5 2026-09-10: writing mechanized — via pipeline.py log; capacity checks and archiving performed by the script; the authoritative source of parameters moved to the script source
- 0.4 2026-09-10: archive path rerouted to `wiki/archive/YYYY-MM/log.md` — grouped by entry month; reserved names exempt from frontmatter
- 0.3 2026-09-10: manifest gained layer: derived — layering established: derived layer, zero dependencies
- 0.2 2026-09-09: the rolling-archive mechanism written down, window of 100 entries; the type enum gained "query"; parameters calibrated against the original repository's measurements, averaging 139 characters per entry
- 0.1 2026-09-08: converted from the original wiki log rules
