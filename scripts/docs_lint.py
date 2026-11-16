#!/usr/bin/env python3
"""docs_lint.py — structural documentation guards (single-source discipline, kernel.md §2.3).

Machine-checkable shape rules only; whether docs tell the truth about behavior
stays with fresh-context review. Checks:

  1. dead-path: repo-relative paths referenced in backticks in the doc set
     must exist on disk (dot-prefixed `.owfa/...` and known top-level names
     alike — inside tables too); runtime prefixes that only exist in installed
     trees are allowlisted; `docs-lint: historical` in the first 400 chars
     exempts narrative docs about past layouts;
  2. version-literal: vX.Y.Z literals must match .owfa/VERSION when they appear
     in a "current release" context line;
  3. mirror: en/zh mirrored docs must have identical heading-level sequences;
  4. changelog: a PLUGIN.md carrying a `## Changelog` section must have its top
     entry version equal the sibling PLUGIN.yaml `version:` (member manifests
     live beside it in package repos; in this repo the check is a no-op unless
     such pairs exist);
  5. snapshot: a doc line `<!-- docs-lint: snapshot YYYY-MM-DD -->` older than
     90 days emits an info-level reminder to re-verify the stated facts.

Usage: python3 scripts/docs_lint.py [--root DIR] [--docs SUBPATH ...]
Exit 0 clean; 1 with findings. Messages one per line, `file:line rule message`.
"""
import argparse
import datetime as dt
import os
import re
import sys

# dot-prefixed and named-root paths both count (`./x`, `.owfa/...`, `.github/...`, `wiki/...`, `scripts/...`)
PATHLIKE = re.compile(r"`(\.{0,2}/?[\w.-]+(?:/[\w.{}$-]+)+/?)`")
KNOWN_ROOTS = {"wiki", "vault", "scripts", "test", "bin", "payloads", "docs", "templates", "connectors", "migrations", "package.json", "README.md"}
VERSION = re.compile(r"v(\d+\.\d+\.\d+)")
CURRENT_CTX = re.compile(r"current( release)?|latest|当前版本|现行版本", re.I)
HEADING = re.compile(r"^(#{1,4}) (.+)$", re.M)
SNAPSHOT = re.compile(r"<!--\s*docs-lint: snapshot (\d{4}-\d{2}-\d{2})\s*-->")
# path prefixes that live in an INSTALLED tree, not the framework repo — legit in docs
RUNTIME_PREFIXES = (
    ".owfa/workspace.yaml", ".owfa/plugins", ".owfa/migrations", ".owfa/kernel-journal",
    ".owfa/registry-cache", ".owfa/protocol", ".owfa/command", ".agents/skills",
    "wiki/", "vault/", "scripts/check.py",
)
VER_KEY = re.compile(r"^version:\s*([0-9.]+)\s*$", re.M)


def runtime_path(p):
    return p.lower().startswith(RUNTIME_PREFIXES)


def is_pathlike(p):
    p = p.rstrip("/")
    if "/" not in p:
        return p in KNOWN_ROOTS
    root = p.split("/", 1)[0].lstrip(".")
    return p.startswith(".") or root in KNOWN_ROOTS or p.startswith(("./", "../"))


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
        historical = "docs-lint: historical" in text[:400]
        for i, line in enumerate(text.splitlines(), 1):
            for m in PATHLIKE.finditer(line):
                p = m.group(1)
                if not is_pathlike(p):
                    continue
                target = os.path.normpath(os.path.join(root, p))
                if not historical and not runtime_path(p) and not os.path.exists(target):
                    issues.append(f"{rel}:{i} dead-path `{p}` does not exist on disk")
            if current and CURRENT_CTX.search(line):
                for m in VERSION.finditer(line):
                    if m.group(1) != current:
                        issues.append(
                            f"{rel}:{i} version-literal v{m.group(1)} != .owfa/VERSION {current} in a current-release line")
        m = SNAPSHOT.search(text)
        if m:
            age = (dt.date.today() - dt.date.fromisoformat(m.group(1))).days
            if age > 90:
                print(f"{rel}:1 snapshot dated {m.group(1)} ({age}d old) — re-verify the stated facts (info; non-gating)")

        # rule 4: changelog top entry == sibling manifest version
        if os.path.basename(path) == "PLUGIN.md":
            yaml_path = os.path.join(os.path.dirname(path), "PLUGIN.yaml")
            if os.path.isfile(yaml_path) and "## Changelog" in text:
                ym = VER_KEY.search(open(yaml_path, encoding="utf-8").read())
                tail = text.split("## Changelog", 1)[1]
                first = next((l for l in tail.splitlines() if l.strip()), "")
                fm = re.search(r"(\d+\.\d+(?:\.\d+)?)", first)
                norm = lambda v: ".".join(v.split(".")[:2]) if v.count(".") > 1 and v.split(".")[-1] == "0" else v
                if ym and fm and norm(ym.group(1)) != norm(fm.group(1)):
                    issues.append(f"{rel}:1 changelog top entry {fm.group(1)} != PLUGIN.yaml version {ym.group(1)}")

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
