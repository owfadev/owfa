# device: device profiles

## Design Overview

- **Why it exists**: static asset facts of personal devices (computers, phones, peripherals) — serial number, purchase date, warranty end — previously had nowhere to live: retrieval relied on chat memory, warranty expiry on human memory. This plugin establishes the minimal norm: one page per device as native knowledge, fields mechanically consultable, an expiry reminder flow
- **Position in the family**: a global plugin, zero territories, zero commands, zero type value additions — devices are not a source outside wiki (no pulling, no reconciliation; human-registered native knowledge), so no domain is established; pages reuse the notes territory (type: entity as a suggested form), retrieval covered naturally; this plugin adds only two layers, 'field norm + expiry mechanism'
- **Key rulings**:
  - Reuse notes, no new territory: entity is already in the registry's default form vocabulary, the provenance definition fits (knowledge whose true copy lives in wiki); an independent territory costs one notch more in structure — rejected
  - Minimal key set + open extension: serial / purchased / warranty_until fixed as three keys (the attached audit scans only the third), remaining keys (model, vendor, etc.) free for instances — the architecture does not enumerate
  - Expiry reminders go through the delegation flow, not a bridge: the attached audit presents a list → user confirms → a todo line appended as a delegation — the todo page's existing 'append upon delegation' semantics; nothing written automatically, no todo dependency edge; the 30-day expiry window is hard-coded, refine through use
  - Asset linking across plugins establishes no dependency: invoice photos materialized in vault, linked via wikilink — the user-profile evidence-domain precedent
  - Static facts carry no TTL: the device block mapping gets no stale_after — not a pulled artifact, no expiry semantics; trust optional, human registration being itself human evidence
  - Tool-environment summary section (2026-10-04 v0.2): the body's `## Tool Environment` records presence-level info on connectors/runtimes/channels — a cross-device lookup registry (the AGENTS shell reaches only this machine; device pages cover all relevant devices, the shell pointing to the pages); presence-level granularity prevents drift (exact versions looked up live), synced when software is (un)installed; no full software inventory — 'what should be known is not stored; it is computed on demand'
- **Rejected alternatives**:
  - Establishing a domain (the domain family): devices are not an external source, no adapter, no pulling — rejected
  - An independent territory wiki/devices/: high structural cost, notes retrieval already covers it — rejected
  - A device command: registration is low-frequency (only when a new device is bought), conversational editing suffices, no command-count bloat — rejected
  - Automatic writes to todo: contrary to the 'disposal goes through confirmation' convention — rejected
- **Mechanism back-references**: notes territory rules and the append-only discipline; trust events (verified appended with each review); todo append-upon-delegation; the attached-audit contract scripts/check.py

## Structure

- `wiki/notes/` one page per device: type: entity (suggested form, open); page name free, same names disambiguated by suffix
- `device` block mapping: serial / purchased / warranty_until minimal key set, the rest open; invoice photos materialized in vault, linked via wikilink
- Zero commands: registration via conversational editing, retrieval via query, expiry via the attached audit

## Invariants

- One page per device; the notes append-only discipline applies; deletion and modification remain the human's freedom
- Nothing enumerated beyond the minimal key set — instances extend fields freely
- Expiry disposal always goes through user confirmation; the attached audit only reports, never writes; a todo line = trigger condition (expiry date) + one sentence + by/at
- Real-time status monitoring and control, and team device lending registration are not done — scope boundary; the tool environment is a semi-static summary, not real-time status, and may be recorded
- Static facts carry no stale_after; trust is optional, human registration naturally carrying human evidence

## Changelog

- 0.5 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.4 (2026-10-06) inject line: sections lost to the kernel comment-strip clip restored (quoted values are now protected), tightened for budget headroom — issue #12 post-migration nit- 0.3 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.2 2026-10-04: added the tool-environment summary section — the body's `## Tool Environment` records presence-level info on connectors/runtimes/channels, a cross-device lookup registry, the AGENTS shell pointing to the pages; presence-level granularity, (un)install syncing, no full inventory
- 0.1 2026-10-04: established — reusing the notes territory (type: entity suggested), the device block mapping minimal key set, the attached-audit expiry scan (30-day window), expiry entering todo via delegation and confirmation; zero commands; depends wiki
