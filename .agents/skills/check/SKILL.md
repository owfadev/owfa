---
name: check
owner: framework
description: "Audit the repository's health: hard-structure checks on the foundation and plugins + semantic checks on plugins and pages. Triggers on: check, 健康检查, 检查插件, lint."
---

# check: repository health audit

This is an audit, not a guardrail. It outputs a graded report: error = structural breakage requiring action; warning = a suggested to-do. Check rules come from two places: the foundation part of this file (protocol level) + the injection region below (a mechanical projection by owfa-kernel from each plugin manifest's checks list; presence means registration).

## Purpose

Run one health audit over the entire instance (foundation + plugins + wiki pages).

## Scope

Read: everything (.owfa/, the AGENTS.md injection region, .agents/skills/, the wiki/, vault/ directory trees)
Write: one line in wiki/log.md (type "check"); regenerable zones are rebuilt directly per the action discipline (scripts: injection region / registry / command copies; semantics: index / tags / hot eviction / log archiving / hash recomputation)

## Steps

1. **Foundation hard checks** (protocol level):
   - **Static self-check script**: `python .owfa/scripts/owfa_kernel.py validate` (directory completeness, manifest seven fields + optional commands, id consistency, dependency existence, acyclicity, command binding owner×commands bidirectional consistency) — any error means FAIL
   - **Idempotent rebuild**: `python .owfa/scripts/owfa_kernel.py all` (injection region / registry plugin section / command copies — mechanical and automatic; drift is fixed here, the script source is the rule list)
   - `.owfa/protocol/registry.yaml` is in place with the protocol / reserved sections intact (the script never touches these two sections; a missing section is an error)
   - **Value-set violation**: scan the frontmatter of all wiki/ pages; a type / status value outside the registry value set → error
   - Every `.owfa/command/` SKILL.md has frontmatter (name / description / owner; optional consumes — an ordered list of plugins whose write-side contracts are consumed; referenced plugins must be present with a usage list; mandatory for owner-driven commands)
2. **Plugin checks**: first run the attached audit `python .owfa/scripts/owfa_kernel.py audit` (mechanical items: each plugin's scripts/check.py executed on audit discovery, read-only reporting; errors count toward FAIL); then execute the items marked "semantic" in the injection-region blocks below
3. **Semantic checks**: read plugin and command files, looking for dangling references (a command referring to nonexistent structure), ghost fields (page fields with no owning plugin and not registry-reserved), and injection-region blocks inconsistent with the PLUGIN.md Checks section
4. Summary output: PASS / WARN / FAIL counts + graded details + vault backlog count (informational)
5. **Fixes are executed by grade per the action discipline** (`.owfa/protocol/actions.md`): mechanical-automatic items are done directly — `pipeline.py index` / `tags` (index rebuild), `owfa_kernel.py all` (registry / injection region / copies), hash recomputation (raw_sha256 of changed frontmatter); hot / log overflows are converged by their own write-pipeline commands; mechanical-confirmation items present a list and ask once; semantic items are reported only; historical entries are never automatically changed
6. Prepend one line to wiki/log.md (type "check", via `pipeline.py log check "<one line>"`); if anything changed (fixes / a log line), commit per the commit discipline (`检查: <conclusion>`, see `.owfa/protocol/actions.md`)

## Tools

grep / file reading suffice; no second scan when one read is enough (call frugality).

## Parameters

- None: full-repository audit
- Plugin id: check that plugin only

## Injected Section (plugin check blocks)

> This region is a owfa-kernel projection from each plugin manifest's checks list (rebuilt by `inject` / `all`; presence means registration); handwritten content does not belong here — to change check rules, edit PLUGIN.yaml.

<!-- check-inject:start -->
<!-- check:device -->
- Mechanical (attached-audit script `scripts/check.py`, executed discovery-style by audit): device block mapping's warranty_until within ≤30 days of today → warning nearing expiry; already expired → warning expired; invalid date → warning
<!-- /check:device -->

<!-- check:hot -->
- Window out of bounds (>25 entries / >5 days / >200 chars per entry) → run `pipeline.py hot <type> "<backfill>"` once, or wait for the next write to converge naturally then re-check
- Contradiction with log (log has records while hot shows no trace) → warning
<!-- /check:hot -->

<!-- check:language -->
- Mechanical (attached-audit script `scripts/check.py`, executed discovery-style by audit): type: language landing outside `wiki/language.md` → error; terms empty values → warning; declaration page absent → info (session-language fallback tolerated)
<!-- /check:language -->

<!-- check:link -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): broken link (target is neither a page full name nor any page's aliases) → warning; hand-written broken link in hot → warning (not counted as an inbound-link source); garbled link (target contains the U+FFFD replacement character, including related items) → error; alias ambiguity (two pages declaring the same aliases, resolution indeterminate) → error; orphan page (no inbound links and no related references, inbound sources counting concept pages only) → warning for notes knowledge pages, info for territory-value registration pages (registry territory values except session, having no inbound links yet being the registration norm); one-way related (A lists B while B does not list back) → info
- Semantic items (check command): inbound-link density top list → info item (evidence for hub emergence, no alert)
<!-- /check:link -->

<!-- check:log -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): undated entries (starting with `- ` yet not matching the date format, main file and archive checked alike) → error
- Semantic items (check command): historical entries modified (verifiable via git) → error; capacity over the limit → re-check after mechanical archiving
<!-- /check:log -->

<!-- check:notes -->
- Traces of a note overwritten by a command → error
- Near-duplicate notes (Jaccard > 0.7) → warning
<!-- /check:notes -->

<!-- check:sessions -->
- Mechanical (covered by audit): session-type pages outside `wiki/sessions/` (or the reverse) → warning; participants missing or entries violating the actor convention → warning
- Semantic: backbone page bloated past due promotion (should have been promoted but was not) → warning
<!-- /check:sessions -->

<!-- check:tag -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): >5 tags on one page → warning; tags restating type → warning; hierarchy over the limit (parent/child ≤2) or empty segment → warning
- Semantic items (check command): near-duplicate tags → warning suggesting a merge; merging is a mechanically-confirmed item (list presented, executed after user confirmation)
<!-- /check:tag -->

