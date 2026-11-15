#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vaultwiki protocol ABI query face (abi-spec v2 §2/§3/§6).

Four semantics, one entry: `proto_query.py <semantic> [args]`, JSON to stdout.

  list [--kind K]      every md page under wiki/ (addr = wiki full name), optional
                       kind filter (unknown kind -> empty result, no error)
  get <addr>           page raw content (no truncation); read-only, never writes
  search <expr>        full-name prefix match OR body substring match
  recent [--window Nd|Nm]   pages whose mtime falls in the window (default 7d);
                       op is best-effort: create only when a log/hot line in the
                       window names the page with a create verb, else unknown/update

Envelope (contract face): each item carries protocol:"vaultwiki" and proto_ver
(read live from this package's PKG.yaml version — never hardcoded). Batch results
are {ok, semantic, count, items}. Query-level failures exit 0 with
{ok:false, error_code, message} (error_code in not_found / bad_request /
unsupported_semantic / internal); only a process crash exits non-zero.

Self-contained: standard library only, no session state, no wikilib import — the
frontmatter subset parsed here mirrors wikilib.parse_frontmatter (top-level
scalars / block lists) so `type` reads identically to pipeline.py without the
framework tree being present.

Location: package root (pipeline.py precedent — the whole tree travels with the
package). Instance path: .owfa/plugins/domains/personal/proto_query.py.
"""
import datetime
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_here = os.path.dirname(os.path.abspath(__file__))
PKG_PATH = os.path.join(_here, "PKG.yaml")
PROTOCOL_ID = "vaultwiki"

# ROOT resolution mirrors pipeline.py: suite install layout
# <root>/.owfa/plugins/domains/personal/  (repo checkout of the package itself
# has no instance wiki/ below it, so queries there walk an empty tree).
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
WIKI = os.path.join(ROOT, "wiki")

SEMANTICS = ("list", "get", "search", "recent")
WINDOW_RE = re.compile(r"^(\d+)([dm])$")
FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.S)
CREATE_HINTS = ("create", "created", "新建", "建立", "创设")


def die(error_code, message):
    """Query-level failure: envelope on stdout, exit 0 (abi-spec §2 M4)."""
    print(json.dumps({"ok": False, "error_code": error_code, "message": message},
                     ensure_ascii=False))
    sys.exit(0)


def proto_ver():
    """Version is pinned to this package's PKG.yaml (single source, abi-spec §4.1)."""
    try:
        text = open(PKG_PATH, encoding="utf-8").read()
    except OSError:
        die("internal", "PKG.yaml unreadable next to proto_query.py")
    m = re.search(r"^version:\s*[\"']?([0-9][^\s\"']*)", text, re.M)
    if not m:
        die("internal", "PKG.yaml has no version field")
    return m.group(1)


def parse_frontmatter(text):
    """Minimal YAML subset, same shape as wikilib.parse_frontmatter (scalar `type` is all we need)."""
    fm = {}
    m = FM_RE.match(text)
    if not m:
        return fm
    for raw in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not mm:
            continue
        key, val = mm.group(1), mm.group(2).strip()
        if val.startswith("#") or val == "":
            fm[key] = None
        elif val.startswith("[") and val.endswith("]"):
            fm[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        else:
            fm[key] = val.strip("\"'")
    return fm


def get_direct_path(addr):
    """Resolve a walk-missed addr to a readable path under wiki/, or None.

    Security: the addr must be a safe relative path (no absolute, no '..' escape, no
    drive/UNC tricks), resolve inside wiki/, and not fall under wiki/tmp/ (invisible
    to this face). Anything else is treated as not found, never opened."""
    if not addr or addr != addr.strip() or "\\" in addr:
        return None
    if addr.startswith("/") or re.match(r"^[A-Za-z]:", addr):
        return None
    rel = addr + ".md"
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return None
    base = os.path.realpath(WIKI)
    path = os.path.realpath(os.path.join(WIKI, *parts))
    if not (path == base or path.startswith(base + os.sep)):
        return None
    rel_checked = os.path.relpath(path, base).replace(os.sep, "/")
    if rel_checked == "tmp.md" or rel_checked.startswith("tmp/"):
        return None
    if not (os.path.isfile(path) and path.endswith(".md")):
        return None
    return path


def walk_pages():
    """Yield (addr, full path, frontmatter, body) for every md under wiki/ (wiki/tmp/
    excluded — tmp plugin invisible-to-derived-layer semantics; the ABI face is an
    external consumer, not the derived layer, so drafts never surface here), addr-sorted."""
    out = []
    for dirpath, dirs, files in os.walk(WIKI):
        dirs.sort()
        dirs[:] = [d for d in dirs if os.path.join(dirpath, d) != os.path.join(WIKI, "tmp")]
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                text = open(p, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            fm = parse_frontmatter(text)
            m = FM_RE.match(text)
            body = text[m.end():] if m else text
            rel = os.path.relpath(p, WIKI).replace(os.sep, "/")
            out.append((rel[:-3], p, fm, body))
    out.sort(key=lambda t: t[0])
    return out


def title_of(addr, fm):
    t = fm.get("title")
    return str(t) if t else addr.rsplit("/", 1)[-1]


def kind_of(fm):
    t = fm.get("type")
    return str(t) if t else ""


def mtime_of(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")


def item(addr, path, fm, extra=None):
    it = {"addr": addr,
          "title": title_of(addr, fm),
          "kind": kind_of(fm),
          "mtime": mtime_of(path),
          "protocol": PROTOCOL_ID,
          "proto_ver": proto_ver()}
    if extra:
        it.update(extra)
    return it


def batch(semantic, items):
    print(json.dumps({"ok": True, "semantic": semantic, "count": len(items),
                      "items": items}, ensure_ascii=False))


def _mention_dates():
    """Best-effort evidence from wiki/log.md + wiki/hot.md: addr -> ([all mention dates], [create-verb mention dates])."""
    found = {}
    for name in ("log.md", "hot.md"):
        p = os.path.join(WIKI, name)
        if not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for line in text.splitlines():
            dm = re.match(r"^- (\d{4}-\d{2}-\d{2})\b", line)
            if not dm:
                continue
            is_create = any(h in line.lower() for h in CREATE_HINTS)
            for addr, _, _, _ in _pages_cache:
                if addr in line or addr.rsplit("/", 1)[-1] in line:
                    alld, cr = found.setdefault(addr, ([], []))
                    alld.append(dm.group(1))
                    if is_create:
                        cr.append(dm.group(1))
    return found


_pages_cache = []


def op_for(addr, mentions, window_start):
    """create only with in-window log/hot create-verb evidence; a mention dated before
    the window proves prior existence -> update; anything else -> unknown (never a lied create)."""
    dates, creates = mentions.get(addr, ([], []))
    if any(d >= window_start for d in creates):
        return "create"
    if any(d < window_start for d in dates):
        return "update"
    return "unknown"


def parse_window(raw):
    m = WINDOW_RE.match(raw or "")
    if not m or int(m.group(1)) == 0:
        return None
    n = int(m.group(1))
    return n if m.group(2) == "d" else n * 30  # month approximated as 30d, a scan window not a calendar promise


def main(argv):
    if not argv:
        die("unsupported_semantic", "no semantic given; expected one of: " + ", ".join(SEMANTICS))
    semantic = argv[0]
    args = argv[1:]

    if semantic not in SEMANTICS:
        die("unsupported_semantic", "unknown semantic %r; expected one of: %s" % (semantic, ", ".join(SEMANTICS)))

    pages = walk_pages()
    _pages_cache.extend(pages)

    if semantic == "list":
        kind = None
        if "--kind" in args:
            i = args.index("--kind")
            if i + 1 >= len(args):
                die("bad_request", "--kind requires a value")
            kind = args[i + 1]
        items = [item(a, p, fm) for a, p, fm, _ in pages if kind is None or kind_of(fm) == kind]
        batch("list", items)

    elif semantic == "get":
        if len(args) != 1 or not args[0]:
            die("bad_request", "get takes exactly one <addr>")
        addr = args[0].strip("/")
        for a, p, fm, body in pages:
            if a == addr:
                it = item(a, p, fm, {"content": body})
                print(json.dumps(it, ensure_ascii=False))
                return
        # Walk miss. The walk skips undecodable pages, so a file may still exist here:
        # never lie about existence — open it directly (read-only) with replacement
        # decoding. wiki/tmp/ stays invisible to this face (tmp plugin semantics).
        path = get_direct_path(addr)
        if path is not None:
            text = open(path, encoding="utf-8", errors="replace").read()
            fm = parse_frontmatter(text)
            m = FM_RE.match(text)
            body = text[m.end():] if m else text
            it = item(addr, path, fm, {"content": body})
            print(json.dumps(it, ensure_ascii=False))
            return
        die("not_found", "no page at addr %r" % addr)

    elif semantic == "search":
        if len(args) != 1 or not args[0]:
            die("bad_request", "search takes exactly one <expr>")
        expr = args[0]
        items = [item(a, p, fm) for a, p, fm, body in pages
                 if a.startswith(expr) or expr in body]
        batch("search", items)

    elif semantic == "recent":
        window = "7d"
        if "--window" in args:
            i = args.index("--window")
            if i + 1 >= len(args):
                die("bad_request", "--window requires a value like 7d / 2m")
            window = args[i + 1]
        days = parse_window(window)
        if days is None:
            die("bad_request", "invalid window %r; expected <N><d|m> with N a positive integer" % window)
        now = datetime.datetime.now()
        try:
            start = now - datetime.timedelta(days=days)
        except OverflowError:  # absurdly large window: clamp to "everything", not a crash
            start = datetime.datetime.min
        start_iso = start.isoformat(timespec="seconds")
        creates = _mention_dates()
        items = []
        for a, p, fm, _ in pages:
            mt = mtime_of(p)
            if mt < start_iso:
                continue
            items.append(item(a, p, fm, {"op": op_for(a, creates, start.date().isoformat())}))
        items.sort(key=lambda it: it["mtime"], reverse=True)
        batch("recent", items)


if __name__ == "__main__":
    main(sys.argv[1:])
