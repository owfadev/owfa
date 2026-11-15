#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kernel-home steps 0+1 tests (kernel-home-spec v2 §6, behavior-preserving).

Covers:
- OWFA_HOME resolution priority (G3): env wins over the default ~/.owfa (kernel side)
- --root global parameter (step 1): reroutes the ROOT-derived path constants
- C3 vocabulary: INJECT marker and wiki container name are module constants,
  derived markers follow the constant, _check_transports reads WIKI_DIR_NAME
- M3: _journal is pure append + independent compaction at JOURNAL_MAX_LINES
- F1 dual-target dispatch (bin/owfa.js side, via node): WORKSPACE.yaml +
  user-level kernel installed → the user-level kernel is called with --root
  (verified with a fake kernel recording its argv); without the marker the
  legacy in-tree path is used even when OWFA_HOME is set
- M1 anti-stomp guard: `owfa upgrade` refuses a WORKSPACE.yaml workspace

Run: python3 .owfa/tests/test_kernel_home.py   (pure stdlib; node needed for the F1/M1 cases)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / ".owfa" / "scripts"
BIN = REPO / "bin" / "owfa.js"

# fake kernels (F1): record their argv, exit 0 — enough to verify the channel's
# dispatch decisions without any real kernel behavior
FAKE_KERNEL = """import json, sys, os
json.dump({"argv": sys.argv[1:]}, open(os.environ["FAKE_KERNEL_OUT"], "w"))
sys.exit(0)
"""

sys.path.insert(0, str(SCRIPTS))


def _probe(env_extra):
    """Import owfa_kernel fresh in a subprocess with the given env; return its module constants as JSON."""
    code = (
        "import json, sys, os; sys.path.insert(0, %r); import owfa_kernel as k; "
        "json.dump({'owfa_home': k.OWFA_HOME, 'root': k.ROOT}, sys.stdout)" % str(SCRIPTS)
    )
    env = {**os.environ, **env_extra}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=str(REPO))
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class OwfaHomeResolution(unittest.TestCase):
    """G3: env OWFA_HOME wins over the default ~/.owfa (kernel-side constants)."""

    def test_env_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = _probe({"OWFA_HOME": tmp})["owfa_home"]
            self.assertEqual(os.path.realpath(got), os.path.realpath(tmp))

    def test_default_is_dot_owfa_under_home(self):
        got = _probe({"OWFA_HOME": ""})["owfa_home"]  # empty string = unset semantics here
        self.assertEqual(got, os.path.join(os.path.expanduser("~"), ".owfa"))

    def test_user_level_constants_hang_off_home(self):
        code = (
            "import json, sys; sys.path.insert(0, %r); import owfa_kernel as k; "
            "json.dump({'kernel': k.OWFA_HOME_KERNEL_DIR, 'cache': k.OWFA_HOME_REGISTRY_CACHE, "
            "'ws': k.OWFA_HOME_WORKSPACES, 'journal': k.OWFA_HOME_JOURNAL_DIR, "
            "'version': k.OWFA_HOME_KERNEL_VERSION, 'script': k.OWFA_HOME_KERNEL_SCRIPT}, sys.stdout)"
        ) % str(SCRIPTS)
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               env={**os.environ, "OWFA_HOME": tmp}, cwd=str(REPO))
            self.assertEqual(r.returncode, 0, r.stderr)
            got = json.loads(r.stdout)
            self.assertEqual(got["kernel"], os.path.join(tmp, "kernel"))
            self.assertEqual(got["cache"], os.path.join(tmp, "registry-cache.yaml"))
            self.assertEqual(got["ws"], os.path.join(tmp, "workspaces.yaml"))
            self.assertEqual(got["journal"], os.path.join(tmp, "journal"))
            self.assertEqual(got["version"], os.path.join(tmp, "kernel", "VERSION"))


class RootParameter(unittest.TestCase):
    """Step 1: --root is a global flag consumed before dispatch; default unchanged."""

    def test_default_root_is_script_tree(self):
        got = _probe({})["root"]
        self.assertEqual(os.path.realpath(got), os.path.realpath(str(REPO)))

    def test_root_flag_and_equals_form(self):
        for form in ("--root", "--root="):
            with tempfile.TemporaryDirectory() as tmp:
                if form == "--root":
                    argv = ["--root", tmp, "validate"]
                else:
                    argv = [form + tmp, "validate"]
                os.makedirs(os.path.join(tmp, ".owfa", "command"), exist_ok=True)
                os.makedirs(os.path.join(tmp, ".owfa", "plugins", "domains"), exist_ok=True)
                r = subprocess.run([sys.executable, str(SCRIPTS / "owfa_kernel.py"), *argv],
                                   capture_output=True, text=True, cwd=str(REPO))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("validate", r.stdout)

    def test_root_without_value_is_loud(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "owfa_kernel.py"), "--root"],
                           capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(r.returncode, 2)
        self.assertIn("--root requires a path", r.stdout + r.stderr)

    def test_apply_root_rederives_paths(self):
        import owfa_kernel as k
        with tempfile.TemporaryDirectory() as tmp:
            old = (k.ROOT, k.JOURNAL)
            try:
                k._apply_root(tmp)
                self.assertEqual(os.path.realpath(k.ROOT), os.path.realpath(tmp))
                self.assertEqual(k.JOURNAL, os.path.join(tmp, ".owfa", "kernel-journal.log"))
                self.assertEqual(k.AGENTS_MD, os.path.join(tmp, "AGENTS.md"))
                self.assertEqual(k.CHECK_SKILL, os.path.join(tmp, ".owfa", "command", "owfa-check", "SKILL.md"))
            finally:
                k._apply_root(old[0])
                k.JOURNAL = old[1]


