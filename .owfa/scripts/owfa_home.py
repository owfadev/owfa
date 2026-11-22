#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OWFA machine substrate: connector homes and workspace bindings (work order #56, B1-B3).

Layout (machine-global — one machine, many workspaces):

    ~/.owfa/connectors/<name>/
    ├── bindings.json      # [{id, root, home, bot?, installed_at}] — the registry
    └── homes/<id>/        # one state dir per binding (credentials, spool, logs)

Resolution order for "which home serves this workspace":

    explicit --root/--home argument
    > OWFA_ROOT environment variable
    > cwd reverse-lookup in the bindings registry
    > homes/default            (single-workspace machines: zero configuration)

Invariants (enforced here so every connector inherits them):

- one home, one active binding — two workspaces draining one spool is a semantic
  error, not a health issue; `exclusivity_violations` reports it
- an unbound workspace is degraded-but-healthy: `resolve_home` falls back to
  homes/default only for machines with exactly one binding-less usage pattern;
  a workspace wanting isolation must bind explicitly
- unbind detaches the binding; homes/<id>/ holds data — deletion is a human act
- stale bindings (root directory gone) are reported by `stale_bindings` and
  cleaned by explicit confirmation, never silently

Migration from pre-0.4 scattered homes (~/.qq-cli and friends): `migrate_legacy_home`
MOVES the legacy directory into homes/<id> (move, never copy — credentials must not
duplicated) and registers the binding.

A connector with more than one state directory (bb + sis, say) keeps them as
components under its single home: homes/<id>/<component>/. `component_dir` is the
accessor and `migrate_legacy_home(..., component=...)` migrates one legacy
directory into one component — a connector never invents a second layout.

Connector bootstrap ABI (how a connector process finds this module):

    1. $OWFA_HOME_HELPER                 explicit path to this file
    2. walk-up from the connector's own __file__ (…/connectors/<name>/<pkg>/x.py
       climbs to <workspace>/.owfa/scripts/owfa_home.py)
    3. walk-up from cwd
    4. no helper found → the connector falls back to its legacy scattered home
       and prints a one-line migration notice; it must never silently create a
       second home.

