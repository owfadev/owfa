# todo: temporary memory

## Design Overview

- **Why it exists**: the cross-session delegation queue — a new session cannot reach past conversations under SASU-L; system prompt, AGENTS, skills, and the user's own words carry none of it; this page plus the AGENTS injection-line pointer is a mount point on the L layer. In essence a **collection of pointers to future moments**, an explicit instance of time-dimensional pointers: upon delegation one writes down 'act when this line is read at such a time' — the agent is a pointer executor
- **Key rulings**:
  - The first settleable page in the whole library: delegated, reminded on trigger, settled — `[x]` plus a log line — cleanup being silent deletion of settled entries beyond a cap of 20. log is append-only, notes append-only, profile converges with traces; only todo has settlement semantics. History goes to log; this page keeps only the live working set
  - Read-priority order: a new session reads this page first, before hot — there may be due delegations requiring proactive action; hot is merely context warm-up
  - No attached command — a pattern exception, by design ruling: entry format minimal, no pipeline linkage; the read/write contract travels with the injection line
  - Two trigger kinds: date — YYYY-MM-DD, mechanically scannable; and context, semantically activated

## Structure

- `wiki/todo.md` single page, type: todo; self-created on first delegation. An entry = a list item `- [ ] trigger: content (by, at)`; triggers come in two kinds, date and context
- Zero page fields: entry-level by and at use the global actor convention, see the registry header; settlement history is written to `wiki/log.md` — crossing into the log plugin's territory, the reason for depends log

## Invariants

- Full entry lifecycle: delegated; reminded on trigger; settled — `[x]` plus a log line; cleaned up — settled capped at 20, silently deleted, log already holding the record. The first settleable page in the whole library: log append-only, notes append-only, profile converging with traces; only todo has settlement semantics
- This page keeps only the live working set; history goes to log: settlement events recorded as they happen, type todo; cleanup is not an event and is not recorded
- Valuable delegations are distilled into knowledge via save upon completion; this page keeps no history
- Read-priority order: a new session reads this page first, before hot — there may be due delegations requiring proactive action; hot is merely context warm-up
- No attached command — a pattern exception, by design ruling: entry format minimal, no pipeline linkage; the read/write contract travels with the injection line

## Bridge: on-demand

A derivation-destination bridge governing action items: domain plugins one-way derive action items into this page, out-only. Constitutional principle 11. Attachment cardinality **on-demand** — domain plugins with such derivations declare it themselves or inherit it via a base, absence tolerated. Format authority is in this plugin's usage, projected to the point of consumption — division-of-labor ruling. This section elaborates: the deriving side creates no pages and invents no formats; an entry takes exactly this page's entry form; the domain plugin keeps a one-sentence self-description disclosure, SASU-L.

## Changelog

- 0.6 2026-11-12: contract-had-no-enforcement fix — mechanical checks (territory placement / entry trigger + by/at contract / overdue info list) landed as the attached-audit script scripts/check.py, closing the gap between the declared checks and execution
- 0.5 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.4 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.3 2026-10-02: global-domain batch two — established the on-demand bridge as the derivation destination; domain-plugin self-descriptions retained with a pointer
- 0.2 2026-10-02: added 'create on absence' — when a new session's first read finds todo.md absent, it creates an empty page, so the entry discipline never falls through; guideline registration entry revised, empirically verified
- 0.1 2026-09-14: established — the `wiki/todo.md` delegation queue, type: todo entered the registry territory values; settlement history goes to log, the log type value set extended with todo; no attached command — the write contract travels with the injection line