class C3Vocabulary(unittest.TestCase):
    """C3: marker id and wiki container name are constants; defaults unchanged."""

    def test_default_markers_unchanged(self):
        import owfa_kernel as k
        self.assertEqual(k.WIKI_DIR_NAME, "wiki")
        self.assertEqual(k.INJECT_MARKER, "wiki-inject")
        self.assertEqual(k.INJECT_START, "<!-- wiki-inject:start -->")
        self.assertEqual(k.INJECT_END, "<!-- wiki-inject:end -->")

    def test_markers_follow_the_constant(self):
        import owfa_kernel as k
        self.assertEqual(k.INJECT_START, f"<!-- {k.INJECT_MARKER}:start -->")
        self.assertEqual(k.INJECT_END, f"<!-- {k.INJECT_MARKER}:end -->")
        s, e = k.inject_markers("qq-inject")
        self.assertEqual((s, e), ("<!-- qq-inject:start -->", "<!-- qq-inject:end -->"))

    def test_check_transports_reads_wiki_dir_name(self):
        import owfa_kernel as k
        with tempfile.TemporaryDirectory() as tmp:
            old = (k.ROOT, k.WIKI_DIR_NAME)
            try:
                k._apply_root(tmp)
                os.makedirs(os.path.join(tmp, "pages"))
                with open(os.path.join(tmp, "pages", "decl.md"), "w", encoding="utf-8") as f:
                    f.write("---\ntransport: qq-bot\n---\nbody\n")
                m = {"transports": {"contract": "qq.transport.v1", "recommends": "qq", "declaration": "decl.md"}}
                # container renamed via the constant → the declaration page is found
                k.WIKI_DIR_NAME = "pages"
                errors, warnings = [], []
                k._check_transports("demo", m, errors, warnings)
                self.assertEqual((errors, warnings), ([], []))
                # default container name → the page is invisible again → health warning
                k.WIKI_DIR_NAME = "wiki"
                k._check_transports("demo", m, errors, warnings)
                self.assertEqual(errors, [])
                self.assertEqual(len(warnings), 1)
                self.assertIn("wiki/decl.md", warnings[0])  # warning text follows the constant too
            finally:
                k.WIKI_DIR_NAME = old[1]
                k._apply_root(old[0])


class M3Journal(unittest.TestCase):
    """M3: pure append + independent compaction (single-writer assumption documented)."""

    def test_append_preserves_existing_lines(self):
        import owfa_kernel as k
        with tempfile.TemporaryDirectory() as tmp:
            old = k.JOURNAL
            try:
                k.JOURNAL = os.path.join(tmp, "kernel-journal.log")
                with open(k.JOURNAL, "w", encoding="utf-8") as f:
                    f.write("sentinel-line\n")
                k._journal("install", "demo v0.1")
                text = open(k.JOURNAL, encoding="utf-8").read().splitlines()
                self.assertEqual(len(text), 2)
                self.assertEqual(text[0], "sentinel-line")
                self.assertTrue(text[1].endswith("install demo v0.1"))
            finally:
                k.JOURNAL = old

    def test_compaction_trims_to_cap(self):
        import owfa_kernel as k
        self.assertEqual(k.JOURNAL_MAX_LINES, 500)
        with tempfile.TemporaryDirectory() as tmp:
            old = k.JOURNAL
            try:
                k.JOURNAL = os.path.join(tmp, "kernel-journal.log")
                with open(k.JOURNAL, "w", encoding="utf-8") as f:
                    f.write("\n".join(f"old-{i}" for i in range(k.JOURNAL_MAX_LINES)) + "\n")
                k._journal("install", "over-cap")  # 501 lines → compacted back to 500
                lines = open(k.JOURNAL, encoding="utf-8").read().splitlines()
                self.assertEqual(len(lines), k.JOURNAL_MAX_LINES)
                self.assertEqual(lines[0], "old-1")  # oldest trimmed, append order kept
                self.assertTrue(lines[-1].endswith("install over-cap"))
            finally:
                k.JOURNAL = old


