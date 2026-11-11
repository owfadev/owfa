#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deprecation shim: the kernel was renamed owfa_kernel.py (0.4 layout).

Keeps 0.3-era paths and muscle memory working through the 0.4 cycle; the shim
is scheduled for removal in 0.5. The real entry is owfa_kernel.py next to it.
"""
import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
print("[deprecated] wiki_plugin_kernel.py -> owfa_kernel.py (shim retires in 0.5)", file=sys.stderr)
sys.argv[0] = os.path.join(_HERE, "owfa_kernel.py")
runpy.run_path(os.path.join(_HERE, "owfa_kernel.py"), run_name="__main__")
