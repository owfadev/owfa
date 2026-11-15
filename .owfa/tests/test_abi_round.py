"""ABI round unit tests (abi-spec §4.2 compat_match + §5 R11 two-state validation).

Group A — compat_match: the single interval parser/evaluator, table-driven over
every op's missing-segment semantics, the boundary case (2.0.0 vs "<2.0"), AND
composition, and the illegal-string refusals. Version-sensitive anchors are
derived from the fixture .owfa/VERSION, never hard-written (bump-proof).

Group B — R11 two-state: absent abi block = warning (0.4.x window, error at
0.5.0); present-but-illegal (semantics not exactly the four / package-root
proto_query.py missing) = error; legal block + script passes install, validate
and the audit ABI smoke.

Synthetic packages and disposable instances only (the test_protocol_kind.py
construction idiom: temp instance + fake packages + kernel subprocess runs,
asserting exit codes and stdout/stderr).

Run: python -m unittest discover -s .owfa/tests -p test_abi_round.py -v
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FRAMEWORK = Path(__file__).resolve().parents[2]
KERNEL = FRAMEWORK / ".owfa" / "scripts" / "owfa_kernel.py"

_spec = importlib.util.spec_from_file_location("abi_round_kernel", KERNEL)
k = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k)

# version anchors derived from the fixture VERSION (X.Y.Z) — never hard-written
_fw = k.framework_version()
assert _fw is not None and len(_fw) == 3, "fixture .owfa/VERSION must carry X.Y.Z"
MAJOR, MINOR, PATCH = _fw
NEXT_MINOR = f"{MAJOR}.{MINOR + 1}"          # e.g. 0.5 line while on 0.4.x
THIS_LINE = f"{MAJOR}.{MINOR}"               # e.g. 0.4


class CompatMatchTests(unittest.TestCase):
    """abi-spec §4.2: interval := comparator { " " comparator }, op glued to version,
    space = AND; ordering ops fill missing segments with the LOWEST value,
    "=" is a prefix match."""

    # ---- table: (version, interval, expected) ----

    def test_table(self):
        table = [
            # canonical examples from the spec
            ("1.5.2", ">=1.0 <2.0", True),
            ("2.0.0", ">=1.0 <2.0", False),
            ("0.9.9", ">=1.0 <2.0", False),
            ("1.2.3", "=1.2.3", True),
            ("1.2.9", "=1.2.3", False),
            # >= missing segments take the lowest value (>=0.8 includes 0.8.0)
            ("0.8.0", ">=0.8", True),
            ("0.8.1", ">=0.8", True),
            ("0.7.9", ">=0.8", False),
            ("1.0.0", ">=1", True),
            ("0.9.0", ">=1", False),
            # > : lowest-value fill means >2.0 excludes 2.0.0 itself
            ("2.0.0", ">2.0", False),
            ("2.0.1", ">2.0", True),
            ("2.1.0", ">1", True),
            ("0.9.0", ">1", False),
        ]
        for version, interval, expected in table:
            with self.subTest(version=version, interval=interval):
                self.assertEqual(k.compat_match(version, interval), expected)

    def test_missing_segments_per_op(self):
        # the boundary the spec pins: "<2.0" <=> excludes 2.0.0 and above
        for v in ["2.0.0", "2.0.1", "2.5.0", "3.0.0"]:
            self.assertFalse(k.compat_match(v, "<2.0"), v)
        for v in ["1.9.9", "1.0.0", "0.0.1"]:
            self.assertTrue(k.compat_match(v, "<2.0"), v)
        # <= with missing segments: <=2.0 includes 2.0.0
        self.assertTrue(k.compat_match("2.0.0", "<=2.0"))
        self.assertFalse(k.compat_match("2.0.1", "<=2.0"))
        # < exact three segments behaves normally
        self.assertTrue(k.compat_match("1.9.9", "<2.0.0"))
        self.assertFalse(k.compat_match("2.0.0", "<2.0.0"))
        # "=" is prefix match: =1.2 <=> 1.2.*
        for v in ["1.2.0", "1.2.9", "1.2"]:
            self.assertTrue(k.compat_match(v, "=1.2"), v)
        for v in ["1.20.0", "1.3.0", "2.1.3"]:
            self.assertFalse(k.compat_match(v, "=1.2"), v)
        # single-segment prefix: =1 <=> 1.*
        self.assertTrue(k.compat_match("1.9.9", "=1"))
        self.assertFalse(k.compat_match("2.0.0", "=1"))

    def test_boundary_derived_from_fixture_version(self):
        # anchors ride the fixture VERSION: the next minor line's floor excludes
        # this line's versions, this line's floor includes them (bump-proof)
        self.assertTrue(k.compat_match(f"{MAJOR}.{MINOR}.{PATCH}", f">={THIS_LINE}"))
        self.assertFalse(k.compat_match(f"{MAJOR}.{MINOR}.{PATCH}", f">={NEXT_MINOR}"))
        # the R11 switch point: "<{NEXT_MAJOR}" boundary uses lowest-value fill
        next_major = f"{MAJOR + 1}"
        self.assertTrue(k.compat_match(f"{MAJOR}.{MINOR}.{PATCH}", f"<{next_major}"))
        self.assertFalse(k.compat_match(f"{next_major}.0.0", f"<{next_major}"))
        self.assertFalse(k.compat_match(f"{next_major}.0.1", f"<{next_major}"))

    def test_and_composition_requires_every_comparator(self):
        # anchors derived from the fixture VERSION line (grammar example, but the
        # line numbers stay bump-proof): >=THIS <NEXT admits this line's patches,
        # rejects the next line and the line below
        interval = f">={THIS_LINE} <{NEXT_MINOR}"
        this_patch = f"{MAJOR}.{MINOR}.{PATCH}"
        prev_patch = f"{MAJOR}.{MINOR}.{max(PATCH - 1, 0)}"
        self.assertTrue(k.compat_match(this_patch, interval))
        self.assertFalse(k.compat_match(f"{NEXT_MINOR}.0", interval))
        if MINOR:  # fixture sits on minor >= 1 (0.4.x) — the minor-below anchor exists
            self.assertFalse(k.compat_match(f"{MAJOR}.{MINOR - 1}.9", interval))
        # a narrower AND never widens: adding =prev excludes other patches
        self.assertFalse(k.compat_match(this_patch, f">={THIS_LINE} <{NEXT_MINOR} ={prev_patch}"))
        self.assertTrue(k.compat_match(prev_patch, f">={THIS_LINE} <{NEXT_MINOR} ={prev_patch}"))

    def test_illegal_intervals_raise(self):
        for bad in ["", "   ", "1.0", ">=1.0.0.0", "=x.y", "1.0 <2.0",
                    ">=1.0 extra", "~1.0", "^1.0", "==1.0", "=>1.0", "=<1.0",
                    ">= 1.0", "< 2.0", ">=1.", ">=.1", ">=1..2"]:
            with self.subTest(interval=bad):
                self.assertRaises(ValueError, k.compat_match, "1.0.0", bad)

    def test_illegal_version_raises(self):
        for bad in ["", "x.y.z", "1.x", "1..2", "v1.0.0", "1.0.0.0", None]:
            with self.subTest(version=bad):
                self.assertRaises(ValueError, k.compat_match, bad, ">=1.0")


class R11TwoStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kernel-abi-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "instance"
        self.root.mkdir()
        for directory in (".owfa", ".agents"):
            shutil.copytree(FRAMEWORK / directory, self.root / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "smoke-tmp"))
        (self.root / "AGENTS.md").write_text(
            "# Synthetic instance\n<!-- wiki-inject:start -->\n<!-- wiki-inject:end -->\n",
            encoding="utf-8")
        self.source = Path(self.temp.name) / "source"
        self.source.mkdir()
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        self.env.pop("PYTHONPATH", None)
        result = self.run_kernel("all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_kernel(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / ".owfa/scripts/owfa_kernel.py"), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8")

    # ---- synthetic protocol package builder (test_protocol_kind idiom) ----

    def manifest(self, name, parent):
        directory = parent / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "PLUGIN.yaml").write_text(
            f"id: {name}\nschema_version: 1\nversion: 0.1\nupdated: 2026-11-15\ndepends: []\n"
            f"attachment: []\nfields:\ninject: \"{name} synthetic member\"\n",
            encoding="utf-8")
        (directory / "PLUGIN.md").write_text("# Synthetic test plugin\n", encoding="utf-8")

    def proto_pkg(self, pid, abi_yaml=None, with_script=True):
        """Build self.source/<pid>src/ : a kind:protocol package; abi_yaml is the raw
        `abi:` block text (None = absent), with_script controls package-root proto_query.py."""
        directory = self.source / f"{pid}src"
        if directory.exists():
            shutil.rmtree(directory)
        self.manifest(f"{pid}m", directory)
        lines = ["schema_version: 1", f"id: {pid}", "version: 0.1", "compat: '>= 0.3'",
                 f"members: [{pid}m]", "depends: [framework]", "kind: protocol",
                 "protocol: vaultwiki", "provides: [vaultwiki.org.v1]"]
        if abi_yaml is not None:
            lines.append(abi_yaml.rstrip("\n"))
        (directory / "PKG.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if with_script:
            (directory / "proto_query.py").write_text(
                "# synthetic ABI entry point: unknown kind -> empty result, exit 0\n"
                "import sys\n"
                "print('{\"ok\": true, \"semantic\": \"list\", \"count\": 0, \"items\": []}')\n",
                encoding="utf-8")
        return directory

    ABI_OK = ("abi:\n"
              "  semantics: [list, get, search, recent]\n"
              "  search_lang: \"full-name prefix + grep substring\"\n"
              "  addr_doc: docs/abi.md")

    def install(self, pid):
        return self.run_kernel("install", pid, "--path", str(self.source / f"{pid}src"))

    # ---- state 1: absent abi block -> warning, never an error (0.4.x window) ----

    def test_absent_abi_block_warns_but_installs(self):
        self.proto_pkg("pw", abi_yaml=None)
        result = self.install("pw")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # warning copy rides the fixture VERSION line: the flip point is the next
        # minor (0.5.0 while the fixture is 0.4.x) — bump-proof
        self.assertIn(f"kind:protocol without abi block — ABI becomes mandatory at {NEXT_MINOR}.0 (R11)", result.stdout)
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[warning] PKG pw: kind:protocol without abi block", result.stdout)

    # ---- the 0.5.0 flip: missing block escalates warning -> error ----

    def test_absent_abi_block_flips_to_error_at_0_5_0(self):
        # guard the R11 switch: inject the framework version (no real VERSION
        # bump) — from the 0.5 line the missing block is an error, the copy
        # carries the injected version, and the 0.4.x window stays a warning
        errs, warns = k.abi_block_issues("pw", {}, default_framework_version=(0, 5, 0))
        self.assertTrue(errs and not warns)
        self.assertIn("kind:protocol without abi block", errs[0])
        self.assertIn("mandatory at 0.5", errs[0])
        # boundary: 0.4.9 (last of the window) still warns with the 0.4.x copy
        errs, warns = k.abi_block_issues("pw", {}, default_framework_version=(0, 4, 9))
        self.assertFalse(errs)
        self.assertEqual(len(warns), 1)
        self.assertIn("becomes mandatory at 0.5.0", warns[0])
        # and the live fixture version (0.4.x today) behaves as the window
        errs, warns = k.abi_block_issues("pw", {})
        self.assertFalse(errs)
        self.assertEqual(len(warns), 1)

    # ---- state 2: block present but illegal -> error ----

    def test_present_block_without_proto_query_errors(self):
        self.proto_pkg("pw", abi_yaml=self.ABI_OK, with_script=False)
        result = self.install("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("proto_query.py is missing", result.stdout)
        self.assertIn("R11", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    def test_present_block_bad_semantics_errors(self):
        for abi in [
            "abi:\n  semantics: [list, get, search]\n  search_lang: \"x\"",
            "abi:\n  semantics: [list, get, search, recent, extra]\n  search_lang: \"x\"",
            "abi:\n  semantics: [list, get, grep, recent]\n  search_lang: \"x\"",
            "abi:\n  search_lang: \"x\"",  # semantics absent entirely
        ]:
            with self.subTest(abi=abi.splitlines()[1] if len(abi.splitlines()) > 1 else abi):
                self.proto_pkg("pw", abi_yaml=abi)
                result = self.install("pw")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("abi.semantics must be exactly list, get, search, recent (R11)", result.stdout)
                self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    def test_present_block_bad_fields_errors(self):
        # missing search_lang
        self.proto_pkg("pw", abi_yaml="abi:\n  semantics: [list, get, search, recent]")
        result = self.install("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("abi.search_lang", result.stdout)
        # unknown key
        self.proto_pkg("pw", abi_yaml=self.ABI_OK + "\n  bogus_key: 1")
        result = self.install("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("unknown key(s) bogus_key", result.stdout)

    # ---- the legal block: install green, validate green, audit smoke green ----

    def test_legal_abi_block_passes_and_smokes(self):
        self.proto_pkg("pw", abi_yaml=self.ABI_OK, with_script=True)
        result = self.install("pw")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("R11", result.stdout)
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("abi block", result.stdout)
        result = self.run_kernel("audit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("(pw) ABI smoke ok", result.stdout)

    def test_audit_smoke_fails_on_dead_script(self):
        self.proto_pkg("pw", abi_yaml=self.ABI_OK, with_script=True)
        self.assertEqual(self.install("pw").returncode, 0)
        # break the live script after install: nonzero exit must fail the audit
        script = self.root / ".owfa/plugins/domains/pw/proto_query.py"
        script.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        result = self.run_kernel("audit")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ABI smoke", result.stdout)
        self.assertIn("exited 3", result.stdout)

    def test_audit_smoke_times_out(self):
        self.proto_pkg("pw", abi_yaml=self.ABI_OK, with_script=True)
        self.assertEqual(self.install("pw").returncode, 0)
        script = self.root / ".owfa/plugins/domains/pw/proto_query.py"
        script.write_text("import time\ntime.sleep(120)\n", encoding="utf-8")
        result = self.run_kernel("audit")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("timed out", result.stdout)


if __name__ == "__main__":
    unittest.main()
