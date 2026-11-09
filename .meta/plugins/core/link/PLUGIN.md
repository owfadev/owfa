# link: Link Layer

## Design Summary

- **Why it exists**: wiki's ontological structure — reference relations between pages; links are where the value of knowledge lies, thinking happens where things collide. A field plugin: owns the link syntax and the related and aliases fields, and hosts the graph-property health checks — broken links and orphans
- **Key rulings**:
  - Full names, not titles: `[[page full name]]` = the relative path within wiki/ minus one .md — an extension of "the path is the origin" into the link layer; truncated references forbidden; same-name ambiguity resolved by path, disambiguation never by guessing
  - Broken links are not defects: a broken link may be knowledge not yet written down, TODO placeholders are a normal state; warning not error; when unsure, better to leave a TODO than to guess
  - Inbound sources for orphan detection count only concept pages: derived pages and tmp don't count — otherwise the index links everything and orphans never trigger; mechanical-registration territory pages drop to info, registration being the norm; notes knowledge pages stay warning
  - The syntax conventions must enter the injection line: when the conventions lived only in the attached-audit source, a zero-prior agent was bound to guess wrong, proven in 0.8 — a lesson specimen of disclosure completeness

## Structure

- `related` field: YAML list; full names of pages related to this page's topic, i.e. wikilinks
- `aliases` field: YAML list; this page's aliases and short names, for link resolution and retrieval
- wikilink syntax conventions: `[[page full name]]`. **Full name = the page file's relative path within wiki/ minus the trailing .md**, e.g. `notes/X`; an md asset's proxy file is `<name>.md.md`, its full name `vault/<name>.md`, only one removed. Truncated partial references are forbidden; long compound names must be written in full; on same-name ambiguity, include the path

## Invariants

- Link targets must resolve: the full name hits a page, or hits some page's aliases
- Broken links are not silent but not treated as defects: a broken link may be knowledge not yet written down, TODO placeholders are a normal shape; when unsure of the target, better to leave a TODO than to guess
- Orphan detection is a graph property: only a page with no inbound links and no related references is an orphan; **inbound sources count only concept pages** — index, hot, log, tags and other derived pages, the archive/ subtree, and the tmp/ temporary zone with its draft broken-link exemption — none count as link sources, otherwise the index links everything and orphans never trigger. Territory-value pages — registry territory values except session, i.e. source, lark, calendar, structure, todo, profile, project, tmp, the mechanical-registration kinds — having no inbound links yet is the registration norm, downgraded to info; notes knowledge pages stay warning. hot is the only derived page with hand-written links: its broken links are checked but it is not an inbound-link source

## Changelog

- 0.15 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.14 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.13 2026-09-19: _concept excluded wiki/tmp/ — the temporary zone is not a link source and is exempt from graph checks; a draft's broken link = not yet written down, closed upon promotion
- 0.12 2026-09-19: the orphan info set changed to dynamically reading registry type.values except session — new territory types covered automatically, the hardcoded set retired, prerequisite for project's establishment
- 0.11 2026-09-19: the orphan info set extended to all territory values except session — calendar smoke testing confirmed false-positive warnings on calendar.md and month pages; the judgment aligned with registry territory values, no more squeezing toothpaste type by type
- 0.10 2026-09-19: the orphan-downgrade criterion changed from path-based to type-based, source and lark treated alike — the lark-family landing smoke test confirmed: new pointer pages falsely warned en masse
- 0.9 2026-09-13: attached audit gained the hot hand-written broken-link scan; orphan grading — proxy pages dropped to info; expert review: warning inflation; the injection line gained the md-asset full-name example
- 0.8 2026-09-13: the full-name definition entered the injection line and Structure — test-repo walkthrough finding: the conventions lived only in the attached-audit source, a zero-prior agent was bound to guess wrong
- 0.7 2026-09-13: injection source moved to the manifest — removed Checks, Inject, Attachments sections, md returned to pure documentation
- 0.6 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.5 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.4 2026-09-11: mechanical items absorbed into the attached-audit script — broken links, garbled text, orphans; new alias-ambiguity as error, and one-way related as info; the hub list kept as a semantic item
- 0.3 2026-09-10: broken links downgraded to warning — knowledge not yet written down, not a defect; the orphan-detection scope written down, derived pages don't count as inbound sources
- 0.2 2026-09-10: manifest gained layer: field — layering established: field layer, zero dependencies
- 0.1 2026-09-09: newly established — link syntax and the related and aliases fields; the broken-link check converted from the original lint; the orphan check moved over from notes
