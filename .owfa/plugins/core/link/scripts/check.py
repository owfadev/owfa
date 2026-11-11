#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""link plugin attached audit: mechanical items (broken links / garbled text / alias ambiguity / orphans / one-way related).

The in-link density top list (evidence for hub emergence) is an analytical item, under the check command's semantic items.
Concept-page determination is isomorphic to the pipeline: reserved names (index/log), wiki-root derived pages (hot/tags),
the archive/ subtree and the tmp/ temporary zone are not link sources and are exempt from graph checks (derived pages link
to everything, otherwise orphans would never trigger; a broken link in a draft = not yet written down, closed upon promotion).
hot is the only derived page with handwritten links: its broken links are checked, but it is not an in-link source and stays
out of the orphan graph.
Territory-value pages (registry type.values except session — the mechanical-registry kind) having no in-links yet is the
registry norm: orphans are downgraded to info level there, while native pages (notes knowledge pages) stay warning. The
territory value set is read dynamically from registry, so new territory types are covered automatically — no per-type upkeep.
"""
import os
import re

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
RESERVED_NAMES = {"index.md", "log.md"}
ROOT_DERIVED = {"hot.md", "tags.md"}


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _name_of(rel):
    return rel[:-3] if rel.endswith(".md") else rel


def _concept(rel):
    d, _, fn = rel.rpartition("/")
    if fn in RESERVED_NAMES:
        return False
    if d == "" and fn in ROOT_DERIVED:
        return False
    if rel.startswith("tmp/") or d.startswith("tmp/") or d == "tmp":
        return False  # temporary zone: not a link source, exempt from graph checks (draft broken-link exemption)
    return not (rel.startswith("archive/") or d.startswith("archive/") or d == "archive")


def _target(text):
    """related item or wikilink text → target full name (tolerates both [[x|display]] and bare-name forms)."""
    return str(text).strip().lstrip("[").split("|")[0].strip().rstrip("]")


TERRITORY_LABELS = {"source": "proxy page", "lark": "pointer page", "calendar": "time page",
                    "structure": "declaration page", "todo": "delegation page", "profile": "profile page", "project": "project page"}


def _territory_types(root):
    """Read registry type.values (closed set of territory values) dynamically; session excluded (knowledge backbone, orphan hint is meaningful there)."""
    try:
        text = open(os.path.join(root, ".meta", "protocol", "registry.yaml"), encoding="utf-8").read()
        m = re.search(r"values: \[([^\]]+)\]", text)
        return {v.strip() for v in m.group(1).split(",") if v.strip()} - {"session"}
    except OSError:
        return set(TERRITORY_LABELS)


def check(ctx):
    issues = []
    pages = list(ctx.pages)
    names = {_name_of(rel) for rel, _fm, _b in pages}
    # alias table and ambiguity (error: makes [[alias]] resolution indeterminate)
    alias_map = {}
    for rel, fm, _b in pages:
        for a in _as_list(fm.get("aliases")):
            alias_map.setdefault(str(a).strip(), set()).add(_name_of(rel))
    for a, owners in sorted(alias_map.items()):
        if len(owners) > 1:
            issues.append({"level": "error", "message": f"alias {a!r} ambiguous: {', '.join(sorted(owners))} — resolution indeterminate, needs adjudication"})
    referenced, related_map = set(), {}
    for rel, fm, body in pages:
        if not _concept(rel):
            continue
        src = _name_of(rel)
        for m in WIKILINK_RE.finditer(body):
            t = m.group(1).strip()
            if "\ufffd" in t:
                issues.append({"level": "error", "message": f"{rel}: garbled link [[{m.group(1)}]]"})
            elif t not in names and t not in alias_map:
                issues.append({"level": "warning", "message": f"{rel}: broken link [[{t}]] (neither a page full name nor any aliases)"})
            referenced.add(t)
        rels = [_target(r) for r in _as_list(fm.get("related"))]
        related_map[src] = {t for t in rels if t}
        for t in rels:
            if "\ufffd" in t:
                issues.append({"level": "error", "message": f"{rel}: related garbled item {t!r}"})
            elif t not in names and t not in alias_map:
                issues.append({"level": "warning", "message": f"{rel}: related broken link [[{t}]]"})
            referenced.add(t)
    # hot: handwritten-link surface (broken links checked; not an in-link source, out of the orphan graph)
    for rel, _fm, body in pages:
        if _name_of(rel) != "hot":
            continue
        for m in WIKILINK_RE.finditer(body):
            t = m.group(1).strip()
            if "\ufffd" in t:
                issues.append({"level": "error", "message": f"{rel}: garbled link [[{m.group(1)}]]"})
            elif t not in names and t not in alias_map:
                issues.append({"level": "warning", "message": f"{rel}: hot broken link [[{t}]] (handwritten summary link no longer valid)"})
    # orphans (no in-links and no related references; sources count concept pages only; territory-value registry pages downgraded to info)
    territory = _territory_types(ctx.root)
    for rel, fm, _b in pages:
        if not _concept(rel):
            continue
        if _name_of(rel) not in referenced:
            ptype = fm.get("type")
            if ptype in territory:
                label = TERRITORY_LABELS.get(ptype, "territory page")
                issues.append({"level": "info", "message": f"{rel}: {label} has no in-links yet (registry norm, not an alert)"})
            else:
                issues.append({"level": "warning", "message": f"{rel}: orphan page (no in-links and no related references)"})
    # related one-way (informational: asymmetry hint, not an error)
    for src, rels in sorted(related_map.items()):
        for t in sorted(rels):
            if t in related_map and src not in related_map[t]:
                issues.append({"level": "info", "message": f"{src}: related one-way (lists [[{t}]], other side does not list back)"})
    return issues
