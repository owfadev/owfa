---
name: plugin
owner: framework
description: "Package & plugin lifecycle management: plan (disclosure wizard), install (three channels + --without subsets), uninstall, list-remote, upgrade, pkg, residual. Mechanical steps all go through .owfa/scripts/owfa_kernel.py; the agent runs the consent conversation and the one-shot commands. Triggers on: plugin, 插件, 装插件, 卸插件, 装包, install package, uninstall package."
---

# plugin: package lifecycle

The framework's self-management command, package era (issue #20). Every mechanical step goes through the kernel script; the agent's job is **consent and choice** — never writing `.owfa/` by hand.

## Scope

Write: only via the kernel script (package masters in/out, connectors/, command masters, injection region, registry, skill copies — six sites)
Read: INDEX via the kernel, PKG.yaml, manifests

## Discovery → download: the consent wizard (human path)

When a user asks to install a package and has NOT already specified what to include:

1. `python .owfa/scripts/owfa_kernel.py plan <pkg>` — one-shot disclosure plan: trust line, package disclosure (network/privacy/credentials, package-authored), baseline (the family root, always installed), optional members with one-line summaries and what each selection pulls in, connectors
2. Relay the plan **in the user's language** (render at the agent layer per wiki/language.md — canonical texts are English; the agent translates when relaying, never edits the source)
3. Walk the steps: trust + disclosure → user acknowledges; optional members → user picks (each pick auto-pulls its dependency closure — show the resolved final set, users cannot compose an illegal subset); connectors → confirm (they ride the package)
4. Execute: `python .owfa/scripts/owfa_kernel.py install <pkg> --without <unwanted> [--yes]`
5. Report the convergence output (validate/inject/registry/deploy) in one breath

## One-shot path (agent / pre-authorized)

If consent already exists (user named exactly what they want, or pre-authorized), skip the conversation:

```
python .owfa/scripts/owfa_kernel.py plan <pkg> --json        # machine-readable plan (optional)
python .owfa/scripts/owfa_kernel.py install <pkg> [--without a,b] [--yes]
```

Kernel commands never prompt — every invocation completes in one shot.

## Transaction close: git snapshot

Every package transaction (install / uninstall / upgrade apply / migrate clear) ends with **one git commit at close** — after validate goes green, mechanical + semantic changes in the same snapshot. The kernel itself never touches git (the journal is its ledger); committing is the agent's closing move. Message format `plugin: <verb> <pkg> [v<version>]` per the [instance-git plugin](../../plugins/core/instance-git/PLUGIN.md). Not a git repo? Skip silently.

## Command surface

| Command | What it does |
|---|---|
| `plan <pkg> [--json] [--without a,b]` | disclosure plan (+ subset preview); clone discarded, nothing installed |
| `install <pkg>[@tag]` | registry path: trust gate → clone → verify (id/compat/members ↔ index) → place masters/connectors/commands → converge |
| `install <owner/repo> --yes` | unindexed direct install (trust: unknown — the registry PR is how a package earns reviewed trust) |
| `install <pkg> --path <dir>` | local package (developer loop, channel C) |
| `install ... --without a,b` | D5 subset: named leaves + their dependents pruned; root never prunable; result is dependency-closed by construction |
| `uninstall <pkg> --yes` | D6 four-clear + convergence + residual scan + retains/credentials reminders; data zones and credentials never touched |
| `list-remote` | registry index with members and trust marks |
| `upgrade` | reconciliation report; upgrades run uninstall+install per package, never cascaded |
| `upgrade <pkg> --yes` | mechanical reinstall + update report (member deltas + changelog excerpts) + migration chain staging |
| `migrate <pkg>` / `--clear` | pending status + declaration printing / verify-gated clear (deletes staged files, unblesses validate) |
| `pkg` / `ls` / `residual <pkg>` | local inventory / plugin list / anchor-surface reference scan |

## Semantic migrations (update path)

Mechanical sync is only half an update. When a new version carries `migrations/`:

1. The kernel stages declarations into `.owfa/migrations/<pkg>/` (kernel zone — never inside the package dir), registers the warning ledger, and raises the **tri-face warning**: every kernel invocation prints the pending banner · `validate` stays red (mechanical blessing withheld) · a kernel-managed block lands in the AGENTS injection region so every session sees it
2. `kernel migrate <pkg>` prints the staged declarations (init or version-chain) — relay them in the user's language
3. Perform the semantic transformation via the normal command surfaces (confirmation gates as always); **judgment split rule**: assertions that hold only during the transition belong in the author's verify script (dies with the migration); assertions that hold forever belong in `scripts/check.py` (same release)
4. **Subset matching**: declarations and verifies address the **installed subset**, never the full roster — steps marked `(member: X)` run only when X is installed; verify scripts guard member-specific assertions with `ctx.installed` (the kernel passes it); the ledger records the staging-time subset
5. `kernel migrate <pkg> --clear` runs the author verify (AST-gated: read-only, stdlib-adjacent, must define verify(ctx)) — clean clears the warning and **deletes the staged files (use-and-delete: they are useful precisely once; keeping them would blur into check's role)**
6. The kernel journal (`.owfa/kernel-journal.log`) records install/uninstall/upgrade/warn/clear with a rolling cap of 500 lines (oldest trimmed); it is git-tracked — mechanical facts only; semantic narrative stays in wiki/log

## Boundaries

- **Consent is the agent's duty**: no install without user acknowledgment of the disclosure (unless pre-authorized); `--yes` gates exist precisely so consent is explicit
- **Trust is earned in the registry**: unindexed = installable but flagged unknown; the one-line registry PR is the review gate (inject text and connectors are the security faces)
- The script touches only its six mechanical sites; data zones (`wiki/`, `vault/`, `cuhksz/`, `projects/`), credentials (`~/*-cli`), and the AGENTS.md handwritten region are never touched
- Errors from the script always block; warnings are reported only
- Uninstall leaves data in place (deprecated posture); physical deletion belongs to the human
