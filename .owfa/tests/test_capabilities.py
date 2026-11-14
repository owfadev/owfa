"""v0.4 capability (needs/provides) + suite-kind + INDEX-extension unit tests.

Synthetic packages and disposable instances only; registry-channel cases use a
local git repo + a local ROOT/INDEX.yaml (load_index reads the local file first,
so no network is ever touched).

Run: python -m unittest discover -s .owfa/tests -p test_capabilities.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FRAMEWORK = Path(__file__).resolve().parents[2]


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kernel-cap-test-")
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
        # v0.4 final shape: the framework tree ships no plugins — the synthetic
        # instances bootstrap exactly like a real init (embedded personal suite)
        result = self.run_kernel("install", "personal", "--path", str(FRAMEWORK / "payloads" / "personal"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_kernel("all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_kernel(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / ".owfa/scripts/owfa_kernel.py"), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8")

    # ---- synthetic package builders ----

    def manifest(self, name, inject, depends="[domain, wiki, trust, log]", parent=None):
        directory = (parent or self.source) / name
        directory.mkdir(parents=True, exist_ok=True)
        dependencies = "".join(f"  - {item.strip()}\n" for item in depends.strip("[]").split(","))
        (directory / "PLUGIN.yaml").write_text(
            f"id: {name}\nschema_version: 1\nversion: 0.1\nupdated: 2026-11-12\n"
            f"depends:\n{dependencies}attachment: []\nfields:\n"
            f"inject: {json.dumps(inject, ensure_ascii=False)}\n", encoding="utf-8")
        (directory / "PLUGIN.md").write_text("# Synthetic test plugin\n", encoding="utf-8")

    def pkg_dir(self, pid, caps="", version="0.1"):
        """A package root self.source/<pid>pkg/ holding PKG.yaml + the member dir."""
        directory = self.source / f"{pid}pkg"
        if not (directory / pid).exists():
            self.manifest(pid, f"{pid} synthetic member", parent=directory)
        lines = ["schema_version: 1", f"id: {pid}", f"version: {version}", "compat: '>= 0.3'",
                 f"members: [{pid}]", "depends: [framework]"]
        lines += [l for l in caps.splitlines() if l.strip()]
        (directory / "PKG.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return directory

    def install_path(self, pid, *extra):
        return self.run_kernel("install", pid, "--path", str(self.source / f"{pid}pkg"), *extra)

    def git_pkg(self, pid, version, provides=None, needs=None):
        """A local git repo package (registry-channel source) + tags; returns the repo path."""
        repo = Path(self.temp.name) / "git" / pid
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        self.manifest(pid, f"{pid} registry member", parent=repo)
        lines = ["schema_version: 1", f"id: {pid}", f"version: {version}", "compat: '>= 0.3'",
                 f"members: [{pid}]", "depends: [framework]"]
        if provides:
            lines.append(f"provides: [{', '.join(provides)}]")
        if needs:
            lines.append(f"needs: [{', '.join(needs)}]")
        (repo / "PKG.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.git(repo, "init", "-q")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "pkg")
        self.git(repo, "tag", f"{pid}-v{version}")
        return repo

    def git(self, repo, *args):
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def git_head(self, repo):
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()

    def index(self, rows):
        lines = ["packages:"] + [f"  {name}: {{{body}}}" for name, body in rows]
        (self.root / "INDEX.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- grammar / prefix ----

    def test_grammar_and_prefix_rule(self):
        self.pkg_dir("probe", caps="needs: [Bad.Cap]\nprovides: [other.org.v1]")
        result = self.install_path("probe")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("fails the capability grammar", result.stdout)
        self.assertIn("first name segment must equal the package id", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/probe").exists())
        # the prefix message and the grammar message are both reported (one per entry)

    def test_owfa_prefix_and_own_namespace_pass_grammar(self):
        # owfa.* is the framework-owned namespace; a non-owfa capability named after
        # the declaring package is the legal third-party form — both pass grammar
        self.pkg_dir("probe", caps="provides: [probe.transport.v1, owfa.net.v1]")
        result = self.install_path("probe")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # ---- exact-name matching ----

    def test_v2_gap_is_reported_as_different_version(self):
        self.pkg_dir("prov", caps="provides: [owfa.org.v1]")
        self.assertEqual(self.install_path("prov").returncode, 0)
        self.pkg_dir("needr", caps="needs: [owfa.org.v2]")
        result = self.install_path("needr")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("present at different version", result.stdout)
        self.assertIn("exact-name", result.stdout)

    def test_unknown_capability_is_missing_entirely(self):
        self.pkg_dir("needr", caps="needs: [owfa.im.v1]")
        result = self.install_path("needr")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("capability missing entirely", result.stdout)
        self.assertNotIn("different version", result.stdout)

    # ---- exclusive slot ----

    def test_exclusive_slot_refuses_second_provider(self):
        self.pkg_dir("alpha", caps="provides: [owfa.org.v1]")
        self.assertEqual(self.install_path("alpha").returncode, 0)
        self.pkg_dir("beta", caps="provides: [owfa.org.v1]")
        result = self.install_path("beta")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("exclusive", result.stdout)
        self.assertIn("alpha", result.stdout)
        self.assertIn("beta", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/beta").exists())

    # ---- trust gate ----

    def test_unverified_provider_needs_yes_and_journals(self):
        # provider installed via --path (no INDEX row): provides are unverified
        self.pkg_dir("prov", caps="provides: [owfa.org.v1]")
        self.assertEqual(self.install_path("prov").returncode, 0)
        self.pkg_dir("needr", caps="needs: [owfa.org.v1]")
        result = self.install_path("needr")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("unverified trust", result.stdout)
        journal = (self.root / ".owfa/kernel-journal.log").read_text(encoding="utf-8")
        self.assertNotIn("trust-override", journal)
        result = self.install_path("needr", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        journal = (self.root / ".owfa/kernel-journal.log").read_text(encoding="utf-8")
        self.assertIn("trust-override needr", journal)

    def test_reviewed_registry_provider_satisfies_needs(self):
        repo = self.git_pkg("prov", "0.1", provides=["owfa.org.v1"])
        self.index([("prov", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: prov")])
        self.assertEqual(self.run_kernel("install", "prov").returncode, 0)
        self.pkg_dir("needr", caps="needs: [owfa.org.v1]")
        result = self.install_path("needr")  # no --yes: the trusted provider satisfies
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # ---- prospective set (upgrade sole provider) ----

    def test_upgrade_of_sole_provider_passes_prospective_preflight(self):
        repo = self.git_pkg("prov", "0.1", provides=["owfa.org.v1"])
        self.index([("prov", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: prov")])
        self.assertEqual(self.run_kernel("install", "prov").returncode, 0)
        self.pkg_dir("needr", caps="needs: [owfa.org.v1]")
        self.assertEqual(self.install_path("needr").returncode, 0)
        # bump the provider: v0.2 still provides owfa.org.v1
        lines = (repo / "PKG.yaml").read_text(encoding="utf-8").replace("version: 0.1", "version: 0.2")
        (repo / "PKG.yaml").write_text(lines, encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "prov-v0.2")
        self.index([("prov", f"repo: {repo}, version: 0.2, trust: reviewed-3rd-party, members: prov")])
        # mid-upgrade the disk briefly lacks the sole provider — the prospective
        # board (installed − old provides + new provides) must let it through
        result = self.run_kernel("upgrade", "prov", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0.1 -> v0.2", result.stdout)
        self.assertEqual(self.run_kernel("validate").returncode, 0)

    # ---- INDEX extension ----

    def test_index_parses_needs_provides_commit_and_strips_single_quotes(self):
        self.index([
            ("prov", "repo: 'https://x/y.git', version: 0.1, trust: 'reviewed-3rd-party', "
                     "members: a/b, needs: owfa.org.v1/qq.im.v1, provides: prov.org.v1/owfa.net.v1, commit: 'ABC123'"),
            ("bare", 'repo: "https://x/z.git", version: 0.2, trust: framework-bundled, members: z'),
        ])
        prefix = "import sys; sys.path.insert(0, '.owfa/scripts'); import owfa_kernel as k; "
        code = ("e,s=k.load_index([]); import json; "
                "print(json.dumps({'trust': e['prov']['trust'], 'commit': e['prov'].get('commit'), "
                "'needs': k._cap_list(e['prov'].get('needs')), "
                "'provides': k._cap_list(e['prov'].get('provides')), "
                "'bare_needs': k._cap_list(e['bare'].get('needs')), "
                "'bare_commit': e['bare'].get('commit')}))")
        r = subprocess.run([sys.executable, "-c", prefix + code], cwd=self.root,
                           env=self.env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["trust"], "reviewed-3rd-party")  # single quotes stripped
        self.assertEqual(data["commit"], "ABC123")
        self.assertEqual(data["needs"], ["owfa.org.v1", "qq.im.v1"])  # '/'-separated
        self.assertEqual(data["provides"], ["prov.org.v1", "owfa.net.v1"])
        self.assertEqual(data["bare_needs"], [])                    # absent = empty set
        self.assertIsNone(data["bare_commit"])                     # absent = no pin

    def test_commit_pin_mismatch_is_refused(self):
        repo = self.git_pkg("prov", "0.1", provides=["owfa.org.v1"])
        self.index([("prov", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: prov, "
                             f"commit: {'0' * 40}")])
        result = self.run_kernel("install", "prov")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("commit pin mismatch", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/probe").exists())

    def test_commit_pin_match_installs(self):
        repo = self.git_pkg("prov", "0.1", provides=["owfa.org.v1"])
        self.index([("prov", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: prov, "
                             f"commit: {self.git_head(repo)}")])
        result = self.run_kernel("install", "prov")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # ---- suite kind ----

    def test_rootless_suite_validates_green(self):
        # rootless suite: parallel members, no root plugin — family-root/closure
        # laws must not apply (the owfa-personal shape; id "synth" — the real
        # "personal" suite is already installed by the v0.4 bootstrap setUp)
        suite = self.source / "synthpkg"
        suite.mkdir()
        for name, deps in (("swiki", "[]"), ("slog", "[swiki]")):
            member = suite / name
            member.mkdir()
            dependencies = ("depends: []\n" if deps == "[]" else "depends:\n  - swiki\n")
            (member / "PLUGIN.yaml").write_text(
                f"id: {name}\nschema_version: 1\nversion: 0.1\nupdated: 2026-11-12\n"
                f"{dependencies}attachment: []\nfields:\n"
                f'inject: "{name} suite member (synthetic)"\n', encoding="utf-8")
            (member / "PLUGIN.md").write_text("# member\n", encoding="utf-8")
        (suite / "PKG.yaml").write_text(
            "id: synth\nkind: suite\nversion: 0.1.0\ncompat: '>= 0.3'\n"
            "members: [swiki, slog]\ndepends: [framework]\n", encoding="utf-8")
        result = self.run_kernel("install", "synth", "--path", str(suite))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.run_kernel("validate").returncode, 0)
        # the same roster WITHOUT kind: suite must fail the family-root laws
        (suite / "PKG.yaml").write_text(
            "id: synth\nversion: 0.1.0\ncompat: '>= 0.3'\n"
            "members: [swiki, slog]\ndepends: [framework]\n", encoding="utf-8")
        self.run_kernel("uninstall", "synth", "--yes")
        result = self.run_kernel("install", "synth", "--path", str(suite))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("family root synth must be a member", result.stdout)

    def test_unknown_kind_is_rejected(self):
        suite = self.source / "weirdpkg"
        suite.mkdir()
        self.manifest("weird", "weird member", parent=suite)
        (suite / "PKG.yaml").write_text(
            "id: weird\nkind: platform\nversion: 0.1\ncompat: '>= 0.3'\n"
            "members: [weird]\ndepends: [framework]\n", encoding="utf-8")
        result = self.run_kernel("install", "weird", "--path", str(suite))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("kind (platform) must be 'suite' or 'domain-family'", result.stdout)

    # ---- provides command (instance view) ----

    def test_kernel_provides_reports_satisfaction(self):
        self.pkg_dir("prov", caps="provides: [owfa.org.v1, prov.util.v1]")
        self.assertEqual(self.install_path("prov").returncode, 0)
        self.pkg_dir("needr", caps="needs: [owfa.org.v1]")
        self.assertEqual(self.install_path("needr", "--yes").returncode, 0)
        result = self.run_kernel("provides")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("pkg prov: provides owfa.org.v1, prov.util.v1", result.stdout)
        # unverified (--path) provides are annotated as such
        self.assertIn("trust: unknown — unverified provides", result.stdout)
        self.assertIn("needs owfa.org.v1 — satisfied by UNVERIFIED provides", result.stdout)
        # uninstall is not a capability convergence point: the need goes unsatisfied
        # (red validate) while the uninstall itself succeeds — the instance view reports it
        self.assertEqual(self.run_kernel("uninstall", "prov", "--yes").returncode, 0)
        result = self.run_kernel("provides")
        self.assertIn("needs owfa.org.v1 — NOT satisfied: capability missing entirely", result.stdout)


if __name__ == "__main__":
    unittest.main()
