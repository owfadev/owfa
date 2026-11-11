#!/usr/bin/env node
/**
 * OWFA — One Workspace For All (agents).
 *
 * The npm channel for the owfa framework. This CLI owns exactly three
 * things the framework itself cannot own: fetching a complete framework tree,
 * initializing a directory without hand-copying it, and replacing that tree
 * on upgrade. Everything semantic stays in the Python kernel
 * (.owfa/scripts/owfa_kernel.py) — this file only orchestrates.
 *
 * Design rules:
 * - zero runtime dependencies; Node is needed to install, not to use
 * - no install/postinstall scripts for consumers (nothing executes on npm install)
 * - additive on init: existing content is never modified outside AGENTS.md's
 *   injection region
 * - upgrade is a tree replacement plus kernel convergence; instance-local
 *   kernel state (migration ledger, journal, registry cache) is preserved
 */
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const CLI_ROOT = path.resolve(__dirname, "..");
const PKG = JSON.parse(fs.readFileSync(path.join(CLI_ROOT, "package.json"), "utf8"));
const FRAMEWORK_VERSION = readVersion(CLI_ROOT) || "?";
const INJECT_START = "<!-- wiki-inject:start -->";
const INJECT_END = "<!-- wiki-inject:end -->";
const PAYLOAD = [".owfa", ".agents"];
const INSTANCE_DIRS = ["vault", path.join("wiki", "notes"), path.join("wiki", "sessions"), path.join("wiki", "vault")];
// 0.3 instances carry the framework in .meta/; upgrade migrates them to .owfa/
// and leaves a .meta shim (symlink/junction) so old absolute paths keep working.
const LEGACY_META = ".meta";
const MIGRATE_SCRATCH = ".owfa-migrate"; // transient replace/ parking (was .owfa — the name now belongs to the framework tree)
const BACKUP_DIR = ".owfa-backup";       // durable opt-in upgrade snapshots (was .owfa/backup)
// Kernel state that belongs to the instance, not to the framework tree.
const PRESERVED = [
  path.join(".owfa", "migrations", "pending.json"),
  path.join(".owfa", "kernel-journal.log"),
  path.join(".owfa", "registry-cache.yaml"),
];

// ---------------------------------------------------------------------------
// small utilities
// ---------------------------------------------------------------------------

function readVersion(root) {
  // ".meta" is the frozen 0.3 layout — a historical constant, safe to inline
  // here (LEGACY_META is declared later and readVersion runs at module init).
  for (const dir of [".owfa", ".meta"]) {
    try {
      return fs.readFileSync(path.join(root, dir, "VERSION"), "utf8").trim();
    } catch {}
  }
  return null;
}

function out(line = "") {
  process.stdout.write(line + "\n");
}

function fail(message, code = 1) {
  process.stderr.write("owfa: " + message + "\n");
  process.exit(code);
}

function rel(root, p) {
  return path.relative(root, p) || ".";
}

const FLAG_VALUE = ["name", "packages", "without", "from", "path"];

function parseArgs(argv) {
  const args = { _: [], flags: new Set(), used: new Set() };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--") {
      args._.push(...argv.slice(i + 1));
      break;
    }
    if (a.startsWith("--")) {
      const [key, inline] = a.slice(2).split("=", 2);
      const takesValue = FLAG_VALUE.includes(key);
      args.used.add(key);
      if (takesValue && inline === undefined) {
        args[key] = argv[++i];
      } else if (takesValue) {
        args[key] = inline;
      } else {
        args.flags.add(key);
      }
    } else if (a.startsWith("-") && a !== "-") {
      args.used.add(a.slice(1)); // short or mistyped flag — validated by the command
    } else {
      args._.push(a);
    }
  }
  return args;
}

