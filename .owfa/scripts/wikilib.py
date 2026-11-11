#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiki page-service load-bearing piece: frontmatter parsing and page traversal, assembled into ctx for the attached-audit runtime.

Plugin attached-audit scripts do not import this module themselves —
owfa_kernel.audit scans wiki/ in a single pass and puts the (relative path,
frontmatter, body) list into ctx.pages for everyone to share (frugal invocation).
The same minimal YAML subset as owfa_kernel.parse_manifest, but with a
different tolerance policy: manifests fail loudly (protocol artifacts), page
frontmatter skips bad lines (user content must not crash attached audits over
format blemishes). Keys are lenient (anything non-blank and colon-free):
block-mapping subkeys may be directory names, Chinese, etc. (a proven need of the
structure declaration page); top-level protocol fields remain ASCII.
"""
import os
import re


def _strip_quotes(s):
    return s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s


def _strip_comment(s):
    return re.split(r"\s+#", s, maxsplit=1)[0].strip()


def parse_frontmatter(text):
    """Parse the minimal YAML subset inside the --- fence; returns an empty dict without a fence, skips bad lines."""
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    data, target = {}, None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            item = _strip_quotes(_strip_comment(raw.strip()[2:]).strip())
            if not isinstance(data.get(target), list):
                data[target] = []
            data[target].append(item)
            continue
        mm = re.match(r"^(\s*)([^:\s][^:]*):\s*(.*)$", raw)
        if not mm:
            continue
        key, val = mm.group(2), _strip_comment(mm.group(3))
        if mm.group(1):
            if not isinstance(data.get(target), dict):
                data[target] = {}
            data[target][key] = _strip_quotes(val)
        else:
            target = key
            if val == "":
                data[key] = None
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                # strip whitespace before unquoting tokens: in [ai, llm] the second item carries a leading space; not stripping it fragments the vocabulary
                data[key] = ([_strip_quotes(v.strip()) for v in inner.split(",") if v.strip()]
                             if inner else [])
            else:
                data[key] = _strip_quotes(val)
    return data


def walk_pages(root):
    """Walk all md pages under wiki/, yielding (wiki-relative path, frontmatter dict, body str)."""
    wiki = os.path.join(root, "wiki")
    for dirpath, dirs, files in os.walk(wiki):
        dirs.sort()
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                text = open(p, encoding="utf-8").read()
            except UnicodeDecodeError:
                text = open(p, encoding="utf-8", errors="replace").read()
            m = re.match(r"^---\n.*?\n---\n?", text, re.S)
            rel = os.path.relpath(p, wiki).replace(os.sep, "/")
            yield rel, parse_frontmatter(text), (text[m.end():] if m else text)
