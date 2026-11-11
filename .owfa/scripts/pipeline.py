#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derived-layer post-write pipeline: index / tags / hot / log / verify.

Positioning (.owfa/protocol/actions.md execution principles): deterministic structural
operations go to this script; semantic judgment goes to the LLM. Rebuild and rolling
rules and window parameters are governed by this file's source (the script source is
the rule list); PLUGIN.md keeps the semantic explanation; commands uniformly end by
invoking this pipeline instead of hand-writing derived pages themselves. verify is
post-write self-attestation (the minimal attester form): the LLM executes, the script
certifies.

Usage:
  python .owfa/scripts/pipeline.py index              # rebuild indexes (overflow-offloading scheme, idempotent; includes deleting surplus indexes after merging back)
  python .owfa/scripts/pipeline.py tags               # rebuild wiki/tags.md (idempotent)
  python .owfa/scripts/pipeline.py hot <type> <one-liner>   # evict out-of-window entries + prepend a hot-cache entry
  python .owfa/scripts/pipeline.py log <type> <one-liner> [--domain domain]   # capacity archive + prepend a log line (domain tag optional — domainless transactions)
  python .owfa/scripts/pipeline.py verify             # post-write self-attestation: attached audits + derived-area drift check

Type enumeration: map / save / query / check / plugin / todo / profile / other (the log plugin).
Concept-page determination (what enters the index): all .md under wiki/, excluding —
reserved names (index.md, log.md), wiki-root derived pages (hot.md, tags.md), the
archive/ subtree (immutable region, never rewritten by this script), and the tmp/
subtree (temporary zone: invisible to the derived layer, no retention promise, see the
tmp plugin). Index overflow-offloading scheme: a single index list holds at most
INDEX_MAX_ENTRIES entries (page entries + directory entries); the root index always
exists; on overflow, split off the subdirectories with the most pages (ties by name)
into their own indexes until it fits; pure-function rebuild (same structure, same result).
"""
import datetime
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIKI = os.path.join(ROOT, "wiki")
FORMAT_VERSION = "0.2"
DESC_MAX = 80
ROOT_RESERVED = {"hot.md", "tags.md"}  # wiki-root derived pages (log.md/index.md are reserved names, excluded uniformly)

# rolling-window parameters (mechanical authoritative source for the hot / log plugins; PLUGIN.md keeps the semantic explanation)
HOT_MAX_ENTRIES = 25
HOT_MAX_DAYS = 5
HOT_MAX_CHARS = 200
LOG_MAX_ENTRIES = 100
INDEX_MAX_ENTRIES = 25  # single index-list window (page entries + directory entries; overflow-offloading split basis)
TYPE_ORDER = ["map", "save", "query", "check", "plugin", "todo", "profile", "other"]
HOT_HEADER = ("# 热缓存\n\n> 最近变更摘要；≤25 条且 <5 日，窗外即删；可整体再生。"
              "规则见 `.owfa/plugins/hot/`，写走 `pipeline.py hot`。\n")
LOG_HEADER = ("# 运行日志\n\n> 置顶追加、只增不删；条目 = `- YYYY-MM-DD <类型> [<域>]：一句话`（域标可缺省——无域事务，log 桥）。"
              "规则见 `.owfa/plugins/log/`，写走 `pipeline.py log`。\n")
DATE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ")


def _today():
    return datetime.date.today().isoformat()


# ---------- concept pages and index / tags ----------

def _cut(text):
    return text if len(text) <= DESC_MAX else text[: DESC_MAX - 1] + "…"


def _desc(fm, body):
    d = fm.get("description")
    if d:
        return _cut(str(d))
    for line in body.splitlines():
        t = line.strip()
        if t and not t.startswith(("#", ">", "|", "```")):
            return _cut(t)
    return "（无描述）"


def concept_pages():
    """[(page full name = path minus .md, containing dir, frontmatter, description)], sorted by full name."""
    out = []
    for rel, fm, body in wikilib.walk_pages(ROOT):
        d, _, fn = rel.rpartition("/")
        if fn in ("index.md", "log.md"):
            continue  # reserved names: not concept pages
        if d == "" and fn in ROOT_RESERVED:
            continue
        if rel.startswith("archive/") or d.startswith("archive/") or d == "archive":
            continue
        if rel.startswith("tmp/") or d.startswith("tmp/") or d == "tmp":
            continue  # temporary zone: invisible to the derived layer
        out.append((rel[:-3], d, fm, _desc(fm, body)))
    return sorted(out)


def all_dirs(pages):
    """The set of directories under wiki/ that should get an index (including empty ones; excluding the archive/ subtree)."""
    dirs = {""}
    for _, d, _, _ in pages:
        parts = d.split("/") if d else []
        for i in range(len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    for dirpath, subdirs, _files in os.walk(WIKI):
        if "archive" in subdirs:
            subdirs.remove("archive")  # do not descend into the immutable region
        if "tmp" in subdirs:
            subdirs.remove("tmp")  # no index for the temporary zone
        rel = os.path.relpath(dirpath, WIKI).replace(os.sep, "/")
        dirs.add("" if rel == "." else rel)
    return dirs


def subdirs_of(d, dirs):
    """Direct subdirectory names of d (sorted)."""
    prefix = d + "/" if d else ""
    depth = d.count("/") + 1 if d else 0
    return sorted(x[len(prefix):] for x in dirs
                  if x != d and x.startswith(prefix) and x.count("/") == depth)


def _count_subtree(full, pages):
    return sum(1 for name, d, _, _ in pages if d == full or d.startswith(full + "/"))


def plan_index_dirs(pages, dirs):
    """Overflow-offloading plan: returns the set of directories that should get an index.md (the root always present).

    A directory's list = its own concept pages + pages of un-split subtrees (transparent
    inlining) + directory entry lines; on overflow, split off the subdirectories with the
    most pages (ties by name) into their own indexes until it fits. A split saves at least
    S-1 lines, so a subdirectory with S<2 is never split; an empty subtree (S=0) costs
    one inline line (the visibility line). Pure function: same structure guarantees the
    same result, no historical state.
    """
    own = {}
    for _, d, _, _ in pages:
        own[d] = own.get(d, 0) + 1

    planned = set()

    def plan(d):
        planned.add(d)
        kids = subdirs_of(d, dirs)
        sizes = {c: _count_subtree((d + "/" + c) if d else c, pages) for c in kids}
        total = own.get(d, 0) + sum(s if s > 0 else 1 for s in sizes.values())
        if total <= INDEX_MAX_ENTRIES:
            return
        for c in sorted((k for k in kids if sizes[k] >= 2),
                        key=lambda c: (-sizes[c], c)):
            if total <= INDEX_MAX_ENTRIES:
                break
            plan((d + "/" + c) if d else c)
            total -= sizes[c] - 1

    plan("")
    return planned


def visible_pages(d, pages, planned):
    """Pages listed directly in d's index: this directory's pages + all descendant pages whose path crosses no split directory (transparent inlining)."""
    pre = d + "/" if d else ""
    out = []
    for name, dd, fm, desc in pages:
        if dd == d:
            out.append((name, fm, desc))
        elif dd.startswith(pre):
            parts = dd[len(pre):].split("/")
            if all((pre + "/".join(parts[:i])) not in planned for i in range(1, len(parts) + 1)):
                out.append((name, fm, desc))
    return out


def render_index(d, pages, dirs, planned):
    """Full text of directory d's index.md (overflow-offloading scheme: reachable pages listed directly; split subdirectories as entry lines)."""
    is_root = d == ""
    lines = []
    if is_root:
        lines += ["---", f"format_version: {FORMAT_VERSION}", "---", ""]
    lines.append("# 索引" if is_root else f"# {d.rsplit('/', 1)[-1]} 索引")
    lines.append("")
    tip = ("溢出减负：本页直列可达页面；清单超窗时子目录自立索引（入口行带页数），下钻读之。"
           if is_root else "本目录索引：直列未切子树页面，已切子目录见入口行。")
    lines.append(f"> {tip}只聚合、永不手编，由 index 插件经 `pipeline.py index` 重建。")
    lines.append("")
    entries = []
    for s in subdirs_of(d, dirs):
        full = (d + "/" + s) if d else s
        n = _count_subtree(full, pages)
        if full in planned:
            entries.append(f"- [[{full}/index|{s}/]]（{n} 页）")
        elif n == 0:
            entries.append(f"- {s}/（0 页）")  # empty-subtree visibility line: no index to link, excluded from the broken-link graph
    if entries:
        lines += ["## 子目录", ""] + entries + [""]
    groups = {}
    for name, fm, desc in visible_pages(d, pages, planned):
        groups.setdefault(str(fm.get("type") or "未分类"), []).append((name, desc))
    for t in sorted(groups):
        lines.append(f"## {t}")
        lines.append("")
        for name, desc in sorted(groups[t]):
            lines.append(f"- [[{name}]] —— {desc}")
        lines.append("")
    if not entries and not groups:
        lines.append("（暂无页面）")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_tags(pages):
    tag_map = {}
    for name, d, fm, _ in pages:
        tags = fm.get("tags")
        if tags is None:
            continue
        if not isinstance(tags, list):
            tags = [tags]
        for t in tags:
            tag_map.setdefault(str(t), []).append(name)
    lines = ["# tag 索引", "",
             "> tag → 页面反向索引；只聚合、永不手编，由 index 插件经 `pipeline.py tags` 重建。", ""]
    if not tag_map:
        lines.append("（暂无）")
        lines.append("")
    for t in sorted(tag_map):
        lines.append(f"## {t}")
        lines.append("")
        for name in sorted(tag_map[t]):
            lines.append(f"- [[{name}]]")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def index_targets():
    pages = concept_pages()
    dirs = all_dirs(pages)
    planned = plan_index_dirs(pages, dirs)
    targets = {(d + "/" if d else "") + "index.md": render_index(d, pages, dirs, planned)
               for d in planned}
    return planned, targets