function copyPayload(target, { replace = false } = {}) {
  const skip = (src) => {
    const base = path.basename(src);
    if (base === "__pycache__" || base.endsWith(".pyc") || base === ".DS_Store") return false;
    if (base === "smoke-tmp") return false;
    return true;
  };
  for (const entry of PAYLOAD) {
    const src = path.join(CLI_ROOT, entry);
    const dst = path.join(target, entry);
    if (!fs.existsSync(src)) fail(`package is missing ${entry}/ — the npm tarball is incomplete`);
    if (replace) {
      // 0.3 → 0.4 migration: the incoming .owfa/ has no counterpart on disk yet,
      // but the legacy .meta/ tree must go through the same park-and-carry swap.
      const legacySwap =
        entry === ".owfa" && !fs.existsSync(dst) && fs.existsSync(path.join(target, LEGACY_META));
      if (fs.existsSync(dst) || legacySwap) replacePayloadTree(target, entry, skip);
    } else {
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.cpSync(src, dst, { recursive: true, force: true, filter: skip });
    }
  }
}

// Instance-owned state inside the payload trees, distinguished from framework-owned
// files (review P1, PR #53): installed package masters (kernel install), migration
// state (ledger / pending / dormant teardown), and skill copies the incoming tree
// does not ship (package connector skills, user standalone skills). Everything else
// under .owfa/ and .agents/ is framework-owned and replaced by the channel.
const META_MERGE_DIRS = [path.join("plugins", "domains"), "migrations"];

// .owfa/command/ is mixed-ownership: framework commands ship in the fresh tree,
// package commands (kernel install) and anything the channel no longer ships are
// carried over by difference — the fresh copy wins for shared names.
function carryOverCommands(target, metaAttic) {
  const oldDir = path.join(metaAttic, "command");
  if (!fs.existsSync(oldDir)) return;
  const freshDir = path.join(target, ".owfa", "command");
  const fresh = new Set(fs.existsSync(freshDir) ? fs.readdirSync(freshDir) : []);
  for (const d of fs.readdirSync(oldDir)) {
    if (fresh.has(d)) continue;
    fs.cpSync(path.join(oldDir, d), path.join(freshDir, d), { recursive: true, force: true });
  }
}

function mergeTree(src, dst) {
  if (!fs.existsSync(src)) return;
  fs.cpSync(src, dst, { recursive: true, force: false, errorOnExist: false });
}

function carryOverEntry(target, entry, attic) {
  if (entry === ".owfa") {
    for (const d of META_MERGE_DIRS) mergeTree(path.join(attic, d), path.join(target, ".owfa", d));
    carryOverCommands(target, attic);
    for (const p of PRESERVED) {
      const s = path.join(attic, path.relative(".owfa", p)); // PRESERVED is target-relative; attic IS the old framework tree
      if (fs.existsSync(s)) {
        const d = path.join(target, p);
        fs.mkdirSync(path.dirname(d), { recursive: true });
        fs.copyFileSync(s, d);
      }
    }
  } else {
    const oldSkills = path.join(attic, "skills");
    if (!fs.existsSync(oldSkills)) return;
    const freshDir = path.join(target, ".agents", "skills");
    const fresh = new Set(fs.existsSync(freshDir) ? fs.readdirSync(freshDir) : []);
    for (const d of fs.readdirSync(oldSkills)) {
      if (fresh.has(d)) continue; // framework-shipped skill — the fresh copy wins
      fs.cpSync(path.join(oldSkills, d), path.join(freshDir, d), { recursive: true, force: true });
    }
  }
}

