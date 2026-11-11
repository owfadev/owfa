#!/usr/bin/env node
/**
 * End-to-end smoke test for the npm channel, using the working tree as the
 * payload (no pack step): init into an empty dir, init over an existing
 * AGENTS.md, refusal on a second init, upgrade with instance-local state.
 *
 * Run: node test/smoke.js
 */
"use strict";

const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const BIN = path.join(ROOT, "bin", "owfa.js");
const PKG = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));
const FW = fs.readFileSync(path.join(ROOT, ".owfa", "VERSION"), "utf8").trim();

function run(args, cwd) {
  return spawnSync(process.execPath, [BIN, ...args], { cwd, encoding: "utf8" });
}

function hasPython() {
  const cands = process.platform === "win32" ? ["py", "python"] : ["python3", "python"];
  return cands.some((cmd) => {
    const r = spawnSync(cmd, ["-c", "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"], { stdio: "ignore" });
    return !r.error && r.status === 0;
  });
}

function countPluginBlocks(text) {
  return (text.match(/<!-- plugin:/g) || []).length;
}

const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "owfa-smoke-"));
let failures = 0;
function step(name, fn) {
  try {
    fn();
    console.log("  ok   " + name);
  } catch (e) {
    failures++;
    console.error("  FAIL " + name + "\n       " + (e && e.message ? e.message.split("\n").join("\n       ") : e));
  }
}

