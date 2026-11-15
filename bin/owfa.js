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
const crypto = require("node:crypto");
const { spawnSync } = require("node:child_process");

const CLI_ROOT = path.resolve(__dirname, "..");
const PKG = JSON.parse(fs.readFileSync(path.join(CLI_ROOT, "package.json"), "utf8"));
const FRAMEWORK_VERSION = readVersion(CLI_ROOT) || "?";
const INJECT_START = "<!-- wiki-inject:start -->";
const INJECT_END = "<!-- wiki-inject:end -->";
const PAYLOAD = [".owfa", ".agents"];
// v0.4 de-parasitization (final shape): the channel no longer hardcodes instance
// skeleton dirs and no longer ships .owfa/plugins/core/ — the 21 core plugins live
// in the owfa-personal suite repo, embedded at payloads/personal/, and that blessed
// copy is what a fresh init installs by default (offline, --path channel). Packages
// declare their own skeleton (`skeleton:` in PKG.yaml; the kernel mkdirs them on
// install), so the default two-stage init lands both framework and skeleton.
const BLESSED_SUITE = path.join(CLI_ROOT, "payloads", "personal");
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

// F1 (kernel-home spec v2, step 0) — user-level kernel home resolution.
// G3 isolation: env OWFA_HOME wins over the default ~/.owfa, so CI containers,
// sandboxes and multi-user SSH sessions each get their own substrate root.
// This step only defines the resolution and the dual-target kernel() dispatch;
// nothing existing changes unless a workspace carries .owfa/WORKSPACE.yaml.
function owfaHome() {
  return process.env.OWFA_HOME
    ? path.resolve(process.env.OWFA_HOME)
    : path.join(os.homedir(), ".owfa");
}

// The user-level-channel workspace marker (spec §2): a tree carrying
// .owfa/WORKSPACE.yaml declares itself served by the user-level kernel.
function hasWorkspaceMarker(target) {
  return fs.existsSync(path.join(target, ".owfa", "WORKSPACE.yaml"));
}

// --- kernel-home step 2 (spec v2): user-level kernel install & resolution ---
// A (Q1a/Q3a/Q8a/G1): kernels live as $OWFA_HOME/kernel/<X.Y.Z>/ — one dir per
// version, multi-version coexistence (G1); `current` is the workspace-
// independent "latest installed" pointer. The kernel payload is the kernel
// script plus its shared lib (owfa_kernel.py imports wikilib from its own dir).
const KERNEL_FILES = ["owfa_kernel.py", "wikilib.py"];

function kernelVersionDir(ver) {
  return path.join(owfaHome(), "kernel", ver);
}

function kernelCurrentFile() {
  return path.join(owfaHome(), "kernel", "current");
}

// G1: installed kernel versions, ascending — the tail is the "latest".
function installedKernels() {
  const base = path.join(owfaHome(), "kernel");
  let names;
  try {
    names = fs.readdirSync(base);
  } catch {
    return [];
  }
  return names
    .filter((n) => /^\d+\.\d+\.\d+$/.test(n) && fs.existsSync(path.join(base, n, "owfa_kernel.py")))
    .sort(cmpVersion);
}

// B: parse the marker's kernel_compat floor (">= X.Y.Z" — minimal-YAML, the
// marker's single key). Returns the floor version or null (absent/unparsable).
function parseKernelCompat(target) {
  try {
    const text = fs.readFileSync(path.join(target, ".owfa", "WORKSPACE.yaml"), "utf8");
    const m = text.match(/^kernel_compat:\s*(.+?)\s*$/m);
    if (!m) return null;
    let raw = m[1].trim();
    if (raw.length >= 2 && raw[0] === raw[raw.length - 1] && "\"'".includes(raw[0])) raw = raw.slice(1, -1);
    const f = raw.match(/^>=\s*(\d+(?:\.\d+){0,2})$/);
    return f ? f[1] : null;
  } catch {
    return null;
  }
}

function satisfiesFloor(ver, floor) {
  if (!floor) return true;
  return cmpVersion(ver, floor) >= 0;
}

// G1 resolution: a marker workspace is served by $OWFA_HOME/kernel/<X.Y.Z>/
// chosen as (a) the registry-bound version when it satisfies the workspace's
// kernel_compat floor, else (b) the latest installed version satisfying the
// floor. Returns null when no user-level kernel is installed at all (the
// dispatch then falls back to the legacy in-tree path) or none satisfies the
// floor (the dispatch fails loudly pointing at install-kernel).
function resolveUserKernelVersion(target) {
  const installed = installedKernels();
  if (!installed.length) return null;
  const floor = parseKernelCompat(target);
  const bound = registryFindByPath(target);
  if (bound && bound.kernel && installed.includes(bound.kernel) && satisfiesFloor(bound.kernel, floor)) {
    return bound.kernel;
  }
  const ok = installed.filter((v) => satisfiesFloor(v, floor));
  return ok.length ? ok[ok.length - 1] : null;
}

// --- user-level journal (M3): pure append, one line per event, under
// $OWFA_HOME/journal/ — compaction stays independent (step 2 keeps append only).
function userJournal(event, detail) {
  try {
    const dir = path.join(owfaHome(), "journal");
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, "events.log"), `${new Date().toISOString()} ${event} ${detail}\n`, "utf8");
  } catch {
    /* the journal must never block the channel */
  }
}

// --- C (spec §4/G2): $OWFA_HOME/workspaces.yaml — the machine workspace
// registry. path + uuid dual identity: the uuid survives re-registrations, the
// path is the live address. WORKSPACE.yaml on disk is the source of truth;
// this file is only an index (`owfa workspaces rescan` rebuilds it).
function registryPath() {
  return path.join(owfaHome(), "workspaces.yaml");
}

function parseYamlScalar(s) {
  const t = s.trim();
  if (t.length >= 2 && t[0] === t[t.length - 1] && "\"'".includes(t[0])) return t.slice(1, -1);
  return t;
}

function loadRegistry() {
  const workspaces = [];
  let cur = null;
  try {
    const text = fs.readFileSync(registryPath(), "utf8");
    for (const raw of text.split("\n")) {
      if (!raw.trim() || raw.trim().startsWith("#")) continue;
      const m = raw.match(/^\s*-\s+([A-Za-z_][\w-]*):\s*(.*)$/);
      if (m) {
        cur = { [m[1]]: parseYamlScalar(m[2]) };
        workspaces.push(cur);
        continue;
      }
      const kv = raw.match(/^\s+([A-Za-z_][\w-]*):\s*(.+)$/);
      if (kv && cur) cur[kv[1]] = parseYamlScalar(kv[2]);
    }
  } catch {
    /* absent registry = empty list */
  }
  return workspaces;
}

