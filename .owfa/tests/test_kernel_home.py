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
        # the fake user-level kernel, step-2 (G1) versioned layout:
        # kernel/<X.Y.Z>/owfa_kernel.py + VERSION, kernel/current = latest
        (self.home / "kernel" / "9.9.9").mkdir()
        (self.home / "kernel" / "9.9.9" / "owfa_kernel.py").write_text(FAKE_KERNEL, encoding="utf-8")
        (self.home / "kernel" / "9.9.9" / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        (self.home / "kernel" / "current").write_text("9.9.9\n", encoding="utf-8")
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
        import shutil
        shutil.rmtree(self.home / "kernel")
        (self.home / "kernel").mkdir()
        r = self._node(["pkg"], marker=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))["argv"]
        self.assertEqual(got, ["pkg"])



    def test_m1_guard_blocks_legacy_init_force_over_marker(self):
        """copyPayload/init --force must refuse over a WORKSPACE.yaml tree (review F1)."""
        import subprocess, tempfile, os, json
        ws = tempfile.mkdtemp()
        os.makedirs(os.path.join(ws, ".owfa"))
        with open(os.path.join(ws, ".owfa", "WORKSPACE.yaml"), "w") as f:
            f.write("kernel_compat: '>= 0.4'\n")
        r = subprocess.run(["node", str(BIN), "init", ws, "--force"],
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
            r = subprocess.run(["node", str(BIN), "doctor", ws],
                               capture_output=True, text=True, env=env)
            out = r.stdout + r.stderr
            self.assertNotIn("9.9.9", out)
            # dispatch fell back to the tree kernel; version report must not be user-level
            self.assertTrue("7.7.7" in out or r.returncode != 0, out)

# ---------------------------------------------------------------------------
# kernel-home step 2 (spec v2 §6): user-level channel A/B/C/D
# ---------------------------------------------------------------------------
FW = (REPO / ".owfa" / "VERSION").read_text(encoding="utf-8").strip()  # channel framework version

# a fake kernel that also reports WHICH version-dir it ran from (multi-version
# resolution tests need to see the chosen version, not just the argv)
def _fake_kernel_v(ver):
    return (
        "import json, sys, os\n"
        f"json.dump({{'argv': sys.argv[1:], 'ver': {ver!r}}}, open(os.environ['FAKE_KERNEL_OUT'], 'w'))\n"
        "sys.exit(0)\n"
    )


def _node2(args, home, cwd=None, extra_env=None):
    """Run bin/owfa.js with an isolated OWFA_HOME."""
    env = {**os.environ, "OWFA_HOME": str(home)}
    if extra_env:
        env.update(extra_env)
    return subprocess.run([os.environ.get("NODE", "node"), str(BIN), *args],
                          capture_output=True, text=True, env=env, cwd=cwd or str(REPO))


def _plant_fake_kernel(home, ver):
    d = Path(home) / "kernel" / ver
    d.mkdir(parents=True, exist_ok=True)
    (d / "owfa_kernel.py").write_text(_fake_kernel_v(ver), encoding="utf-8")
    (d / "VERSION").write_text(ver + "\n", encoding="utf-8")
    return d


class InstallKernelTests(unittest.TestCase):
    """A (Q1a/Q3a/Q7/G1): owfa install-kernel — versioned layout + hash check + journal."""

    def test_install_files_current_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            r = _node2(["install-kernel"], home)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            kd = home / "kernel" / FW
            for name in ("owfa_kernel.py", "wikilib.py", "VERSION"):
                self.assertTrue((kd / name).exists(), name)
            self.assertEqual((kd / "VERSION").read_text(encoding="utf-8").strip(), FW)
            # current = latest installed (only one so far)
            self.assertEqual((home / "kernel" / "current").read_text(encoding="utf-8").strip(), FW)
            # M3: the user-level journal got an append line
            j = (home / "journal" / "events.log").read_text(encoding="utf-8")
            self.assertIn("kernel-install", j)
            # Q7: install result is byte-identical to the channel master
            import hashlib
            for name in ("owfa_kernel.py", "wikilib.py"):
                a = hashlib.sha256((REPO / ".owfa" / "scripts" / name).read_bytes()).hexdigest()
                b = hashlib.sha256((kd / name).read_bytes()).hexdigest()
                self.assertEqual(a, b, name)

    def test_reinstall_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            self.assertEqual(_node2(["install-kernel"], home).returncode, 0)
            r = _node2(["install-kernel"], home)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)


