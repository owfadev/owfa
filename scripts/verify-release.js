#!/usr/bin/env node
/**
 * Release invariant gate — runs on `npm publish` (prepublishOnly), in CI before
 * publish, and by hand. Publishing without the tag/version/framework triple
 * agreeing is how a distribution channel starts lying; this is the mechanical
 * refusal.
 *
 * It inspects the actual packlist (`npm pack --dry-run --json`) rather than the
 * working tree: what ships is the only thing that matters, and `.npmignore`
 * decides that.
 */
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const problems = [];

// Target name owfa, fallback owfadev; both keep the owfa command.
if (!["owfa", "owfadev"].includes(pkg.name)) problems.push(`package name ${pkg.name} is neither the target (owfa) nor the fallback (owfadev)`);
if (!pkg.bin || pkg.bin.owfa !== "bin/owfa.js") problems.push("bin.owfa must point at bin/owfa.js");
if (!pkg.bin || pkg.bin[pkg.name] !== "bin/owfa.js") {
  problems.push(`bin.${pkg.name} is missing — npx ${pkg.name} must resolve to the CLI (declare both bins on the fallback package)`);
}
for (const hook of ["preinstall", "install", "postinstall"]) {
  if (pkg.scripts && pkg.scripts[hook]) problems.push(`${hook} script present — consumers must install without executing package code`);
}

const fw = (() => {
  try {
    return fs.readFileSync(path.join(root, ".owfa", "VERSION"), "utf8").trim();
  } catch {
    return null;
  }
})();
if (!fw) problems.push(".owfa/VERSION is missing — the framework anchor must ship");
else if (pkg.version !== fw) {
  problems.push(`package version ${pkg.version} does not equal the framework release version ${fw} (VERSION carries the full release A.B.C — the architecture line is derived, not stored)`);
}

const tag = process.env.GITHUB_REF_NAME || "";
if (process.env.GITHUB_REF_TYPE === "tag" && tag !== `v${pkg.version}`) {
  problems.push(`release tag ${tag} does not match package version v${pkg.version}`);
}

// payloads/personal/ must ship: the two-stage init installs this embedded copy
// offline; a channel tarball without it cannot bootstrap a usable instance once
// core stops shipping (refuse the release, not the user's init).
const REQUIRED = [
  "package.json",
  "README.md",
  "README.zh-CN.md",
  "LICENSE",
  ".owfa/VERSION",
  ".owfa/scripts/owfa_kernel.py",
  ".owfa/docs/deployment.md",
  ".owfa/docs/quickstart.md",
  ".agents/skills/owfa-map/SKILL.md",
  "bin/owfa.js",
  "payloads/personal/PKG.yaml",
  "payloads/personal/README.md",
  "templates/AGENTS.template.md",
];
const ALLOWED_TOP = [".owfa/", ".agents/", "bin/", "payloads/", "templates/", "package.json", "README.md",
  "README.zh-CN.md", "LICENSE"];
const FORBIDDEN = [/__pycache__/, /\.pyc$/, /(^|\/)test-repo\//, /^test\//, /^scripts\//, /^\.github\//, /pending\.json$/, /kernel-journal\.log$/, /registry-cache\.yaml$/, /^CONTRIBUTING\.md$/];

// What ships is decided by package.json files + physical absence of generated
// state (npm does not apply .npmignore inside whitelisted directories).
spawnSync(process.execPath, [path.join(__dirname, "clean-local-state.js")], { cwd: root, stdio: "ignore" });

const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const pack = spawnSync(npm, ["pack", "--dry-run", "--json", "--ignore-scripts"], { cwd: root, encoding: "utf8" });
if (pack.status !== 0) {
  problems.push(`npm pack --dry-run failed:\n${(pack.stderr || pack.stdout || "").trim()}`);
} else {
  let files = [];
  try {
    const parsed = JSON.parse(pack.stdout);
    files = (Array.isArray(parsed) ? parsed[0] : parsed).files.map((f) => f.path);
  } catch (e) {
    problems.push(`could not parse the packlist: ${e.message}`);
  }
  for (const req of REQUIRED) if (!files.includes(req)) problems.push(`missing from the tarball: ${req}`);
  for (const f of files) {
    if (!ALLOWED_TOP.some((p) => (p.endsWith("/") ? f.startsWith(p) : f === p))) problems.push(`unexpected file in the tarball: ${f}`);
    for (const bad of FORBIDDEN) if (bad.test(f)) problems.push(`local/dev state would ship: ${f}`);
  }
  if (files.some((f) => f.startsWith("vault/") || f.startsWith("wiki/"))) problems.push("instance data (vault/ or wiki/) would ship");
}

if (problems.length) {
  console.error("release gate failed:");
  for (const p of [...new Set(problems)]) console.error("  - " + p);
  process.exit(1);
}
console.log(`release gate ok — owfa ${pkg.version} (framework release ${fw})${tag ? ` (tag ${tag})` : ""}`);
