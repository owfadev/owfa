# instance-git: the snapshot ledger of real use

The instance library's git is a **snapshot surface** — a time machine and an undo button, not a collaboration tool. This plugin declares the contract and mechanically audits the red lines; it never executes git writes itself, and neither does the kernel (the journal is the kernel's own ledger).

## Three authors, one ledger

| Snapshot | Author | When | Scope |
|---|---|---|---|
| kernel snapshot | — none. The kernel never touches git; its mechanical facts live in the kernel journal | — | — |
| session snapshot | the agent, on the user's behalf | every transaction close (package transactions after validate goes green; session close commits the dirty tree) | the whole tree |
| manual snapshot | the human | any time, freely | anything |

Beyond these, usage (remotes, branches, bundles, whether to rebase) is the user's own; the framework does not regulate it.

## The minimal contract

1. **Message format**: `type: summary` — the same shape as a wiki/log entry (type from the log enumeration: map / save / query / check / plugin / todo / profile / other; optional `[domain]` tag). Git history becomes the mechanical twin of the log
2. **Red lines, exactly three**:
   - credentials and session files never enter git
   - adding an ignore must sweep already-tracked matches out of tracking
   - project-domain entities keep their own git — the instance discloses, never hosts
3. **The recovery entrance**: a check-flagged page → `git log -- <page>` (who changed it) → `git checkout -- <page>` (yesterday's truth back)

## Attached audit (read-only)

`scripts/check.py` runs on `check` and reports:

| Check | Catches |
|---|---|
| ignore-rule vs tracked-file residue | files matching an ignore rule that are still tracked (the dsh-router lesson, mechanized) |
| credential-pattern filenames | `*.ses`, `.env*`, `*cookie*`, `*secret*`, `credentials*` tracked |
| sensitive faces + remote | a remote is configured while `vault/` / `cuhksz/` faces are tracked — confirm it is private |
| entity self-git tracked | `projects/*/` carrying their own `.git` yet tracked by the parent |

Not a git repository at the root (no `.git`)? The contract is dormant — one info line, no warnings.

## One upgrade path, FYI

Pure local (the default) → a `git bundle` file copied elsewhere → a private remote. Before any remote, sweep the sensitive faces (vault/ assets, cuhksz course records — anything you would not hand to a stranger); public remotes are out of the question for an instance.

## Changelog

- 0.2 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.1 2026-10-13: established (see git history)
