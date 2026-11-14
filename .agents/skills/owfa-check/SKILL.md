---
name: owfa-check
owner: framework
description: "Audit the repository's health: hard-structure checks on the foundation and plugins + semantic checks on plugins and pages. Triggers on: check, 健康检查, 检查插件, lint."
---

# owfa-check: repository health audit

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

<!-- check-inject:end -->
