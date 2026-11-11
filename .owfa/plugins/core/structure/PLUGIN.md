# structure: vault Layout

## Design Summary

- **Why it exists**: vault presets no structure, but a total absence of structure means fast-growing entropy — user-write manuscript 2026-09-07. This plugin sets the layout rules: structure is declared by the instance, the framework provides a preset menu, placement rules, and drift detection. Another instance of skeleton/instance separation; the vault side is henceforth symmetric with the wiki side: the concept plugin governs "what it is", the structure plugin governs "how it is organized"
- **Key rulings**:
  - Declaration page machine-readable plus a human-readable body: the frontmatter `structure` block mapping holds the declaration proper, the body holds preset notes; page absent = flat tolerance, a legal state — structure is an optional enhancement, not a requirement
  - vault belongs to the human: structural adjustment is free; the agent only places and reminds, never coerces. The declaration is intent, the diff is a drift reminder, disposition always belongs to the human
  - The two-way diff is mechanically decidable, done by the attached audit: constraining only top-level directories; loose top-level files are the flat slot
  - Governance pages inside wiki, governance targets outside in vault — the same-shaped general rule of the domain contract

## Structure

- `wiki/structure.md` — the structure declaration page, type: structure. The frontmatter `structure` block mapping holds the declaration proper — top-level directory to one-line semantics, machine-readable; the body holds preset choices and notes, for humans; page absent = flat tolerance, a legal state
- Preset menu: date — `xxxx-xx-xx` daily folders; format — `pdf/`, `md/`; type — semantic categories such as diary, clippings; mixed — nesting without mutual exclusion
- The shell's natural-language declaration retired: inside wiki is the only retrieval-reachable zone for agents; the shell keeps a pointer to the declaration page

## Invariants

- Structural choice is instance configuration, not architecture. Touchstone: a concrete directory layout cannot be carried into a new instance
- vault belongs to the human: structural adjustment is free; the agent only places and reminds, never coerces
- The two-way diff between declaration and reality is mechanically decidable, via the attached-audit script; the declaration is intent, the diff is a drift reminder, disposition always belongs to the human
- The diff constrains only top-level directories; loose top-level files are the flat slot, unconstrained by the declaration

## Changelog

- 0.4 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.3 2026-09-22: domain-ization — the first paragraph gained in-domain governance positioning, transitively belonging to the vault domain, governance page inside and target outside; depends unchanged, transitivity means membership
- 0.2 2026-09-14: territory moved into wiki — declaration page `wiki/structure.md`, frontmatter structure block mapping machine-readable; drift detection upgraded from a semantic item to the attached-audit script, i.e. the declaration diff; depends gained wiki; the shell's natural-language declaration retired
- 0.1 2026-09-14: established — from the user-write manuscript, i.e. the four presets plus the AGENTS declaration, distilled with the vault governance discussion; the layout responsibility separated from the vault concept plugin, symmetric to the wiki side's concept-and-structure layering
