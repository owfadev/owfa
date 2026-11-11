#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owfa_home unit tests: resolution order, bind/unbind, exclusivity, stale, migration.

Run: python3 .owfa/tests/test_owfa_home.py  (pure stdlib; OWFA_HOME pointed at a temp dir)
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import owfa_home as h  # noqa: E402


class OwfaHomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        os.environ["OWFA_HOME"] = str(self.root / "machine")
        self.ws1 = self._ws("ws1")
        self.ws2 = self._ws("ws2")
        os.environ.pop("OWFA_ROOT", None)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("OWFA_HOME", None)
        os.environ.pop("OWFA_ROOT", None)

    def _ws(self, name):
        p = self.root / name
        p.mkdir(parents=True)
        return str(p)

    def test_default_home_is_zero_config(self):
        os.chdir(self.ws1)
        home = h.resolve_home("qq-cli")
        self.assertEqual(home, self.root / "machine" / "connectors" / "qq-cli" / "homes" / "default")

    def test_explicit_root_binding_wins(self):
        os.chdir(self.ws1)
        h.bind("qq-cli", self.ws1, "personal", bot="appid-1")
        self.assertEqual(h.resolve_home("qq-cli"), Path(h.home_dir("qq-cli", "personal")))
        entry = h.load_bindings("qq-cli")[0]
        self.assertEqual(entry["bot"], "appid-1")
        self.assertTrue(os.path.isdir(entry["home"]), "bind must create the home dir")

    def test_resolution_order_env_then_cwd(self):
        h.bind("qq-cli", self.ws1, "a")
        h.bind("qq-cli", self.ws2, "b")
        os.environ["OWFA_ROOT"] = self.ws2
        self.assertEqual(h.resolve_home("qq-cli"), Path(h.home_dir("qq-cli", "b")))
        os.environ.pop("OWFA_ROOT", None)
        os.chdir(self.ws1)
        self.assertEqual(h.resolve_home("qq-cli"), Path(h.home_dir("qq-cli", "a")))  # cwd lookup
        self.assertEqual(h.resolve_home("qq-cli", explicit_root=self.ws2), Path(h.home_dir("qq-cli", "b")))  # explicit wins

    def test_rebind_same_root_replaces(self):
        h.bind("qq-cli", self.ws1, "first")
        h.bind("qq-cli", self.ws1)  # no id: re-binds under the existing id for this root
        bindings = h.load_bindings("qq-cli")
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0]["id"], "first")

    def test_unbind_detaches_but_keeps_home(self):
        b = h.bind("qq-cli", self.ws1, "keep-data")
        h.unbind("qq-cli", "keep-data")
        self.assertEqual(h.load_bindings("qq-cli"), [])
        self.assertTrue(os.path.isdir(b["home"]), "unbind must not delete home data")

    def test_exclusivity_violation_detected(self):
        home = h.home_dir("qq-cli", "shared")
        for ws, bid in ((self.ws1, "one"), (self.ws2, "two")):
            b = h.bind("qq-cli", ws, bid)
            b["home"] = str(home)  # force two bindings onto one home
            h.save_bindings("qq-cli", [x for x in h.load_bindings("qq-cli") if x["id"] != bid] + [b])
        v = h.exclusivity_violations("qq-cli")
        self.assertEqual(len(v), 1)
        self.assertEqual(sorted(v[0]["bindings"]), ["one", "two"])

    def test_stale_bindings_reported(self):
        gone = self._ws("gone")
        h.bind("qq-cli", gone, "dying")
        os.rmdir(gone)
        stale = h.stale_bindings("qq-cli")
        self.assertEqual([s["id"] for s in stale], ["dying"])

    def test_migrate_moves_and_symlinks(self):
        legacy = Path(self._ws("legacy-home"))
        (legacy / "credentials.json").write_text("{}", encoding="utf-8")
        os.chdir(self.ws1)
        entry = h.migrate_legacy_home("qq-cli", str(legacy), "default", root=self.ws1)
        self.assertFalse(legacy.exists() and not legacy.is_symlink(), "legacy dir must move, not copy")
        self.assertTrue((Path(entry["home"]) / "credentials.json").exists(), "contents must land in the new home")
        self.assertTrue(legacy.is_symlink() and os.path.realpath(legacy) == os.path.realpath(entry["home"]))
        self.assertEqual(os.path.basename(os.path.realpath(legacy)), "default")


if __name__ == "__main__":
    unittest.main(verbosity=2)