def write_changed(path, content):
    if os.path.exists(path) and open(path, encoding="utf-8").read() == content:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(content)
    return True


def do_index(check_only=False):
    _, targets = index_targets()
    drift, changed = [], 0
    for rel, content in sorted(targets.items()):
        path = os.path.join(WIKI, rel)
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if cur == content:
            continue
        if check_only:
            drift.append(rel)
        elif write_changed(path, content):
            changed += 1
            print(f"[index] rebuilt wiki/{rel}")
    # unplanned index.md files (old indexes after offloading merges back): delete / report drift; archive/ and tmp/ subtrees untouched
    for dirpath, subdirs, files in os.walk(WIKI):
        if "archive" in subdirs:
            subdirs.remove("archive")  # do not descend into the immutable region
        if "tmp" in subdirs:
            subdirs.remove("tmp")  # the temporary zone is outside this pipeline's jurisdiction
        if "index.md" not in files:
            continue
        rel = os.path.relpath(os.path.join(dirpath, "index.md"), WIKI).replace(os.sep, "/")
        if rel not in targets:
            if check_only:
                drift.append(rel)
            else:
                os.remove(os.path.join(WIKI, rel))
                changed += 1
                print(f"[index] removed wiki/{rel} (merged back into parent)")
    if not check_only:
        print(f"[index] done, {changed} file(s) changed (idempotent)")
    return drift


