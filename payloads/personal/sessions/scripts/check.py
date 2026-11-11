#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sessions plugin attached audit: mechanical items (territory boundary / participants contract).

Whether a backbone page should have been promoted but was not is a semantic item (bloat judgment), under the check command.
"""
import re

ACTOR_RE = re.compile(r"^(human:.+|process:.+|agent/.+)$")


def check(ctx):
    issues = []
    for rel, fm, body in ctx.pages:
        if rel.endswith("/index.md") or rel == "index.md":
            continue  # derived pages are not backbone pages and take no part in territory determination
        ptype = fm.get("type")
        in_sessions = rel.startswith("sessions/")
        if ptype == "session" and not in_sessions:
            issues.append({"level": "warning", "message": f"{rel}: session-type page should live under wiki/sessions/ (sessions plugin territory)"})
        elif in_sessions and ptype != "session":
            issues.append({"level": "warning", "message": f"{rel}: pages under wiki/sessions/ should be type: session (actually {ptype or 'untyped'})"})
        if ptype == "session" or in_sessions:
            parts = fm.get("participants")
            if parts is None:
                issues.append({"level": "warning", "message": f"{rel}: missing participants (actor list)"})
            else:
                if not isinstance(parts, list):
                    parts = [parts]
                for p in parts:
                    if not ACTOR_RE.match(str(p)):
                        issues.append({"level": "warning", "message": f"{rel}: participants item {p!r} does not match the actor convention (human:name / process:name / agent/model)"})
    return issues
