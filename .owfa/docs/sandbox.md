# Using the sandbox

> Reader: team members who need to run experiments against real data. The authoritative source for sandbox governance red lines is the "User requirements" section of AGENTS.md; this document covers operations. Written 2026-10-04; updated 2026-10-13 — the in-repo sandbox left git tracking (owner re-ruling) and is local-only now.

## What it is

test-repo is a scratch deployment instance living inside the development repository — **local-only and untracked since 2026-10-13**: a fresh clone of the framework carries none of it, and nothing inside (mirrors included) can enter history. Its `.owfa/` and `.agents/` trees are a mirror of the framework, re-copied wholesale from the root side when a batch closes; everything else is the sandbox's own data zone. The inside of the sandbox is unaware of this project: a session opened at the sandbox root reads the sandbox's own AGENTS.md and skills.

## Enabling it

The sandbox is not initialized in a fresh clone. To set one up (or redo it from scratch), four steps:

1. `mkdir test-repo` at the framework root
2. Copy the framework trees in: `.owfa/` and `.agents/` from the root side
3. Create the `AGENTS.md` shell inside: one identity paragraph plus a layout description, and insert the injection region marker block — from `<!-- wiki-inject:start -->` to `<!-- wiki-inject:end -->`, keeping the region header and the explanatory lines (see [agents-example.md](agents-example.md))
4. Create four empty directories (`vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`) and run `python .owfa/scripts/owfa_kernel.py all` at the sandbox root — the injection region fills, all-green validate makes it a usable instance

## Running experiments

Open an agent session at the sandbox root and use commands normally: map, save, query, check, and the course family all work. The data zone grows naturally — wiki derived pages are built on first run, course data lands on the bb side. Artifacts and derivatives are all to be treated as local temporary material.

## Red lines

Three summarized here; the authoritative source is AGENTS.md:

- Nothing inside `test-repo/` is ever committed — the whole tree is gitignored; mirrors, data, derived pages, all of it
- Mirror updates go only through root-side re-copy. The sandbox side may modify mirror files for framework experiments, but the next re-copy overwrites them; framework-level changes should be made on a root-side branch and go through review-and-merge
- Conclusions travel via conversation reports or docs, never via sandbox archives

## Wrap-up and reset

Whether experiment data stays or goes is up to you; resetting means deleting everything outside the mirror trees — `bb/`, `wiki/`, and `__pycache__` inside the mirror — then walking "Enabling it" once more yields a clean sandbox.

## Mirror sync

Re-copy happens when a root-side batch closes. To trigger it yourself: delete the sandbox's two mirror trees, copy the whole trees in from the root side, then run kernel convergence once more. The sandbox carries no `connectors/` sources, so kernel deploy will report connector skill copies as orphans — the warning is expected; keep the copies, they remain usable.

## Sandbox vs. local

The constitution and the usage guide both say "experiments land in the sandbox or locally". The two are the same thing at two scales: test-repo is the shared-in-place sandbox inside your template checkout; opening your own local sandbox elsewhere is just a manual deployment (see [deployment.md](deployment.md)) — clone (or copy two trees), write the shell, create the directories, run convergence — and the target vault is your choice. One selection criterion: use test-repo when you need to stay in sync with the template mirror at hand; deploy elsewhere for long-term private use or for something close to your real vault.
