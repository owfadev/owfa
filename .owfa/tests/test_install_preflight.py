"""Offline install regressions; synthetic packages and disposable instances only.

Run: python -m unittest discover -s .owfa/tests -p test_install_preflight.py -v
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FRAMEWORK = Path(__file__).resolve().parents[2]


class InstallPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kernel-install-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "instance"
        self.root.mkdir()
        for directory in (".meta", ".agents"):
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

    def run_code(self, code):
        prefix = "import sys; sys.path.insert(0, '.owfa/scripts'); import owfa_kernel as k; "
        return subprocess.run([sys.executable, "-c", prefix + code], cwd=self.root,
                              env=self.env, capture_output=True, text=True, encoding="utf-8")

    def manifest(self, name, inject, depends="[domain, wiki, trust, log]", tier=None):
        directory = self.source / name
        directory.mkdir(exist_ok=True)
        dependencies = "".join(f"  - {item.strip()}\n" for item in depends.strip("[]").split(","))
        text = (f"id: {name}\nschema_version: 1\nversion: 0.1\nupdated: 2026-10-24\n"
                f"depends:\n{dependencies}attachment: []\nfields:\n"
                f"inject: {json.dumps(inject, ensure_ascii=False)}\n")
        if tier:
            text += f"inject_tier: {tier}\n"
        (directory / "PLUGIN.yaml").write_text(text, encoding="utf-8")
        (directory / "PLUGIN.md").write_text("# Synthetic test plugin\n", encoding="utf-8")

    def package(self, inject="Synthetic test", members="[probe]"):
        (self.source / "PKG.yaml").write_text(
            "schema_version: 1\nid: probe\nversion: 0.1\ncompat: '>= 0.3'\n"
            f"members: {members}\ndepends: [framework]\n", encoding="utf-8")
        self.manifest("probe", inject)

    def install(self, *extra):
        return self.run_kernel("install", "probe", "--path", str(self.source), *extra)

    def snapshot(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob("*") if path.is_file()}

    def budget_text(self, extra=0):
        result = self.run_code(
            "p,e=k.load_plugins(); assert not e; b,_=k.build_inject_blocks(p); "
            "print(k.INJECT_BUDGET-sum(len(x.encode('utf-8')) for x in b))")
        self.assertEqual(result.returncode, 0, result.stderr)
        overhead = len("<!-- plugin:probe v0.1 -->\n- \n<!-- /plugin:probe -->".encode("utf-8"))
        room = int(result.stdout.strip()) - overhead + extra
        return "界" * (room // 3) + "x" * (room % 3)

    def test_over_budget_leaves_all_instance_state_unchanged(self):
        self.package(self.budget_text(extra=1))
        # These would all land or change if rejection happened after copy/staging.
        for relative in ("connectors/test-connector/file.txt", "command/test-command/file.txt",
                         "migrations/init.md"):
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Synthetic payload", encoding="utf-8")
        ledger = self.root / ".owfa/migrations/pending.json"
        ledger.parent.mkdir(exist_ok=True)
        ledger.write_text(json.dumps({"probe": {"kind": "teardown", "items": []}}), encoding="utf-8")
        before = self.snapshot()
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("over the 16384 B budget", result.stdout)
        self.assertIn("preflight failed", result.stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue((self.source / "probe/PLUGIN.yaml").exists())

    def test_exact_utf8_budget_installs_and_converges(self):
        self.package(self.budget_text())
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugin:probe", (self.root / "AGENTS.md").read_text(encoding="utf-8"))
        result = self.run_kernel("all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_without_cascade_uses_only_the_installed_subset(self):
        self.package(members="[probe, optional, child]")
        self.manifest("optional", "界" * 6000, depends="[probe]")
        self.manifest("child", "界" * 6000, depends="[optional]")
        result = self.install("--without", "optional")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = self.root / ".owfa/plugins/domains/probe"
        self.assertFalse((installed / "optional").exists())
        self.assertFalse((installed / "child").exists())
        self.assertEqual(self.run_kernel("validate").returncode, 0)

    def test_member_tier_does_not_consume_injection_budget(self):
        self.package(members="[probe, member]")
        self.manifest("member", "界" * 6000, depends="[probe]", tier="member")
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("plugin:member", (self.root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_duplicate_installed_id_is_rejected_before_copy(self):
        self.package(members="[probe, language]")
        self.manifest("language", "Duplicate", depends="[probe]")
        before = self.snapshot()
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("duplicate plugin id", result.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_post_copy_binding_failure_returns_nonzero_and_warns(self):
        self.package()
        path = self.source / "probe/PLUGIN.yaml"
        path.write_text(path.read_text(encoding="utf-8") + "commands:\n  - missing-command\n", encoding="utf-8")
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("install incomplete", result.stdout)
        self.assertIn("missing command", result.stdout)
        self.assertTrue((self.root / ".owfa/plugins/domains/probe/PKG.yaml").exists())

    def test_projection_failure_returns_nonzero(self):
        self.package()
        (self.root / "AGENTS.md").write_text("# Missing injection markers\n", encoding="utf-8")
        result = self.install()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("projection failed (do_inject)", result.stdout)
        self.assertIn("install incomplete", result.stdout)

    def test_semantic_init_stays_pending_without_becoming_mechanical_failure(self):
        self.package()
        migration = self.source / "migrations/init.md"
        migration.parent.mkdir()
        migration.write_text("# Synthetic manual initialization\n", encoding="utf-8")
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("semantic migration staged", result.stdout)
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("pending semantic migration", result.stdout)

    def test_deploy_failure_is_propagated(self):
        self.package()
        result = self.run_code(
            "k.do_deploy=lambda: False; "
            f"sys.exit(k.do_install('probe', ['--path', {str(self.source)!r}]))")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("deployment failed", result.stdout)
        self.assertIn("install incomplete", result.stdout)


if __name__ == "__main__":
    unittest.main()
