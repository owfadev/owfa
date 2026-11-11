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
console.log(`clean: ${removed} generated item(s) removed from the framework trees`);