// Review round 2 (PR #53): the parked tree under .owfa-migrate/replace/ holds the only
// copy of the instance state between set-aside and carry-over. An interrupted
// swap (Windows: rename of a tree with an open file) must therefore never be
// implicitly cleaned by a retry, and a failure must roll the parked tree back.
function replacePayloadTree(target, entry, skip) {
  const dst = path.join(target, entry);
  // 0.3 → 0.4 layout migration: an instance whose framework still lives in
  // .meta/ parks that tree the same way, so crash semantics and carry-over
  // are identical to a normal same-layout swap.
  const parkedFrom =
    fs.existsSync(dst)
      ? dst
      : entry === ".owfa" && fs.existsSync(path.join(target, LEGACY_META))
        ? path.join(target, LEGACY_META)
        : null;
  const attic = path.join(target, MIGRATE_SCRATCH, "replace", path.basename(entry).replace(/^\./, ""));
  if (fs.existsSync(attic)) {
    fail(
      `interrupted replace detected: instance state is parked at ${attic} — ` +
      `do NOT simply rerun. Restore it manually (delete the fresh ${entry}/, ` +
      `rename the parked tree back to ${parkedFrom || entry}/), then rerun.`
    );
  }
  if (!parkedFrom) return; // fresh init into a tree that never existed — nothing to replace
  fs.mkdirSync(path.dirname(attic), { recursive: true });
  try {
    fs.renameSync(parkedFrom, attic); // same volume — atomic enough for a directory swap
    fs.cpSync(path.join(CLI_ROOT, entry), dst, { recursive: true, force: true, filter: skip });
    carryOverEntry(target, entry, attic);
  } catch (e) {
    try {
      fs.rmSync(dst, { recursive: true, force: true }); // partial fresh copy
      fs.renameSync(attic, parkedFrom); // parked tree back in place
      fail(`replace failed (${e.message}) — rolled back: ${parkedFrom} restored from the parked tree; fix the underlying error before rerunning`);
    } catch (e2) {
      fail(
        `replace failed (${e.message}) AND rollback failed (${e2.message}) — the previous tree ` +
        `is parked at ${attic}; do NOT rerun until it is restored to ${parkedFrom}`
      );
    }
  }
  fs.rmSync(path.join(target, MIGRATE_SCRATCH, "replace"), { recursive: true, force: true });
}

// The 0.4 layout shim: 0.3-era absolute paths (.meta/...) keep working through a
// directory shim. POSIX symlink; Windows junction (no admin rights needed).
// Idempotent and self-healing (review P1/P2 on this PR):
// - written on fresh init too — released 0.3 packages (cuhksz/lark/github) still
//   instruct .meta/ paths, so EVERY instance shape gets the shim until 0.5;
// - on upgrade a stale shim (instance dir renamed or copied — Windows junctions
//   are absolute) is detected via realpath and re-created;
// - a real .meta directory (0.3 layout that never migrated) is never touched.
function ensureMetaShim(target) {
  const metaPath = path.join(target, LEGACY_META);
  const owfa = path.join(target, ".owfa");
  if (!fs.existsSync(owfa)) return "absent";
  let kind = "missing";
  if (fs.existsSync(metaPath)) {
    if (!fs.lstatSync(metaPath).isSymbolicLink()) return "real-dir";
    kind = "link";
    let stale = true;
    try {
      stale = fs.realpathSync(metaPath) !== fs.realpathSync(owfa);
    } catch {
      stale = true; // dangling link
    }
    if (!stale) {
      ensureGitignore(target, LEGACY_META);
      return "ok";
    }
    fs.rmSync(metaPath, { force: true }); // symlink/junction only — never a real dir
  }
  try {
    fs.symlinkSync(".owfa", metaPath, process.platform === "win32" ? "junction" : "dir");
  } catch (e) {
    out(`warning: could not create the .meta shim (${e.message}) — 0.3-era scripts calling .meta/... will not resolve`);
    return "failed";
  }
  ensureGitignore(target, LEGACY_META);
  return kind === "link" ? "recreated" : "created";
}

