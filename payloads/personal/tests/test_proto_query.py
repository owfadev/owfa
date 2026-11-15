#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package self-tests for proto_query.py (abi-spec v2 §7.2: envelope fields, one case
per semantic, error envelopes, proto_ver derived from PKG.yaml — version never hardcoded).

Runs with the standard library only: python3 -m unittest discover -s tests
(or python3 tests/test_proto_query.py). The fixture builds a tmp workspace with the
installed layout (<tmp>/.owfa/plugins/domains/personal/{proto_query.py, PKG.yaml}) plus a
wiki/ tree, then invokes the script as a subprocess — the same channel a consumer uses.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(PKG_ROOT, "proto_query.py")
PKG = os.path.join(PKG_ROOT, "PKG.yaml")


def pkg_version():
    with open(PKG, encoding="utf-8") as f:
        text = f.read()
    return re.search(r"^version:\s*[\"']?([^\s\"']+)", text, re.M).group(1)


class Fixture:
    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="abi-pq-")
        suite = os.path.join(self.tmp, ".owfa", "plugins", "domains", "personal")
        os.makedirs(suite)
        os.makedirs(os.path.join(self.tmp, "wiki", "notes"))
        shutil.copy(SCRIPT, os.path.join(suite, "proto_query.py"))
        shutil.copy(PKG, os.path.join(suite, "PKG.yaml"))
        self.mkdate("2020-01-01")
        self.write("notes/old.md", "old page never touched\n", mtime="2020-01-02")
        self.write("notes/fresh.md", "---\ntype: note\n---\nbody with needle42\n")
        self.write("sessions/backbone.md", "---\ntype: session\n---\nsession page\n")
        self.write("log.md",
                   "- 2020-01-05 save: created notes/old.md\n"
                   "- %s query: touched notes/fresh.md\n" % datetime.date.today().isoformat())
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text, mtime=None):
        p = os.path.join(self.tmp, "wiki", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        if mtime:
            self.mkdate(mtime, p)

    @staticmethod
    def mkdate(day, path=None):
        t = datetime.datetime.strptime(day, "%Y-%m-%d").timestamp()
        os.utime(path, (t, t)) if path else None

    def write_bytes(self, rel, data, mtime=None):
        p = os.path.join(self.tmp, "wiki", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        if mtime:
            self.mkdate(mtime, p)

    def run(self, *args):
        script = os.path.join(self.tmp, ".owfa", "plugins", "domains", "personal", "proto_query.py")
        r = subprocess.run([sys.executable, script] + list(args),
                           capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)


class TestProtoQuery(unittest.TestCase):
    def test_batch_envelope_and_proto_ver(self):
        with Fixture() as fx:
            code, out = fx.run("list")
            self.assertEqual(code, 0)
            self.assertEqual(out["ok"], True)
            self.assertEqual(out["semantic"], "list")
            self.assertEqual(out["count"], len(out["items"]))
            for it in out["items"]:
                self.assertEqual(it["protocol"], "vaultwiki")
                self.assertEqual(it["proto_ver"], pkg_version())  # derived, not hardcoded
            addrs = [it["addr"] for it in out["items"]]
            self.assertIn("notes/fresh", addrs)
            self.assertIn("log", addrs)  # derived pages listed too (v2: full listing)

    def test_list_kind_filter(self):
        with Fixture() as fx:
            code, out = fx.run("list", "--kind", "note")
            self.assertEqual((code, out["ok"]), (0, True))
            self.assertEqual([it["addr"] for it in out["items"]], ["notes/fresh"])
            code, out = fx.run("list", "--kind", "__abi_smoke")  # unknown kind: empty, no error
            self.assertEqual((code, out["ok"], out["items"]), (0, True, []))

    def test_get(self):
        with Fixture() as fx:
            code, out = fx.run("get", "notes/fresh")
            self.assertEqual(code, 0)
            self.assertEqual(out["addr"], "notes/fresh")
            self.assertEqual(out["title"], "fresh")
            self.assertEqual(out["kind"], "note")
            self.assertIn("content", out)
            self.assertIn("needle42", out["content"])  # full raw text, not truncated

    def test_search(self):
        with Fixture() as fx:
            code, out = fx.run("search", "needle42")       # body substring
            self.assertEqual([it["addr"] for it in out["items"]], ["notes/fresh"])
            code, out = fx.run("search", "notes/")         # full-name prefix (+ body hits: log names the page too)
            got = [it["addr"] for it in out["items"]]
            self.assertIn("notes/fresh", got)
            self.assertIn("notes/old", got)

    def test_recent_window_and_op(self):
        with Fixture() as fx:
            code, out = fx.run("recent")                   # default 7d
            addrs = {it["addr"]: it["op"] for it in out["items"]}
            self.assertNotIn("notes/old", addrs)           # 2020 mtime outside window
            self.assertIn("notes/fresh", addrs)
            for it in out["items"]:
                self.assertIn(it["op"], ("create", "update", "unknown"))
            self.assertEqual(addrs["notes/fresh"], "unknown")  # mtime in window, no create/prior evidence
            today = datetime.date.today().isoformat()
            fx.write("notes/newborn.md", "brand new\n")
            fx.write("log.md", "- %s save: created notes/newborn.md\n" % today)
            code, out = fx.run("recent")
            ops = {it["addr"]: it["op"] for it in out["items"]}
            self.assertEqual(ops.get("notes/newborn"), "create")  # in-window create-verb log evidence
            code, out = fx.run("recent", "--window", "999999d")
            self.assertIn("notes/old", {it["addr"] for it in out["items"]})

    def test_error_envelopes(self):
        with Fixture() as fx:
            code, out = fx.run("get", "notes/missing")
            self.assertEqual((code, out["ok"], out["error_code"]), (0, False, "not_found"))
            code, out = fx.run("recent", "--window", "7x")
            self.assertEqual((code, out["ok"], out["error_code"]), (0, False, "bad_request"))
            code, out = fx.run("frobnicate")
            self.assertEqual((code, out["ok"], out["error_code"]), (0, False, "unsupported_semantic"))

    def test_tmp_subtree_invisible(self):
        with Fixture() as fx:
            fx.write("tmp/draft.md", "---\ntype: note\n---\ndraft needle42\n")
            code, out = fx.run("list")
            self.assertNotIn("tmp/draft", [it["addr"] for it in out["items"]])
            code, out = fx.run("search", "needle42")
            self.assertNotIn("tmp/draft", [it["addr"] for it in out["items"]])
            code, out = fx.run("recent")
            self.assertNotIn("tmp/draft", {it["addr"] for it in out["items"]})
            code, out = fx.run("get", "tmp/draft")     # tmp invisible to the ABI face
            self.assertEqual((code, out["ok"], out["error_code"]), (0, False, "not_found"))
            code, out = fx.run("get", "tmp/../notes/fresh")  # traversal-ish tmp path: refused
            self.assertEqual((code, out["ok"], out["error_code"]), (0, False, "not_found"))

    def test_get_undecodable_page_returns_content(self):
        with Fixture() as fx:
            fx.write_bytes("notes/binary.md",
                           b"---\ntype: note\n---\nraw \xff\xfe bytes\n")
            code, out = fx.run("get", "notes/binary")
            self.assertEqual((code, out.get("addr")), (0, "notes/binary"))  # exists -> never not_found
            self.assertIn("raw ", out["content"])
            code, out = fx.run("list")               # walk still skips it
            self.assertNotIn("notes/binary", [it["addr"] for it in out["items"]])

    def test_crlf_frontmatter_kind(self):
        with Fixture() as fx:
            fx.write_bytes("notes/crlf.md",
                           b"---\r\ntype: note\r\ntitle: CRLF Page\r\n---\r\nbody\r\n")
            code, out = fx.run("get", "notes/crlf")
            self.assertEqual(out["kind"], "note")
            self.assertEqual(out["title"], "CRLF Page")
            code, out = fx.run("list", "--kind", "note")
            self.assertIn("notes/crlf", [it["addr"] for it in out["items"]])


if __name__ == "__main__":
    unittest.main()