def do_tags(check_only=False):
    path = os.path.join(WIKI, "tags.md")
    content = render_tags(concept_pages())
    cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if cur == content:
        if not check_only:
            print("[tags] unchanged")
        return []
    if check_only:
        return ["tags.md"]
    write_changed(path, content)
    print("[tags] rebuilt wiki/tags.md")
    return []


# ---------- hot / log rolling ----------

def do_hot(kind, text):
    if kind not in TYPE_ORDER:
        print(f"[hot] type must be one of {'/'.join(TYPE_ORDER)} (got {kind})")
        return False
    entry = f"- {_today()} {text}"[:HOT_MAX_CHARS]
    # collect existing entries (with section membership), mechanically evict out-of-window ones
    sections = {t: [] for t in TYPE_ORDER}
    hot_path = os.path.join(WIKI, "hot.md")
    if os.path.exists(hot_path):
        cur = None
        for raw in open(hot_path, encoding="utf-8").read().splitlines():
            m = re.match(r"^##\s*Recent (\S+)", raw)
            if m and m.group(1) in TYPE_ORDER:
                cur = m.group(1)
                continue
            dm = DATE_RE.match(raw)
            if dm and cur:
                if (datetime.date.today() - datetime.date.fromisoformat(dm.group(1))).days < HOT_MAX_DAYS:
                    sections[cur].append(raw[:HOT_MAX_CHARS])
    sections[kind].insert(0, entry)  # prepend
    flat = [e for t in TYPE_ORDER for e in sections[t]]
    if len(flat) > HOT_MAX_ENTRIES:  # overall overflow: keep the 25 most recent by date uniformly (stable sort, same-day keeps section order)
        keep = set(sorted(flat, key=lambda e: e[2:12], reverse=True)[:HOT_MAX_ENTRIES])
        for t in TYPE_ORDER:
            sections[t] = [e for e in sections[t] if e in keep]
    body = [HOT_HEADER.rstrip()]
    any_entry = False
    for t in TYPE_ORDER:
        if not sections[t]:
            continue
        any_entry = True
        body += ["", f"## Recent {t}", ""] + sections[t]
    if not any_entry:
        body += ["", "（暂无）"]
    write_changed(hot_path, "\n".join(body) + "\n")
    print(f"[hot] written ({kind}), {min(len(flat), HOT_MAX_ENTRIES)} entries")
    return True


