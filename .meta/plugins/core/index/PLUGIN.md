# index: Index

## Design Summary

- **Why it exists**: a cheap retrieval entry, the second layer of query, a pointer structure for drilling down level by level. A derived-layer aggregation page — born of the parent's offloading need, not a directory's "supposed duty"
- **Key rulings**:
  - Overflow-offloading scheme, final shape in 0.10: a small repository lists all content directly in the root index, one page serves all — the engineering repository went 4-to-1, test-repo measured 8-to-1; wherever content grows, the disclosure boundary appears there. The cure is always subdirectories, never index changes
  - Pure-function rebuild, never hand-edited: the offloading split is a function of the structural status quo; same structure, same result, no historical state
  - Indexes do not invent structure: an index only reflects structure, never hints how directories should be organized — silent on content quality
  - The root index is the version self-statement spot: format_version is the page-format contract version, bumped on incompatible changes

## Structure

- The root `wiki/index.md` is always present: a format_version frontmatter, i.e. the page-format contract version, bumped on incompatible changes — the root index is the version self-statement spot; it directly lists reachable pages, taking in this directory and un-split subtrees, full-path wikilinks
- Other directories' `index.md` are born of overflow offloading: when some index list — page entries plus directory entries — overflows the window, subtrees are split out in descending page-count order, ties by name order, into their own index, until it fits; applies recursively
- Entry = wikilink plus description — frontmatter `description` first, falling back to the body's first non-empty non-structural line truncated at 80 characters; concept pages grouped by type; a split-out subdirectory's entry line carries the subtree count; an empty subtree keeps a 0-page visibility line, with no link, outside the broken-link graph
- `wiki/tags.md`: the tag-to-page reverse index, aggregating the tag plugin's field

## Invariants

- Index pages are wholly regenerable, never hand-edited: aggregate only, originate nothing; pure-function rebuild — the offloading split is a function of the structural status quo, same structure same result, no historical state
- Window parameters defer to the `pipeline.py` source code; the script source is the rule list; obsolete old indexes after merge-back into the parent are mechanically deleted on rebuild
- Indexes do not invent structure: the existence and content of an index only reflect structure, never hint how directories should be organized; when a level's flat files overflow the window, they are listed over the window as-is; splitting directories belongs to humans and territory plugins
- Consistent with the actual page set; reserved-name files, i.e. index and log, the wiki root's derived pages, i.e. hot and tags, the archive/ subtree, and the tmp/ temporary zone are invisible to the derived layer: not concept pages, not indexed

## Changelog

- 0.14 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.13 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.12 2026-09-23: added the wiki dependency edge — inner-side plugins attach to wiki, aligning with the domain 0.1 declaration; omitted from the 2026-09-22 domain-ization batch
- 0.11 2026-09-19: concept-page detection excluded wiki/tmp/ — the temporary zone stays out of indexes and tags, in step with the tmp plugin's establishment
- 0.10 2026-09-19: the per-directory scheme changed to the overflow-offloading scheme — list window of at most M, subtree-descending splits, the root always present, empty-subtree visibility lines; small repositories collapse to a single index, the engineering repository 4-to-1, test-repo measured 8-to-1; invariants gained "pure-function rebuild" and "indexes do not invent structure"
- 0.9 2026-09-13: the format_version semantics entered the in-repository disclosure — expert review: no provenance inside the instance; index-description truncation gained an ellipsis, pipeline `_cut`
- 0.8 2026-09-13: injection source moved to the manifest — removed Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.7 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.6 2026-09-13: the root index's version self-statement field renamed format_version — the format contract internalized, the plugin's external contract references zeroed
- 0.5 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical order, direction checks removed
- 0.4 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enums, pipeline call parameters
- 0.3 2026-09-10: per-directory indexing, progressive disclosure — root page carrying the version self-statement field, subdirectories carrying counts; rebuilds scripted as pipeline.py index and tags, LLMs never hand-write
- 0.2 2026-09-10: manifest gained layer: derived — layering established: derived layer, depending only on tag
- 0.1 2026-09-08: converted from the original wiki index, i.e. the master-catalog rules; changed to whole rebuilds only, no incremental writes
