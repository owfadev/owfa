#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""log plugin attached audit: mechanical items (entry date contract).

Auditing modification of historical entries relies on git traces (semantic item, under the check command); capacity archiving is converged by the write pipeline.
"""
import re

DATE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2} ")


def check(ctx):
    issues = []
    for rel, _fm, body in ctx.pages:
        if rel != "log.md" and not (rel.startswith("archive/") and rel.endswith("/log.md")):
            continue
        for i, raw in enumerate(body.splitlines(), 1):
            line = raw.rstrip()
            if line.startswith("- ") and not DATE_RE.match(line):
                issues.append({"level": "error", "message": f"{rel}:{i}: entry missing date ({line[:40]}…)"})
    return issues
