#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""instance-git attached audit: read-only checks of the snapshot-contract red lines.

Never writes, never prompts. Four checks:
1. ignore-rule vs tracked-file residue (files matching an ignore rule yet still tracked)
2. credential-pattern filenames among tracked files
3. sensitive faces (vault/, cuhksz/) tracked while a remote is configured
4. projects/*/ self-git repos tracked by the parent
Not a git repository at the root -> contract dormant, one info line.
"""
import fnmatch
import os
import subprocess

IGNORE_BASE = ["*.ses", ".env", ".env.*", "*cookie*", "*secret*", "credentials*", "*.pem"]
SENSITIVE_TOP = {"vault", "cuhksz"}


def _git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=30)


def _ignore_rules(root):
    """Parse the root .gitignore: non-negated patterns only, trailing slashes stripped."""
    path = os.path.join(root, ".gitignore")
    rules = []
    if not os.path.exists(path):
        return rules
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        rules.append(line.rstrip("/"))
    return rules


def _matches_rule(rel, rule):
    """Directory-prefix or fnmatch, mirroring gitignore spirit closely enough for an audit."""
    if fnmatch.fnmatch(rel, rule) or fnmatch.fnmatch(rel, rule + "/*"):
        return True
    parts = rel.split("/")
    for i in range(1, len(parts)):
        if fnmatch.fnmatch("/".join(parts[:i]), rule):
            return True
    return False


def check(ctx):
    issues = []
    root = ctx.root
    if not os.path.exists(os.path.join(root, ".git")):
        issues.append({"level": "info", "message": "instance-git: no .git at the root — snapshot contract dormant"})
        return issues
    tracked = [l for l in _git(root, "ls-files").stdout.splitlines() if l.strip()]
    if not tracked:
        issues.append({"level": "info", "message": "instance-git: nothing tracked — snapshot contract dormant"})
        return issues
    # 1. ignore vs tracked residue
    rules = _ignore_rules(root)
    residue = sorted({rel for rel in tracked for rule in rules if _matches_rule(rel, rule)})
    if residue:
        issues.append({"level": "warning", "message": "instance-git: ignored-but-tracked residue (sweep out: git rm --cached) — " + ", ".join(residue[:6]) + (" …" if len(residue) > 6 else "")})
    # 2. credential patterns
    hits = sorted({rel for rel in tracked for pat in IGNORE_BASE if fnmatch.fnmatch(os.path.basename(rel), pat)})
    if hits:
        issues.append({"level": "warning", "message": "instance-git: credential-pattern files tracked (red line 1) — " + ", ".join(hits[:6])})
    # 3. sensitive faces + remote
    remotes = _git(root, "remote").stdout.split()
    tops = {rel.split("/")[0] for rel in tracked if "/" in rel}
    if remotes and tops & SENSITIVE_TOP:
        issues.append({"level": "warning", "message": f"instance-git: remote(s) configured ({', '.join(remotes)}) while sensitive faces ({', '.join(sorted(tops & SENSITIVE_TOP))}/) are tracked — confirm private; public remotes are out of the question"})
    # 4. entity self-git tracked by the parent (a gitlink shows as bare "projects/<name>", a stray add as "projects/<name>/...")
    pdir = os.path.join(root, "projects")
    if os.path.isdir(pdir):
        for name in sorted(os.listdir(pdir)):
            if os.path.isdir(os.path.join(pdir, name, ".git")):
                leaked = [rel for rel in tracked if rel == f"projects/{name}" or rel.startswith(f"projects/{name}/")]
                if leaked:
                    issues.append({"level": "warning", "message": f"instance-git: projects/{name}/ keeps its own git yet {len(leaked)} entr{'y' if len(leaked) == 1 else 'ies'} tracked by the parent (red line 3 — disclose, never host)"})
    return issues


if __name__ == "__main__":
    import types as _t
    _r = check(_t.SimpleNamespace(root=os.getcwd(), pages=[]))
    if not _r:
        print("instance-git attached audit: all clean")
    for _i in _r:
        print(_i["level"] + ": " + _i["message"])