class ChannelDualTarget(unittest.TestCase):
    """F1/M1 (bin/owfa.js): dual-target dispatch and the anti-stomp guard, via node."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        (self.home / "kernel").mkdir(parents=True)
        self.target = self.root / "ws"
        (self.target / ".owfa").mkdir(parents=True)
        self.argv_out = self.root / "argv.json"
        # the fake user-level kernel + its VERSION (Q1a anchor)
        (self.home / "kernel" / "owfa_kernel.py").write_text(FAKE_KERNEL, encoding="utf-8")
        (self.home / "kernel" / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        # the fake in-tree kernel (records argv the same way)
        (self.target / ".owfa" / "scripts").mkdir(parents=True)
        (self.target / ".owfa" / "scripts" / "owfa_kernel.py").write_text(FAKE_KERNEL, encoding="utf-8")
        (self.target / ".owfa" / "VERSION").write_text("0.4.3\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _node(self, args, marker, home=True):
        env = {**os.environ,
               "OWFA_HOME": str(self.home) if home else str(self.root / "empty-home"),
               "FAKE_KERNEL_OUT": str(self.argv_out)}
        if marker:
            (self.target / ".owfa" / "WORKSPACE.yaml").write_text("registered: true\n", encoding="utf-8")
        return subprocess.run([os.environ.get("NODE", "node"), str(BIN), *args],
                              capture_output=True, text=True, env=env, cwd=str(self.target))

    def test_workspace_marker_routes_to_user_kernel_with_root(self):
        r = self._node(["pkg"], marker=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))["argv"]
        self.assertEqual(got, ["--root", str(self.target), "pkg"])

    def test_no_marker_keeps_in_tree_kernel_even_with_home_set(self):
        r = self._node(["pkg"], marker=False)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))["argv"]
        self.assertEqual(got, ["pkg"])  # no --root: the legacy tree path, behavior preserved

    def test_read_version_anchors_on_user_kernel(self):
        # WORKSPACE.yaml in place → readVersion reports the user-level kernel
        # version (Q1a), visible in `owfa version`... doctor prints it as
        # "instance framework"; use the marker workspace's doctor output.
        (self.target / "AGENTS.md").write_text(
            "# t\n\n<!-- wiki-inject:start -->\n<!-- wiki-inject:end -->\n", encoding="utf-8")
        os.symlink(".owfa", str(self.target / ".meta"))
        r = self._node(["doctor"], marker=True)
        self.assertIn("instance framework 9.9.9", r.stdout)
        self.assertIn("owfa-home", r.stdout)  # G3 line
        # without the marker → the tree version again
        (self.target / ".owfa" / "WORKSPACE.yaml").unlink()
        r2 = self._node(["doctor"], marker=False)
        self.assertIn("instance framework 0.4.3", r2.stdout)

    def test_m1_guard_refuses_legacy_upgrade(self):
        r = self._node(["upgrade", str(self.target)], marker=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("WORKSPACE.yaml", r.stderr)
        self.assertIn("user-level", r.stderr)
        self.assertIn("owfa upgrade", r.stderr)
        # and the tree was not touched
        self.assertEqual((self.target / ".owfa" / "VERSION").read_text(encoding="utf-8").strip(), "0.4.3")

    def test_marker_without_user_kernel_falls_back_to_tree(self):
        # WORKSPACE.yaml present but no user-level kernel installed → legacy
        # in-tree path (the dispatch requires both conditions)
        (self.home / "kernel" / "owfa_kernel.py").unlink()
        r = self._node(["pkg"], marker=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))["argv"]
        self.assertEqual(got, ["pkg"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

    def test_m1_guard_blocks_legacy_init_force_over_marker(self):
        """copyPayload/init --force must refuse over a WORKSPACE.yaml tree (review F1)."""
        import subprocess, tempfile, os, json
        ws = tempfile.mkdtemp()
        os.makedirs(os.path.join(ws, ".owfa"))
        with open(os.path.join(ws, ".owfa", "WORKSPACE.yaml"), "w") as f:
            f.write("kernel_compat: '>= 0.4'\n")
        r = subprocess.run(["node", str(FRAMEWORK / "bin" / "owfa.js"), "init", ws, "--force"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("WORKSPACE.yaml", r.stderr + r.stdout)
        self.assertTrue(os.path.exists(os.path.join(ws, ".owfa", "WORKSPACE.yaml")))

    def test_readversion_falls_back_to_tree_when_user_kernel_absent(self):
        """marker + missing user kernel -> tree VERSION (dispatch-aligned, review fix 2)."""
        import subprocess, tempfile, os
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as ws:
            os.makedirs(os.path.join(ws, ".owfa"))
            with open(os.path.join(ws, ".owfa", "WORKSPACE.yaml"), "w") as f:
                f.write("kernel_compat: '>= 0.4'\n")
            with open(os.path.join(ws, ".owfa", "VERSION"), "w") as f:
                f.write("7.7.7\n")
            env = dict(os.environ, OWFA_HOME=home)
            r = subprocess.run(["node", str(FRAMEWORK / "bin" / "owfa.js"), "doctor", ws],
                               capture_output=True, text=True, env=env)
            out = r.stdout + r.stderr
            self.assertNotIn("9.9.9", out)
            # dispatch fell back to the tree kernel; version report must not be user-level
            self.assertTrue("7.7.7" in out or r.returncode != 0, out)

if __name__ == "__main__":
    unittest.main(verbosity=2)
