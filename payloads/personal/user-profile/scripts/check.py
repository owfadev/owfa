#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""user-profile plugin attached audit: mechanical items (territory placement / page presence).

Assertion evidence-wikilink grading is a semantic item, under the check command.
"""


def check(ctx):
    issues = []
    present = False
    for rel, fm, _body in ctx.pages:
        if fm.get("type") == "profile":
            if rel.startswith("notes/") or rel.startswith("vault/"):
                issues.append({"level": "error", "message": f"{rel}: type: profile in the wrong territory (single-page territory, wiki/profile.md only)"})
            if rel == "profile.md":
                present = True
    if not present:
        issues.append({"level": "info", "message": "no profile page (the untriggered norm; profile self-creates on first trigger)"})
    return issues
