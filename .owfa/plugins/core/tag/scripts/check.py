#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tag plugin attached audit: mechanical items (per-page count cap / restating type / hierarchy depth).

Near-duplicate tags are a semantic item (cross-language synonyms are not decidable at the string level), under the check command.
"""


def check(ctx):
    issues = []
    for rel, fm, body in ctx.pages:
        tags = fm.get("tags")
        if tags is None:
            continue
        if not isinstance(tags, list):
            tags = [tags]
        if len(tags) > 5:
            issues.append({"level": "warning", "message": f"{rel}: {len(tags)} tags (>5 soft cap)"})
        ptype = fm.get("type")
        if ptype and ptype in tags:
            issues.append({"level": "warning", "message": f"{rel}: tag restates type ({ptype})"})
        for t in tags:
            s = str(t)
            if "/" in s:
                parts = s.split("/")
                if len(parts) > 2 or any(not p.strip() for p in parts):
                    issues.append({"level": "warning", "message": f"{rel}: tag hierarchy over limit or empty segment ({s}, parent/child ≤2)"})
    return issues