function saveRegistry(list) {
  const file = registryPath();
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const lines = [
    "# machine workspace registry (kernel-home spec v2 §4/G2) — channel-owned index;",
    "# WORKSPACE.yaml on disk is the source of truth; rebuild with `owfa workspaces rescan`",
    "workspaces:",
  ];
  for (const e of list) {
    lines.push(`  - id: ${e.id}`);
    lines.push(`    path: ${e.path}`);
    lines.push(`    kernel: ${e.kernel || ""}`);
    if (e.compat) lines.push(`    compat: ">= ${e.compat}"`);
    lines.push(`    registered: ${e.registered || ""}`);
  }
  fs.writeFileSync(file, lines.join("\n") + "\n", "utf8");
}

function registryFindByPath(target) {
  const hit = loadRegistry().find((e) => e.path === target);
  return hit || null;
}

function registerWorkspace(target, kernelVer) {
  const list = loadRegistry();
  let e = list.find((x) => x.path === target);
  if (!e) {
    e = { id: crypto.randomUUID(), path: target }; // G2: uuid identity survives re-registrations
    list.push(e);
  }
  e.kernel = kernelVer || "";
  const floor = parseKernelCompat(target);
  if (floor) e.compat = floor;
  e.registered = new Date().toISOString();
  saveRegistry(list);
  userJournal("workspace-register", `${target} kernel=${kernelVer || "?"}`);
  return e;
}

function unregisterWorkspace(target, reason) {
  const list = loadRegistry();
  const i = list.findIndex((x) => x.path === target);
  if (i === -1) return false;
  const [e] = list.splice(i, 1);
  saveRegistry(list);
  userJournal("workspace-unregister", `${e.path}${reason ? " — " + reason : ""}`);
  return true;
}

// G2 lazy sweep: touching the registry with a dangling path removes the entry
// and tells the user how to get it back (re-adopt after restoring the tree).
function registryLazySweep() {
  const alive = [];
  const dropped = [];
  for (const e of loadRegistry()) {
    if (fs.existsSync(path.join(e.path, ".owfa", "WORKSPACE.yaml"))) alive.push(e);
    else dropped.push(e);
  }
  if (dropped.length) {
    saveRegistry(alive);
    for (const e of dropped) {
      out(`dangling workspace removed from registry: ${e.path} — restore the tree and re-adopt (\`owfa adopt ${e.path}\`), or \`owfa workspaces rescan\` after moving it`);
      userJournal("workspace-unregister", `${e.path} — dangling path (lazy sweep, G2)`);
    }
  }
  return alive;
}

// G2 rescan: rebuild the index from disk — a bounded scan (default: the user's
// home) discovers marker workspaces; existing ids survive for live paths,
// registered-but-missing entries are dropped. Entries outside the scan root
// are kept as long as their path is alive (the registry is machine-wide).
function rescanRegistry(under) {
  const root = path.resolve(under);
  const PRUNE = new Set([".git", "node_modules", "__pycache__", ".cache", ".owfa"]);
  const found = [];
  const stack = [[root, 0]];
  let budget = 20000; // dir budget — a runaway tree must not hang the CLI
  while (stack.length && budget > 0) {
    const [dir, depth] = stack.pop();
    budget--;
    if (fs.existsSync(path.join(dir, ".owfa", "WORKSPACE.yaml"))) {
      found.push(dir);
      continue;
    }
    if (depth >= 6) continue;
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const d of entries) {
      if (d.isDirectory() && !PRUNE.has(d.name)) stack.push([path.join(dir, d.name), depth + 1]);
    }
  }
  const old = loadRegistry();
  const byPath = new Map(old.map((e) => [e.path, e]));
  const merged = [];
  for (const e of old) {
    // outside-scope or in-scope: keep every entry whose path is alive on disk
    if (fs.existsSync(path.join(e.path, ".owfa", "WORKSPACE.yaml"))) merged.push(e);
    else out(`dangling workspace dropped: ${e.path} (G2 rescan)`);
  }
  let added = 0;
  for (const p of found) {
    if (byPath.has(p)) continue;
    const e = { id: crypto.randomUUID(), path: p, kernel: resolveUserKernelVersion(p) || "" };
    const floor = parseKernelCompat(p);
    if (floor) e.compat = floor;
    e.registered = new Date().toISOString();
    merged.push(e);
    added++;
  }
  saveRegistry(merged);
  userJournal("workspace-rescan", `under=${root} found=${found.length} added=${added} kept=${merged.length}`);
  return { merged, found, added };
}

// --- A (Q7): master-hash verification. The npm tarball ships the kernel
// master; installing to $OWFA_HOME is a same-source copy, so the sha256 of
// every payload file must be equal on both sides. Same-source today — the
// check stays as the interface for any future non-same-source channel.
function kernelMasterPath(name) {
  return name === "VERSION"
    ? path.join(CLI_ROOT, ".owfa", "VERSION")
    : path.join(CLI_ROOT, ".owfa", "scripts", name);
}

function sha256File(p) {
  return crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
}

function verifyKernelInstall(verDir) {
  const problems = [];
  for (const name of [...KERNEL_FILES, "VERSION"]) {
    const a = kernelMasterPath(name);
    const b = path.join(verDir, name);
    let ha = null;
    let hb = null;
    try {
      ha = sha256File(a);
    } catch {
      problems.push(`master missing ${name}`);
    }
    try {
      hb = sha256File(b);
    } catch {
      problems.push(`install result missing ${name}`);
    }
    if (ha && hb && ha !== hb) problems.push(`${name}: master ${ha.slice(0, 12)} != installed ${hb.slice(0, 12)}`);
  }
  return problems;
}

// A (Q1a/Q3a/Q8a): install this channel's kernel master into
// $OWFA_HOME/kernel/<X.Y.Z>/ and refresh the `current` pointer to the latest
// installed version. Idempotent for the same version (files are overwritten
// with the same bytes and re-verified).
function installKernel() {
  const ver = readVersion(CLI_ROOT) || PKG.version;
  if (!/^\d+\.\d+\.\d+$/.test(ver)) fail(`channel VERSION "${ver}" is not X.Y.Z — refusing to install a kernel`);
  const verDir = kernelVersionDir(ver);
  fs.mkdirSync(verDir, { recursive: true });
  for (const name of [...KERNEL_FILES, "VERSION"]) {
    const src = kernelMasterPath(name);
    if (!fs.existsSync(src)) fail(`channel tree is missing ${rel(CLI_ROOT, src)} — the kernel master must ship (Q7)`);
    fs.copyFileSync(src, path.join(verDir, name));
  }
  const problems = verifyKernelInstall(verDir);
  if (problems.length) {
    fs.rmSync(verDir, { recursive: true, force: true });
    fail(`kernel install hash verification failed (Q7): ${problems.join("; ")}`);
  }
  const installed = installedKernels();
  fs.writeFileSync(kernelCurrentFile(), `${installed[installed.length - 1]}\n`, "utf8");
  userJournal("kernel-install", `${ver} -> ${verDir}`);
  return ver;
}

