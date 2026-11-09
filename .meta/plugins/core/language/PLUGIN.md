# language: output language and writing

## Design Overview

- **Why it exists**: output-language choice and term translations were previously scattered across a one-line charter clause (AGENTS principle 7) and stray conventions in each domain — nowhere to look up across sessions, translations drifting with the session (today '检索增强生成', tomorrow '检索增强式生成'). This plugin establishes one declaration page: language and writing baselines in writing, the term table mechanically consultable, a rule to follow before the pen touches the page
- **Position in the family**: a global cross-cutting plugin, declaration-page pattern (structure precedent) — the plugin governs the mechanism, concrete norms are instance configuration landing on the page; division of labor with user-profile — the profile governs dynamic cognition of the individual user (evidence-driven, convergence-style), this page governs the instance-level constant writing regime (declarative, true for all sessions); division of labor with tag — tag governs `tags` field word forms, this page governs body prose
- **Key rulings**:
  - Absence tolerance: page or key absent = follow the session language (conversation language is the output language); a language norm is an optional enhancement, not a requirement — isomorphic with structure; proper nouns, code, paths, commands, and file names always keeping their original form is the language-neutrality discipline, invariant under configuration
  - Language neutrality (2026-10-04 batch): the framework hard-codes no specific language — output language is entirely instance data (declaration page values or session language); layered ruling: source alignment (materials are in whatever language they are in, e.g. exam language follows course materials) belongs to domain-plugin discipline, reader alignment (what language lectures and solutions use) belongs to this page's canonical keys (the teaching/annotation precedent); 'Chinese-first' demoted to a development-period instance fact (AGENTS principle 7) — when English unification finally comes, project docs change, not the architecture
  - A default baseline, not a mandate: the domain plugins' source-alignment discipline takes precedence over this page; this page never overrides in-domain self-managed language discipline
  - Emergence-based term registry: annotate the original on first occurrence, register only after recurring hits — the email source-archive emergence philosophy, preventing a page-per-term explosion
  - Two-form partitioning: the two frontmatter mappings are the mechanical zone (regenerably maintained), the body distillation section is append-only (translation rationale, usage examples, abandoned renderings)
- **Rejected alternatives**:
  - Merging into user-profile: observation-convergence and instance configuration are heterogeneous in nature, and the term table is a shared asset, not personal cognition — rejected
  - Writing into AGENTS principle 7: the charter is law, not data, and the term table keeps growing — rejected
  - A page per term (`wiki/terms/`): terms are lookup pieces, not written artifacts; a single-page mapping suffices, with an upgrade path to discuss if it overflows the window — rejected
- **Mechanism back-references**: declaration-page absence-tolerance precedent structure; emergence precedent the email source archive; block mappings draw on the wiki frontmatter minimal YAML subset; usage lands on the save command via usage_routes — the first application of the source-side routing mechanism, 2026-10-04

## Structure

- `wiki/language.md` — the writing declaration page, type: language. Frontmatter `language` block mapping = canonical key → one-sentence rule (open vocabulary, self-extended by instances); `terms` block mapping = term original → unified translation (single-line value); the body `## Distillations` section holds long notes, append-only
- Zero commands: reading is consuming (hung on save via usage_routes), writing goes through conversational editing; v0.1 sets no registration command

## Invariants

- This page is a default baseline, not a mandate: the domain plugins' source-alignment discipline takes precedence; this page never touches in-domain self-managed discipline
- Three boundary non-involvements: forms of address and personal dynamic preferences belong to user-profile, tag word forms belong to tag, in-domain term tables (the bb courseware glossary) are self-managed in-domain and never lifted up
- Canonical keys are an open vocabulary, not enumerated by the architecture (principle 3)
- Emergence-based term registration; direct human edits are legitimate, the agent never overwrites human-defined entries (objections reported)
- Page absence = a legal state (follow the session language); no error, no proxy-creation
- The framework presets no specific language: output language is entirely instance data (declaration page values or session language); Chinese is merely a development-period fact of this project

## Changelog

- 0.6 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.5 (2026-10-23): restore the register discipline in manifest usage routed to save and align the field description; generated command projections now retain it across rebuilds (issue #26).
- 0.4 (2026-10-07): register key — the `register` canonical key governs the audience reading level (program default first/second-year undergraduates, AGENTS principle 12), consumed by bb-teach (teaching) / bb-quiz (annotation) / save (PR #23, renumbered past master's 0.3 compression)
- 0.3 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.2 2026-10-04: language neutralization — the absence fallback changed from 'Chinese-first' to 'follow the session language', Chinese demoted to a development-period instance fact; layered ruling: source alignment belongs to domain plugins, reader alignment to this page's canonical keys (the teaching/annotation precedent); same batch as bb-teach/bb-quiz v0.4
- 0.1 2026-10-04: established — the writing declaration page with two-form partitioning (language/terms block mappings + distillation section), absence tolerance, default-baseline-not-mandate, emergence-based term registry; usage_routes landing on save, first application; depends wiki