// Windows: core.symlinks=false makes git traverse the junction as a plain
// directory, so without this line the framework is tracked twice (.owfa/ plus
// every .meta/* entry) and the 0.5 shim retirement reads as a mass deletion.
// Instance-git contract: adding an ignore sweeps tracked matches out — the CLI
// writes the line, and upgrade tells the user the one-time sweep command.
function ensureGitignore(target, line) {
  const p = path.join(target, ".gitignore");
  let text = "";
  if (fs.existsSync(p)) text = fs.readFileSync(p, "utf8");
  const hit = new RegExp(`^${line.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`, "m");
  if (hit.test(text)) return false;
  const glue = text && !text.endsWith("\n") ? "\n" : "";
  fs.writeFileSync(p, `${text}${glue}# 0.4 layout shim (retires in 0.5)\n${line}\n`, "utf8");
  return true;
}

function ensureDirs(target) {
  for (const d of INSTANCE_DIRS) fs.mkdirSync(path.join(target, d), { recursive: true });
}

function ensureAgents(target, name) {
  const file = path.join(target, "AGENTS.md");
  const seed = fs
    .readFileSync(path.join(CLI_ROOT, "templates", "AGENTS.template.md"), "utf8")
    .replaceAll("{{name}}", name);
  if (!fs.existsSync(file)) {
    fs.writeFileSync(file, seed, "utf8");
    return "written";
  }
  const text = fs.readFileSync(file, "utf8");
  const hasStart = text.includes(INJECT_START);
  const hasEnd = text.includes(INJECT_END);
  if (hasStart && hasEnd) return "kept (injection region already present)";
  if (hasStart || hasEnd) fail("AGENTS.md has only one injection marker — restore both markers (or remove the broken one) and rerun");
  const region = seed.slice(seed.indexOf(INJECT_START));
  const glue = text.endsWith("\n") ? "\n" : "\n\n";
  fs.writeFileSync(file, text + glue + region + "\n", "utf8");
  return "appended (existing AGENTS.md preserved)";
}

function findPython() {
  if (process.env.OWFA_PYTHON) {
    return { cmd: process.env.OWFA_PYTHON, args: [] };
  }
  const candidates =
    process.platform === "win32"
      ? [{ cmd: "py", args: ["-3"] }, { cmd: "python", args: [] }, { cmd: "python3", args: [] }]
      : [{ cmd: "python3", args: [] }, { cmd: "python", args: [] }];
  for (const cand of candidates) {
    const probe = spawnSync(cand.cmd, [...cand.args, "-c", "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"], {
      stdio: "ignore",
    });
    if (!probe.error && probe.status === 0) {
      const v = spawnSync(cand.cmd, [...cand.args, "--version"], { encoding: "utf8" });
      return { ...cand, version: (v.stdout || v.stderr || "").trim() };
    }
  }
  return null;
}

function pythonOrFail() {
  const py = findPython();
  if (!py) {
    fail(
      "Python 3.9+ not found. The framework itself is pure-stdlib Python; install Python 3 and rerun " +
        "(or set OWFA_PYTHON=/path/to/python3)."
    );
  }
  return py;
}

function kernel(target, kernelArgs) {
  const py = pythonOrFail();
  const script = path.join(target, ".owfa", "scripts", "owfa_kernel.py");
  if (!fs.existsSync(script)) fail(`no kernel at ${rel(target, script)} — is this an OWFA instance?`);
  const res = spawnSync(py.cmd, [...py.args, script, ...kernelArgs], {
    cwd: target,
    stdio: "inherit",
    // Instances should not accumulate bytecode; the framework tree stays clean.
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  return res.status === null ? 1 : res.status;
}

function versionTuple(v) {
  return String(v || "")
    .split(".")
    .map((x) => parseInt(x, 10) || 0);
}

function cmpVersion(a, b) {
  const x = versionTuple(a);
  const y = versionTuple(b);
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    const d = (x[i] || 0) - (y[i] || 0);
    if (d !== 0) return d > 0 ? 1 : -1;
  }
  return 0;
}

function timestamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}


function pendingPackages(target) {
  for (const dir of [".owfa", LEGACY_META]) {
    try {
      return Object.keys(JSON.parse(fs.readFileSync(path.join(target, dir, "migrations", "pending.json"), "utf8")));
    } catch {}
  }
  return [];
}

