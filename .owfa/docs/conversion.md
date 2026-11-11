# Converting a legacy instance (pre-split flat layout) to the package era

> Walked end-to-end on a real instance (2026-10-13 conversion drill: 35 flat plugins → core 21 + 5 registry packages, 36 green, all inits cleared on real assets). Before you start: **commit a baseline** — the conversion is a snapshot boundary; if anything goes wrong, `git checkout` back.

## Eight steps

1. **Baseline commit** at the instance root — the rollback anchor
2. **Survey**: `ls .owfa/plugins` (a flat list = legacy), `ls .owfa/command`, `ls .agents/skills` — note any *non-framework* skills you keep (the drill kept `dsh-token`)
3. **Swap the framework trees**: delete `.owfa/{plugins,command,scripts,protocol,docs}` and the framework entries of `.agents/skills/` (keep your own tool skills); copy in the template's `.owfa/{plugins,command,scripts,protocol,docs,VERSION}` and `.agents/skills/*`. Data zones (`wiki/`, `vault/`, domain data directories), `connectors/`, `AGENTS.md`, `.gitignore` are never touched
4. **Converge**: `kernel all` — core 21 green; the AGENTS injection region rebuilds wholesale (the old flat blocks are replaced)
5. **Install packages**: `kernel list-remote`, then `kernel install <pkg> --yes` per package. Connectors already present are **kept existing** (running venvs survive; connector code updates arrive via uninstall+install of the owning package)
6. **Clear the inits**: `kernel migrate <pkg>` prints each declaration; a real instance usually already satisfies the verify criteria (identity / profile / declaration pages exist on real assets) → `kernel migrate <pkg> --clear`
7. **Derived layer**: `pipeline.py index` (idempotent rebuild); `hot.md` needs no rebuild — entries are managed per-write with window eviction
8. **Close the transaction**: one commit (`plugin: converted to the package era …`) + a log line; `kernel upgrade` should now report framework and every package up to date

## Findings from the drill (already baked into the mechanism)

- **Injection budget**: a fully-loaded instance (core 21 + all five packages) projects ~15.7K — the original 15 KiB budget (a core-20-era figure) was raised to 16 KiB; the 16K harness floor stays the anchor
- **Existing connectors kept on install** (conservative semantics) — credential dirs and venvs are never touched
- The **tri-face pending warning** makes the mid-conversion state visible in every session; clearing inits on real assets typically passes verify in one shot

## If something breaks

The baseline commit is your exit: `git log` finds it, `git checkout` restores the framework trees. Data zones were never touched — the worst case is a framework redo, never data loss.
