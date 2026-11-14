#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Version-scheme unit tests (versioning scheme, 0.4): three-part anchor parse,
B-line extraction, and the migration staging range [prev_line, new_line).

Run: python3 -m unittest discover -s .owfa/tests -p test_version_scheme.py
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import owfa_kernel as k  # noqa: E402


class VersionSchemeTests(unittest.TestCase):
    def test_framework_version_parses_three_part_anchor(self):
        # the repo's own VERSION is the full release version now — expect
        # exactly the anchor's own three-part tuple (version-agnostic: the
        # test survives release bumps)
        text = open(os.path.join(k.ROOT, ".owfa", "VERSION"), encoding="utf-8").read().strip()
        expected = tuple(int(x) for x in text.split("."))
        self.assertEqual(len(expected), 3)
        self.assertEqual(k.framework_version(), expected)

    def test_framework_version_tolerates_legacy_two_part(self):
        import tempfile
        vpath = os.path.join(k.ROOT, ".owfa", "VERSION")
        original = open(vpath, encoding="utf-8").read()
        try:
            open(vpath, "w", encoding="utf-8").write("0.3\n")
            self.assertEqual(k.framework_version(), (0, 3))
        finally:
            open(vpath, "w", encoding="utf-8").write(original)

    def test_vline_extracts_major_minor(self):
        self.assertEqual(k._vline("0.3.0"), (0, 3))
        self.assertEqual(k._vline("0.3.11"), (0, 3))
        self.assertEqual(k._vline("0.2"), (0, 2))

    def test_compat_floor_tuple_semantics(self):
        fw = k.framework_version()  # the live anchor, whatever release it says
        self.assertFalse((0, 3) > fw)                      # floor below the line passes
        self.assertFalse(fw[:2] > fw)                      # floor at the line passes
        self.assertFalse(fw > fw)                          # floor equal to the release passes
        self.assertTrue((fw[0], fw[1], fw[2] + 1) > fw)    # floor demanding a later patch refuses
        self.assertTrue((fw[0] + 1,) > fw)                 # floor above the line refuses

    def test_staging_line_range(self):
        # mirror of the _stage_migrations predicate: stage when prev_line <= from_line < new_line
        def stages(name, prev, new):
            m = re.fullmatch(r"(\d+\.\d+)-to-(\d+\.\d+)\.md", name)
            if not m:
                return False
            prev_line, new_line = k._vline(prev), k._vline(new)
            return prev_line <= k._vt(m.group(1)) < new_line

        self.assertTrue(stages("0.3-to-0.4.md", "0.3.2", "0.4.0"))   # line crossing stages
        self.assertTrue(stages("0.3-to-0.4.md", "0.3", "0.4.0"))     # legacy two-part prev works
        self.assertTrue(stages("0.2-to-0.3.md", "0.2", "0.4.0"))     # chained crossings stage together
        self.assertFalse(stages("0.3-to-0.4.md", "0.3.1", "0.3.2"))  # same-line C update stages nothing
        self.assertFalse(stages("0.2-to-0.3.md", "0.3", "0.4.0"))    # already past does not re-stage
        self.assertFalse(stages("0.4-to-0.5.md", "0.3", "0.4.0"))    # future lines do not stage


if __name__ == "__main__":
    unittest.main()
