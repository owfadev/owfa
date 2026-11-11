# Machine substrate: `~/.owfa` — connector homes and workspace bindings

> v0.4 work order #56 (B1-B3). One machine hosts many OWFA workspaces; connector
> state must not collide across them. This is the shared contract every OWFA
> connector inherits by importing `.owfa/scripts/owfa_home.py` — no connector
> invents its own layout.

## Layout

```
~/.owfa/                                  # machine substrate (env: OWFA_HOME)
└── connectors/<name>/
    ├── bindings.json                     # registry: [{id, root, home, bot?, installed_at}]
    └── homes/<id>/                       # one state dir per binding — credentials,
                                          # spool, logs; 0600/0700, never in any repo
```

- `<id>` = human alias + 2-byte hash (`repo-a1b2`); the singleton case is
  literally `default`.
- Homes are **machine-global, not per-instance**: a connector does not read the
  workspace; only its binding records which workspace drains it.

## Resolution order

`--root/--home` argument → `OWFA_ROOT` env → cwd reverse-lookup in the registry
→ `homes/default` (single-workspace machines: zero configuration).

## Invariants

1. **One home, one active binding.** Two workspaces draining one spool is a
   semantic error (`exclusivity_violations` → error, the only error-level health
   state in the substrate).
2. **Unbound workspace = degraded-but-healthy** (warning in domain checks): the
   domain is installed, the skill answers with guidance, nothing drains.
3. **Unbind detaches, never deletes.** `homes/<id>/` holds credentials and
   spool data — deletion is a human act, confirmed.
4. **Stale bindings** (workspace root gone) are reported and cleaned on
   confirmation — same rhythm as the tmp zone's stale_after.

## Migration from pre-0.4 scattered homes

`owfa_home.migrate_legacy_home("qq-cli", "~/.qq-cli")` **moves** the legacy
directory into `homes/<id>` (move, never copy — credentials must not exist in
two places) and leaves a symlink at the old path so old absolute references keep
resolving; the symlink is the 0.5-cleanup item. Version-gated per connector: a
connector that finds its legacy home on first run offers the migration instead
of silently creating a second home.

## Harness scope

Connector manifests (PKG.yaml `connectors[]`) may declare `home:` for external
connectors whose state lives outside this substrate (declared, not migrated).
The registry mirrors per-package `harness:` — `universal` connectors are the
first class; harness-locked ones register honestly and health checks surface the
mismatch.
