#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trust plugin attached audit: mechanical items (trust-field contract / stale list / trust watermark).

Triage of stale pages (refresh stale_after, re-verify, or deprecate) is a semantic item, under the check command.
"""
import datetime
import re

ACTOR_RE = re.compile(r"^(human:.+|process:.+|agent/.+)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _bad_actor(val):
    return not ACTOR_RE.match(str(val))


def _bad_date(val):
    s = str(val)
    if not DATE_RE.match(s):
        return True
    try:  # calendar validity (dates like 2026-13-99 that match the format but are not real dates)
        datetime.date.fromisoformat(s)
        return False
    except ValueError:
        return True


def check(ctx):
    issues = []
    today = datetime.date.today()
    reviewed = confirmed = 0
    for rel, fm, body in ctx.pages:
        gen = fm.get("generated")
        verified = fm.get("verified")
        stale_after = fm.get("stale_after")
        if gen is not None:
            if not isinstance(gen, dict):
                issues.append({"level": "warning", "message": f"{rel}: generated should be a block mapping by/at"})
            elif gen.get("by") is None or gen.get("at") is None:
                issues.append({"level": "warning", "message": f"{rel}: generated missing by or at"})
            else:
                if _bad_actor(gen["by"]):
                    issues.append({"level": "warning", "message": f"{rel}: generated.by {gen['by']!r} does not match the actor convention"})
                if _bad_date(gen["at"]):
                    issues.append({"level": "warning", "message": f"{rel}: generated.at {gen['at']!r} not YYYY-MM-DD"})
        if verified is not None:
            events = verified if isinstance(verified, list) else [verified]
            has_human = False
            for ev in events:
                text = ev if isinstance(ev, str) else str(ev)
                m_by = re.search(r"by:\s*(.+?)(?:\s*,\s*at:|$)", text)
                m_at = re.search(r"at:\s*(\S+)", text)
                if not m_by or not m_at:
                    issues.append({"level": "warning", "message": f"{rel}: verified event missing by or at ({text.strip()!r})"})
                    continue
                by, at = m_by.group(1).strip(), m_at.group(1).rstrip(",");  # tolerate trailing comma
                if _bad_actor(by):
                    issues.append({"level": "warning", "message": f"{rel}: verified.by {by!r} does not match the actor convention"})
                if _bad_date(at):
                    issues.append({"level": "warning", "message": f"{rel}: verified.at {at!r} not YYYY-MM-DD"})
                if by.startswith("human:"):
                    has_human = True
            if has_human:
                reviewed += 1
            else:
                confirmed += 1
        if stale_after is not None:
            if _bad_date(stale_after):
                issues.append({"level": "warning", "message": f"{rel}: stale_after {stale_after!r} not YYYY-MM-DD"})
            elif datetime.date.fromisoformat(str(stale_after)) <= today:
                issues.append({"level": "info", "message": f"{rel}: past stale_after ({stale_after}) — stale page, disposal belongs to the human"})
        if fm.get("sources") is not None and not isinstance(fm.get("sources"), list):
            issues.append({"level": "warning", "message": f"{rel}: sources should be a list"})
    if reviewed or confirmed:
        issues.append({"level": "info", "message": f"trust watermark: human-reviewed {reviewed} pages / machine-confirmed {confirmed} pages (the rest unverified)"})
    return issues
