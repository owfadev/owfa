# user-profile: user profile

## Design Overview

- **Why it exists**: a continuing cognition profile of the user — turning 'who the user is and what they prefer' from conversational memory into a checkable page: assertions carry evidence, preferences expire, updates leave traces. Positioned as the user profile of the agent memory line, facing the real user; not the fictional persona of the product-design line. The dimension framework borrows from the former's research, the update mechanism from the latter; selection rationale in `research-user-profile.md`
- **Key rulings**:
  - Convergence-style updates: new values replace old ones, trace left in the body — distinct from notes' append-only; the profile page is the first semantically updatable page in the whole library
  - Zero own fields: traces and trust fully reuse trust; dimensions not enumerated, the architecture presets no field list
  - Assertion evidence = inline wikilinks in the body, pointing to any page inside wiki — a citation is a link, no cross-domain mechanism dependencies
  - Updates uniformly go through the profile command, shedding the map/save parasitism on 2026-09-29; dual-track triggering: explicit user request, or the agent recognizing significant signals
  - The mapping edge was removed 2026-10-02: under the bridge law it reached domain via the vault chain, causing a global plugin to be misjudged — caught by an actual kernel test; the 'hanging edges are harmless' premise failed
  - Privacy double safeguard: diary-type assets record only meta-signals, content never entering the profile; profile content is instance data, never entering the repo

## Structure

- `wiki/profile.md` — a single-page profile, type: profile. Static identity layer — form of address, language, background — and dynamic preference layer — subjects, style, habits — in open sections; dimensions not enumerated
- Zero own fields: traces and trust fully reuse trust, namely generated, verified, stale_after, sources
- Assertion evidence = inline wikilinks in the body, pointing to any page inside wiki — session pages, vault proxy pages, lark archive pages, notes. A citation is a link, no cross-domain mechanism dependencies; three depends edges: wiki, trust, sessions. The mapping edge was removed 2026-10-02 — under the bridge law it reached domain via the vault chain, causing a global plugin to be misjudged; the 2026-09-29 'hanging edges are harmless' premise failed

## Invariants

- Convergence-style updates: new values replace old ones, trace left in the body, a single line recording who changed what and when — distinct from notes' append-only; the profile page is the first semantically updatable page in the whole library
- Updates uniformly go through the profile command, dual-track triggering — explicit user request, or the agent's spontaneous call upon recognizing significant signals; since 2026-09-29 free of the map/save parasitism, profile evidence naturally cross-domain
- Assertions must carry evidence wikilinks; a single incremental assertion is not itself a preference — preferences are patterns aggregated within the page
- Diary-type assets record only meta-signals — presence, cadence; content never enters the profile. The exemption followed mapping; a second privacy red-line safeguard
- Privacy red line: profile content is instance data, never entering the framework repo or test-repo
- The profile page carries no tags: a single-page territory, read directly, not in vocabulary retrieval — an explicit decision, not an omission
- Profile page absence is not an error: untriggered is the norm; profile self-creates on first trigger, independent of any initialization mechanism

## Bridge: on-demand

The cognition bridge: the global profile's extension point toward domain-level cognition pages, constitutional principle 11. The profile body carries a `## Domain Cognition` section; a line = domain name plus a path-form wikilink to the cognition page, bb-track user.md the first case, the path form wildcarding multiple courses and archives. Attachment cardinality **on-demand**: domain plugins with cognition profiles register, and registration is maintained by the domain plugin's archive-creation action; if the profile is absent the domain plugin works as usual — on-demand bridge absence tolerance; even with the profile present it only aggregates pointers, never copying domain state. Consumption discipline: before personalized output, read the profile **and its registered cognition pages** — the bridge holds only 'who is present, where to read'; cognition-page shape knowledge belongs to the domain plugins, each disclosing its own, SASU-L. The zero-own-fields ruling stands unbroken: registration goes through a body section, never touching frontmatter. Line-format authority lives in the registering-side domain plugin's usage, the bb-track precedent; this section is the elaboration — division-of-labor ruling.

## Changelog

- 0.7 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.6 (2026-10-06) inject line: sections lost to the kernel comment-strip clip restored (quoted values are now protected), tightened for budget headroom — issue #12 post-migration nit- 0.5 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.4 2026-10-02: global-domain batch three — established the cognition bridge, on-demand: the profile body `## Domain Cognition` registration section, aggregate-don't-copy, read-first discipline; bb-track user.md the first registration; the mapping edge removed — under the bridge law it reached domain via the vault chain, causing a global plugin to be misjudged, caught by an actual kernel test; the 'hanging edges are harmless' premise failed
- 0.3 2026-09-29: profile command established — the write side shed its parasitism on the map and save dual entry points, both commands' consumes entries removed; the evidence domain opened to any page inside wiki, dissolving the cross-domain ownership suspension; first creation self-builds on trigger, absorbing the profile part of the pending initialization items; tags explicitly not applied; depends kept, ruling: reference-level edges retained, not cut
- 0.2 2026-09-14: usage added the profile distillation methodology — signal criteria, layered placement, assertions concrete and verifiable; the executable part of the distillation entered the write-side contract, closing the SASU-L disclosure loop: an agent running map or save knows how to distill, without relying on model priors; the full text remains in `docs/research-user-profile.md`
- 0.1 2026-09-13: established — `wiki/profile.md` convergence-style cognition profile, type: profile entered the registry value set; depends were wiki, trust, mapping, sessions; dual signal channels hung on save and map, consumes inserted after trust and before derivation; three checks — the assertion evidence gate as warning, wrong territory as error, page absence as info-level
