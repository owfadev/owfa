"""step2 protocol formalization unit tests (spec §9, 14 groups).

kind:protocol + protocol: field + org-capability exclusivity (R9) + all-or-nothing
(R6) + member-level needs (Q12/R10) + R5 retains coverage + registry row
kind/protocol/default pass-through + uninstall/doctor protocol-less shell hint.

Synthetic packages and disposable instances only (the test_capabilities.py
construction idiom: temp instance + fake packages + kernel subprocess runs,
asserting exit codes and stderr/stdout).

Run: python -m unittest discover -s .owfa/tests -p test_protocol_kind.py -v
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


class ProtocolKindTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kernel-proto-test-")
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

    def install_blessed(self):
        """Install the embedded blessed suite (itself a protocol package since 0.4.3).
        Protocol-shape tests must NOT have it installed: their synthetic package is
        the workspace's sole protocol (R9 one-protocol-per-workspace)."""
        result = self.run_kernel("install", "personal", "--path", str(FRAMEWORK / "payloads" / "personal"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def run_kernel(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / ".owfa/scripts/owfa_kernel.py"), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8")

    # ---- synthetic package builders ----

    def manifest(self, name, inject, depends=None, needs=None, parent=None):
        directory = (parent or self.source) / name
        directory.mkdir(parents=True, exist_ok=True)
        deps = depends or []
        dep_text = "depends: []\n" if not deps else "depends:\n" + "".join(f"  - {d}\n" for d in deps)
        lines = [f"id: {name}\nschema_version: 1\nversion: 0.1\nupdated: 2026-11-12\n",
                 dep_text, "attachment: []\nfields:\n"]
        if needs:
            lines.append(f"needs: [{', '.join(needs)}]\n")
        lines.append(f"inject: {json.dumps(inject, ensure_ascii=False)}\n")
        (directory / "PLUGIN.yaml").write_text("".join(lines), encoding="utf-8")
        (directory / "PLUGIN.md").write_text("# Synthetic test plugin\n", encoding="utf-8")

    def pkg_src(self, pid, members, kind=None, protocol=None, provides=None,
                needs=None, version="0.1", member_deps=None, member_needs=None,
                skeleton=None, retains=None):
        """Build self.source/<pid>src/ : PKG.yaml + member plugin dirs; returns the path."""
        directory = self.source / f"{pid}src"
        if directory.exists():
            shutil.rmtree(directory)
        for m in members:
            self.manifest(m, f"{m} synthetic member",
                          depends=(member_deps or {}).get(m), needs=(member_needs or {}).get(m),
                          parent=directory)
        lines = ["schema_version: 1", f"id: {pid}", f"version: {version}", "compat: '>= 0.3'",
                 f"members: [{', '.join(members)}]", "depends: [framework]"]
        if kind:
            lines.append(f"kind: {kind}")
        if protocol:
            lines.append(f"protocol: {protocol}")
        if provides:
            lines.append(f"provides: [{', '.join(provides)}]")
        if needs:
            lines.append(f"needs: [{', '.join(needs)}]")
        if skeleton:
            lines.append(f"skeleton: [{', '.join(skeleton)}]")
        if retains is not None:
            lines.append("uninstall:")
            lines.append(f"  retains: [{', '.join(retains)}]")
        (directory / "PKG.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return directory

    def install_path(self, pid, *extra):
        return self.run_kernel("install", pid, "--path", str(self.source / f"{pid}src"), *extra)

    def git(self, repo, *args):
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def git_proto_pkg(self, pid, version, proto="vaultwiki"):
        """A local git repo protocol package + tag; returns the repo path."""
        repo = Path(self.temp.name) / "git" / pid
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        directory = self.pkg_src(pid, [f"{pid}m"], kind="protocol", protocol=proto,
                                 provides=[f"{proto}.org.v1"], version=version)
        for item in sorted(os.listdir(directory)):
            if item != "PKG.yaml":
                shutil.move(str(directory / item), str(repo / item))
        shutil.copyfile(directory / "PKG.yaml", repo / "PKG.yaml")
        self.git(repo, "init", "-q")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "pkg")
        self.git(repo, "tag", f"{pid}-v{version}")
        return repo

    def index(self, rows):
        lines = ["packages:"] + [f"  {name}: {{{body}}}" for name, body in rows]
        (self.root / "INDEX.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def doctor(self):
        return subprocess.run(["node", str(FRAMEWORK / "bin/owfa.js"), "doctor", str(self.root)],
                              capture_output=True, text=True, encoding="utf-8")

    # ---- 0. legal protocol shape (baseline for everything below) ----

    def test_valid_protocol_shape_installs_green(self):
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1", "vaultwiki.util.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.run_kernel("validate").returncode, 0)
        result = self.run_kernel("pkg")
        self.assertIn("(protocol: vaultwiki)", result.stdout)

    # ---- 1. R1: kind: protocol <=> protocol: field, both directions ----

    def test_r1_kind_protocol_without_protocol_field(self):
        self.pkg_src("pw", ["pwm"], kind="protocol", provides=["vaultwiki.org.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("kind: protocol requires the protocol: field", result.stdout)
        self.assertIn("R1", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    def test_r1_protocol_field_without_kind(self):
        self.pkg_src("pw", ["pwm"], protocol="vaultwiki", provides=["vaultwiki.org.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("requires kind: protocol", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    # ---- 2. R7: empty members ----

    def test_r7_empty_members_refused(self):
        directory = self.source / "pwsrc"
        directory.mkdir()
        (directory / "PKG.yaml").write_text(
            "schema_version: 1\nid: pw\nkind: protocol\nprotocol: vaultwiki\nversion: 0.1\n"
            "compat: '>= 0.3'\nmembers: []\ndepends: [framework]\nprovides: [vaultwiki.org.v1]\n",
            encoding="utf-8")
        result = self.run_kernel("install", "pw", "--path", str(directory))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("members must be a non-empty list", result.stdout)
        self.assertIn("R7", result.stdout)

    # ---- 3. R4/R7: protocol id reserved word + clash with an installed package id ----

    def test_protocol_id_owfa_reserved_and_package_id_clash(self):
        self.install_blessed()  # the clash target: an installed package named personal
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="owfa",
                     provides=["owfa.org.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("protocol id 'owfa' is reserved", result.stdout)
        # a protocol id may not clash with any installed package id (personal is)
        self.pkg_src("px", ["pxm"], kind="protocol", protocol="personal",
                     provides=["personal.org.v1"])
        result = self.install_path("px")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("conflicts with installed package id personal", result.stdout)
        self.assertIn("R7", result.stdout)

    # ---- 4. R2/R8: provides org shape — double org / missing org / v1+v2 ----

    def test_r2_provides_org_shape(self):
        # v1+v2 coexisting = the "exactly one" violation (R8: upgrade is in-place)
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1", "vaultwiki.org.v2"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("exactly one vaultwiki.org.v<N>", result.stdout)
        self.assertIn("R2", result.stdout)
        # missing org capability entirely
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.util.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("got none", result.stdout)
        # org capability with a prefix != the protocol id (R9 at the grammar gate)
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["other.org.v1"])
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("exactly one", result.stdout)

    # ---- 5. R9: a non-protocol package providing an org capability is refused ----

    def test_r9_non_protocol_org_capability_refused(self):
        self.pkg_src("probe", ["probe"], provides=["probe.org.v1"])
        result = self.install_path("probe")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("org capabilities (*.org.vN) are provided only by the kind:protocol package",
                      result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/probe").exists())

    # ---- 6. R10: member-level needs grammar + owfa.* reserved ----

    def test_r10_member_needs_grammar_and_reserved(self):
        self.pkg_src("ten", ["ten", "extra"], member_deps={"extra": ["ten"]},
                     member_needs={"extra": ["Bad.Cap"]})
        result = self.install_path("ten")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("fails the capability grammar", result.stdout)
        self.assertIn("R10", result.stdout)
        self.pkg_src("ten", ["ten", "extra"], member_deps={"extra": ["ten"]},
                     member_needs={"extra": ["owfa.net.v1"]})
        result = self.install_path("ten")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("owfa.* is reserved, member-level needs cannot use the framework namespace",
                      result.stdout)

    # ---- 7. R10 trust semantics: untrusted provides do not satisfy member needs ----

    def test_untrusted_member_needs_prune_then_yes_override_then_validate_info(self):
        # protocol provider installed via --path: provides are unverified
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1"])
        self.assertEqual(self.install_path("pw").returncode, 0)
        self.pkg_src("ten", ["ten", "extra"], member_deps={"extra": ["ten"]},
                     member_needs={"extra": ["vaultwiki.org.v1"]})
        # untrusted → treated unsatisfied → domain member pruned (rides the cascade)
        result = self.install_path("ten")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("member-level needs: pruned extra", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/ten/extra").exists())
        journal = (self.root / ".owfa/kernel-journal.log").read_text(encoding="utf-8")
        self.assertNotIn("trust-override ten", journal)
        # --yes overrides the member-level trust gate (journaled), member rides back in
        self.assertEqual(self.run_kernel("uninstall", "ten", "--yes").returncode, 0)
        result = self.install_path("ten", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / ".owfa/plugins/domains/ten/extra").exists())
        journal = (self.root / ".owfa/kernel-journal.log").read_text(encoding="utf-8")
        self.assertIn("trust-override ten — member-level needs", journal)
        # losing the provider later: validate reports info (member pruned by
        # unsatisfied need), never an error — pruning is an install-time signal
        self.assertEqual(self.run_kernel("uninstall", "pw", "--yes").returncode, 0)
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("member pruned by unsatisfied need", result.stdout)

    # ---- 8. R6: --without on protocol members + member-needs refusal ----

    def test_r6_without_protocol_member_refused(self):
        self.pkg_src("pw", ["pwm", "pwq"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1"])
        result = self.install_path("pw", "--without", "pwq")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("protocol packages are all-or-nothing", result.stdout)
        self.assertIn("R6", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    def test_r6_unsatisfied_member_needs_refuse_whole_protocol_package(self):
        self.pkg_src("pw", ["pwm", "pwq"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1"],
                     member_needs={"pwq": ["vaultwiki.org.v1", "missing.cap.v1"]})
        result = self.install_path("pw")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("the whole package is refused", result.stdout)
        self.assertIn("R6", result.stdout)
        self.assertFalse((self.root / ".owfa/plugins/domains/pw").exists())

    # ---- 9. upgrade of the sole protocol passes (prospective prev_pkgm board) ----

    def test_upgrade_sole_protocol_and_needer_passes(self):
        repo = self.git_proto_pkg("pw", "0.1")
        self.index([("pw", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: pwm, "
                          "kind: protocol, protocol: vaultwiki, provides: vaultwiki.org.v1, default: true")])
        self.assertEqual(self.run_kernel("install", "pw").returncode, 0)
        self.pkg_src("ten", ["ten"], needs=["vaultwiki.org.v1"])
        result = self.install_path("ten")  # trusted registry row satisfies, no --yes
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # bump the protocol package 0.1 -> 0.2 (same org capability, in place — R8)
        text = (repo / "PKG.yaml").read_text(encoding="utf-8").replace("version: 0.1", "version: 0.2")
        (repo / "PKG.yaml").write_text(text, encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "bump")
        self.git(repo, "tag", "pw-v0.2")
        self.index([("pw", f"repo: {repo}, version: 0.2, trust: reviewed-3rd-party, members: pwm, "
                          "kind: protocol, protocol: vaultwiki, provides: vaultwiki.org.v1, default: true")])
        result = self.run_kernel("upgrade", "pw", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0.1 -> v0.2", result.stdout)
        self.assertEqual(self.run_kernel("validate").returncode, 0)

    # ---- 10. R6 pin: INDEX<->PKG reconciliation is source-side full, subset-proof ----

    def test_index_pkg_reconciliation_is_source_side_full(self):
        # a legal --without subset installs against the FULL source roster row ...
        self.pkg_src("fam", ["fam", "opt"], member_deps={"opt": ["fam"]})
        repo = Path(self.temp.name) / "git" / "fam"
        self.index([("fam", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: fam/opt")])
        shutil.copytree(self.source / "famsrc", repo)
        self.git(repo, "init", "-q")
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "pkg")
        self.git(repo, "tag", "fam-v0.1")
        result = self.run_kernel("install", "fam", "--without", "opt")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # ... while a row that matches the INSTALLED SUBSET (not the source roster)
        # is drift and refuses — reconciliation never reads the installed subset
        self.index([("fam", f"repo: {repo}, version: 0.1, trust: reviewed-3rd-party, members: fam")])
        self.run_kernel("uninstall", "fam", "--yes")
        result = self.run_kernel("install", "fam")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("index members", result.stdout)
        self.assertIn("drift", result.stdout)

    # ---- 11. R5: last-protocol uninstall hint lands in uninstall + doctor ----

    def test_uninstall_last_protocol_hint_in_uninstall_and_doctor(self):
        result = self.doctor()
        self.assertIn("protocol-less", result.stdout)  # shell from the start
        self.pkg_src("pw", ["pwm"], kind="protocol", protocol="vaultwiki",
                     provides=["vaultwiki.org.v1"])
        self.assertEqual(self.install_path("pw").returncode, 0)
        self.assertNotIn("protocol-less", self.doctor().stdout)
        result = self.run_kernel("uninstall", "pw", "--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("workspace is protocol-less — a shell", result.stdout)
        self.assertIn("protocol-less", self.doctor().stdout)

    # ---- 12. transition window: 0.3-era kind:suite products stay green ----

    def test_transition_window_suite_without_protocol_stays_green(self):
        self.pkg_src("synth", ["sm1", "sm2"], kind="suite", member_deps={"sm2": ["sm1"]})
        result = self.install_path("synth")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.run_kernel("validate").returncode, 0)
        # ... but R9 has no transition window: a suite providing an org capability refuses
        self.run_kernel("uninstall", "synth", "--yes")
        self.pkg_src("synth", ["sm1", "sm2"], kind="suite", member_deps={"sm2": ["sm1"]},
                     provides=["synth.org.v1"])
        result = self.install_path("synth")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("R9", result.stdout)

    # ---- 13. R5: skeleton dirs not covered by uninstall.retains → validate warning ----

    def test_r5_retains_gap_warns(self):
        self.pkg_src("fam", ["fam"], skeleton=["data/"], retains=["vault/"])
        result = self.install_path("fam")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / "data").is_dir())
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)  # warning, not error
        self.assertIn("not covered by uninstall.retains", result.stdout)
        self.assertIn("R5", result.stdout)
        # covered skeleton stays silent
        self.run_kernel("uninstall", "fam", "--yes")
        self.pkg_src("fam", ["fam"], skeleton=["data/"], retains=["vault/", "data/"])
        self.assertEqual(self.install_path("fam").returncode, 0)
        result = self.run_kernel("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("not covered by uninstall.retains", result.stdout)

    # ---- 14. list-remote: protocol marks + three-key pass-through + multi default ----

    def test_list_remote_protocol_marks_and_multi_default_warning(self):
        self.index([
            ("pw", "repo: https://x/pw.git, version: 0.2, trust: framework-bundled, members: pwm, "
                  "kind: protocol, protocol: vaultwiki, provides: vaultwiki.org.v1, default: true"),
            ("qx", "repo: https://x/qx.git, version: 0.1, trust: framework-bundled, members: qxm, "
                   "kind: protocol, protocol: quantum, provides: quantum.org.v1, default: true"),
            ("bare", "repo: https://x/b.git, version: 0.3, trust: reviewed-3rd-party, members: z"),
        ])
        result = self.run_kernel("list-remote")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # protocol marks + the blessed default flag
        self.assertIn("[protocol: vaultwiki]", result.stdout)
        self.assertIn("(default)", result.stdout)
        # registry discipline: at most one default:true row, globally
        self.assertIn("at most one blessed default", result.stdout)
        self.assertIn("pw, qx", result.stdout)
        # kind/protocol keys are pure pass-through: a non-protocol row shows no mark
        bare_line = [l for l in result.stdout.splitlines() if l.startswith("  bare")][0]
        self.assertNotIn("[protocol:", bare_line)


if __name__ == "__main__":
    unittest.main()
