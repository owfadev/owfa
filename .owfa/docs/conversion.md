# Conversion: a 0.3 instance → the 0.4 package era

> Reader: the owner of an existing OWFA 0.3 instance (framework in `.meta/`, or a 0.4-layout instance that still carries core plugins in-tree) who wants to move to v0.4 without touching instance data. Fresh installs don't need this page — `npx owfadev init` already lands the split layout. Full upgrade mechanics for already-current instances live in [deployment.md](deployment.md).

## Who needs to convert

Two shapes are pre-split and get converted by one `upgrade` run:

- **`.meta/` layout** — the framework tree lives under `.meta/` (detected by the absence of `.owfa/VERSION` but presence of a version file).
- **in-tree core** — a `.owfa/plugins/core/` directory exists. Since v0.4 the channel ships no plugins at all; those masters are instance state and get adopted as the `personal` suite package.

If neither matches (no `.meta/`, no `plugins/core/`), `upgrade` is an ordinary framework refresh — see [deployment.md](deployment.md).

## One command

```bash
npx owfadev upgrade
```

Use `npx owfadev`, not `npx owfa` — the `owfa` npm name is frozen by similarity policy and `npx owfa` does not work (the installed package does expose both `owfa` and `owfadev` binaries, so an existing global `owfa upgrade` keeps working).

Useful flags: `--check` (read-only dry run), `--backup` (copy the outgoing trees under `.owfa-backup/`), `--force`.

## What it does, step by step

1. **Framework swap with attic parking.** The old framework tree (`.meta/` or `.owfa/`) is renamed aside into `.owfa-migrate/replace/`, the channel's fresh tree is copied in, and package-owned state is carried back over by difference (package command masters, non-framework skills, the kernel state files). A failure here rolls the parked tree back — the parked copy is never implicitly discarded.
2. **Attic rescue of the core masters.** If the parked tree carried `.owfa/plugins/core/` but the incoming channel tree doesn't ship it, those masters are the only copy — and your only copy of any *uncommitted local edits* to core plugins. They are moved out of the attic to `.owfa-migrate/convert/core/` before the attic is deleted.
3. **Staging the `personal` package.** The rescued masters are copied to `.owfa-migrate/convert/personal/`, their manifests' retired 0.3 command ids (`map`, `save`, `profile`, …) are rewritten to the v0.4 `owfa-*` successors, the suite's command masters ride along from the channel's embedded blessed copy, and a synthetic `PKG.yaml` is written (`id: personal`, `kind: suite`, skeleton and uninstall anchors matching the pre-0.4 channel contract).
4. **Install.** `kernel install personal --path .owfa-migrate/convert/personal --yes` — the `--yes` is legitimate mechanical adoption of the channel's own former payload, not a trust decision.
5. **Convergence.** A `.meta` → `.owfa` layout shim is (re)created so 0.3-era absolute paths keep resolving until 0.5, then `kernel all` runs: validate, inject, registry, deploy.

The product is a **rootless suite**: `kind: suite` skips the kernel's family-root/closure law entirely — no synthesized root plugin, no synthetic `personal` dependency edges. The converted package matches the canonical `owfa-personal` shape (21 members, no root) and is replaceable via `kernel upgrade personal`.

> **⚠ Read this before rerunning a failed conversion**
>
> The breakpoint resume is **by design reuse**: the rescued masters at `.owfa-migrate/convert/core/` are deliberately kept across reruns (the conversion resumes from them), and the staging directory is likewise reused — a rerun copies *into* the existing `.owfa-migrate/convert/personal/` without cleaning it first.
>
> **After a failed `kernel install` step, remove the stale staging before rerunning:**
>
> ```bash
> rm -rf .owfa-migrate/convert/personal
> ```
>
> Otherwise the rerun installs on top of the old staging and converges a dirty mixture of two attempts — plugin masters, manifests, and projections from both runs. This is not hypothetical: a real incident had a converted instance overflow the 16 KiB injection budget and it took two debugging rounds to trace the cause back to a reused staging directory. The `convert/core/` hold, in contrast, is safe (and intended) to keep.

## After the conversion, self-check

```bash
python3 .owfa/scripts/owfa_kernel.py validate   # all green
npx owfadev doctor                              # ok
```

Then confirm **instance data is untouched**: the swap only replaces framework trees (`.owfa/`, `.agents/skills/`) — `wiki/` pages, `vault/` assets, domain data directories, connectors, `AGENTS.md`, `.gitignore` are never modified. Spot-check a few wiki pages and assets: they should be byte-identical and in place. Commit once to close the transaction (`git add -A && git commit`); the pre-upgrade commit is your rollback anchor, so make one *before* running `upgrade` too.

If `.meta/` was tracked by instance git before 0.4, sweep it once: `git rm -r --cached .meta` (the upgrade output reminds you).

## Manual escape hatch

If the mechanical path is unattractive (heavily edited core, distrust of the auto-conversion), the alternative is: `npx owfadev init` a fresh workspace (two-phase: kernel bootstrap, then offline install of the embedded `personal` suite), then move your data zones (`vault/`, `wiki/`, domain data, connectors) over by hand and run `kernel all`. The full procedure — components, channels, first-run verification — is [deployment.md](deployment.md).

## Where the old migration pages went

The pre-split `migrations/init.md` (the manual eight-step conversion walk and the manual first-run recipe) is superseded: the routine it described is now performed mechanically by `npx owfadev upgrade` / `init`, and the deployment-side guidance lives in [deployment.md](deployment.md). The only piece not covered there is the **git-channel manual install** — copying `.owfa/` + `.agents/skills/` from the template repository instead of using npm — which is the git-channel row of the channels table in deployment.md.