<!-- check:tmp -->
- Semantic (v0.1 manual, attached audit deferred): type: tmp landing outside wiki/tmp/ → error; stale_after already past → warning (cleanup prompt); tmp page count > 20 → info (backlog triage)
<!-- /check:tmp -->

<!-- check:trust -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): generated missing by/at or wrong actor format, verified event missing by/at or wrong format, stale_after not YYYY-MM-DD, sources not a list → warning
- Mechanical items (info level): stale page list (past stale_after); trust-level counts (human-reviewed / machine-confirmed counts)
- Semantic (check command): stale-page disposition triage (refresh the moment / re-verify / deprecate) — human decides
<!-- /check:trust -->

<!-- check:calendar -->
- Semantic (v0.1 manual, attached audit deferred): month page file name not YYYY-MM or landing outside wiki/calendar/ → error; traces of rewriting a past month's page → error (git audit); declaration page missing the `calendar` block → info (the manual-only norm)
<!-- /check:calendar -->

<!-- check:cron -->
- Mechanical: a type: cron page landing outside wiki/cron/ → error; task page missing the cron block or the minimal key set (trigger/action/form/status) → warning; malformed condition trigger (kind outside the open vocabulary or missing target) → warning; time form: last_run beyond the schedule period with active → warning (projection-lost signal)
- Semantic (attached audit deferred): per-form drift between readable execution-side lists (scheduler / system tasks / conditional-executor watches, best-effort) and the declaration page set → warning; unreadable executor → info
<!-- /check:cron -->

<!-- check:index -->
- Deviation between indexes and the actual page set (including merged-back indexes pending deletion) → fixed by running `pipeline.py index` to rebuild (idempotent; no diff means consistent); same for tags (`pipeline.py tags`)
- Traces of hand editing → warning
<!-- /check:index -->

<!-- check:todo -->
- Mechanical (info-level): the list of date-triggered, overdue and unsettled entries (the mechanical basis for new-session reminders); page absent (the no-delegation norm)
- Mechanical: entry missing trigger condition or by/at → warning; type: todo landing outside `wiki/todo.md` → error
- Semantic (check command): open entries > 50 → warning (bloat triage: do what should be done, distill what should be distilled via save, confirm with the user what should be dropped)
<!-- /check:todo -->

<!-- check:user-profile -->
- Semantic (check command): profile assertion missing an evidence wikilink → warning
- Mechanical: a type: profile page landing in `wiki/notes/` or `wiki/vault/` (wrong territory) → error
- Mechanical (info-level): profile page absent (the untriggered norm; profile self-creates on first trigger)
<!-- /check:user-profile -->

<!-- check:mapping -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): mirror diff (file in vault without proxy → info backlog; proxy without counterpart → error, message carries the reference count — see the impact surface before deleting); missing registration fields (raw_file / raw_sha256) → error; dangling raw_file → error; raw_sha256 mismatch → warning; suspected full-text duplication (md asset body ≥80% of the original) → warning; description-less stub with updated older than 90 days → warning
- Semantic items (check command): mismatch-disposition triage (description still applies → mechanical recalculation auto-repairs, writing a log line on completion (type map, one sentence with the asset name and 'original changed, description still applies'); suspected invalid → human decides remap or delete); diary-type full-text duplication exemption judgment; before disposing an orphan proxy, handle its references first (update references in sync or leave aliases to redirect)
<!-- /check:mapping -->

<!-- check:structure -->
- Mechanical items (attached-audit script `scripts/check.py`, executed on audit discovery): declaration diff — vault top-level directory undeclared → warning, declaration key pointing to a nonexistent directory → warning; type: structure landing outside `wiki/structure.md` → error; declaration page absent → info (flat tolerance)
<!-- /check:structure -->
<!-- check-inject:end -->
