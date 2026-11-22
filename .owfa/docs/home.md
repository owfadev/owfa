# Machine substrate: `~/.owfa` — connector homes

> Status: 0.5.x ABI. Supersedes the pre-0.4 scattered-home habit (`~/.bb-cli`,
> `~/.sis-cli`, `~/.bili-cli`, `~/.config/mail-cli`, `~/.qq-cli`, …).
> Implementation: `.owfa/scripts/owfa_home.py` (stdlib, no dependencies).

One machine hosts many OWFA workspaces. A connector's credentials, sessions and
spool belong to the **machine**, not to any single workspace tree — but two
workspaces must not silently drain one state directory either. The substrate is
the one place that answers both needs.

## Layout

```
~/.owfa/                                   # machine substrate (env: OWFA_HOME)
├── kernel/<X.Y.Z>/                        # user-level kernel versions (+ current pointer)
├── journal/events.log                     # machine journal
├── workspaces.yaml                        # workspace registry
└── connectors/<name>/
    ├── bindings.json                      # [{id, root, home, bot?, installed_at}]
    └── homes/<id>/                        # one state dir per binding (0600/0700)
        └── <component>/                   # optional: multi-directory connectors
```

- `<name>` is the **connector name** — the distribution/repo name (`cuhksz-cli`,
  `bili-cli`, `mail-cli`, `qq-cli`, …), never a workspace-chosen label.
- `<id>` is a human alias plus a 2-byte hash (`repo-a1b2`); the singleton case on
  a one-workspace machine is literally `default`.
- **Components** — a connector that owns more than one state directory keeps
  them as components under its single home (`cuhksz-cli` → `bb/` and `sis/`)
  instead of growing a second home. `component_dir()` is the accessor;
  `migrate_legacy_home(..., component="bb")` migrates one legacy directory into
  one component.

## Resolution order

```
explicit --root / --home argument
> OWFA_ROOT environment variable
> cwd reverse-lookup in bindings.json
> homes/default
```

On a machine with two or more bindings, a workspace matching none of them still
falls through to `homes/default` (degraded-but-healthy) but prints a loud stderr
warning — two unmatched workspaces sharing `default` would be invisible to the
exclusivity check. Bind the root or set `OWFA_ROOT` to remove the ambiguity.

## Connector bootstrap ABI

A connector resolves its state **at import/run time**, never from a build-time
constant. The canonical bootstrap (keep it byte-identical across connectors):

```python
import importlib.util
import os
from pathlib import Path

HELPER_ENV = "OWFA_HOME_HELPER"   # explicit path to owfa_home.py


def _candidates():
    out = []
    env = os.environ.get(HELPER_ENV)
    if env:
        out.append(Path(env).expanduser())
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for parent in (start, *start.parents):
            out.append(parent / ".owfa" / "scripts" / "owfa_home.py")
    return out


def load_owfa_home():
    """Import the machine substrate helper, or None when this connector runs outside a workspace."""
    seen = set()
    for helper in _candidates():
        if helper in seen or not helper.is_file():
            continue
        seen.add(helper)
        spec = importlib.util.spec_from_file_location("owfa_home", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None
```

Rules:

1. **Never guess the layout.** All paths come from the helper (`resolve_home`,
   `component_dir`, `migrate_legacy_home`). A connector does not assemble
   `~/.owfa/connectors/...` by hand.
2. **Fallback is legacy, and it is loud.** When no helper is found (connector
   installed outside any workspace), the connector keeps using its old scattered
   home and prints one stderr line naming the migration command. The same rule
   holds *after* the helper appears but before the state has moved: a connector
   that still finds its legacy directory populated keeps serving it (loudly,
   naming `home migrate`) instead of silently switching to an empty substrate
   home. It must never create a second, silently preferred home.
3. **Explicit overrides stay explicit.** Existing per-connector overrides
   (`BB_CLI_HOME`, `SIS_CLI_HOME`, …) are honoured first and mean "use exactly
   this directory"; they are compatibility escape hatches, not the default path.
4. **Migration is an explicit command, not a side effect.** `migrate_legacy_home`
   moves (never copies) and leaves a symlink at the legacy path so old absolute
   references keep resolving. Connectors expose it as `home status` / `home
   migrate [--dry-run]`.

## Delivery to connectors

`owfa_home.py` ships in the channel payload (`.owfa/scripts/`). How it reaches a
workspace depends on the channel:

| channel | where the helper lives |
|---|---|
| legacy (in-tree kernel) | copied with the payload tree: `<ws>/.owfa/scripts/owfa_home.py` |
| user-level kernel (0.5.x) | planted by `owfa init` / `owfa adopt` into `<ws>/.owfa/scripts/owfa_home.py` (the kernel itself lives in `$OWFA_HOME/kernel/<ver>/`); an existing workspace is repaired with the idempotent `owfa plant-helper <ws>` |

`owfa doctor` fails a marker workspace whose helper is missing and names
`owfa plant-helper`; the legacy `owfa upgrade` refuses marker workspaces by
design (M1 anti-stomp guard), so `plant-helper` is the supported repair path. Connectors therefore only need the walk-up in the ABI
above; `OWFA_HOME_HELPER` exists for unusual layouts and tests.

## Invariants

1. **One home, one active binding.** Two workspaces draining one spool is a
   semantic error (`exclusivity_violations`), not a health warning.
2. **Unbound workspace = degraded-but-healthy.** The connector still answers;
   nothing is drained; bind the root to isolate.
3. **Unbind detaches, never deletes.** `homes/<id>/` holds credentials — deletion
   is a human act, confirmed.
4. **Stale bindings** (workspace root gone) are reported (`stale_bindings`) and
   cleaned only on confirmation.
5. **No state in any repository.** Homes are machine-global; a repo may hold the
   connector code, never a home.

## Migration from pre-0.4 scattered homes

```bash
# inspect first
python3 .owfa/scripts/owfa_home.py status cuhksz-cli
# one legacy directory per call; <id> defaults to the root's binding
python3 .owfa/scripts/owfa_home.py migrate cuhksz-cli --legacy ~/.bb-cli  --component bb
python3 .owfa/scripts/owfa_home.py migrate cuhksz-cli --legacy ~/.sis-cli --component sis
```

The move is atomic on one volume; the symlink left behind is a cleanup item for
the human, never removed by the kernel. Connectors print the same two commands
when they find a legacy directory and no substrate home.

## Health

- `exclusivity_violations(connector)` → error-level (the only error state in the
  substrate).
- `stale_bindings(connector)` → report, clean on confirmation.
- `connector_status(connector)` → read-only view used by connector `home status`
  and by checks: home, components, bindings, both hazards above.

## Versioning

The helper is versioned with the kernel (`$OWFA_HOME/kernel/<X.Y.Z>/`). The
bootstrap imports **whatever the workspace planted**, so a workspace pinned to an
older kernel keeps an older ABI; connectors must only rely on functions present
since `subdir/component` landed (0.5.2+). Additions stay backward-compatible;
a breaking ABI change bumps the kernel and the connector's `compat` floor.
