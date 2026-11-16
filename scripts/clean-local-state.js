#!/usr/bin/env node
/**
 * Remove generated local state from the framework trees before packing.
 *
 * `files` in package.json is a whitelist, and npm does not apply .npmignore
 * inside whitelisted directories — so bytecode and kernel state have to be
 * physically absent when the tarball is built. Only the framework trees are
 * touched; instance data, test-repo and dev files are outside the payload.
 */
"use strict";

const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const FRAMEWORK_TREES = [".owfa", ".agents"];
const STATE = [
  ".owfa/migrations/pending.json",
  ".owfa/kernel-journal.log",
  ".owfa/registry-cache.yaml",
  ".owfa/smoke-tmp",
];

function versionTuple(v) {
  return String(v || "").split(".").map((x) => parseInt(x, 10) || 0);
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

// 0.5.0 shim retirement: from 0.5.0 on the pipeline host shim
// (.owfa/scripts/pipeline.py) must not ship — npm applies no per-file excludes
// inside the whitelisted .owfa/ tree, so physical absence at pack time is the
// only mechanism (verify-release.js independently forbids it in the packlist).
// OWFA_TEST_SHIMS_RETIRED=1 mirrors the gate in bin/owfa.js for local trials.
function shimsRetired() {
  if (process.env.OWFA_TEST_SHIMS_RETIRED === "1") return true;
  try {
    const fw = fs.readFileSync(path.join(root, ".owfa", "VERSION"), "utf8").trim();
    return cmpVersion(fw, "0.5.0") >= 0;
  } catch {
    return false;
  }
}
const RETIRED_PAYLOAD = [".owfa/scripts/pipeline.py"];


function walk(dir, hit) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "__pycache__") hit(p);
      else walk(p, hit);
    } else if (entry.name.endsWith(".pyc")) {
      hit(p);
    }
  }
}

let removed = 0;
for (const tree of FRAMEWORK_TREES) {
  walk(path.join(root, tree), (p) => {
    fs.rmSync(p, { recursive: true, force: true });
    removed++;
  });
}
for (const rel of STATE) {
  const p = path.join(root, rel);
  if (fs.existsSync(p)) {
    fs.rmSync(p, { recursive: true, force: true });
    removed++;
  }
}
if (shimsRetired()) {
  for (const rel of RETIRED_PAYLOAD) {
    const p = path.join(root, rel);
    if (fs.existsSync(p)) {
      fs.rmSync(p, { recursive: true, force: true });
      removed++;
      console.log(`clean: removed retired shim ${rel} from the payload (0.5.0 retirement — restore with git checkout if developing pre-0.5.0)`);
    }
  }
}
console.log(`clean: ${removed} generated item(s) removed from the framework trees`);
