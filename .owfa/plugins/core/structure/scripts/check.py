#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""structure plugin attached audit: structure declaration page existence, diff between declarations and vault's actual top-level directories, territory misplacement.

A missing declaration page = flat-layout tolerance (legal, info); the diff covers top-level directories only — loose top-level files are flat slots, unconstrained.
"""
import os


def check(ctx):
    issues = []
    # territory misplacement: type: structure is allowed only at wiki/structure.md
    decl = None
    for rel, fm, _body in ctx.pages:
        if fm.get("type") == "structure" and rel != "structure.md":
            issues.append({"level": "error", "message": f"{rel}: type: structure outside the declaration page (territory misplacement)"})
        if rel == "structure.md":
            decl = fm.get("structure") or {}
    if decl is None:
        issues.append({"level": "info", "message": "no structure declaration page (flat-layout tolerance)"})
        return issues
    vroot = os.path.join(ctx.root, "vault")
    if not os.path.isdir(vroot):
        return issues
    actual = {d + "/" for d in os.listdir(vroot)
              if os.path.isdir(os.path.join(vroot, d)) and not d.startswith(".")}
    declared = {str(k).strip() for k in decl}
    for d in sorted(actual - declared):
        issues.append({"level": "warning", "message": f"vault top-level directory undeclared: {d} (add a declaration or put it in place)"})
    for d in sorted(declared - actual):
        issues.append({"level": "warning", "message": f"declaration points to a nonexistent directory: {d} (declaration outdated; sync or delete)"})
    return issues
