---
name: owfa-check
owner: framework
description: "Audit workspace health, protocol-neutral: the kernel's mechanical checks + the installed protocol's attached audits and injected check blocks — no protocol is presupposed. Triggers on: check, 健康检查, 检查插件, lint."
---

# owfa-check: workspace health audit

This is an audit, not a guardrail. It outputs a graded report: error = structural breakage
requiring action; warning = a suggested to-do. **Protocol-neutral by ruling (2026-11-16)**:
this command presupposes no content protocol — every concrete notion (what a "page" is,
which territories exist, what the log looks like) arrives from the installed protocol
through the kernel's attached-audit discovery and the injection regions below. Where the
installed protocol provides no check face, only the framework's mechanical layer runs.

## Purpose

Run one health audit over the workspace (framework machinery + installed packages).

## Scope

Read: framework machinery (.owfa/ — scripts, registry, command masters; the AGENTS.md
injection region; .agents/skills/); whatever the installed protocol's attached audits
and injected usage blocks declare
Write: none hardcoded — reporting is this command's job; any write (log lines, page
repairs, rebuilds) follows the installed protocol's injected usage, never a preset path

## Steps

1. **Framework hard checks** (protocol-independent):
   - **Static self-check**: `python .owfa/scripts/owfa_kernel.py validate` (directory
     completeness, manifest fields, id consistency, dependency existence + acyclicity,
     command binding owner×commands bidirectional consistency, capability needs) — any
     error means FAIL
   - **Idempotent rebuild**: `python .owfa/scripts/owfa_kernel.py all` (injection
     regions / registry plugin section / command copies — mechanical and automatic;
     drift is fixed here, the script source is the rule list)
   - `.owfa/protocol/registry.yaml` in place with the protocol / reserved sections
     intact (the script never touches these two sections; a missing section is an error)
   - Every `.owfa/command/` SKILL.md has frontmatter (name / description / owner;
     optional consumes — referenced plugins must be present with a usage list)
2. **Installed-protocol checks**: `python .owfa/scripts/owfa_kernel.py audit` — each
   installed package's attached `scripts/check.py` (read-only, graded reporting) plus the
   protocol ABI smoke; errors count toward FAIL. This is where protocol-specific health
   arrives: the audit walks whatever territory the installed protocol owns
3. **Injected check blocks**: execute the semantic items registered in the
   `check-inject` region below (presence means registration — the rules themselves come
   from the installed packages' manifests)
4. Summary output: PASS / WARN / FAIL counts + graded details
5. **Fixes follow the installed protocol's own commands** (surfaced in the usage blocks
   the kernel injects here): mechanical-automatic repairs run through the protocol's
   declared tools; semantic findings are reported only; historical entries are never
   automatically changed
6. Close-out (logging, commits) follows the installed protocol's injected usage — this
   command hardcodes none

## Tools

grep / file reading suffice; no second scan when one read is enough (call frugality).

## Parameters

- None: full-workspace audit
- Plugin id: check that plugin only

## Injected Section (plugin check blocks)

> This region is a owfa-kernel projection from each plugin manifest's checks list (rebuilt by `inject` / `all`; presence means registration); handwritten content does not belong here — to change check rules, edit PLUGIN.yaml.

<!-- check-inject:start -->

<!-- check-inject:end -->

## Injected Section (plugin usage blocks)

> This region is a owfa-kernel projection: consumes pulls merged with usage_routes source-side routing; disclosure order = owner first, routed blocks in the middle, pulled blocks last (rebuilt by inject / all); handwritten content does not belong here — to change the write-side contract, edit PLUGIN.yaml.

<!-- cmd-inject:start -->
<!-- cmd-inject:end -->
