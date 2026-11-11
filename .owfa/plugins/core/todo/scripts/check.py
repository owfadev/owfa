#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""todo plugin attached audit: mechanical items (territory placement / entry contract / overdue list).

Entry shape per the manifest: `- [ ] <trigger: date YYYY-MM-DD or context phrase>: one sentence (by: <actor>, at: <date>)`.
Bloat triage (open entries > 50) is a semantic item, under the check command.
"""
import datetime
import re

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(ctx):
    issues = []
    today = datetime.date.today()
    todo_page = None
    for rel, fm, _body in ctx.pages:
        if fm.get("type") == "todo" and rel != "todo.md":
            issues.append({"level": "error", "message": f"{rel}: type: todo outside wiki/todo.md (territory misplacement)"})
        if rel == "todo.md":
            todo_page = _body
    if todo_page is None:
        return issues  # page absent = the no-delegation norm, nothing to check
    for i, raw in enumerate(todo_page.splitlines(), 1):
        line = raw.rstrip()
        if not line.startswith("- [ ]"):
            continue  # settled entries ([x]) and non-entry lines are out of scope
        rest = line[len("- [ ]"):].strip()
        # strip the trailing (by: …, at: …) parenthetical first, so its colons cannot be mistaken for the trigger separator
        meta = ""
        m = re.search(r"\(([^()]*)\)\s*$", rest)
        if m and ("by:" in m.group(1) or "at:" in m.group(1)):
            meta = m.group(1)
            rest = rest[: m.start()].strip()
        trig, sep, tail = rest.partition(":")
        trig = trig.strip()
        if not sep or not trig:
            issues.append({"level": "warning", "message": f"todo.md:{i}: entry missing trigger condition ({line[:40]}…)"})
        scope = meta or tail
        if not re.search(r"by:\s*\S", scope):
            issues.append({"level": "warning", "message": f"todo.md:{i}: entry missing by ({line[:40]}…)"})
        if not re.search(r"at:\s*\S", scope):
            issues.append({"level": "warning", "message": f"todo.md:{i}: entry missing at ({line[:40]}…)"})
        if trig and sep and DATE_RE.match(trig):
            try:
                if datetime.date.fromisoformat(trig) < today:
                    issues.append({"level": "info", "message": f"todo.md:{i}: overdue and unsettled entry ({trig}: {tail[:40]}…)"})
            except ValueError:
                issues.append({"level": "warning", "message": f"todo.md:{i}: trigger date not a real calendar date ({trig})"})
    return issues