Pure stdlib. State writes are atomic (tmp + os.replace) with 0600 perms; the
registry is single-writer by convention (human or installer), so no file lock.
"""
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ENV_HOME = "OWFA_HOME"      # machine substrate root (default ~/.owfa)
ENV_ROOT = "OWFA_ROOT"      # workspace root (set by executors / nested sessions)
BINDINGS_VERSION = 1
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def machine_root() -> Path:
    raw = os.environ.get(ENV_HOME)
    return Path(raw).expanduser() if raw else Path.home() / ".owfa"


def connectors_root() -> Path:
    return machine_root() / "connectors"


def connector_dir(connector: str) -> Path:
    return connectors_root() / connector


def bindings_path(connector: str) -> Path:
    return connector_dir(connector) / "bindings.json"


def homes_root(connector: str) -> Path:
    return connector_dir(connector) / "homes"


def home_dir(connector: str, binding_id: str) -> Path:
    return homes_root(connector) / binding_id


def component_dir(
    connector: str,
    component: str,
    explicit_root: str = "",
    explicit_home: str = "",
    create: bool = True,
) -> Path:
    """One state directory of a multi-directory connector: homes/<id>/<component>/.

    Single-directory connectors use resolve_home() directly; a connector that
    carries more than one (cuhksz-cli: bb + sis) names components instead of
    growing a second home. `create` makes the directory 0700 on demand.
    """
    if not component or os.sep in component or component in (".", ".."):
        raise ValueError(f"invalid component name: {component!r}")
    path = resolve_home(connector, explicit_root, explicit_home) / component
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_bindings(connector: str) -> list:
    try:
        with open(bindings_path(connector), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    out = data.get("bindings") if isinstance(data, dict) else None
    return out if isinstance(out, list) else []


def save_bindings(connector: str, bindings: list) -> None:
    path = bindings_path(connector)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": BINDINGS_VERSION, "bindings": bindings}, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def _slug(root: str) -> str:
    base = os.path.basename(os.path.normpath(root)).lower()
    slug = _SLUG_RE.sub("-", base).strip("-")[:24] or "ws"
    return f"{slug}-{secrets.token_hex(2)}"


def resolve_root(connector: str, explicit: str = "") -> str:
    """Explicit argument > OWFA_ROOT env > cwd reverse-lookup > '' (unresolved → default)."""
    if explicit:
        return str(Path(explicit).expanduser().resolve())
    env = os.environ.get(ENV_ROOT)
    if env:
        return str(Path(env).expanduser().resolve())
    cwd = os.getcwd()
    for b in load_bindings(connector):
        try:
            root = str(Path(b.get("root", "")).resolve())
        except OSError:
            continue
        if root and (cwd == root or cwd.startswith(root + os.sep)):
            return root
    return ""


def resolve_home(connector: str, explicit_root: str = "", explicit_home: str = "") -> Path:
    """The home directory serving the resolved workspace (B1: homes/<id>, default = zero-config)."""
    if explicit_home:
        return Path(explicit_home).expanduser()
    root = resolve_root(connector, explicit_root)
    bindings = load_bindings(connector)
    for b in bindings:
        if root and os.path.normpath(b.get("root", "")) == os.path.normpath(root):
            return Path(b["home"])
        if not root and len(bindings) == 1:
            return Path(b["home"])  # single binding, no better signal — it is the default
    if len(bindings) >= 2:
        # multi-binding machine, workspace matches nothing: default would be an
        # unregistered home that two unmatched workspaces could silently share
        # (review round 3) — degraded-but-healthy, but it must be loud
        print(
            f"[owfa-home] warning: workspace matches none of {len(bindings)} bindings — "
            "serving homes/default; bind this root or set OWFA_ROOT to remove the ambiguity",
            file=sys.stderr,
        )
    return home_dir(connector, "default")


def bind(connector: str, root: str, binding_id: str = "", bot: str = "") -> dict:
    """Register a workspace binding (B2). Re-binding the same root replaces the entry."""
    root = str(Path(root).expanduser().resolve())
    bindings = load_bindings(connector)
    entry = {
        "id": binding_id or next((b["id"] for b in bindings if os.path.normpath(b.get("root", "")) == os.path.normpath(root)), ""),
        "root": root,
        "home": str(home_dir(connector, binding_id or "")) if binding_id else "",
        "bot": bot,
        "installed_at": _now_iso(),
    }
    if not entry["id"]:
        entry["id"] = "default" if not bindings else _slug(root)
    entry["home"] = str(home_dir(connector, entry["id"]))
    bindings = [b for b in bindings if b.get("id") != entry["id"]]
    bindings.append(entry)
    save_bindings(connector, bindings)
    Path(entry["home"]).mkdir(parents=True, exist_ok=True, mode=0o700)  # docs/home.md: 0600/0700
    return entry


def unbind(connector: str, binding_id: str) -> bool:
    """Detach a binding. homes/<id>/ keeps its data — deletion belongs to the human (B3)."""
    bindings = load_bindings(connector)
    kept = [b for b in bindings if b.get("id") != binding_id]
    if len(kept) == len(bindings):
        return False
    save_bindings(connector, kept)
    return True


def exclusivity_violations(connector: str) -> list:
    """Homes served by more than one active binding (B3: this is an error, not a warning)."""
    seen = {}
    for b in load_bindings(connector):
        seen.setdefault(b.get("home", ""), []).append(b.get("id", ""))
    return [{"home": h, "bindings": ids} for h, ids in sorted(seen.items()) if len(ids) > 1]


def stale_bindings(connector: str) -> list:
    """Bindings whose workspace root disappeared — report and clean on confirmation (B3)."""
    return [b for b in load_bindings(connector) if not os.path.isdir(b.get("root", ""))]


def connector_status(connector: str, explicit_root: str = "") -> dict:
    """Read-only substrate view for a connector's `home status` command / health checks.

    Reports where the connector's state lives, which components exist, and the
    two substrate-level hazards (exclusivity violations, stale bindings). It
    never creates or moves anything.
    """
    home = resolve_home(connector, explicit_root)
    comps = []
    try:
        comps = sorted(p.name for p in home.iterdir() if p.is_dir())
    except OSError:
        pass
    return {
        "connector": connector,
        "connector_dir": str(connector_dir(connector)),
        "bindings": load_bindings(connector),
        "resolved_root": resolve_root(connector, explicit_root),
        "home": str(home),
        "components": comps,
        "exclusivity_violations": exclusivity_violations(connector),
        "stale_bindings": stale_bindings(connector),
    }


def migrate_legacy_home(
    connector: str,
    legacy_dir: str,
    binding_id: str = "",
    root: str = "",
    component: str = "",
) -> dict:
    """Move a pre-0.4 scattered home (e.g. ~/.qq-cli) into homes/<id> and bind it.

    MOVE, never copy: credentials must not exist in two places. The legacy
    directory is left as a symlink to the new home so old absolute paths keep
    resolving — the symlink is the 0.5-cleanup item.

    `component` targets homes/<id>/<component> for connectors that carry more
    than one state directory (cuhksz-cli: bb, sis); the default targets the
    home itself.
    """
    if component and (os.sep in component or component in (".", "..")):
        raise ValueError(f"invalid component name: {component!r}")
    src = Path(legacy_dir).expanduser()
    if not src.exists() and not src.is_symlink():
        print(f"[owfa-home] warning: legacy home {src} does not exist — registering the binding only")
    entry = bind(connector, root or os.getcwd(), binding_id)  # empty id → reuse the root's existing binding
    dst = Path(entry["home"]) / component if component else Path(entry["home"])
    if src.is_symlink():
        return entry  # already migrated
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        # bind() pre-creates homes/<id>; POSIX rename replaces an empty existing
        # directory, Windows raises WinError 183 — clear the empty pre-creation
        # first so the move works on both (review P1, PR #57 round 2).
        if dst.is_dir():
            if any(dst.iterdir()):
                raise SystemExit(
                    f"[owfa-home] refusing to migrate: target home {dst} already exists and is not empty"
                )
            dst.rmdir()
        os.rename(src, dst)  # same volume — atomic enough
        try:
            if os.name == "nt":
                import _winapi

                # Junctions need no admin rights / Developer Mode, unlike
                # os.symlink on Windows. Argument order matches os.symlink:
                # junction AT src pointing TO dst.
                _winapi.CreateJunction(str(dst), str(src))
            else:
                os.symlink(dst, src, target_is_directory=True)
        except OSError as exc:
            print(f"[owfa-home] warning: could not link {src} -> {dst} ({exc}); old absolute paths will not resolve")
    return entry


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="OWFA machine substrate: connector home bindings")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bind", "unbind", "resolve", "list", "stale", "exclusive", "migrate", "component", "status"):
        s = sub.add_parser(name)
        s.add_argument("connector")
        if name in ("bind", "resolve", "migrate", "status"):
            s.add_argument("--root", default="")
        if name in ("bind", "migrate"):
            s.add_argument("--id", default="")
            s.add_argument("--bot", default="")
        if name == "migrate":
            s.add_argument("--legacy", required=True)
            s.add_argument("--component", default="")
        if name == "component":
            s.add_argument("component")
        if name == "unbind":
            s.add_argument("binding_id")
    args = ap.parse_args()
    c = args.connector
    if args.cmd == "bind":
        print(json.dumps(bind(c, args.root or os.getcwd(), args.id, args.bot), ensure_ascii=False))
    elif args.cmd == "unbind":
        print("unbound" if unbind(c, args.binding_id) else "no such binding")
    elif args.cmd == "resolve":
        print(resolve_home(c, args.root))
    elif args.cmd == "list":
        print(json.dumps(load_bindings(c), ensure_ascii=False, indent=2))
    elif args.cmd == "stale":
        print(json.dumps(stale_bindings(c), ensure_ascii=False))
    elif args.cmd == "exclusive":
        print(json.dumps(exclusivity_violations(c), ensure_ascii=False))
    elif args.cmd == "migrate":
        print(json.dumps(
            migrate_legacy_home(c, args.legacy, args.id, args.root or os.getcwd(), args.component),
            ensure_ascii=False,
        ))
    elif args.cmd == "component":
        print(component_dir(c, args.component))
    elif args.cmd == "status":
        print(json.dumps(connector_status(c, args.root), ensure_ascii=False, indent=2))
