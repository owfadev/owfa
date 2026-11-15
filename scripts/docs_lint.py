#!/usr/bin/env python3
"""docs_lint.py — structural documentation guards (single-source discipline, kernel.md §2.3).

Machine-checkable shape rules only; whether docs tell the truth about behavior
stays with fresh-context review. Checks:

  1. dead-path: repo-relative paths referenced in backticks in the doc set
     must exist on disk (catches pointers at retired layouts);
  2. version-literal: vX.Y.Z literals in the doc set must match .owfa/VERSION
     when they appear in a "current release" context line (heuristic: the line
     also matches current/release/当前/现行);
  3. mirror: en/zh mirrored docs must have identical heading sets.

Usage: python3 scripts/docs_lint.py [--root DIR] [--docs SUBPATH ...]
Exit 0 clean; 1 with findings. Messages one per line, `file:line rule message`.
"""
import argparse
import os
import re
import sys

PATHLIKE = re.compile(r"`(\.[\w./-]+(?:\.\w+)?)`")   # `./x`, `.owfa/...`, `.github/...`
# paths that live in an INSTALLED tree, not the framework repo itself — legit in docs

VERSION = re.compile(r"v(\d+\.\d+\.\d+)")
CURRENT_CTX = re.compile(r"current( release)?|latest|当前版本|现行版本", re.I)
HEADING = re.compile(r"^(#{1,4}) (.+)$", re.M)
# path prefixes that live in an INSTALLED tree, not the framework repo — legit in docs
RUNTIME_PREFIXES = (
    ".owfa/workspace.yaml", ".owfa/plugins", ".owfa/migrations", ".owfa/kernel-journal",
    ".owfa/registry-cache", ".owfa/protocol", ".owfa/command", ".agents/skills",
)


def runtime_path(p):
    return p.lower().startswith(RUNTIME_PREFIXES)


def lint(root, docs):
    issues = []
    version_file = os.path.join(root, ".owfa", "VERSION")
    current = open(version_file, encoding="utf-8").read().strip() if os.path.isfile(version_file) else None
    files = []
    for sub in docs:
        base = os.path.join(root, sub)
        if os.path.isfile(base):
            files.append((sub, base))
        elif os.path.isdir(base):
            for dirpath, _dirs, names in os.walk(base):
                for n in sorted(names):
                    if n.endswith((".md", ".yaml", ".yml")):
                        rel = os.path.relpath(os.path.join(dirpath, n), root)
                        files.append((rel, os.path.join(dirpath, n)))

    en_zh = {}
    for rel, path in files:
        text = open(path, encoding="utf-8").read()
        historical = "docs-lint: historical" in text[:400]   # narrative about past layouts — dead paths are the point
        for i, line in enumerate(text.splitlines(), 1):
            for m in PATHLIKE.finditer(line):
                p = m.group(1).rstrip("/")
                if "/" not in p and not runtime_path(p):
                    continue   # `.tgz`-style suffix tokens are not paths
                target = os.path.normpath(os.path.join(root, p))
                if not historical and not runtime_path(p) and not os.path.exists(target):
                    issues.append(f"{rel}:{i} dead-path `{p}` does not exist on disk")
            if current and CURRENT_CTX.search(line):
                for m in VERSION.finditer(line):
                    if m.group(1) != current:
                        issues.append(
                            f"{rel}:{i} version-literal v{m.group(1)} != .owfa/VERSION {current} in a current-release line")
        if "/zh/" in rel or rel.startswith("zh/"):
            en = rel.replace("/zh/", "/").replace("zh/", "", 1)
            en_zh[rel] = en

    for zh_rel, en_rel in en_zh.items():
        zh_path, en_path = os.path.join(root, zh_rel), os.path.join(root, en_rel)
        if not os.path.isfile(en_path):
            continue  # zh-only doc, no mirror contract
        strip_code = lambda t: re.sub(r"```.*?```", "", t, flags=re.S)
        h_zh = HEADING.findall(strip_code(open(zh_path, encoding="utf-8").read()))
        h_en = HEADING.findall(strip_code(open(en_path, encoding="utf-8").read()))
        if [h[0] for h in h_zh] != [h[0] for h in h_en]:
            issues.append(f"{zh_rel} mirror heading levels differ from {en_rel} "
                          f"(zh {len(h_zh)} vs en {len(h_en)} headings)")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--docs", nargs="+", default=[".owfa/docs", "README.md", "README.zh-CN.md"])
    args = ap.parse_args()
    issues = lint(args.root, args.docs)
    for i in issues:
        print(i)
    print(f"docs_lint: {len(issues)} finding(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