function reportPending(target) {
  const pending = pendingPackages(target);
  if (!pending.length) return false;
  out("");
  out(`semantic migration pending: ${pending.join(", ")} — the package is installed, but its first-run step is an agent act, not a mechanical one.`);
  out(`  run: python .owfa/scripts/owfa_kernel.py migrate ${pending[0]}`);
  out("  (read the printed page, perform the step, then rerun with --clear)");
  return true;
}

// ---------------------------------------------------------------------------
// commands
// ---------------------------------------------------------------------------

function cmdInit(args) {
  const target = path.resolve(args._[0] || ".");
  const force = args.flags.has("force");
  const hasOwfa = fs.existsSync(path.join(target, ".owfa"));
  const hasLegacyMeta = fs.existsSync(path.join(target, LEGACY_META));
  if (hasLegacyMeta && !hasOwfa) {
    fail(
      `${target} uses the 0.3 layout (.meta/) — run \`owfa upgrade\` to migrate to the .owfa layout ` +
        `(the upgrade preserves all instance state and leaves a .meta shim for old paths).`
    );
  }
  if (hasOwfa && !force) {
    fail(
      `${target} already contains .owfa/ — refusing to overwrite. Use \`owfa upgrade\` to update the framework, ` +
        `or pass --force to re-copy the framework trees (instance data is never touched either way).`
    );
  }
  const name = args.name || path.basename(target) || "workspace";
  fs.mkdirSync(target, { recursive: true });

  out(`OWFA init — framework ${FRAMEWORK_VERSION} → ${target}`);
  if (!hasOwfa && fs.existsSync(path.join(target, ".agents", "skills"))) {
    out("note: .agents/skills/ exists — framework skill copies are updated in place, other skills stay untouched");
  }
  if (hasOwfa) out("warning: --force replaces the framework trees; instance vault/ and wiki/ are untouched");
  copyPayload(target, { replace: hasOwfa });
  ensureDirs(target);
  // P1 (review): the shim is part of the 0.4 layout for EVERY instance shape —
  // released 0.3 packages (cuhksz/lark/github) still instruct .meta/ paths,
  // fresh instances included.
  if (ensureMetaShim(target) === "created") {
    out("shim: .meta → .owfa written — 0.3-era package paths keep working (retires in 0.5)");
  }
  out(`agents.md: ${ensureAgents(target, name)}`);

  out("");
  out("converging projections (python .owfa/scripts/owfa_kernel.py all)");
  if (kernel(target, ["all"]) !== 0) {
    const pending = pendingPackages(target);
    if (pending.length) {
      fail(`convergence blocked by pending semantic migrations (${pending.join(", ")}) — clear them with \`python .owfa/scripts/owfa_kernel.py migrate <pkg>\``);
    }
    fail("kernel convergence failed — the framework tree is incomplete; nothing was deleted, fix and rerun");
  }

  let installed = 0;
  if (args.packages) {
    for (const pkg of String(args.packages)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)) {
      out("");
      out(`installing package ${pkg} from the registry`);
      const installArgs = ["install", pkg, "--yes"];
      if (args.without) installArgs.push("--without", String(args.without));
      if (kernel(target, installArgs) !== 0) fail(`package ${pkg} failed to install (earlier packages stay installed)`);
      installed++;
      if (reportPending(target)) fail(`framework and ${pkg} are installed, but the workspace is not converged until the semantic migration above is cleared`);
    }
  }

  out("");
  out(`done — framework ${FRAMEWORK_VERSION}${installed ? ` + ${installed} package(s)` : ""} in ${target}`);
  out("");
  out("next:");
  out(`  cd ${target}`);
  out("  git init && git add -A && git commit -m \"init: OWFA workspace\"   # recommended: instance snapshots");
  out("  put any file into vault/, open your agent here, say \"map\"");
  out("  owfa doctor        # anytime: python, framework, kernel validate");
  return 0;
}