class InitUserLevelTests(unittest.TestCase):
    """B (spec §2/C1): init --user-level full chain — kernel installed, marker
    written (no protocol field), workspace registered, validate green through
    the user-level kernel; legacy init (no flag) unchanged."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.home = cls.root / "home"
        cls.ws = cls.root / "ws"
        r = _node2(["init", str(cls.ws), "--name", "ul", "--user-level"], cls.home)
        assert r.returncode == 0, r.stdout + r.stderr
        cls.out = r.stdout

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_kernel_installed_and_journal(self):
        self.assertTrue((self.home / "kernel" / FW / "owfa_kernel.py").exists())
        self.assertIn("workspace-register", (self.home / "journal" / "events.log").read_text(encoding="utf-8"))

    def test_tree_has_no_kernel_and_no_version(self):
        # Q1a/Q2a: the tree carries neither scripts/ nor VERSION — the anchor
        # lives at $OWFA_HOME/kernel/<ver>/VERSION
        self.assertTrue((self.ws / ".owfa" / "scripts" / "owfa_kernel.py").read_text().find("FORWARDER") >= 0)
        self.assertFalse((self.ws / ".owfa" / "scripts" / "wikilib.py").exists(), "scripts must hold only the P2 forwarder")
        self.assertFalse((self.ws / ".owfa" / "VERSION").exists())

    def test_marker_is_minimal_yaml(self):
        marker = (self.ws / ".owfa" / "WORKSPACE.yaml").read_text(encoding="utf-8")
        self.assertIn(f'kernel_compat: ">= {FW}"', marker)
        self.assertNotIn("protocol:", marker)  # C1: protocol identity is never written

    def test_registered(self):
        reg = (self.home / "workspaces.yaml").read_text(encoding="utf-8")
        self.assertIn(str(self.ws), reg)
        r = _node2(["workspaces", "list"], self.home)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn(str(self.ws), r.stdout)

    def test_doctor_green_user_level(self):
        r = _node2(["doctor", str(self.ws)], self.home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"kernel source: user-level {FW}", r.stdout)
        self.assertIn("registry: registered", r.stdout)
        self.assertIn("doctor: ok", r.stdout)

    def test_legacy_init_unchanged(self):
        """Regression: without the flag nothing user-level happens (M1/legacy chain intact)."""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            ws = Path(tmp) / "legacy"
            r = _node2(["init", str(ws)], home)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertTrue((ws / ".owfa" / "scripts" / "owfa_kernel.py").exists())
            self.assertTrue((ws / ".owfa" / "VERSION").exists())
            self.assertFalse((ws / ".owfa" / "WORKSPACE.yaml").exists())
            self.assertFalse((home / "kernel").exists())
            self.assertFalse((home / "workspaces.yaml").exists())


class MultiVersionResolution(unittest.TestCase):
    """A/G1: kernel_compat floor + registry binding pick the serving version."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        _plant_fake_kernel(self.home, "4.4.4")
        _plant_fake_kernel(self.home, "5.0.0")
        (self.home / "kernel" / "current").write_text("5.0.0\n", encoding="utf-8")
        self.target = self.root / "ws"
        (self.target / ".owfa" / "scripts").mkdir(parents=True)
        (self.target / ".owfa" / "scripts" / "owfa_kernel.py").write_text(_fake_kernel_v("tree"), encoding="utf-8")
        self.argv_out = self.root / "argv.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, compat):
        (self.target / ".owfa" / "WORKSPACE.yaml").write_text(f'kernel_compat: ">= {compat}"\n', encoding="utf-8")
        return _node2(["pkg"], self.home, cwd=str(self.target),
                      extra_env={"FAKE_KERNEL_OUT": str(self.argv_out)})

    def test_floor_picks_the_newest_satisfying(self):
        r = self._run("5.0.0")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))
        self.assertEqual(got["ver"], "5.0.0")
        self.assertEqual(got["argv"][:2], ["--root", str(self.target)])

    def test_registry_binding_wins_over_newer_installed(self):
        # bind the workspace to 4.4.4; 5.0.0 is installed and satisfies the
        # floor, but the binding is the resolution source (G1)
        self._run("4.4.4")
        reg = self.home / "workspaces.yaml"
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(
            "workspaces:\n"
            f"  - id: 11111111-2222-3333-4444-555555555555\n"
            f"    path: {self.target}\n"
            "    kernel: 4.4.4\n"
            '    compat: ">= 4.4.4"\n'
            "    registered: 2026-01-01T00:00:00Z\n",
            encoding="utf-8",
        )
        r = _node2(["pkg"], self.home, cwd=str(self.target),
                   extra_env={"FAKE_KERNEL_OUT": str(self.argv_out)})
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        got = json.loads(self.argv_out.read_text(encoding="utf-8"))
        self.assertEqual(got["ver"], "4.4.4")

    def test_unsatisfiable_floor_fails_loudly(self):
        # the floor is unsatisfiable while kernels ARE installed — doctor (and
        # the dispatch) must fail pointing at install-kernel, not silently fall
        # back to a tree kernel that is not there
        self._run("9.9.9")  # marker in place with an unsatisfiable floor
        r = _node2(["doctor", str(self.target)], self.home, cwd=str(self.target))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("install-kernel", r.stdout + r.stderr)