def _split_domain(args):
    """Extract --domain <domain> / --domain=<domain> from the argument list (the log bridge's domain tag); the remaining args are returned in order."""
    dom, rest, i = None, [], 0
    while i < len(args):
        if args[i] == "--domain" and i + 1 < len(args):
            dom = args[i + 1]
            i += 2
            continue
        if args[i].startswith("--domain="):
            dom = args[i].split("=", 1)[1]
            i += 1
            continue
        rest.append(args[i])
        i += 1
    return dom, rest


def do_log(kind, text, domain=None):
    if kind not in TYPE_ORDER:
        print(f"[log] type must be one of {'/'.join(TYPE_ORDER)} (got {kind})")
        return False
    log_path = os.path.join(WIKI, "log.md")
    entries = []
    if os.path.exists(log_path):
        for raw in open(log_path, encoding="utf-8").read().splitlines():
            if DATE_RE.match(raw):
                entries.append(raw)
    tag = f" [{domain}]" if domain else ""
    entries.insert(0, f"- {_today()} {kind}{tag}：{text}")  # prepend; existing entries are never rewritten
    overflow = entries[LOG_MAX_ENTRIES:]
    if overflow:  # window overflow: the oldest stretch is grouped by entry month into archive/<month>/log.md (position move only)
        for month in sorted({e[2:9] for e in overflow}):
            moved = [e for e in overflow if e[2:9] == month]
            adir = os.path.join(WIKI, "archive", month)
            apath = os.path.join(adir, "log.md")
            old = open(apath, encoding="utf-8").read() if os.path.exists(apath) else f"# 归档 {month}\n"
            write_changed(apath, old.rstrip() + "\n" + "\n".join(moved) + "\n")
            print(f"[log] archived {len(moved)} entries to wiki/archive/{month}/log.md")
    write_changed(log_path, LOG_HEADER + "\n" + "\n".join(entries[:LOG_MAX_ENTRIES]) + "\n")
    print(f"[log] written ({kind}), main file {min(len(entries), LOG_MAX_ENTRIES)} entries")
    return True


# ---------- post-write self-attestation ----------

def do_verify():
    ok = True
    r = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "owfa_kernel.py"), "audit"])
    if r.returncode != 0:
        ok = False
        print("[verify] plugin audit has errors")
    drift = do_index(check_only=True) + do_tags(check_only=True)
    if drift:
        ok = False
        print("[verify] derived drift: " + ", ".join("wiki/" + d for d in drift) + " (run pipeline.py index / tags to fix)")
    else:
        print("[verify] derived area consistent")
    print("[verify] " + ("passed" if ok else "failed"))
    return 0 if ok else 1


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "index":
        do_index()
        return 0
    if cmd == "tags":
        do_tags()
        return 0
    if cmd == "hot":
        return 0 if do_hot(sys.argv[2], " ".join(sys.argv[3:])) else 1
    if cmd == "log":
        dom, rest = _split_domain(sys.argv[3:])
        return 0 if do_log(sys.argv[2], " ".join(rest), domain=dom) else 1
    if cmd == "verify":
        return do_verify()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