function cmdUpgrade(args) {
  const target = path.resolve(args._[0] || ".");
  const local = readVersion(target);
  if (!local) fail(`${target} is not an OWFA instance (no .owfa/VERSION or .meta/VERSION) — run \`owfa init\` first`);
  const legacyLayout = !fs.existsSync(path.join(target, ".owfa", "VERSION"));
  const incoming = FRAMEWORK_VERSION;
  const cmp = cmpVersion(local, incoming);
  const frozen = args.flags.has("check") || args.flags.has("dry-run");
  const force = args.flags.has("force");

  out(`OWFA upgrade — instance ${local} → channel ${incoming} (CLI ${PKG.version})`);
  if (legacyLayout) {
    out(`layout migration: 0.3 instance (.meta/) → 0.4 layout (.owfa/ + .meta shim for old paths)`);
  }
  if (cmp > 0) {
    if (!force) fail(`instance framework ${local} is newer than this CLI's ${incoming} — run \`npx owfa@latest upgrade\``);
    out(`warning: downgrading framework ${local} → ${incoming} (--force)`);
  }
  if (cmp === 0 && !force && !legacyLayout) {
    out("already at this framework version — nothing to do (pass --force to re-sync the trees)");
    return 0;
  }
  if (frozen) {
    out(`would replace ${PAYLOAD.join(" + ")}${legacyLayout ? " (migrating .meta/ → .owfa/)" : ""} and rerun kernel all (dry run)`);
    return 0;
  }

  if (args.flags.has("backup")) {
    const dir = path.join(target, BACKUP_DIR, `${local}-${timestamp()}`);
    for (const entry of PAYLOAD) {
      const src = path.join(target, entry === ".owfa" && legacyLayout ? LEGACY_META : entry);
      if (fs.existsSync(src)) fs.cpSync(src, path.join(dir, entry), { recursive: true, force: true });
    }
    out(`backup: ${rel(target, dir)} (add .owfa-backup/ to the instance .gitignore if you do not want it tracked)`);
  }

  out(`warning: local edits under ${PAYLOAD.join("/, ")}/ are replaced by the channel's tree — keep instance hotfixes in git`);
  copyPayload(target, { replace: true });
  // P2 (review): self-heal a stale shim here too — instance dirs get renamed and
  // copied, and Windows junction targets are absolute. The .gitignore sweep hint
  // covers the "tracked twice" half only the user's git can perform.
  const shimState = ensureMetaShim(target);
  if (legacyLayout) {
    if (shimState === "created" || shimState === "recreated") {
      out(`shim: .meta → .owfa ${shimState} — 0.3-era paths keep resolving until the shim retires (0.5)`);
    }
    if (shimState !== "failed") {
      out("instance git: if .meta/ was tracked before 0.4, sweep it once — git rm -r --cached .meta");
    }
  }

  out("");
  out("converging projections (python .owfa/scripts/owfa_kernel.py all)");
  if (kernel(target, ["all"]) !== 0) {
    const pending = pendingPackages(target);
    if (pending.length) {
      fail(`trees replaced, but convergence is blocked by pending semantic migrations (${pending.join(", ")}) — run \`python .owfa/scripts/owfa_kernel.py migrate <pkg>\``);
    }
    fail("kernel convergence failed after the tree replacement — the instance git snapshot is your rollback");
  }

  const pending = pendingPackages(target);
  if (pending.length) {
    out("");
    out(`pending semantic migrations: ${pending.join(", ")} — run \`python .owfa/scripts/owfa_kernel.py migrate <pkg>\` and follow the page`);
  }
  out("");
  out(`done — framework ${local} → ${incoming}${legacyLayout ? " (layout migrated to .owfa/)" : ""}`);
  return 0;
}

