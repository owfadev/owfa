"""Upgrade atomicity tests (issue #72) + step2 review Low regressions.

`kernel upgrade <pkg> --yes` runs uninstall -> install. When the install half
fails, the completed first half (old package already uninstalled) used to be
treated as orphaned residue by the journal sweep — destroying the parked old
package state and the projections. The invariant under test: a failed upgrade
is non-destructive (rolled back whole, or held with an explicit marker the
sweep refuses).

Run: python -m unittest discover -s .owfa/tests -p test_upgrade_atomicity.py -v
"""
import glob
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FRAMEWORK = Path(__file__).resolve().parents[2]


class UpgradeAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kernel-upgrade-atomic-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "instance"
        self.root.mkdir()
        for directory in (".owfa", ".agents"):
            shutil.copytree(FRAMEWORK / directory, self.root / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
        (self.root / "AGENTS.md").write_text(
            "# Synthetic instance\n<!-- wiki-inject:start -->\n<!-- wiki-inject:end -->\n",
            encoding="utf-8")
        self.source = Path(self.temp.name) / "source"
        self.source.mkdir()
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        self.env.pop("PYTHONPATH", None)
        self.assertEqual(self.run_kernel("all").returncode, 0)

    def run_kernel(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / ".owfa/scripts/owfa_kernel.py"), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8")

    def git(self, repo, *args):
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def proto_pkg(self, pid, version, provides, kind="protocol", members=None):
        """A local git repo package + tag; returns the repo path."""
        directory = self.source / f"{pid}src"
        if directory.exists():
            shutil.rmtree(directory)
        members = members or [f"{pid}m"]
        for m in members:
            d = directory / m
            d.mkdir(parents=True)
            usage = (f"\n  - synthetic usage line for the binding checks" if m == members[0] else "")
            # members[0] owns the command projection: claims it, carries a usage list
            commands = f"\ncommands:\n  - {m}" if m == members[0] else ""
            (d / "PLUGIN.yaml").write_text(
                f"id: {m}\nschema_version: 1\nversion: {version}\nupdated: 2026-11-15\n"
                f"depends: []\nattachment: []\nfields: {{}}{commands}\n"
                f"inject: \"{m} projection line (upgrade atomicity fixture)\"\nusage:{usage or ' []'}\n",
                encoding="utf-8")
            (d / "PLUGIN.md").write_text("# synthetic member\n", encoding="utf-8")
        lines = [f"schema_version: 1", f"id: {pid}", f"version: {version}", "compat: '>= 0.3'",
                 f"members: [{', '.join(members)}]", "depends: [framework]",
                 "connectors:", f"  - name: {pid}tool"]
        if kind:
            lines.append(f"kind: {kind}")
        if kind == "protocol":
            lines.append("protocol: vaultwiki")
            # R11 (from the 0.5 line the missing block is an install-refusing
            # error): fixtures under test for upgrade atomicity carry a legal
            # block so the R11 gate cannot mask the behaviors under test
            lines += ["abi:", "  semantics: [list, get, search, recent]",
                      "  search_lang: \"synthetic test protocol search semantics\"",
                      "  addr_doc: docs/abi.md"]
        if provides:
            lines.append(f"provides: [{', '.join(provides)}]")
        (directory / "PKG.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if kind == "protocol":
            # R11: package-root ABI entry point accompanies the declared block
            (directory / "proto_query.py").write_text(
                "# synthetic ABI entry point: unknown kind -> empty result, exit 0\n"
                "import sys\n"
                "print('{\"ok\": true, \"semantic\": \"list\", \"count\": 0, \"items\": []}')\n",
                encoding="utf-8")
        # F1 (#72 review): fixture packages carry connectors/ and command/ projections —
        # uninstall removes them and the rollback must bring them back
        tool = directory / "connectors" / f"{pid}tool"
        tool.mkdir(parents=True, exist_ok=True)
        (tool / "cli.py").write_text("# synthetic connector\n", encoding="utf-8")
        (tool / "SKILL.md").write_text(f"---\nowner: framework\n---\n# {pid}tool\n", encoding="utf-8")
        cmd = directory / "command" / members[0]
        cmd.mkdir(parents=True, exist_ok=True)
        (cmd / "SKILL.md").write_text(
            f"---\nowner: {members[0]}\nconsumes: [{members[0]}]\n---\n"
            f"# {members[0]} command\n\n<!-- cmd-inject:start -->\n<!-- cmd-inject:end -->\n",
            encoding="utf-8")
        repo = Path(self.temp.name) / "git" / pid
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        shutil.copytree(directory, repo, dirs_exist_ok=True)
        self.git(repo, "init", "-q")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "pkg")
        self.git(repo, "tag", f"{pid}-v{version}")
        return repo

    def index(self, repo, version, provides):
        (self.root / "INDEX.yaml").write_text(
            "packages:\n"
            f"  pw: {{repo: {repo}, version: {version}, trust: reviewed-3rd-party, members: pwm, "
            f"kind: protocol, protocol: vaultwiki, provides: {', '.join(provides)}}}\n",
            encoding="utf-8")

    def journal(self):
        return (self.root / ".owfa/kernel-journal.log").read_text(encoding="utf-8")

    # ---- issue #72: failed upgrade is rolled back whole, never swept ----

    def test_failed_upgrade_rolls_back_old_package(self):
        """install side fails (bad new shape) -> old package restored, projections
        rebuilt, and a later kernel command must NOT sweep it as orphan residue."""
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        # v0.2 drops the org capability — R2 refuses the install half
        (repo / "PKG.yaml").write_text(
            (repo / "PKG.yaml").read_text(encoding="utf-8")
            .replace("version: 0.1", "version: 0.2")
            .replace("vaultwiki.org.v1", "vaultwiki.util.v1"),
            encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "pw-v0.2")
        self.index(repo, "0.2", ["vaultwiki.util.v1"])

        result = self.run_kernel("upgrade", "pw", "--yes")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("R2", result.stdout)  # the install half genuinely failed
        self.assertIn("rolled back to v0.1", result.stdout)
        # old package whole again: masters, version, projection
        pkg_yaml = (self.root / ".owfa/plugins/domains/pw/PKG.yaml").read_text(encoding="utf-8")
        self.assertIn("version: 0.1", pkg_yaml)
        self.assertIn("pwm projection line",
                      (self.root / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("upgrade-rollback", self.journal())
        # F1 (#72 review): connectors/ and .owfa/command/ ride the park and come
        # back with the masters (the five install steps, whole)
        self.assertTrue((self.root / "connectors" / "pwtool" / "cli.py").exists(),
                        "connector projection lost by the failed upgrade")
        self.assertTrue((self.root / ".owfa" / "command" / "pwm" / "SKILL.md").exists(),
                        "command projection lost by the failed upgrade")
        # the sweep must not fire afterwards
        after = self.run_kernel("validate")
        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
        self.assertNotIn("sweep", after.stdout)
        self.assertNotIn("auto-swept", self.journal().split("upgrade-rollback")[-1])
        self.assertTrue((self.root / ".owfa/plugins/domains/pw").exists())

    def test_interrupted_upgrade_hold_blocks_sweep(self):
        """A crash mid-upgrade leaves an upgrade-hold marker: the sweep refuses the
        parked state and says so instead of destroying it (issue #72)."""
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        # simulate the mid-transaction crash shape: old package gone, hold marker set
        shutil.rmtree(self.root / ".owfa/plugins/domains/pw")
        led_path = self.root / ".owfa/migrations/pending.json"
        led_path.write_text(json.dumps(
            {"pw": {"kind": "upgrade-hold", "from": "0.1", "to": "0.2", "items": []}}),
            encoding="utf-8")
        result = self.run_kernel("ls")
        self.assertIn("interrupted upgrade hold: pw", result.stdout)
        self.assertNotIn("[sweep] orphaned migration state removed", result.stdout)
        # the parked roster (dormant PKG copy) survives for the rerun
        self.assertTrue((self.root / ".owfa/migrations/pw/PKG.yaml").exists())
        self.assertNotIn("auto-swept", self.journal())

    def test_successful_upgrade_clears_hold_and_leaves_no_marker(self):
        """The happy path leaves no upgrade-hold residue in the ledger."""
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        (repo / "PKG.yaml").write_text(
            (repo / "PKG.yaml").read_text(encoding="utf-8").replace("version: 0.1", "version: 0.2"),
            encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "pw-v0.2")
        self.index(repo, "0.2", ["vaultwiki.org.v1"])
        result = self.run_kernel("upgrade", "pw", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0.1 -> v0.2", result.stdout)
        led = json.loads((self.root / ".owfa/migrations/pending.json").read_text(encoding="utf-8"))
        self.assertNotIn("pw", led)
        self.assertEqual(self.run_kernel("validate").returncode, 0)

    def test_rollback_converge_failure_keeps_hold_and_does_not_claim_success(self):
        """F1 (#72 review): converge failing after the file restore must NOT report
        success — the upgrade-hold marker stays, no upgrade-rollback "restored"
        journal line, and the sweep keeps its hands off."""
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        # v0.2 drops the org capability — the install half fails on R2
        (repo / "PKG.yaml").write_text(
            (repo / "PKG.yaml").read_text(encoding="utf-8")
            .replace("version: 0.1", "version: 0.2")
            .replace("vaultwiki.org.v1", "vaultwiki.util.v1"),
            encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "pw-v0.2")
        self.index(repo, "0.2", ["vaultwiki.util.v1"])
        # break convergence: AGENTS.md loses its inject markers -> do_inject fails
        (self.root / "AGENTS.md").write_text("# Synthetic instance\n", encoding="utf-8")

        result = self.run_kernel("upgrade", "pw", "--yes")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("R2", result.stdout)  # the install half genuinely failed
        self.assertIn("convergence after rollback failed", result.stdout)
        self.assertNotIn("rolled back to v0.1", result.stdout)  # no false success
        self.assertNotIn("upgrade-rollback", self.journal())    # no "restored" lie
        # the hold marker survives so the sweep refuses the state
        led = json.loads((self.root / ".owfa/migrations/pending.json").read_text(encoding="utf-8"))
        self.assertEqual(led.get("pw", {}).get("kind"), "upgrade-hold")
        # files ARE back on disk (masters + projections) — just not claimed green
        self.assertIn("version: 0.1",
                      (self.root / ".owfa/plugins/domains/pw/PKG.yaml").read_text(encoding="utf-8"))
        self.assertTrue((self.root / "connectors/pwtool").exists())
        self.assertTrue((self.root / ".owfa/command/pwm").exists())
        after = self.run_kernel("ls")
        self.assertIn("interrupted upgrade hold: pw", after.stdout)
        self.assertNotIn("auto-swept", self.journal())
        self.assertTrue((self.root / ".owfa/plugins/domains/pw").exists())

    def test_interrupted_upgrade_rerun_recovers_from_park(self):
        """F2 (#72 review): killed between the uninstall and install halves — the
        rerun finds the in-tree park (migrations/<pkg>-upgrade-hold/, path in the
        ledger item), restores the old package whole, and the upgrade proceeds."""
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        self.assertTrue((self.root / "connectors/pwtool").exists())
        (repo / "PKG.yaml").write_text(
            (repo / "PKG.yaml").read_text(encoding="utf-8").replace("version: 0.1", "version: 0.2"),
            encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "pw-v0.2")
        self.index(repo, "0.2", ["vaultwiki.org.v1"])
        # simulate the kill shape exactly as the kernel parks it: in-tree park +
        # package/projections gone + hold marker carrying the park path
        park = self.root / ".owfa/migrations/pw-upgrade-hold"
        shutil.copytree(self.root / ".owfa/plugins/domains/pw", park / "pw")
        (park / "connectors").mkdir()
        shutil.copytree(self.root / "connectors/pwtool", park / "connectors/pwtool")
        (park / "command").mkdir()
        shutil.copytree(self.root / ".owfa/command/pwm", park / "command/pwm")
        shutil.rmtree(self.root / ".owfa/plugins/domains/pw")
        shutil.rmtree(self.root / "connectors/pwtool")
        shutil.rmtree(self.root / ".owfa/command/pwm")
        (self.root / ".owfa/migrations/pending.json").write_text(json.dumps(
            {"pw": {"kind": "upgrade-hold", "from": "0.1", "to": "0.2", "items": [str(park)]}}),
            encoding="utf-8")

        result = self.run_kernel("upgrade", "pw", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("recovered from an interrupted upgrade", result.stdout)
        self.assertIn("0.1 -> v0.2", result.stdout)
        self.assertIn("version: 0.2",
                      (self.root / ".owfa/plugins/domains/pw/PKG.yaml").read_text(encoding="utf-8"))
        # the new edition is whole: connector + command projections present
        self.assertTrue((self.root / "connectors/pwtool").exists())
        self.assertTrue((self.root / ".owfa/command/pwm").exists())
        led = json.loads((self.root / ".owfa/migrations/pending.json").read_text(encoding="utf-8"))
        self.assertNotIn("pw", led)
        self.assertFalse(park.exists())  # the park is consumed, not left as residue
        self.assertEqual(self.run_kernel("validate").returncode, 0)

    # ---- step2 review Low 2: --without refusal paths must not leak the clone ----

    def test_without_refusals_do_not_leak_the_clone(self):
        """R6 / bad-member / family-root refusals drop the cloned source (mkdtemp
        leak otherwise)."""
        before = set(glob.glob(os.path.join(tempfile.gettempdir(), "vw-pkg-*")))
        # R6: protocol all-or-nothing
        repo = self.proto_pkg("pw", "0.1", ["vaultwiki.org.v1"])
        self.index(repo, "0.1", ["vaultwiki.org.v1"])
        r1 = self.run_kernel("install", "pw", "--without", "pwm")
        self.assertEqual(r1.returncode, 1, r1.stdout + r1.stderr)
        self.assertIn("all-or-nothing", r1.stdout)
        # bad member + family root on a domain-family package
        fam = self.proto_pkg("fam", "0.1", [], kind="domain-family", members=["fam", "fam-a"])
        (self.root / "INDEX.yaml").write_text(
            "packages:\n"
            f"  fam: {{repo: {fam}, version: 0.1, trust: reviewed-3rd-party, members: fam/fam-a}}\n",
            encoding="utf-8")
        r2 = self.run_kernel("install", "fam", "--without", "notamember")
        self.assertEqual(r2.returncode, 1, r2.stdout + r2.stderr)
        self.assertIn("not members of fam", r2.stdout)
        r3 = self.run_kernel("install", "fam", "--without", "fam")
        self.assertEqual(r3.returncode, 1, r3.stdout + r3.stderr)
        self.assertIn("family root is never prunable", r3.stdout)
        # F4 (INFO): the cascade rmtree paths — whole-package --without cascade and
        # member-needs cascade — must drop the clone too
        # --without cascade pruning every tenant: fam-b depends on fam-a
        fam2 = self.source / "fam2src"
        for m in ("fam2-a", "fam2-b"):
            (fam2 / m).mkdir(parents=True)
            deps = "depends:\n  - fam2-a\n" if m == "fam2-b" else "depends: []\n"
            (fam2 / m / "PLUGIN.yaml").write_text(
                f"id: {m}\nschema_version: 1\nversion: 0.1\nupdated: 2026-11-15\n"
                f"{deps}attachment: []\nfields: {{}}\n"
                f"inject: \"{m} projection line\"\nusage: []\n", encoding="utf-8")
            (fam2 / m / "PLUGIN.md").write_text("# synthetic member\n", encoding="utf-8")
        (fam2 / "PKG.yaml").write_text(
            "schema_version: 1\nid: fam2\nversion: 0.1\ncompat: '>= 0.3'\n"
            "members: [fam2-a, fam2-b]\ndepends: [framework]\nkind: suite\n",
            encoding="utf-8")
        repo2 = Path(self.temp.name) / "git" / "fam2"
        shutil.copytree(fam2, repo2)
        self.git(repo2, "init", "-q")
        self.git(repo2, "add", "-A")
        self.git(repo2, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "pkg")
        self.git(repo2, "tag", "fam2-v0.1")
        (self.root / "INDEX.yaml").write_text(
            "packages:\n"
            f"  fam2: {{repo: {repo2}, version: 0.1, trust: reviewed-3rd-party, members: fam2-a/fam2-b}}\n",
            encoding="utf-8")
        r4 = self.run_kernel("install", "fam2", "--without", "fam2-a")
        self.assertEqual(r4.returncode, 1, r4.stdout + r4.stderr)
        self.assertIn("--without cascade prunes the whole package", r4.stdout)
        # member-needs cascade pruning every tenant: the sole member needs a missing capability
        (repo2 / "fam2-a/PLUGIN.yaml").write_text(
            (repo2 / "fam2-a/PLUGIN.yaml").read_text(encoding="utf-8").replace(
                "usage: []\n", "usage: []\nneeds:\n  - nothing.anywhere.v1\n"),
            encoding="utf-8")
        self.git(repo2, "add", "-A")
        self.git(repo2, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "needs")
        self.git(repo2, "tag", "-f", "fam2-v0.1")  # the clone resolves the tag — retag after the edit
        r5 = self.run_kernel("install", "fam2")
        self.assertEqual(r5.returncode, 1, r5.stdout + r5.stderr)
        self.assertIn("member-level needs pruning cascades to the whole package", r5.stdout)
        after = set(glob.glob(os.path.join(tempfile.gettempdir(), "vw-pkg-*")))
        self.assertEqual(after - before, set(), f"--without refusal leaked clones: {after - before}")


if __name__ == "__main__":
    unittest.main()
