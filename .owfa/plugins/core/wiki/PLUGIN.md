# wiki: The md World

## Design Summary

- **Why it exists**: the **inner root** of the dual-root concept — paired with the outer root domain, it declares what wiki is and how page origin is determined. A concept-declaration plugin: it owns no territory, fields, commands, or scripts, holding only invariants; the "inner" half of Section 8 of mechanics
- **Key rulings**:
  - The inner/outer distinction is the first cut: wiki = the totality of the md world — projections of all domains plus native knowledge, the common language layer between agent and human; everything on the outer side belongs to the domain contract
  - Origin dichotomy, expanded in 0.7 into two territory forms: to determine what a page is, look at the path first, then the frontmatter — the path is the origin proof, not a metadata self-claim
  - Two territory forms, 2026-10-02 group meeting: proxy pages — projections of reconcilable external sources; plus in-domain native pages — domain-side archives whose true body lives here, first case bb-track user.md. This legitimizes the existing tension of lark and email archive pages, it does not open an exception hatch
  - Session pages are minutes, not mirrors: once the conversation vanishes the page is the true body, writing is birth — the line versus lark-im archives is whether the source is alive and reconcilable
  - frontmatter takes a minimal YAML subset: the parser is lenient but this is the boundary — top-level scalars, block lists, one-level block mappings; more complex structures silently deform; this is the page-format contract

## Structure

Container `wiki/`, zoned by the origin dichotomy, pages have three origin layers:

- Domain territories, pages each domain declares as its territory, in two forms: proxy pages are the default — projections of reconcilable external sources, vault assets, lark objects, etc., territory paths self-disclosed by each domain's injection line; **in-domain native pages** are domain-side archives declared by a domain — the true body lives here, no external source to reconcile, shape owned by the domain plugin; first case bb-track cognition profile user.md; lark person files and email person files carried this tension all along, this move legitimizes them rather than opening a hatch
- Native territory, everything else: writings whose true body lives here — notes knowledge, sessions minutes, tmp and todo workspaces, profile cognition profile. Among them session pages are minutes, not mirrors: once the conversation runtime vanishes the page is the true body, writing is birth; the line versus lark-im archives is whether the source is alive and reconcilable, judgment method in domain
- Derived facilities: index, tags, hot, log — mechanical projections, zero edges to the environment

Cross-cutting plugins — tag, trust, link — occupy fields and syntax, not pages, and do not belong to the page-origin layering.

## Invariants

- The path is the origin proof: to determine what a page is, first look at where it is — among the three zones above — then at the frontmatter; which domain a territory belongs to is likewise read from path convention, the declaration proper lives in each domain's manifest
- All text in the repository is UTF-8; type is required on knowledge pages; reserved-name exemptions apply
- frontmatter takes a minimal YAML subset — top-level scalars, block lists, one-level block mappings: the parser is lenient but this is the boundary; more complex structures will silently deform

## Changelog

- 0.8 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.7 2026-10-02: two territory forms — proxy pages as the default, plus in-domain native pages, i.e. domain-side archives declared by a domain with shape owned by the domain plugin; group-meeting ruling, first case bb-track cognition profile user.md; legitimizes the existing tension of lark and email archive pages, not an exception hatch
- 0.6 2026-09-29: narrative reinforcement — the origin dichotomy spelled out as three page-origin layers: domain territories, native territory, derived facilities; added cross-cutting plugin positioning; sessions characterized as minutes not mirrors, the source vanishes and the page is the true body
- 0.5 2026-09-22: domain-ization — the origin dichotomy generalized to "pages each domain declares as its territory", removing the vault-specific hardcoding; territory-to-domain mapping read from path convention, declarations in each domain's manifest; first paragraph rewritten to the inner/outer narrative
- 0.4 2026-09-13: injection line gained the minimal-YAML-subset frontmatter boundary — expert review: the legal subset was undefined
- 0.3 2026-09-13: injection source moved to the manifest — removed Checks, Inject, Attachments sections, md returned to pure documentation
- 0.2 2026-09-13: purification — removed "see plugin X" back-references and nominal anchors, zones stated self-sufficiently by origin
- 0.1 2026-09-12: established — concept-declaration plugin, the origin-dichotomy invariant migrated from the original vault plugin's PLUGIN.md