class AdoptTests(unittest.TestCase):
    """D (Q6a/M2/#72): adopt success / failure rollback / idempotency / M1."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.home = cls.root / "home"
        cls.src = cls.root / "legacy-src"
        r = _node2(["init", str(cls.src), "--name", "legacy"], cls.home)
        assert r.returncode == 0, r.stdout + r.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _copy(self, name):
        import shutil
        dst = self.root / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(self.src, dst, symlinks=True)
        return dst

    def test_adopt_success_full_chain(self):
        ws = self._copy("ws-ok")
        r = _node2(["adopt", str(ws)], self.home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # tree kernel exited: scripts + VERSION gone, hold cleared
        self.assertFalse((ws / ".owfa" / "scripts" / "owfa_kernel.py").read_text().find("FORWARDER") == -1 or (ws / ".owfa" / "scripts" / "wikilib.py").exists(), "scripts must hold only the P2 forwarder")
        self.assertFalse((ws / ".owfa" / "VERSION").exists())
        self.assertFalse((ws / ".owfa" / "migrations" / "kernel-exit-hold").exists())
        # marker floor = tree VERSION; registry bound; kernel installed
        marker = (ws / ".owfa" / "WORKSPACE.yaml").read_text(encoding="utf-8")
        self.assertIn(f'kernel_compat: ">= {FW}"', marker)
        self.assertTrue((self.home / "kernel" / FW / "owfa_kernel.py").exists())
        self.assertIn(str(ws), (self.home / "workspaces.yaml").read_text(encoding="utf-8"))
        # doctor green through the user-level kernel
        d = _node2(["doctor", str(ws)], self.home)
        self.assertEqual(d.returncode, 0, d.stdout + d.stderr)
        self.assertIn(f"kernel source: user-level {FW}", d.stdout)
        return ws

    def test_adopt_is_idempotent(self):
        ws = self.test_adopt_success_full_chain()
        before = (ws / ".owfa" / "WORKSPACE.yaml").read_text(encoding="utf-8")
        r = _node2(["adopt", str(ws)], self.home)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("already adopted", r.stdout)
        self.assertEqual(before, (ws / ".owfa" / "WORKSPACE.yaml").read_text(encoding="utf-8"))

    def test_adopt_failure_rolls_back_park(self):
        ws = self._copy("ws-fail")
        # pre-existing damage (not ours): an unparsable manifest makes validate
        # fail THROUGH THE NEW KERNEL after the park — the whole adopt must undo
        import glob
        manifests = sorted(glob.glob(str(ws / ".owfa" / "plugins" / "domains" / "*" / "*" / "PLUGIN.yaml")))
        self.assertTrue(manifests)
        with open(manifests[0], "a", encoding="utf-8") as f:
            f.write("!!! [[ unparsable\n")
        r = _node2(["adopt", str(ws)], self.home)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all-or-nothing", r.stdout + r.stderr)
        # park restored exactly: scripts + VERSION back, no marker, no hold
        self.assertTrue((ws / ".owfa" / "scripts" / "owfa_kernel.py").exists())
        self.assertTrue((ws / ".owfa" / "VERSION").exists())
        self.assertFalse((ws / ".owfa" / "WORKSPACE.yaml").exists())
        self.assertFalse((ws / ".owfa" / "migrations" / "kernel-exit-hold").exists())
        self.assertNotIn(str(ws), (self.home / "workspaces.yaml").read_text(encoding="utf-8"))

    def test_adopt_refuses_interrupted_park(self):
        ws = self._copy("ws-int")
        hold = ws / ".owfa" / "migrations" / "kernel-exit-hold" / "scripts"
        hold.mkdir(parents=True)
        (hold / "owfa_kernel.py").write_text("# parked\n", encoding="utf-8")
        r = _node2(["adopt", str(ws)], self.home)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("interrupted adopt", r.stdout + r.stderr)
        # and the park is untouched (no implicit cleanup)
        self.assertTrue((hold / "owfa_kernel.py").exists())

    def test_m1_guards_after_adopt(self):
        """M1 in the new shape: the legacy channel still refuses an adopted tree."""
        ws = self.test_adopt_success_full_chain()
        r = _node2(["upgrade", str(ws)], self.home)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("WORKSPACE.yaml", r.stderr)
        r2 = _node2(["init", str(ws), "--force"], self.home)
        self.assertNotEqual(r2.returncode, 0)
        self.assertIn("WORKSPACE.yaml", r2.stderr + r2.stdout)


class RegistryTests(unittest.TestCase):
    """C (§4/G2): dangling lazy sweep + rescan rebuild."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir(parents=True)
        self.argv_out = self.root / "argv.json"
        _plant_fake_kernel(self.home, "9.9.9")

    def tearDown(self):
        self.tmp.cleanup()

    def _marker_ws(self, name, compat="9.9.9"):
        d = self.root / name
        (d / ".owfa").mkdir(parents=True)
        (d / ".owfa" / "WORKSPACE.yaml").write_text(f'kernel_compat: ">= {compat}"\n', encoding="utf-8")
        return d

    def test_dangling_entry_lazily_removed_on_list(self):
        live = self._marker_ws("live")
        gone = self.root / "gone"
        reg = self.home / "workspaces.yaml"
        reg.write_text(
            "workspaces:\n"
            "  - id: aaaaaaaa-0000-0000-0000-000000000001\n"
            f"    path: {live}\n"
            "    kernel: 9.9.9\n"
            '    compat: ">= 9.9.9"\n'
            "    registered: 2026-01-01T00:00:00Z\n"
            "  - id: aaaaaaaa-0000-0000-0000-000000000002\n"
            f"    path: {gone}\n"
            "    kernel: 9.9.9\n"
            '    compat: ">= 9.9.9"\n'
            "    registered: 2026-01-01T00:00:00Z\n",
            encoding="utf-8",
        )
        r = _node2(["workspaces", "list"], self.home)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("dangling", r.stdout)
        self.assertIn("re-adopt", r.stdout)
        text = reg.read_text(encoding="utf-8")
        self.assertIn(str(live), text)
        self.assertNotIn(str(gone), text)

    def test_rescan_rebuilds_from_disk(self):
        a = self._marker_ws("alpha")
        b = self._marker_ws("beta")
        # pre-register alpha by hand (its id must survive the rescan); a stale
        # entry for a vanished path must be dropped
        reg = self.home / "workspaces.yaml"
        reg.write_text(
            "workspaces:\n"
            "  - id: bbbbbbbb-0000-0000-0000-00000000000a\n"
            f"    path: {a}\n"
            "    kernel: 9.9.9\n"
            '    compat: ">= 9.9.9"\n'
            "    registered: 2026-01-01T00:00:00Z\n"
            "  - id: bbbbbbbb-0000-0000-0000-0000000000z\n"
            f"    path: {self.root / 'vanished'}\n"
            "    kernel: 9.9.9\n"
            '    compat: ">= 9.9.9"\n'
            "    registered: 2026-01-01T00:00:00Z\n",
            encoding="utf-8",
        )
        r = _node2(["workspaces", "rescan", "--under", str(self.root)], self.home)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        text = reg.read_text(encoding="utf-8")
        self.assertIn(str(a), text)
        self.assertIn(str(b), text)
        self.assertIn("bbbbbbbb-0000-0000-0000-00000000000a", text)  # id preserved
        self.assertNotIn("vanished", text)
        r2 = _node2(["workspaces", "list"], self.home)
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(r2.stdout.count("path-"), 0)  # sanity: list is clean


if __name__ == "__main__":
    unittest.main(verbosity=2)
