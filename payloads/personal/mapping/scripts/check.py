#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mapping plugin attached audit: mirror diff, registry-field completeness, raw_file dangling, hash verification, suspected full-text copies, stub aging.

Read-only report — repair actions such as hash recalculation belong to the command (actions.md mechanical automatic items); the attached audit does not execute them.
Parameter basis: forensic evidence from the original library (40% hash mismatch, 33% full-text copies) and the progressive-enrichment promise (new stubs exempt from alerts).
"""
import datetime
import hashlib
import os
import re

TODAY = datetime.date.today()


def _file_set(root, sub, strip_md):
    """Collect the file set under a subdirectory (ignore .gitkeep); when strip_md, collect md only and strip the suffix (proxy page set)."""
    out = set()
    base = os.path.join(root, sub)
    for dirpath, dirs, files in os.walk(base):
        dirs.sort()
        for fn in sorted(files):
            if fn == ".gitkeep":
                continue
            if strip_md and fn == "index.md":
                continue  # directory index: navigation-layer reserved name (per-directory by the index plugin), not a concept page, no counterpart
            if strip_md and not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), base).replace(os.sep, "/")
            out.add(rel[:-3] if strip_md else rel)
    return out


def _ref_count(ctx, full):
    """Count references across the whole library pointing to full (page full name): body wikilinks + related field."""
    n = 0
    pat = re.compile(r"\[\[([^\]\|#]+)")
    for _rel, fm, body in ctx.pages:
        for m in pat.finditer(str(body)):
            if m.group(1).strip() == full:
                n += 1
        for r in (fm.get("related") or []):
            if str(r).strip() == full:
                n += 1
    return n


def check(ctx):
    issues = []
    root = ctx.root
    real = _file_set(root, "vault", strip_md=False)
    proxy = _file_set(root, os.path.join("wiki", "vault"), strip_md=True)
    for f in sorted(real - proxy):
        issues.append({"level": "info", "message": f"vault pending registration (backlog): {f}"})
    for p in sorted(proxy - real):
        refs = _ref_count(ctx, f"vault/{p}")
        note = f", referenced from {refs} places" if refs else ", no references"
        issues.append({"level": "error", "message": f"orphan proxy (no vault counterpart{note}): wiki/vault/{p}"})
    for rel, fm, body in ctx.pages:
        if not rel.startswith("vault/"):
            continue
        if os.path.basename(rel) == "index.md":
            continue  # directory index: navigation-layer reserved name, not a proxy page
        rf = fm.get("raw_file")
        if not rf:
            issues.append({"level": "error", "message": f"{rel}: missing registry field raw_file (mandatory on proxy pages)"})
            continue
        if not fm.get("raw_sha256"):
            issues.append({"level": "error", "message": f"{rel}: missing registry field raw_sha256 (mandatory on proxy pages)"})
        fp = os.path.join(root, rf)
        if not os.path.exists(fp):
            issues.append({"level": "error", "message": f"{rel}: raw_file points to a nonexistent file ({rf})"})
            continue
        sh = fm.get("raw_sha256")
        if sh and hashlib.sha256(open(fp, "rb").read()).hexdigest() != sh:
            issues.append({"level": "warning", "message": f"{rel}: raw_sha256 mismatch (source file changed; if the description still applies, recalculate mechanically)"})
        if rf.endswith(".md"):
            try:
                raw_text = open(fp, encoding="utf-8").read()
            except UnicodeDecodeError:
                raw_text = open(fp, encoding="utf-8", errors="replace").read()
            if raw_text and len(body) >= 0.8 * len(raw_text):
                issues.append({"level": "warning", "message": f"{rel}: suspected full-text copy (body ≥80% of the source; diary-type exemption is a semantic judgment)"})
        if not body.strip():  # stub: body has no one-line description
            m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(fm.get("updated") or ""))
            if m:
                age = (TODAY - datetime.date(*map(int, m.groups()))).days
                if age > 90:
                    issues.append({"level": "warning", "message": f"{rel}: stub over 90 days without a description (new stubs exempt)"})
    return issues
