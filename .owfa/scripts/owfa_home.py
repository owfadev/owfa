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

Pure stdlib. State writes are atomic (tmp + os.replace) with 0600 perms; the
registry is single-writer by convention (human or installer), so no file lock.
"""
import json
import os
import re
import secrets
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
    for b in load_bindings(connector):
        if root and os.path.normpath(b.get("root", "")) == os.path.normpath(root):
            return Path(b["home"])
        if not root and len(load_bindings(connector)) == 1:
            return Path(b["home"])  # single binding, no better signal — it is the default
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
    Path(entry["home"]).mkdir(parents=True, exist_ok=True)
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


def migrate_legacy_home(connector: str, legacy_dir: str, binding_id: str = "", root: str = "") -> dict:
    """Move a pre-0.4 scattered home (e.g. ~/.qq-cli) into homes/<id> and bind it.

    MOVE, never copy: credentials must not exist in two places. The legacy
    directory is left as a symlink to the new home so old absolute paths keep
    resolving — the symlink is the 0.5-cleanup item.
    """
    src = Path(legacy_dir).expanduser()
    if not src.exists() and not src.is_symlink():
        print(f"[owfa-home] warning: legacy home {src} does not exist — registering the binding only")
    entry = bind(connector, root or os.getcwd(), binding_id)  # empty id → reuse the root's existing binding
    dst = Path(entry["home"])
    if src.is_symlink():
        return entry  # already migrated
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        os.rename(src, dst)  # same volume — atomic enough
        try:
            os.symlink(dst, src, target_is_directory=True)
        except OSError as exc:
            print(f"[owfa-home] warning: could not symlink {src} -> {dst} ({exc}); old absolute paths will not resolve")
    return entry


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="OWFA machine substrate: connector home bindings")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bind", "unbind", "resolve", "list", "stale", "exclusive", "migrate"):
        s = sub.add_parser(name)
        s.add_argument("connector")
        if name in ("bind", "resolve", "migrate"):
            s.add_argument("--root", default="")
        if name in ("bind", "migrate"):
            s.add_argument("--id", default="")
            s.add_argument("--bot", default="")
        if name == "migrate":
            s.add_argument("--legacy", required=True)
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
        print(json.dumps(migrate_legacy_home(c, args.legacy, args.id, args.root or os.getcwd()), ensure_ascii=False))
