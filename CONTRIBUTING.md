# Contributing

Dev rules of the owfa framework. The framework repo is a library: no instance data, no run log — the change trail is git history + PRs + issues.

## Roles

- **Three members, all with write access** — develop and experiment
- **Owner holds final say** — repo settings, member permissions and protection rules are owner-only; charter and kernel changes (`.owfa/`, `AGENTS`-level contracts) are owner-reviewed
- Everything moves through PRs: **any PR needs 1 approving review to merge** (`enforce_admins` is on — the owner pushes through PRs too; the protection switch itself is the owner's escape hatch for emergency fixes)
- **PR aging policy (2026-10-27, owner ruling)**: a PR left unreviewed for more than 1 day will be force-processed by the administrator — reviewed-and-merged, rebased-and-merged, or closed with reasons on the record. Reviews are a courtesy deadline, not a parking lot; if you need more time, say so on the PR

## Commit flow

1. Branch off latest master, name it `module/topic` (e.g. `feature/bb-notes`, `kernel/pkg-reconcile`)
2. Small commits, one thing each, message format `模块: 概述`
3. Before opening the PR, self-check: at the framework root `python .owfa/scripts/owfa_kernel.py validate` (plus `pkg` when package manifests changed) must pass; a full mechanical run needs an AGENTS.md context — use a local sandbox (see [`.owfa/docs/sandbox.md`](.owfa/docs/sandbox.md)) or a real instance, and `kernel all` must be green. Touching the npm channel (`bin/`, `package.json`, `templates/`, `scripts/verify-release.js`) also runs `node scripts/verify-release.js && node test/smoke.js`. The diff contains development artifacts only
4. Push the branch, open a PR against master — the standard review channel
5. Kernel/charter PRs: owner reviews. Content/domain PRs: peer review among members
6. After merge the head branch is deleted automatically; every merge is recorded (PR + commit trail)

## Template + instance workflow

Development happens in the **template** (this repository); real use happens in an **instance** — a separately deployed vault whose `.owfa/` and `.agents/skills/` derive from the template. Two repos, two rule sets:

- The template stays a library: no instance data, no AGENTS.md, no run log (the opening rule). Mechanical verification that needs an AGENTS.md context runs in a **local sandbox** — a scratch deployment of the template (see [`.owfa/docs/sandbox.md`](.owfa/docs/sandbox.md)); the in-repo `test-repo/` sandbox is local-only and untracked since 2026-10-13
- Instance-side upstream updates: fetch/pull the template → diff `.owfa/` and `.agents/` → sync selectively (an instance may carry packages and local state the template does not know) — the diff must always include `.owfa/docs/` (agent-facing docs are instance runtime dependencies, not optional reading) → at the instance root `kernel all` → `validate` green. Never blind-copy over an instance that has pending migrations
- Instances do not author framework code (`.owfa/`, `.agents/skills/`) — development happens here and in the `owfa-*` package repos; instances pull and sync. Exactly two instance-side touches are legitimate:
  - **Verification** — a defect that only manifests in an instance environment (its sandbox, its data shape, its connectors' live auth) is reproduced and its fix verified there: the instance is the test bench, never the author
  - **Reconciled hotfix** — when merge latency blocks real use: minimal patch, byte-identical with the upstream proposal where possible, an upstream PR/issue opened in the same transaction; after merge the upstream final version wins, so a byte-identical hotfix converges to a no-op diff at the next sync
- Development keeps the dev docs exposed: whoever touches framework code — even instance-side, even a hotfix — reads this document first; the [docs map](.owfa/docs/map.md) routes here, instance sync diffs always carry `.owfa/docs/`, and package-repo PRs self-check against this file
- Instances report framework bugs back as template issues — an instance's own wiki never becomes the framework's change trail

## Data red lines — never in git

Real course files; grades and submission records; personal privacy; account credentials and sessions; sandbox experiment output. Scan your diff before pushing — if any of the above slipped in, pull it back. Granting an exception for ignored data requires the owner's explicit say-so; nobody edits `.gitignore` to let data through on their own.

`test-repo/` is the in-repo sandbox path — untracked and local-only since 2026-10-13: nothing inside it can enter history, mirrors included.

## Version discipline

Read the current state before changing a plugin or connector: versions advance along the changelog — no pre-reserving numbers, no gaps. Conflicts with existing plans get aligned in the group first. Framework-level version is the `.owfa/VERSION` anchor + git tag (see [`.owfa/docs/packages.md`](.owfa/docs/packages.md)); package versions ride their own tags and never lockstep with member plugin versions.

### Release (npm channel)

The framework body ships as the npm package `owfadev`, and the package version rides the framework anchor: `.owfa/VERSION` `0.4` → package `0.4.x`. A release is a version bump in both files, a commit `release: framework X.Y.Z`, and a `vX.Y.Z` tag push. The tag triggers [`.github/workflows/publish.yml`](.github/workflows/publish.yml), which re-runs the release gate and publishes with provenance; the gate refuses version/tag drift and any local state (bytecode, ledger, journal, cache) in the tarball. Full runbook: [`.owfa/docs/releasing.md`](.owfa/docs/releasing.md).

## Packages

Changes to package membership, PKG.yaml, or the plugin layout must keep `kernel validate` green — the roster-vs-closure reconciliation runs as part of it. New domain families land as `domains/<pkg>/` packages (declaration first, code second); see the packages doc for the invariants.

## When something is off

A branch gets rejected: read the reviewer's reason, fix, re-push — the PR updates itself. Disagreeing with a review: comment on the PR or raise it in the group. Unsure whether some data may enter git: ask first, then act.

## The bootstrap charter (2026-11-16)

The framework repo hosts itself by the rules it ships. The rulings below are already in force from practice; this section is their canonical record.

- **Review freshness (严禁自审).** The PR author never provides the approving review — GitHub enforces the human case; for agent-assisted work the review must come from a context that did not author or co-develop the change. An independent audit transcript (reproduced verification, not trusted narration) is the review evidence; the maintainer posts it as the formal review. Protection rules are the owner's escape hatch, not a merge shortcut — lifting protection to self-merge is an emergency move, recorded on the PR. Incident record: on 2026-11-16 a fresh review found master protection absent (unknown window); restored same day (1 approving review + enforce_admins). An independent audit transcript posted as the review satisfies the approval requirement's intent; the maintainer records it before any emergency self-merge.
- **Release discipline is repo-wide.** Every INDEX version bump: tag `<pkg>-v<version>` (the only fetched ref) + optional `commit:` pin (post-clone veto) + version == PKG.yaml — canonical text in the [registry](https://github.com/owfadev/owfa-registry) README; framework releases additionally require `.owfa/VERSION` == `package.json` == tag (the gate refuses otherwise). A merged-but-unbumped package fix is INVISIBLE to instances (installs fetch PKG-tagged snapshots) — version bumps are part of the fix, not an afterthought.
- **Vocabulary rulings bind docs.** 2026-11-16: the landlord/tenant metaphor is retired from living docs (protocol = this workspace's law, domain = a defined information kind with its own charter); the plugin ontology (kernel.md §2.1) is the canonical vocabulary. Docs obey the single-source discipline (kernel.md §2.3) and `scripts/docs_lint.py` gates CI.
- **Version cadence.** 0.x minor lines are milestone releases with declared breaking changes (0.5.0: R11 flips to error, host forwarder + pipeline shim no longer planted); patch releases carry no new framework runtime features — guard/tooling hardening (lint rules, CI) and documentation rulings may ride patches. Breaking changes are documented in releasing.md at the release PR, never discovered by users.
- **Org layout.** This repo (kernel + channel) / the registry (index + trust gate) / `owfa-*` package repos (self-hosted contents) — one workspace one protocol; cross-workspace reference is read-only (the bridge plugin); instance repos never author framework code (the template+instance workflow above).
