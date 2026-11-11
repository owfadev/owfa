# calendar: time territory

## Design Overview

- **Why it exists**: the wiki's time dimension — what happens when. The source model is open: manual notes plus each adapter's projections converge on the same page, lark-calendar being the first adapter. Time is a single cross-tenant dimension; multi-source convergence is precisely this territory's reason for being
- **Key rulings**:
  - Events are lines, not pages: the calendar registers only the timeline; weighty events are distilled via save into a note or session, then wikilinked from the calendar line — consistent with 'the wiki receives distillates'
  - Boundary with todo: the calendar stores 'what happens when', todo stores 'what is pending'; events may derive todo entries, never merged the other way
  - Month pages two-section scheme: `## Schedule` is the source projection, refreshed wholesale by section; `## Manual Notes` is append-only — the mechanical-zone/distillation-zone boundary sits at section level
  - Future rolling, past frozen: a month may not be rewritten once over; rewrite traces = error, git audit; missed changes are recorded in the new month's page — history stays truthful
  - The month page is the only mixed-provenance page in the whole library: territory ownership and section-content provenance are separated. Named, not mechanized; a single instance raises no architectural concept

## Structure

- `wiki/calendar.md` — declaration page, type: calendar. Frontmatter `calendar` block mapping = source key to source declaration; value syntax belongs to the adapter, e.g. `lark/<profile> <calendar_id>`. The body holds usage notes; may be absent when manual-only
- `wiki/calendar/<YYYY-MM>.md` — month page, one page per month, ASCII file name. **Two-section scheme**: `## Schedule` is the source-projection zone, regenerable and refreshed wholesale by section; `## Manual Notes` is for human and agent writing, append-only
- Event line: `- MM-DD HH:MM~HH:MM Title (source key)`, may carry a wikilink — people, group archives, notes; all-day events written `MM-DD all-day`

## Invariants

- Future rolling, past frozen: a month freezes once over, its page never rewritten; rewrite traces → error, git audit; missed changes are recorded in the new month's page, history staying truthful
- A refresh only wholesale-replaces the `## Schedule` section; the manual-notes section is never touched by source sync
- Month pages carry trust: stale_after short TTL, default 2 days, leaving headroom for the daily-refresh cadence
- Events get no pages; meeting conclusions go to group-archive topic records or notes, the calendar line keeping only the link
- The declaration page's source list is instance configuration; no declaration page = manual-only, a legal norm
- The month page is the only mixed-provenance page in the whole library: the `## Schedule` section is a true projection, reconcilable with an external source, lodging in a native territory — territory ownership and section-content provenance separated; named, not mechanized; a single instance raises no architectural concept

## Bridge: on-demand

A derivation-destination bridge governing schedules: domain plugins one-way derive source-keyed schedule lines into the current month's `## Schedule`, out-only; never touching manual notes, never touching frozen month pages. Constitutional principle 11. Attachment cardinality **on-demand**. Format authority is in this plugin's usage, projected to the point of consumption — division-of-labor ruling. This section elaborates: event lines carry the source key; the source key is defined by the deriving domain itself and registered on the declaration page.

## Changelog

- 0.5 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.4 (2026-10-06) inject line: sections lost to the kernel comment-strip clip restored (quoted values are now protected), tightened for budget headroom — issue #12 post-migration nit- 0.3 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.2 2026-10-02: global-domain batch two — established the on-demand bridge as the derivation destination; domain-plugin self-descriptions retained with a pointer
- 0.1 2026-09-19: established — month-page two-section scheme, the open source model, the freezing regime; lark-calendar as the first source adapter
