#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""device plugin attached audit: scan device profile pages for warranty_until near-expiry and expiry.

Near-expiry window is 30 days (hardcoded, adjust as we go); disposal goes through todo upon confirmation — this script only reports.
"""
from datetime import date


def check(ctx):
    issues = []
    today = date.today()
    for rel, fm, _body in ctx.pages:
        dev = fm.get("device")
        if not dev or not isinstance(dev, dict):
            continue
        wu = str(dev.get("warranty_until") or "").strip()
        if not wu:
            continue
        try:
            due = date.fromisoformat(wu)
        except ValueError:
            issues.append({"level": "warning", "message": f"{rel}: warranty_until invalid date: {wu}"})
            continue
        if due < today:
            issues.append({"level": "warning", "message": f"{rel}: warranty/coverage expired {wu} (add to todo upon confirmation for disposal)"})
        elif (due - today).days <= 30:
            issues.append({"level": "warning", "message": f"{rel}: warranty/coverage near-expiry {wu} (≤30 days; add to todo upon confirmation for disposal)"})
    return issues