function cmdDoctor(args) {
  const target = path.resolve(args._[0] || ".");
  const local = readVersion(target);
  const py = findPython();
  out(`owfa ${PKG.version} (channel framework ${FRAMEWORK_VERSION})`);
  out(`node ${process.version}`);
  out(`python ${py ? py.version || `${py.cmd} ${py.args.join(" ")}` : "NOT FOUND"}`);
  out(`target ${target}`);
  if (!local) fail("not an OWFA instance (no .owfa/VERSION) — run `owfa init` first");
  out(`instance framework ${local}`);
  const problems = []; // required conditions — any hit fails doctor (review P2, PR #53)
  // layout-shim health (review P2 on the layout PR): a renamed/copied instance
  // leaves the Windows junction pointing at the old absolute path; a real .meta
  // directory means the 0.3 layout was never migrated. doctor reports; upgrade heals.
  const owfaDir = path.join(target, ".owfa");
  const metaPath = path.join(target, LEGACY_META);
  if (fs.existsSync(owfaDir) && fs.existsSync(metaPath)) {
    const st = fs.lstatSync(metaPath);
    if (!st.isSymbolicLink()) {
      out(".meta: real directory — 0.3 layout never migrated; run `owfa upgrade`");
      problems.push(".meta is not the layout shim");
    } else {
      let same = false;
      try {
        same = fs.realpathSync(metaPath) === fs.realpathSync(owfaDir);
      } catch {
        same = false; // dangling
      }
      if (!same) {
        out(".meta: shim resolves outside this instance — run `owfa upgrade` to re-create it");
        problems.push(".meta shim target is stale");
      } else {
        out(".meta shim: ok (resolves into this instance)");
      }
    }
  }
  const agents = path.join(target, "AGENTS.md");
  if (!fs.existsSync(agents)) {
    out("AGENTS.md: MISSING — the agent will not see the structural contract");
    problems.push("AGENTS.md is missing");
  } else {
    const text = fs.readFileSync(agents, "utf8");
    const ok = text.includes(INJECT_START) && text.includes(INJECT_END);
    out(`AGENTS.md: ${ok ? "injection markers present" : "MISSING injection markers"}`);
    if (!ok) problems.push("AGENTS.md injection markers are missing or broken");
  }
  if (!py) {
    out("kernel validate: skipped (no python)");
    problems.push("Python 3.9+ not found — kernel validate not run");
  } else {
    out("");
    if (kernel(target, ["validate"]) !== 0) problems.push("kernel validate failed (see above)");
  }
  out("");
  if (problems.length) {
    for (const p of problems) out(`problem: ${p}`);
    out("doctor: failed — fix the problems above");
    return 1;
  }
  out("doctor: ok");
  return 0;
}


function cmdList() {
  const target = process.cwd();
  if (!readVersion(target)) fail(`${target} is not an OWFA instance — run \`owfa init\` first`);
  return kernel(target, ["list-remote"]);
}

function cmdPkg() {
  const target = process.cwd();
  if (!readVersion(target)) fail(`${target} is not an OWFA instance — run \`owfa init\` first`);
  return kernel(target, ["pkg"]);
}

function cmdAdd(args) {
  const target = process.cwd();
  const pkg = args._[0];
  if (!pkg) fail("usage: owfa add <package> [--yes] [--without a,b] (run inside the instance)");
  if (!readVersion(target)) fail(`${target} is not an OWFA instance — run \`owfa init\` first`);
  const kernelArgs = ["install", pkg];
  if (args.flags.has("yes")) kernelArgs.push("--yes");
  if (args.without) kernelArgs.push("--without", args.without);
  const code = kernel(target, kernelArgs);
  if (code !== 0) return code;
  if (reportPending(target)) return 1;
  return kernel(target, ["all"]);
}