// B (spec §2/C1): the workspace marker is minimal-YAML — kernel_compat is the
// single key; protocol identity is deliberately NOT written (it derives from
// the installed protocol packages — C1 single source of truth). At most
// comment lines ride along.
function writeWorkspaceMarker(target, floorVersion) {
  const file = path.join(target, ".owfa", "WORKSPACE.yaml");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(
    file,
    [
      `# OWFA workspace marker — served by the user-level kernel (kernel-home spec v2 §2).`,
      `# Protocol identity derives from the installed protocol packages (C1) — never written here.`,
      `kernel_compat: ">= ${floorVersion}"`,
      ``,
    ].join("\n"),
    "utf8"
  );
}

function readVersion(root) {
  // F1 dual-target version source (step 2): a WORKSPACE.yaml workspace anchors
  // the five-carrier equation on the user-level kernel (Q1a) — read the
  // VERSION of the kernel version that would serve this tree, not the tree's.
  // Every other instance keeps reading the in-tree VERSION.
  if (hasWorkspaceMarker(root)) {
    const ver = resolveUserKernelVersion(root);
    if (ver) {
      try {
        return fs.readFileSync(path.join(kernelVersionDir(ver), "VERSION"), "utf8").trim();
      } catch {
        return null;
      }
    }
  }
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

const FLAG_VALUE = ["name", "packages", "without", "from", "path", "core", "under"];

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

// 0.3 quirk (review P1 round 3): the 0.3 channel wrote `upgrade --backup`
// snapshots to .owfa/backup/ even though its framework lived in .meta/. On
// migration that stray .owfa made replacePayloadTree park-and-delete the
// user's only pre-upgrade snapshots AND left .meta unparked (legacySwap never
// fired: no shim, no journal carry). Rescue the snapshots into the 0.4 backup
// home first; an emptied leftover .owfa is removed so the legacy swap takes
// over. A real 0.4 framework tree (.owfa/VERSION present) is never touched.
function rescueLegacyBackup(target) {
  const owfa = path.join(target, ".owfa");
  const meta = path.join(target, LEGACY_META);
  if (!fs.existsSync(owfa) || fs.existsSync(path.join(owfa, "VERSION"))) return;
  if (!fs.existsSync(path.join(meta, "VERSION"))) return; // no legacy framework — not the 0.3 shape
  const stray = path.join(owfa, "backup");
  if (fs.existsSync(stray)) {
    const home = path.join(target, BACKUP_DIR);
    fs.mkdirSync(home, { recursive: true });
    for (const d of fs.readdirSync(stray)) {
      if (fs.existsSync(path.join(home, d))) {
        out(`warning: backup snapshot ${d} left in .owfa/backup/ — ${BACKUP_DIR}/${d} already exists`);
        continue;
      }
      fs.renameSync(path.join(stray, d), path.join(home, d));
    }
    fs.rmSync(stray, { recursive: true, force: true });
    out(`rescued: 0.3-era upgrade snapshots moved to ${BACKUP_DIR}/`);
  }
  if (fs.readdirSync(owfa).length === 0) fs.rmSync(owfa, { recursive: true });
}

function copyPayload(target, { replace = false, userLevel = false } = {}) {
  // M1 (kernel-home spec v2 §4.5): the legacy channel must never re-plant the
  // in-tree framework over a user-level-channel workspace — a replace would
  // both dual-plant the kernel and silently drop the WORKSPACE.yaml marker.
  if (hasWorkspaceMarker(target)) {
    err(`refused: ${target} carries .owfa/WORKSPACE.yaml (user-level channel) — the legacy init/upgrade payload must not replace it; use the user-level channel (owfa upgrade)`);
    process.exit(1);
  }
  const skip = (src) => {
    const base = path.basename(src);
    if (base === "__pycache__" || base.endsWith(".pyc") || base === ".DS_Store") return false;
    if (base === "smoke-tmp") return false;
    // B (Q1a/Q2a, step 2): the user-level channel plants no tree kernel —
    // .owfa/scripts/ and .owfa/VERSION live in $OWFA_HOME/kernel/<ver>/
    // instead (install-kernel); the tree keeps everything else.
    if (userLevel) {
      const r = path.relative(path.join(CLI_ROOT, ".owfa"), src);
      if (r === "VERSION" || r.startsWith(`scripts${path.sep}`)) return false;
    }
    return true;
  };
  for (const entry of PAYLOAD) {
    const src = path.join(CLI_ROOT, entry);
    const dst = path.join(target, entry);
    if (!fs.existsSync(src)) fail(`package is missing ${entry}/ — the npm tarball is incomplete`);
    if (replace) {
      // 0.3 → 0.4 migration: the incoming .owfa/ has no counterpart on disk yet,
      // but the legacy .meta/ tree must go through the same park-and-carry swap.
      if (entry === ".owfa") rescueLegacyBackup(target);
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

// v0.4 renames the framework command/skill masters to owfa-* (review P1, PR #57
// round 2): a real 0.3 tree carries the retired names, and the difference-based
// carry-over would otherwise treat them as package-owned state and resurrect
// them beside their successors — 8 duplicate masters, `kernel all` blocked by
// one-sided owner-mapping errors. Retired framework names never carry; the map
// documents where each one lives now.
const RETIRED_MASTERS = new Map([
  ["check", "owfa-check"],
  ["docs", "owfa-docs"],
  ["map", "owfa-map"],
  ["plugin", "owfa-plugin"],
  ["profile", "owfa-profile"],
  ["query", "owfa-query"],
  ["save", "owfa-save"],
  ["wiki_plugin_kernel", "owfa-kernel"],
]);

// .owfa/command/ is mixed-ownership: framework commands ship in the fresh tree,
// package commands (kernel install) and anything the channel no longer ships are
// carried over by difference — the fresh copy wins for shared names.
function carryOverCommands(target, metaAttic) {
  const oldDir = path.join(metaAttic, "command");
  if (!fs.existsSync(oldDir)) return;
  const freshDir = path.join(target, ".owfa", "command");
  const fresh = new Set(fs.existsSync(freshDir) ? fs.readdirSync(freshDir) : []);
  for (const d of fs.readdirSync(oldDir)) {
    if (fresh.has(d) || RETIRED_MASTERS.has(d)) continue;
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
      if (fresh.has(d) || RETIRED_MASTERS.has(d)) continue; // framework-shipped / retired-via-rename — the fresh copy wins
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
    if (entry === ".owfa") rescueCoreForConversion(target, attic, dst);
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

// v0.4 core de-parasitization, rescue half: when the parked tree carries
// .owfa/plugins/core/ but the incoming channel tree does not (core stopped
// shipping), the parked masters are the only copy — move them out of the attic
// before it is deleted. The conversion itself (below) runs once the whole
// payload replace has finished, so it converges against the complete fresh tree.
// Inside the replace try-block: a failure here rolls the whole swap back.
function rescueCoreForConversion(target, attic, freshOwfa) {
  const parkedCore = path.join(attic, "plugins", "core");
  if (!fs.existsSync(parkedCore)) return;
  if (fs.existsSync(path.join(freshOwfa, "plugins", "core"))) return; // compat: channel still ships core — nothing to convert
  const hold = path.join(target, MIGRATE_SCRATCH, "convert", "core");
  if (fs.existsSync(hold)) return; // a previous failed attempt kept the rescued masters — the convert step will rerun
  fs.mkdirSync(path.dirname(hold), { recursive: true });
  fs.renameSync(parkedCore, hold);
  out("rescued: .owfa/plugins/core/ parked at " + rel(target, hold) + " — converting it into the personal suite package below");
}

// v0.4 core de-parasitization, convert half: mechanically adopt the rescued
// core masters as the `personal` suite package (a fact-accomplished conversion —
// the plugins are already in daily use in this instance, the package shape is
// new). Stages a synthetic package under .owfa-migrate/convert/personal/ (NOT
// directly under domains/ — `kernel install --path` owns that landing) and runs
// `kernel install --path ... --yes` for sweep symmetry + projection convergence
// (--yes is legitimate here: the channel itself is converting its own former
// payload, a mechanical adoption, not a trust decision).
//
// Rootless-suite conversion (kind: suite): the kernel's family-root/closure law
// does not apply, so no synthesized root plugin and no synthetic dependency
// edges — the staged package matches the canonical owfa-personal shape (21
// members, no root). The conversion stages no semantic migration (no
// migrations/ dir: nothing semantic changes — plugin bodies and projections are
// byte-identical), so there is nothing to verify-clear.
function convertCoreToPersonal(target) {
  const hold = path.join(target, MIGRATE_SCRATCH, "convert", "core");
  if (!fs.existsSync(hold)) return;
  const pkgDir = path.join(target, ".owfa", "plugins", "domains", "personal");
  if (fs.existsSync(pkgDir)) {
    out("convert: domains/personal already present — rescued core treated as already converted, holding tree discarded");
    return;
  }
  const members = fs
    .readdirSync(hold)
    .filter((d) => fs.existsSync(path.join(hold, d, "PLUGIN.yaml")))
    .sort();
  if (!members.length) fail("convert: rescued .owfa/plugins/core/ carries no plugin masters — nothing to convert");
  const staging = path.join(target, MIGRATE_SCRATCH, "convert", "personal");
  fs.mkdirSync(staging, { recursive: true });
  for (const m of members) fs.cpSync(path.join(hold, m), path.join(staging, m), { recursive: true });

  // 0.3-era rescued manifests still declare the pre-rename command ids (map /
  // profile / save) while the command masters riding with this conversion carry
  // the v0.4 successors — rewrite the staging copies' `commands:` lists so the
  // adopted roster binds (flow list and block list both handled).
  for (const m of members) {
    const mf = path.join(staging, m, "PLUGIN.yaml");
    const lines = fs.readFileSync(mf, "utf8").split("\n");
    let inCommands = false;
    for (let i = 0; i < lines.length; i++) {
      const flow = lines[i].match(/^((?:commands|usage_routes):\s*)\[(.*)\](\s*)$/);
      if (flow) {
        const items = flow[2].split(",").map((s) => s.trim()).filter(Boolean)
          .map((s) => RETIRED_MASTERS.get(s) || s);
        lines[i] = `${flow[1]}[${items.join(", ")}]${flow[3]}`;
        continue;
      }
      if (/^(commands|usage_routes):\s*$/.test(lines[i])) {
        inCommands = true;
        continue;
      }
      if (inCommands) {
        const item = lines[i].match(/^(\s*-\s*)(\S+)\s*$/);
        if (!item) {
          inCommands = false;
          continue;
        }
        lines[i] = item[1] + (RETIRED_MASTERS.get(item[2]) || item[2]);
      }
    }
    fs.writeFileSync(mf, lines.join("\n"), "utf8");
  }

  // the suite's command masters ride along: the members adopted above declare
  // them (mapping/notes/sessions/user-profile `commands:`), and the embedded
  // blessed copy carries the canonical copies — without them the converted
  // instance would lose map/save/profile until a manual `kernel upgrade personal`
  const blessedCmd = path.join(CLI_ROOT, "payloads", "personal", "command");
  if (fs.existsSync(blessedCmd)) {
    const stagingCmd = path.join(staging, "command");
    fs.mkdirSync(stagingCmd, { recursive: true });
    for (const d of fs.readdirSync(blessedCmd)) {
      fs.cpSync(path.join(blessedCmd, d), path.join(stagingCmd, d), { recursive: true });
    }
  }

  // rootless suite: kind=suite skips the family-root/closure law entirely
  // (owfa_kernel validate_packages), so no synthesized root plugin and no
  // synthetic `personal` dependency edges — the converted package matches the
  // canonical owfa-personal shape (21 members, no root). This also keeps the
  // projected injection region within the 16 KiB budget: near-capacity 0.3
  // instances (domains installed) have no headroom for an extra block.

  // synthesize PKG.yaml — skeleton and anchors preserve the pre-0.4 channel
  // contract mechanically (INSTANCE_DIRS and the kernel's former teardown
  // anchor surface), so the adopted instance behaves exactly as before
  const anchors = ["wiki/profile.md", "wiki/language.md", "wiki/calendar.md", "wiki/todo.md", "wiki/cron/"];
  const lines = [
    `# synthesized by the owfa channel: v0.4 core de-parasitization conversion (upgrade)`,
    `id: personal`,
    // kind: suite — the conversion product is a rootless-suite package: the
    // canonical owfa-personal shape, replaceable via `kernel upgrade personal`
    `kind: suite`,
    `version: 0.1.0`,
    `compat: ">= 0.4"`,
    `members:`,
    ...members.map((m) => `  - ${m}`),
    `skeleton: [vault/, wiki/notes/, wiki/sessions/, wiki/vault/]`,
    `uninstall:`,
    `  anchors: [${anchors.join(", ")}]`,
    ``,
  ];
  fs.writeFileSync(path.join(staging, "PKG.yaml"), lines.join("\n"), "utf8");

  out("");
  out(`convert: core suite (${members.length} members) -> package personal (kernel install --path, --yes: mechanical adoption)`);
  if (kernel(target, ["install", "personal", "--path", staging, "--yes"]) !== 0) {
    fail(
      `core -> personal conversion failed — the rescued masters are preserved at ${rel(target, hold)}; ` +
        `fix the error above and rerun \`owfa upgrade\` (the conversion resumes from the hold)`
    );
  }
  // success: drop the conversion scratch (and the migrate root if now empty)
  fs.rmSync(path.join(target, MIGRATE_SCRATCH, "convert"), { recursive: true, force: true });
  const scratchRoot = path.join(target, MIGRATE_SCRATCH);
  if (fs.existsSync(scratchRoot) && fs.readdirSync(scratchRoot).length === 0) fs.rmdirSync(scratchRoot);
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
  // lstat, not existsSync: a dangling shim (instance dir moved — review P2 round 2)
  // makes existsSync false, which would skip the stale branch and hit EEXIST below.
  let mst = null;
  try {
    mst = fs.lstatSync(metaPath);
  } catch {
    mst = null; // genuinely absent
  }
  if (mst) {
    if (!mst.isSymbolicLink()) return "real-dir";
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
  // F1 dual-target dispatch, step-2 form (spec §2/G1): a WORKSPACE.yaml
  // workspace is served by $OWFA_HOME/kernel/<ver>/owfa_kernel.py pointed at
  // the tree via --root, where <ver> is the registry binding or the latest
  // installed kernel satisfying the marker's kernel_compat floor. With no
  // user-level kernel installed at all, the dispatch falls back to the legacy
  // in-tree path (adopt window / behavior preservation); an installed-but-
  // unsatisfiable floor fails loudly pointing at install-kernel.
  let script = null;
  let args = kernelArgs;
  if (hasWorkspaceMarker(target)) {
    const ver = resolveUserKernelVersion(target);
    if (ver) {
      script = path.join(kernelVersionDir(ver), "owfa_kernel.py");
      args = ["--root", target, ...kernelArgs];
    } else if (installedKernels().length) {
      const floor = parseKernelCompat(target);
      fail(
        `no installed user-level kernel satisfies kernel_compat ${floor ? ">= " + floor : "(unparsable)"} for ${target} — ` +
          `run \`owfa install-kernel\` (installed: ${installedKernels().join(", ")})`
      );
    }
  }
  if (!script) {
    script = path.join(target, ".owfa", "scripts", "owfa_kernel.py");
    if (!fs.existsSync(script)) {
      fail(`no kernel at ${rel(target, script)} and no user-level kernel installed — run \`owfa install-kernel\`, or adopt this tree (\`owfa adopt ${target}\`)`);
    }
  }
  const res = spawnSync(py.cmd, [...py.args, script, ...args], {
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
  // B (kernel-home spec v2 §2, step 2): --user-level installs the kernel into
  // $OWFA_HOME, writes the WORKSPACE.yaml marker and registers the workspace.
  // The default (no flag) is byte-for-byte the legacy tree channel.
  const userLevel = args.flags.has("user-level");
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

  // two-stage bootstrap (v0.4 core de-parasitization, final shape). Stage ①: the
  // kernel payload. Stage ② (after convergence): the personal suite — by default
  // the blessed copy embedded in this channel tarball (offline, --path channel);
  // `--core none` skips it; `--core <pkg-id>` takes the suite from the registry.
  // Defensive compat branch: this channel stopped shipping .owfa/plugins/core/ in
  // v0.4.0 — if a future (or hand-assembled) channel tree ever carries core again,
  // the suite already lives in the framework tree and stage ② must not double-
  // install; saying otherwise is refused up front.
  const coreShipped =
    fs.existsSync(path.join(CLI_ROOT, ".owfa", "plugins", "core")) ||
    fs.existsSync(path.join(CLI_ROOT, ".meta", "plugins", "core"));
  if (coreShipped && args.core && args.core !== "none") {
    fail(
      `--core ${args.core}: this channel still ships the core suite inside the framework tree ` +
        `(compat period) — suite install is unavailable until the channel stops shipping core`
    );
  }

  out(`OWFA init${userLevel ? " (user-level)" : ""} — framework ${FRAMEWORK_VERSION} → ${target}`);
  if (!hasOwfa && fs.existsSync(path.join(target, ".agents", "skills"))) {
    out("note: .agents/skills/ exists — framework skill copies are updated in place, other skills stay untouched");
  }
  if (hasOwfa) out("warning: --force replaces the framework trees; instance vault/ and wiki/ are untouched");
  let kernelVer = null;
  if (userLevel) {
    // A: the user-level kernel first — convergence below dispatches onto it
    out(`user-level kernel: installing into ${path.join(owfaHome(), "kernel")} (G3 home: ${owfaHome()})`);
    kernelVer = installKernel();
    out(`user-level kernel: ${kernelVer} at ${kernelVersionDir(kernelVer)} (hash-verified, Q7)`);
  }
  copyPayload(target, { replace: hasOwfa, userLevel });
  if (userLevel) {
    // B: marker + registry — the new shape's identity pair
    writeWorkspaceMarker(target, FRAMEWORK_VERSION);
    out(`workspace marker: .owfa/WORKSPACE.yaml written (kernel_compat >= ${FRAMEWORK_VERSION}; protocol identity derives from installed packages — C1)`);
    registerWorkspace(target, kernelVer);
    out(`registry: workspace registered in ${registryPath()}`);
  } else if (ensureMetaShim(target) === "created") {
    // P1 (review): the shim is part of the 0.4 layout for EVERY legacy instance
    // shape — released 0.3 packages (cuhksz/lark/github) still instruct .meta/
    // paths, fresh instances included. User-level workspaces skip it: nothing
    // 0.3-era will ever point into a tree born on the new channel.
    out("shim: .meta → .owfa written — 0.3-era package paths keep working (retires in 0.5)");
  }
  out(`agents.md: ${ensureAgents(target, name)}`);

  out("");
  out(userLevel
    ? `converging projections (user-level kernel ${kernelVer} all --root)`
    : "converging projections (python .owfa/scripts/owfa_kernel.py all)");
  if (kernel(target, ["all"]) !== 0) {
    const pending = pendingPackages(target);
    if (pending.length) {
      fail(`convergence blocked by pending semantic migrations (${pending.join(", ")}) — clear them with \`python .owfa/scripts/owfa_kernel.py migrate <pkg>\``);
    }
    fail("kernel convergence failed — the framework tree is incomplete; nothing was deleted, fix and rerun");
  }

  // ---- stage ②: the core suite ----
  let suiteNote;
  if (coreShipped) {
    suiteNote = "core suite ships inside the framework tree (defensive compat branch — this channel does not)";
    out(`suite: ${suiteNote} — no separate suite package is installed`);
  } else if (args.core === "none") {
    suiteNote = "no suite installed — this instance cannot install packages that depend on core capabilities until a suite is installed";
    out(`suite: ${suiteNote}`);
  } else if (args.core) {
    out("");
    out(`installing core suite ${args.core} from the registry (no --yes — the trust gate stays interactive)`);
    if (kernel(target, ["install", args.core]) !== 0) {
      fail(`suite package ${args.core} failed to install — the framework itself is in place; run \`owfa doctor\``);
    }
    suiteNote = `suite ${args.core} installed from the registry`;
    if (reportPending(target)) {
      fail(`framework and suite ${args.core} are installed, but the workspace is not converged until the semantic migration above is cleared`);
    }
  } else {
    // default: the embedded blessed copy — 100% offline, local --path trust.
    // A copy without plugin masters is the placeholder state (suite repo not yet
    // synced into the channel): report it exactly like --core none. A --force
    // re-init over an instance that already carries the suite keeps it (the
    // package tree is instance state, the channel never replaces it here).
    const pkgDir = path.join(target, ".owfa", "plugins", "domains", "personal");
    const hasMasters =
      fs.existsSync(path.join(BLESSED_SUITE, "PKG.yaml")) &&
      fs.readdirSync(BLESSED_SUITE, { withFileTypes: true }).some(
        (d) => d.isDirectory() && fs.existsSync(path.join(BLESSED_SUITE, d.name, "PLUGIN.yaml"))
      );
    if (fs.existsSync(pkgDir)) {
      suiteNote = "personal suite already installed — kept";
      out(`suite: ${suiteNote}`);
    } else if (hasMasters) {
      out("");
      out("installing the blessed personal suite (embedded copy — offline)");
      if (kernel(target, ["install", "personal", "--path", BLESSED_SUITE]) !== 0) {
        fail("the embedded personal suite failed to install — the channel tarball is inconsistent; report this (the framework itself is in place)");
      }
      suiteNote = "personal suite installed (embedded blessed copy)";
      if (reportPending(target)) {
        fail("framework and suite are installed, but the workspace is not converged until the semantic migration above is cleared");
      }
    } else {
      suiteNote = "no suite installed — this instance cannot install packages that depend on core capabilities until a suite is installed (this channel build carries no populated embedded suite)";
      out(`suite: ${suiteNote}`);
    }
  }

  let installed = 0;
  if (args.packages) {
    for (const pkg of String(args.packages)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)) {
      out("");
      out(`installing package ${pkg} from the registry`);
      // no --yes forwarding (v0.4): auto-installable trust levels pass on their
      // own; anything else must go through the kernel's interactive trust gate
      const installArgs = ["install", pkg];
      if (args.without) installArgs.push("--without", String(args.without));
      if (kernel(target, installArgs) !== 0) fail(`package ${pkg} failed to install (earlier packages stay installed)`);
      installed++;
      if (reportPending(target)) fail(`framework and ${pkg} are installed, but the workspace is not converged until the semantic migration above is cleared`);
    }
  }

  out("");
  out(`done — framework ${FRAMEWORK_VERSION}${installed ? ` + ${installed} package(s)` : ""}; ${suiteNote} in ${target}`);
  out("");
  out("next:");
  out(`  cd ${target}`);
  out("  git init && git add -A && git commit -m \"init: OWFA workspace\"   # recommended: instance snapshots");
  out(`  skeleton dirs (vault/, wiki/...) came with the suite — its PKG.yaml \`skeleton:\` declared them`);
  out("  owfa doctor        # anytime: python, framework, kernel validate");
  return 0;
}

function cmdUpgrade(args) {
  const target = path.resolve(args._[0] || ".");
  // M1 anti-stomp guard (kernel-home spec §4.5): a workspace registered in the
  // user-level channel (.owfa/WORKSPACE.yaml) must not be tree-replaced by this
  // legacy channel — the two channels would clobber each other's kernel state.
  // Refuse and point at the user-level upgrade (that `owfa upgrade` lands in
  // step 2; here the refusal text is the stub).
  if (hasWorkspaceMarker(target)) {
    fail(
      `${target} carries .owfa/WORKSPACE.yaml — it is served by the user-level kernel channel, ` +
        `which this legacy tree channel refuses to upgrade (M1 anti-stomp guard). ` +
        `Use the user-level channel instead: \`owfa upgrade\` (user-level upgrade command — kernel-home step 2).`
    );
  }
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
  // v0.4 core de-parasitization: if the replace rescued a parked core/ (the
  // channel stopped shipping it), convert it into the personal suite package
  // BEFORE converging — the conversion's own install converges the adopted set.
  convertCoreToPersonal(target);
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
  // G3: report which substrate root this machine serves the workspace from —
  // env override vs default — so isolation misconfiguration is visible.
  out(`owfa-home ${owfaHome()}${process.env.OWFA_HOME ? " (OWFA_HOME)" : " (default ~/.owfa)"}`);
  out(`target ${target}`);
  if (!local) fail(
    hasWorkspaceMarker(target)
      ? `${target} carries .owfa/WORKSPACE.yaml but no servable user-level kernel — run \`owfa install-kernel\``
      : "not an OWFA instance (no .owfa/VERSION) — run `owfa init` first"
  );
  out(`instance framework ${local}`);
  // D (step 2): a marker workspace reports its kernel source and registry
  // standing — informational (registration hints never fail doctor)
  if (hasWorkspaceMarker(target)) {
    const ver = resolveUserKernelVersion(target);
    if (ver) out(`kernel source: user-level ${ver} (${kernelVersionDir(ver)})`);
    else out("kernel source: user-level, but NO installed kernel satisfies the marker's kernel_compat — run `owfa install-kernel`");
    const reg = registryFindByPath(target);
    out(`registry: ${reg ? `registered (id ${String(reg.id).slice(0, 8)}, kernel ${reg.kernel || "?"})` : `NOT registered — run \`owfa workspaces register ${target}\``}`);
  }
  const problems = []; // required conditions — any hit fails doctor (review P2, PR #53)
  // layout-shim health (review P2 on the layout PR): a renamed/copied instance
  // leaves the Windows junction pointing at the old absolute path; a real .meta
  // directory means the 0.3 layout was never migrated. doctor reports; upgrade heals.
  const owfaDir = path.join(target, ".owfa");
  const metaPath = path.join(target, LEGACY_META);
  if (fs.existsSync(owfaDir)) {
    // lstat, not existsSync: a dangling shim must reach the stale branch, not
    // silently skip the whole check (review P2, PR #57 round 2).
    let mst = null;
    try {
      mst = fs.lstatSync(metaPath);
    } catch {
      mst = null;
    }
    if (!mst) {
      out(".meta: shim missing — 0.3-era .meta/... paths will not resolve; run `owfa upgrade` to re-create it");
      problems.push(".meta shim is missing");
    } else if (!mst.isSymbolicLink()) {
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
  // step2 protocol formalization: a workspace with no protocol package installed
  // is protocol-less — a shell. Informational hint (not a problem): the user may
  // be running the bare framework deliberately; the same hint fires at uninstall
  // of the last protocol (validate is a pure plugin-graph check and never carries it).
  {
    const domainsDir = path.join(target, ".owfa", "plugins", "domains");
    let hasProtocol = false;
    if (fs.existsSync(domainsDir)) {
      for (const d of fs.readdirSync(domainsDir)) {
        try {
          const t = fs.readFileSync(path.join(domainsDir, d, "PKG.yaml"), "utf8");
          if (/^kind:\s*protocol\s*$/m.test(t)) { hasProtocol = true; break; }
        } catch { /* unreadable PKG.yaml — validate reports it */ }
      }
    }
    if (!hasProtocol) {
      out("protocol: none installed — this workspace is protocol-less (a shell); install a protocol package (see `owfa list`) or confirm bare framework use deliberately");
    } else {
      out("protocol: present");
    }
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

// A (Q1a/Q3a/Q8a): install this channel's kernel master into $OWFA_HOME.
// Internal workhorse for init --user-level / adopt; directly runnable.
function cmdInstallKernel() {
  const ver = installKernel();
  out(`installed: user-level kernel ${ver} at ${kernelVersionDir(ver)} (sha256-verified against the channel master, Q7)`);
  const installed = installedKernels();
  out(`kernels installed: ${installed.join(", ")} — current: ${fs.readFileSync(kernelCurrentFile(), "utf8").trim()}`);
  return 0;
}

// C (spec §4/G2): the machine workspace registry surface.
function cmdWorkspaces(args) {
  const sub = args._[0] || "list";
  if (sub === "list") {
    const list = registryLazySweep();
    out(`workspaces (${list.length}) — registry ${registryPath()}`);
    for (const e of list) {
      out(`  ${e.path}  kernel=${e.kernel || "?"}${e.compat ? ` compat=>= ${e.compat}` : ""}  id=${e.id}  registered=${e.registered || "?"}`);
    }
    if (!list.length) out("  (none — init --user-level and adopt register automatically; `owfa workspaces rescan` rebuilds from disk)");
    return 0;
  }
  if (sub === "register") {
    const dir = path.resolve(args._[1] || ".");
    if (!hasWorkspaceMarker(dir)) {
      fail(`${dir} carries no .owfa/WORKSPACE.yaml — only user-level workspaces register (init --user-level, or adopt a legacy tree)`);
    }
    const ver = resolveUserKernelVersion(dir);
    if (!ver) fail(`no installed user-level kernel serves ${dir} — run \`owfa install-kernel\` first`);
    const e = registerWorkspace(dir, ver);
    out(`registered: ${dir} (id ${e.id}, kernel ${ver})`);
    return 0;
  }
  if (sub === "unregister") {
    const dir = path.resolve(args._[1] || ".");
    if (!unregisterWorkspace(dir, `explicit unregister`)) {
      out(`not registered: ${dir}`);
      return 1;
    }
    out(`unregistered: ${dir}`);
    return 0;
  }
  if (sub === "rescan") {
    const under = args.under || os.homedir();
    out(`rescan: rebuilding ${registryPath()} from disk markers under ${under} (WORKSPACE.yaml is the source, the registry is the index)`);
    const { merged, found, added } = rescanRegistry(under);
    out(`rescan: ${found.length} marker workspace(s) found, ${added} newly registered, ${merged.length} total`);
    return 0;
  }
  fail("usage: owfa workspaces [list|register <dir>|unregister <dir>|rescan [--under DIR]]");
}

// D (spec Q6a/M2, issue #72): migrate an existing legacy tree onto the
// user-level kernel channel. All-or-nothing — any failed step restores the
// park exactly and exits non-zero; an interrupted adopt (park without marker)
// is never implicitly cleaned.
function cmdAdopt(args) {
  const target = path.resolve(args._[0] || ".");
  const markerFile = path.join(target, ".owfa", "WORKSPACE.yaml");
  const hold = path.join(target, ".owfa", "migrations", "kernel-exit-hold");
  // idempotent anchor (M2): WORKSPACE.yaml in place = already adopted
  if (fs.existsSync(markerFile)) {
    out(`already adopted: ${target} carries .owfa/WORKSPACE.yaml — nothing to do`);
    return 0;
  }
  // ① tree shape: a legacy 0.4 tree carries the kernel in .owfa/scripts/
  const scriptsDir = path.join(target, ".owfa", "scripts");
  if (!fs.existsSync(path.join(scriptsDir, "owfa_kernel.py"))) {
    if (fs.existsSync(path.join(target, ".meta", "VERSION"))) {
      fail(`${target} uses the 0.3 layout (.meta/) — run \`owfa upgrade\` to reach the 0.4 layout first, then adopt`);
    }
    fail(`${target} is not a legacy OWFA tree (no .owfa/scripts/owfa_kernel.py) — nothing to adopt`);
  }
  // M2/#72: a park without the marker = an interrupted adopt — refuse, restore
  // is a manual act, never an implicit cleanup retry
  if (fs.existsSync(hold)) {
    fail(
      `interrupted adopt detected: tree scripts are parked at ${rel(target, hold)} — do NOT rerun. ` +
        `Restore manually (move ${rel(target, path.join(hold, "scripts"))} back to .owfa/scripts/ and the parked VERSION to .owfa/VERSION), then rerun.`
    );
  }
  const treeVersion = readVersion(target);
  if (!treeVersion) fail(`${target} carries no readable VERSION — refusing to adopt an unidentified tree`);
  if (cmpVersion(FRAMEWORK_VERSION, treeVersion) < 0) {
    fail(`tree framework ${treeVersion} is newer than this channel's ${FRAMEWORK_VERSION} — run \`npx owfa@latest adopt\``);
  }
  out(`OWFA adopt — ${target} (tree ${treeVersion}) onto the user-level kernel channel`);
  // ② install/reuse the user-level kernel (A)
  const kernelVer = installKernel();
  out(`user-level kernel: ${kernelVer} at ${kernelVersionDir(kernelVer)}`);
  // ③ park the tree scripts (the upgrade park precedent — M2): the hold is the
  // only copy between set-aside and green validate
  fs.mkdirSync(path.dirname(hold), { recursive: true });
  fs.renameSync(scriptsDir, path.join(hold, "scripts"));
  const treeVersionFile = path.join(target, ".owfa", "VERSION");
  if (fs.existsSync(treeVersionFile)) fs.renameSync(treeVersionFile, path.join(hold, "VERSION"));
  out(`park: tree scripts held at ${rel(target, hold)} (cleared only after a green validate)`);
  // ④⑤ marker + registry + validate through the NEW kernel — any failure rolls
  // the park back whole
  try {
    writeWorkspaceMarker(target, treeVersion);
    registerWorkspace(target, kernelVer);
    out("validating through the user-level kernel (kernel validate --root)");
    if (kernel(target, ["validate"]) !== 0) throw new Error("kernel validate failed (see above)");
  } catch (e) {
    try {
      if (fs.existsSync(markerFile)) fs.rmSync(markerFile, { force: true });
      unregisterWorkspace(target, `adopt rollback (${e.message})`);
      fs.mkdirSync(path.dirname(scriptsDir), { recursive: true });
      fs.renameSync(path.join(hold, "scripts"), scriptsDir);
      if (fs.existsSync(path.join(hold, "VERSION"))) fs.renameSync(path.join(hold, "VERSION"), treeVersionFile);
      fs.rmSync(hold, { recursive: true, force: true });
    } catch (e2) {
      fail(
        `adopt failed (${e.message}) AND rollback failed (${e2.message}) — the tree scripts are parked at ${rel(target, hold)}; ` +
          `do NOT rerun until they are restored to .owfa/scripts/`
      );
    }
    fail(`adopt failed (${e.message}) — park restored, ${target} is exactly as before (all-or-nothing, #72)`);
  }
  // green: clear the hold
  fs.rmSync(hold, { recursive: true, force: true });
  userJournal("workspace-adopt", `${target} tree=${treeVersion} kernel=${kernelVer}`);
  out("");
  out(`done — ${target} now served by user-level kernel ${kernelVer} (kernel_compat >= ${treeVersion}); tree scripts removed`);
  out("next: owfa doctor — kernel source + registry status");
  return 0;
}

function usage() {
  out(`owfa ${PKG.version} — One Workspace For All (agents)
the owfa framework's install and upgrade channel

usage:
  owfa init [dir] [--name NAME] [--core none|<pkg-id>] [--packages a,b] [--force] [--user-level]
      deploy a fresh workspace (framework ${FRAMEWORK_VERSION}); additive to existing content;
      two-stage: kernel payload, then the core suite (default: embedded blessed copy,
      offline; --core none skips it; --core <pkg-id> installs from the registry)
      --user-level (kernel-home spec v2, step 2): install the kernel into
      $OWFA_HOME/kernel/<ver>/, write .owfa/WORKSPACE.yaml and register the
      workspace — no tree scripts/ or tree VERSION; the default stays legacy
  owfa install-kernel
      install this channel's kernel master into $OWFA_HOME/kernel/<X.Y.Z>/
      (multi-version coexistence, G1; sha256-verified against the master, Q7)
  owfa adopt <dir>
      migrate a legacy tree onto the user-level kernel channel: park the tree
      scripts, write the marker, register, validate through the new kernel —
      all-or-nothing (#72); idempotent (already adopted = no-op)
  owfa workspaces [list|register <dir>|unregister <dir>|rescan [--under DIR]]
      the machine workspace registry ($OWFA_HOME/workspaces.yaml); dangling
      paths are lazily unregistered with a re-adopt hint (G2); rescan rebuilds
      the index from disk WORKSPACE.yaml markers
  owfa upgrade [dir] [--check] [--backup] [--force]
      replace the framework trees with this channel's version and converge;
      if this channel stopped shipping core, the instance's core plugins are
      converted into the personal suite package (mechanical adoption)
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
  - skeleton dirs (vault/, wiki/...) come from package declarations (PKG.yaml
    \`skeleton:\`), created on install — the default init already installed the
    embedded personal suite and its skeleton
  - no install/postinstall scripts: npm install executes nothing
`);
}

const COMMAND_HELP = {
  init: "usage: owfa init [dir] [--name NAME] [--core none|<pkg-id>] [--packages a,b] [--without m,n] [--force]\n\n" +
        "deploy a fresh workspace (additive: existing files and AGENTS.md are preserved).\n" +
        "python 3.9+ required for the framework; node 16.7+ runs this installer only.\n" +
        "two-stage bootstrap: ① kernel payload ② core suite — default the blessed copy embedded\n" +
        "in the channel tarball (offline); --core none skips stage ②; --core <pkg-id> installs\n" +
        "the suite from the registry (online; the kernel's trust gate stays interactive).\n" +
        "--packages installs further registry packages; --without prunes members (dependency-closed subsets only).\n" +
        "--force re-copies the framework trees over an existing instance (instance data is never touched).\n" +
        "--user-level (kernel-home spec v2 step 2) serves the workspace from the user-level kernel\n" +
        "($OWFA_HOME/kernel/<ver>/): installs the kernel, writes .owfa/WORKSPACE.yaml (kernel_compat\n" +
        "floor = channel version; protocol identity derives from installed packages, C1) and registers\n" +
        "the workspace in $OWFA_HOME/workspaces.yaml. The tree gets no scripts/ and no VERSION.",
  "install-kernel": "usage: owfa install-kernel\n\n" +
        "install this channel's kernel master (owfa_kernel.py + wikilib.py + VERSION) into\n" +
        "$OWFA_HOME/kernel/<X.Y.Z>/ — versions coexist (G1); `kernel/current` tracks the latest\n" +
        "installed. The install result is sha256-verified against the tarball master (Q7).\n" +
        "Internal workhorse for init --user-level and adopt; directly runnable.",
  adopt: "usage: owfa adopt <dir>\n\n" +
        "migrate an existing legacy tree onto the user-level kernel channel (kernel-home spec v2\n" +
        "Q6a): park the tree scripts under .owfa/migrations/kernel-exit-hold/, write the\n" +
        "WORKSPACE.yaml marker (compat floor = tree VERSION), register the workspace, then validate\n" +
        "through the new kernel — the hold is cleared only on green. Any failure restores the park\n" +
        "exactly (all-or-nothing, #72); rerunning on an adopted tree is a no-op.",
  workspaces: "usage: owfa workspaces [list|register <dir>|unregister <dir>|rescan [--under DIR]]\n\n" +
        "the machine workspace registry ($OWFA_HOME/workspaces.yaml — path + uuid identity, G2).\n" +
        "list lazily drops dangling paths (with a re-adopt hint); rescan rebuilds the index from\n" +
        "disk WORKSPACE.yaml markers (bounded scan, default under the user's home).",
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
  init: ["force", "user-level", "help", "h", ...FLAG_VALUE],
  "install-kernel": ["help", "h"],
  adopt: ["help", "h"],
  workspaces: ["under", "help", "h"],
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
    case "install-kernel":
      return cmdInstallKernel();
    case "adopt":
      return cmdAdopt(args);
    case "workspaces":
      return cmdWorkspaces(args);
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