try {
  if (!hasPython()) {
    console.log("smoke: no python3 on PATH — skipping (the framework itself is Python; the channel test needs it)");
    process.exit(0);
  }

  const empty = path.join(tmpRoot, "empty");
  const existing = path.join(tmpRoot, "existing");

  step("init on an empty directory", () => {
    const r = run(["init", empty, "--name", "smoke-vault"]);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "VERSION"), "utf8").trim(), FW);
    for (const d of ["vault", "wiki/notes", "wiki/sessions", "wiki/vault", ".agents/skills/owfa-map"]) {
      assert.ok(fs.existsSync(path.join(empty, d)), `missing ${d}`);
    }
    const agents = fs.readFileSync(path.join(empty, "AGENTS.md"), "utf8");
    assert.ok(agents.includes("# smoke-vault"), "name not substituted");
    assert.ok(agents.includes("<!-- wiki-inject:start -->") && agents.includes("<!-- wiki-inject:end -->"));
    assert.ok(countPluginBlocks(agents) >= 20, `expected core plugin blocks, got ${countPluginBlocks(agents)}`);
  });

  step("doctor passes on the fresh instance", () => {
    const r = run(["doctor", empty]);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.ok(/doctor: ok/.test(r.stdout), r.stdout);
  });

  step("owfa pkg lists the core inventory", () => {
    const r = run(["pkg"], empty);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.match(r.stdout, /core \(framework\): \d+/);
    assert.ok(r.stdout.includes("calendar"), r.stdout);
  });

  step("second init refuses without --force", () => {
    const r = run(["init", empty], tmpRoot);
    assert.notStrictEqual(r.status, 0);
    assert.ok(/already contains \.owfa/.test(r.stderr), r.stderr);
  });

  step("init preserves an existing AGENTS.md and appends the region", () => {
    fs.mkdirSync(existing, { recursive: true });
    fs.writeFileSync(path.join(existing, "AGENTS.md"), "# my own constitution\n\nkeep this line\n", "utf8");
    const r = run(["init", existing]);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    const text = fs.readFileSync(path.join(existing, "AGENTS.md"), "utf8");
    assert.ok(text.startsWith("# my own constitution"), "handwritten prefix lost");
    assert.ok(text.includes("keep this line"));
    assert.ok(text.includes("<!-- wiki-inject:start -->"));
    assert.ok(countPluginBlocks(text) >= 20);
  });

  step("upgrade replaces the framework and preserves instance kernel state", () => {
    fs.writeFileSync(path.join(empty, ".owfa", "VERSION"), "0.2", "utf8");
    fs.writeFileSync(path.join(empty, ".owfa", "kernel-journal.log"), "keep-me\n", "utf8");
    fs.mkdirSync(path.join(empty, ".owfa", "migrations"), { recursive: true });
    fs.writeFileSync(path.join(empty, ".owfa", "migrations", "pending.json"), "{}\n", "utf8");
    const r = run(["upgrade", empty], tmpRoot);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "VERSION"), "utf8").trim(), FW);
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "kernel-journal.log"), "utf8"), "keep-me\n");
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "migrations", "pending.json"), "utf8"), "{}\n");
  });

  // 0.4 layout migration: a 0.3 instance (framework in .meta/) upgrades in place —
  // the old tree parks the same way, PRESERVED state carries over, and a .meta
  // shim keeps 0.3-era absolute paths resolving until the shim retires (0.5).
  step("legacy .meta/ layout migrates to .owfa/ with a shim", () => {
    const legacy = path.join(tmpRoot, "legacy");
    const r0 = run(["init", legacy], tmpRoot);
    assert.strictEqual(r0.status, 0, r0.stderr + r0.stdout);
    fs.renameSync(path.join(legacy, ".owfa"), path.join(legacy, ".meta")); // simulate a 0.3 instance
    fs.writeFileSync(path.join(legacy, ".meta", "kernel-journal.log"), "legacy-journal\n", "utf8");
    const r = run(["upgrade", legacy], tmpRoot);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.ok(/layout migration/.test(r.stdout), "migration banner missing: " + r.stdout);
    assert.ok(fs.existsSync(path.join(legacy, ".owfa", "VERSION")), ".owfa tree missing after migration");
    assert.strictEqual(
      fs.readFileSync(path.join(legacy, ".owfa", "kernel-journal.log"), "utf8"),
      "legacy-journal\n",
      "journal did not carry across the layout migration"
    );
    const metaStat = fs.lstatSync(path.join(legacy, ".meta"));
    if (metaStat.isSymbolicLink()) {
      assert.strictEqual(fs.readlinkSync(path.join(legacy, ".meta")), ".owfa", "shim does not point at .owfa");
      assert.ok(
        fs.existsSync(path.join(legacy, ".meta", "scripts", "owfa_kernel.py")),
        "0.3-era absolute path broken through the shim"
      );
    } else {
      assert.ok(/could not create the \.meta shim/.test(r.stdout), "no shim and no warning — silent path breakage");
    }
    const d = run(["doctor", legacy], tmpRoot);
    assert.strictEqual(d.status, 0, "migrated instance fails doctor: " + d.stdout);
  });

  // Review P1 (PR #53): a replace must carry instance-owned state across —
  // installed package masters, package commands, pending-migration materials
  // and skills the incoming tree does not ship.
  const DEMO_PLUGIN = [
    "id: demo", "schema_version: 1", "version: 0.1", "depends:", "  - vault",
    "updated: 2026-10-26", 'attachment: []', "fields: {}",
    'inject: "demo package projection line (smoke fixture)"', "usage: []",
  ].join("\n") + "\n";
  const DEMO_CMD = [
    "---", "name: demo-cmd", "description: smoke fixture command", "owner: framework",
    "---", "", "# demo-cmd", "", "fixture body",
  ].join("\n") + "\n";

  step("upgrade preserves installed package, package command, pending migration and standalone skill", () => {
    fs.writeFileSync(path.join(empty, ".owfa", "VERSION"), "0.2", "utf8"); // stale again
    const blocksBefore = countPluginBlocks(fs.readFileSync(path.join(empty, "AGENTS.md"), "utf8"));
    const dom = path.join(empty, ".owfa", "plugins", "domains", "demo");
    fs.mkdirSync(dom, { recursive: true });
    fs.writeFileSync(path.join(dom, "PLUGIN.yaml"), DEMO_PLUGIN, "utf8");
    fs.writeFileSync(path.join(dom, "PLUGIN.md"), "# demo\n\nsmoke fixture package\n", "utf8");
    fs.mkdirSync(path.join(empty, ".owfa", "command", "demo-cmd"), { recursive: true });
    fs.writeFileSync(path.join(empty, ".owfa", "command", "demo-cmd", "SKILL.md"), DEMO_CMD, "utf8");
    fs.mkdirSync(path.join(empty, ".owfa", "migrations", "demo"), { recursive: true });
    fs.writeFileSync(path.join(empty, ".owfa", "migrations", "demo", "init.md"), "pending migration fixture\n", "utf8");
    fs.writeFileSync(path.join(empty, ".owfa", "migrations", "pending.json"), '{"demo":{}}\n', "utf8");
    fs.mkdirSync(path.join(empty, ".agents", "skills", "custom-user"), { recursive: true });
    fs.writeFileSync(path.join(empty, ".agents", "skills", "custom-user", "SKILL.md"), "# custom-user\n\nkeep me\n", "utf8");
    // pending semantic migrations keep validate red by design (tri-face warning):
    // the trees ARE replaced, but the upgrade reports the blocked convergence.
    const r = run(["upgrade", empty], tmpRoot);
    assert.notStrictEqual(r.status, 0, "upgrade should report the pending-migration block");
    assert.ok(/pending semantic migrations/.test(r.stdout + r.stderr), r.stdout + r.stderr);
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "VERSION"), "utf8").trim(), FW, "trees not replaced");
    assert.ok(fs.existsSync(path.join(empty, ".owfa", "plugins", "domains", "demo", "PLUGIN.yaml")), "package master lost");
    assert.ok(fs.existsSync(path.join(empty, ".owfa", "command", "demo-cmd", "SKILL.md")), "package command lost");
    assert.ok(fs.existsSync(path.join(empty, ".owfa", "migrations", "demo", "init.md")), "pending migration material lost");
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "migrations", "pending.json"), "utf8"), '{"demo":{}}\n');
    assert.ok(fs.existsSync(path.join(empty, ".agents", "skills", "custom-user", "SKILL.md")), "standalone skill lost");
    // fresh framework skills must not be shadowed by the carry-over
    assert.ok(fs.existsSync(path.join(empty, ".agents", "skills", "owfa-map", "SKILL.md")), "framework skill lost");
    // with the migration cleared, the same instance converges green and the
    // package command re-deploys (deploy rides after validate in `kernel all`)
    fs.writeFileSync(path.join(empty, ".owfa", "migrations", "pending.json"), "{}\n", "utf8");
    const r2 = run(["upgrade", empty, "--force"], tmpRoot);
    assert.strictEqual(r2.status, 0, "re-sync after clearing pending failed: " + r2.stdout + r2.stderr);
    assert.ok(fs.existsSync(path.join(empty, ".agents", "skills", "demo-cmd", "SKILL.md")), "package command not re-deployed");
    const v = run(["doctor", empty], tmpRoot);
    assert.strictEqual(v.status, 0, "instance with carried package fails doctor: " + v.stdout);
    // review round 2: the repro signal was the plugin count dropping 22 -> 21 —
    // pin the carried package: the fresh region plus the demo block, never fewer
    const blocksAfter = countPluginBlocks(fs.readFileSync(path.join(empty, "AGENTS.md"), "utf8"));
    assert.strictEqual(blocksAfter, blocksBefore + 1, "carried package not injected (or a framework plugin dropped)");
    assert.ok(fs.readFileSync(path.join(empty, "AGENTS.md"), "utf8").includes("<!-- plugin:demo"), "demo block missing");
    // scrub the fixture so later steps start from a clean instance
    fs.rmSync(path.join(empty, ".owfa", "plugins", "domains", "demo"), { recursive: true, force: true });
    fs.rmSync(path.join(empty, ".owfa", "command", "demo-cmd"), { recursive: true, force: true });
    fs.rmSync(path.join(empty, ".agents", "skills", "custom-user"), { recursive: true, force: true });
    fs.rmSync(path.join(empty, ".agents", "skills", "demo-cmd"), { recursive: true, force: true });
    fs.rmSync(path.join(empty, ".owfa", "migrations", "demo"), { recursive: true, force: true });
  });

  // Review round 2 (PR #53): a parked attic from an interrupted replace holds the
  // only copy of instance state — a rerun must refuse, never delete it.
  step("interrupted replace protects the parked attic", () => {
    fs.writeFileSync(path.join(empty, ".owfa", "VERSION"), "0.2", "utf8");
    const attic = path.join(empty, ".owfa-migrate", "replace", "owfa");
    fs.mkdirSync(attic, { recursive: true });
    fs.writeFileSync(path.join(attic, "kernel-journal.log"), "only-copy\n", "utf8");
    const r = run(["upgrade", empty, "--force"], tmpRoot);
    assert.notStrictEqual(r.status, 0, "upgrade ran over a parked attic");
    assert.ok(/interrupted replace/.test(r.stdout + r.stderr), r.stdout + r.stderr);
    assert.strictEqual(fs.readFileSync(path.join(attic, "kernel-journal.log"), "utf8"), "only-copy\n", "parked attic was deleted");
    fs.rmSync(path.join(empty, ".owfa-migrate"), { recursive: true, force: true }); // scrub fixture
  });

  // Review P2 (PR #53): doctor fails when a required condition is missing.
  step("doctor fails when AGENTS.md is missing", () => {
    const agents = path.join(empty, "AGENTS.md");
    const backup = agents + ".smoke-bak";
    fs.renameSync(agents, backup);
    const r = run(["doctor", empty], tmpRoot);
    fs.renameSync(backup, agents);
    assert.notStrictEqual(r.status, 0, "doctor exited 0 with AGENTS.md missing");
    assert.ok(/AGENTS\.md: MISSING/.test(r.stdout), r.stdout);
    assert.ok(/doctor: failed/.test(r.stdout), r.stdout);
  });

  step("doctor fails when injection markers are broken", () => {
    const agents = path.join(empty, "AGENTS.md");
    const original = fs.readFileSync(agents, "utf8");
    fs.writeFileSync(agents, original.replace("<!-- wiki-inject:end -->", "<!-- removed -->"), "utf8");
    const r = run(["doctor", empty], tmpRoot);
    fs.writeFileSync(agents, original, "utf8");
    assert.notStrictEqual(r.status, 0, "doctor exited 0 with broken markers");
    assert.ok(/MISSING injection markers/.test(r.stdout), r.stdout);
  });

  step("init --force preserves kernel state and instance data", () => {
    fs.writeFileSync(path.join(empty, "vault", "keep.txt"), "asset\n", "utf8");
    const r = run(["init", empty, "--force"]);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.strictEqual(fs.readFileSync(path.join(empty, "vault", "keep.txt"), "utf8"), "asset\n");
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "kernel-journal.log"), "utf8"), "keep-me\n");
  });

  step("init --packages forwards --without to the kernel install", () => {
    const sub = path.join(tmpRoot, "subset");
    const r = run(["init", sub, "--packages", "cuhksz", "--without", "sis"], tmpRoot);
    // cuhksz stages a first-run semantic migration: init exits non-zero after a
    // successful install — that is the designed tri-face, not a forwarding failure
    assert.notStrictEqual(r.status, 0, "pending migration should surface");
    assert.ok(/semantic migration/i.test(r.stdout + r.stderr), r.stdout + r.stderr);
    const dom = path.join(sub, ".owfa", "plugins", "domains", "cuhksz");
    assert.ok(fs.existsSync(path.join(dom, "cuhksz", "PLUGIN.md")), "family root missing");
    assert.ok(fs.existsSync(path.join(dom, "bb", "PLUGIN.md")), "kept member missing");
    assert.ok(!fs.existsSync(path.join(dom, "sis", "PLUGIN.md")), "pruned member masters landed");
  });

  // CLI UX: per-command help, unknown flags and commands must not execute (user feedback 2026-10-27)
  step("init --help prints usage without creating anything", () => {
    const dir = path.join(tmpRoot, "help-target");
    const r = run(["init", dir, "--help"], tmpRoot);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.ok(/usage: owfa init/.test(r.stdout), r.stdout);
    assert.ok(!fs.existsSync(dir), "--help was executed as init");
  });

  step("unknown options and commands are rejected", () => {
    const r = run(["init", path.join(tmpRoot, "nope"), "--bogus"], tmpRoot);
    assert.strictEqual(r.status, 2, r.stdout + r.stderr);
    assert.ok(/unknown option/.test(r.stdout), r.stdout);
    assert.ok(!fs.existsSync(path.join(tmpRoot, "nope")), "unknown-flag init ran anyway");
    const r2 = run(["frobnicate"], tmpRoot);
    assert.strictEqual(r2.status, 2, r2.stdout);
    assert.ok(/unknown command/.test(r2.stdout), r2.stdout);
  });

  step("upgrade --check is read-only", () => {
    fs.writeFileSync(path.join(empty, ".owfa", "VERSION"), "0.2", "utf8");
    const r = run(["upgrade", empty, "--check"]);
    assert.strictEqual(r.status, 0, r.stderr + r.stdout);
    assert.strictEqual(fs.readFileSync(path.join(empty, ".owfa", "VERSION"), "utf8").trim(), "0.2");
  });

  console.log(`\nsmoke: ${failures ? failures + " failure(s)" : "all green"} (owfa ${PKG.version}, framework ${FW})`);
} finally {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
}
process.exit(failures ? 1 : 0);