function usage() {
  out(`owfa ${PKG.version} — One Workspace For All (agents)
the owfa framework's install and upgrade channel

usage:
  owfa init [dir] [--name NAME] [--packages a,b] [--force]
      deploy a fresh workspace (framework ${FRAMEWORK_VERSION}); additive to existing content
  owfa upgrade [dir] [--check] [--backup] [--force]
      replace the framework trees with this channel's version and converge
  owfa doctor [dir]     python / framework / AGENTS.md / kernel validate
  owfa add <pkg> [--yes] [--without a,b]
      install a domain package from the registry, then converge
  owfa list             registry catalog (versions, compat, installed marks)
  owfa pkg              installed package inventory (members, core remainder)
  owfa version          CLI and framework versions
  owfa help

notes:
  - python 3.9+ is required to run the framework; node is only the installer
  - \`init\` never deletes instance data; \`upgrade\` preserves the kernel's
    migration ledger, journal and registry cache
  - no install/postinstall scripts: npm install executes nothing
`);
}

const COMMAND_HELP = {
  init: "usage: owfa init [dir] [--name NAME] [--packages a,b] [--without m,n] [--force]\n\n" +
        "deploy a fresh workspace (additive: existing files and AGENTS.md are preserved).\n" +
        "python 3.9+ required for the framework; node 16.7+ runs this installer only.\n" +
        "--packages installs registry packages; --without prunes members from them (dependency-closed subsets only).\n" +
        "--force re-copies the framework trees over an existing instance (instance data is never touched).",
  upgrade: "usage: owfa upgrade [dir] [--check] [--backup] [--force]\n\n" +
        "replace the framework trees with this channel's version and converge.\n" +
        "--check (alias --dry-run) is read-only; --backup snapshots the current trees to .owfa-backup/.\n" +
        "instance data, installed packages, pending migrations and standalone skills are preserved.",
  doctor: "usage: owfa doctor [dir]\n\n" +
        "health check: python, framework version, AGENTS.md injection markers, kernel validate.\n" +
        "exits non-zero when any required condition fails.",
  add: "usage: owfa add <pkg> [--yes] [--without m,n]  (run inside the instance)\n\n" +
       "install a domain package from the registry, then converge.\n" +
       "--without prunes members (dependency-closed subsets only); unindexed repos need --yes.",
  list: "usage: owfa list\n\nregistry catalog: versions, compat floors, installed marks.",
  pkg: "usage: owfa pkg\n\ninstalled package inventory: members, connectors, core remainder.",
};

const COMMAND_FLAGS = {
  init: ["force", "help", "h", ...FLAG_VALUE],
  upgrade: ["check", "dry-run", "backup", "force", "help", "h"],
  doctor: ["help", "h"],
  add: ["yes", "without", "path", "from", "help", "h", ...[]],
  list: ["help", "h"],
  pkg: ["help", "h"],
};

function main() {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") {
    usage();
    return 0;
  }
  if (cmd === "version" || cmd === "--version" || cmd === "-v") {
    out(`owfa ${PKG.version} (framework ${FRAMEWORK_VERSION})`);
    return 0;
  }
  if (!(cmd in COMMAND_HELP)) {
    out(`unknown command: ${cmd}`);
    out("");
    usage();
    return 2;
  }
  if (argv.slice(1).includes("--help") || argv.slice(1).includes("-h")) {
    out(`owfa ${PKG.version}`);
    out(COMMAND_HELP[cmd]);
    return 0;
  }
  const args = parseArgs(argv.slice(1));
  const known = new Set(COMMAND_FLAGS[cmd]);
  const bad = [...args.used].filter((k) => !known.has(k));
  if (bad.length) {
    out(`unknown option${bad.length > 1 ? "s" : ""} for ${cmd}: ${bad.map((b) => "--" + b.replace(/^-+/, "")).join(", ")}`);
    out(`see: owfa ${cmd} --help`);
    return 2;
  }
  switch (cmd) {
    case "init":
      return cmdInit(args);
    case "upgrade":
      return cmdUpgrade(args);
    case "doctor":
      return cmdDoctor(args);
    case "add":
      return cmdAdd(args);
    case "list":
      return cmdList();
    case "pkg":
      return cmdPkg();
    default:
      usage();
      return 2;
  }
}

process.exitCode = main();
