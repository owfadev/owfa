#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""language plugin attached audit: declaration page existence, territory misplacement, empty terms values.

A missing declaration page = tolerated default posture (legal, info); an empty terms value is a registry defect.
"""


def check(ctx):
    issues = []
    decl = False
    for rel, fm, _body in ctx.pages:
        if fm.get("type") == "language" and rel != "language.md":
            issues.append({"level": "error", "message": f"{rel}: type: language outside the declaration page (territory misplacement)"})
        if rel == "language.md":
            decl = True
            terms = fm.get("terms") or {}
            for k, v in terms.items():
                if not str(v).strip():
                    issues.append({"level": "warning", "message": f"terms empty value: {k} (translated name missing; fill in or remove)"})
    if not decl:
        issues.append({"level": "info", "message": "no language declaration page (default posture tolerated)"})
    return issues
