# notes: native notes

## Design Overview

- **Why it exists**: knowledge whose provenance is the wiki itself — the 'original text' is the wiki, with no counterpart in vault. The main territory of native knowledge; session minutes and profile cognition are routed by closed type values to their own territories
- **Key rulings**:
  - No-regeneration zone: pipelines and commands must not overwrite or rewrite existing notes; they may only add, and humans may edit freely — the true copy lives here, writing is birth
  - Subdivision relies on the type field, not directories: form values are open, default vocabulary in registry, self-extended by instances — the architecture takes no responsibility for form classification. The 0.13 ruling: the 'concept/question/decision/entity' enumeration was a residue of the personal-library migration and had drifted from registry
  - The boundary with the proxy layer is proven by path: wiki/vault/ always has a counterpart, wiki/notes/ never does — the path is the provenance

## Structure

- `wiki/notes/**`; file names free, named by humans, in contrast to the mechanical naming of the mirror zone
- Subdivision via the type field, not directories; form values open, default vocabulary in registry, self-extended by instances; territory values session and profile are closed and must land in their own territories

## Invariants

- No-regeneration zone: pipelines and commands must not overwrite or rewrite existing notes; only additions or manual human edits
- The boundary with the vault proxy layer is proven by path: wiki/vault/ always has a counterpart, wiki/notes/ never does
- The boundary with sessions and user-profile is proven by type: type: session lands in `wiki/sessions/`; type: profile lands in `wiki/profile.md`; neither lands in this zone

## Bridge: on-demand

A derivation-destination bridge governing high-value conclusions: domain plugins one-way derive high-value conclusions that emerge as native notes, with a required back-link to the source page. Constitutional principle 11. Attachment cardinality **on-demand**. Format authority is in this plugin's usage, projected to the point of consumption — division-of-labor ruling. This section elaborates: the type is freely chosen within the form vocabulary, the body back-links via wikilink; the domain plugin keeps a one-sentence self-description disclosure, SASU-L.

## Changelog

- 0.16 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.15 2026-10-02: global-domain batch two — established the on-demand bridge as the derivation destination; domain-plugin self-descriptions retained with a pointer
- 0.14 2026-09-23: added the wiki dependency edge — inner plugins attach to wiki, aligning with the domain 0.1 declaration; missed in the 2026-09-22 domainization batch
- 0.13 2026-09-14: slimmed down; ruling: the architecture takes no responsibility for form classification — the form enumeration removed from body and inject line; 'concept/question/decision/entity' was personal-library migration residue, drifted from registry, comparison missed; type layering: territory values closed, namely source, session, profile — the basis for mechanical checks; form values demoted to an instance default vocabulary, registry defaults, open to self-extension
- 0.12 2026-09-13: usage updated for semantic stitching — update = append-style merge under user instruction leaving a trace, or manual edits; expert review: two tellings alongside the save dedup section
- 0.11 2026-09-13: usage dropped the type enumeration; the value set's single source is registry, removing triple restatement
- 0.10 2026-09-13: inject source moved to the manifest — deleted the Checks, Usage, Inject, Attachments sections; md returns to pure documentation
- 0.9 2026-09-13: established the Usage section — write-side contracts handed to command injection regions for projection, single text source
- 0.8 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical, direction checks removed
- 0.7 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enumerations, pipeline call parameters
- 0.6 2026-09-11: manifest added commands: [save] — save is jointly driven by this plugin and sessions
- 0.5 2026-09-10: narrowed scope — session backbone pages moved to the sessions plugin, an independent territory `wiki/sessions/`; this zone kept concept, question, decision, entity
- 0.4 2026-09-10: type enumeration wording fixed — defers to the registry value set, resolving the contradiction with registry closure
- 0.3 2026-09-10: manifest added layer: origin — layering established: the provenance layer, zero dependencies
- 0.2 2026-09-09: orphan checks moved to the link plugin — graph properties belong to the link layer
- 0.1 2026-09-08: merged and simplified from the original wiki concepts, questions, comparisons, and sessions zones; subdivision batch two
