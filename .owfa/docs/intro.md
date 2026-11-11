# Introduction

> Reader: team members, contributors, and anyone who wants to understand this design. For what the mechanics *are*, the authoritative sources are the kernel reference skill and the AGENTS.md injection region. This document explains *why* we arrived here: narrative and lineage, not a mirror of the mechanics. Written 2026-10-04.

## 1. The starting problem

In every session, the agent acquires information in SASU-L order: system prompt, AGENTS.md, Skills, the user's own words, loop. The system prompt carries no information about the vault; users assume the agent remembers last time, which is impossible. Cross-session information acquisition can only rely on the agent actively reading, and in real deployments the agent has zero prior knowledge of the vault. The pain of using an AI assistant is often not a lack of intelligence, but having to reintroduce yourself every time: where your assets are, what you are studying, where the last decision left off.

## 2. The file foundation

Markdown plus plain files is the foundation. No tool-private formats; Obsidian and WebUIs are merely replaceable viewers. Now the agent can read the vault—but "being able to read" is not "knowing what to read". Reading without signposts is blind: read everything and the context explodes; miss a read and information goes dark. What the framework solves is not storage, but the structure of information disclosure.

## 3. The pointer mechanism

Pointers are low-cost signposts resident in context: location and summary are always present, and the summary is the entire source of filtering efficiency; trigger conditions and post-trigger actions are paired as needed. Progressive disclosure has three layers: pointers stay resident at minimal context cost; the pointed-to targets are read on demand; referenced material is drilled into further. index drilling down level by level is exactly this structure.

Two corollaries run through the whole framework:

- **Never hand-write what can be derived**. Hand-written pointers rot—targets move, descriptions go stale; derived pointers are mechanically regenerated, immune to rot. This is the philosophical starting point of one source, five projections
- **The ultimate purpose of disclosure is not "can be found", but "recalled when it should be recalled"**. todo is the explicit instance of a time-dimension pointer, pointing at what should be recalled at some future moment; injection lines carrying a "when to read first" condition are proactive pointers; consumes brings rules on-site when a command triggers—the same idea

## 4. Pluginization

The architecture does not enumerate. File formats and note types do not enter the constitution—types are frontmatter fields; structure is specified by each plugin on its own. One plugin, one directory: the manifest is the machine-readable essence; PLUGIN.md records the design rationale; attached-audit scripts are optional. A plugin holds a territory—which slice of paths belongs to whom, and what the write model is—and holds the outward-facing fields and disciplines.

The domain is the core abstraction. wiki recognizes only inside versus outside; an external domain is an adapter contract, embodied in six questions: external territory, landing strategy, identity proof, wiki territory, write model, trust model. Landing is essentially a write-model choice: final-state assets go into append-only storage; process containers get full read-write authority; when the truth lives elsewhere, use pointers. Borrowing vault or pointers is the default posture; a self-standing container is the exception.

## 5. Projections

One set of manifests is mechanically projected to five places: the AGENTS injection region; the check inspection blocks; the command usage blocks, ordered by consumes; the registry field section; the deployed skill copies. All are idempotently rebuilt, automatically synchronized on (un)install, and presence is registration. There is no second source of truth: to change the contract, change the manifest, and one command converges everything. A deployed instance is self-sufficient carrying only the injection region and skills—mechanism documentation lives in the runtime-visible surface, and no separate set of architecture documents that would drift is written.

## 6. Layering and bridges

- **Material layer vs. archive layer**: process artifacts live in domain workspaces—fetched material, notes, graded quizzes all included; distilled conclusions live in the wiki. The wiki receives distillates, not process
- **Global components vs. domain components**: cross-cutting services and their homes are global components—trust, log, todo, calendar, notes, user-profile—which may declare bridges; domain components belong to a domain transitively via depends. The bridge carries validation and declaration—required-bridge completeness, optional-bridge tolerance; disclosure distribution belongs to the projections
- **Collection channels**: consumer-side plugins can take the thinnest form—zero territory, pure workflow, with usage routed via the source side and aggregated on-site at the hub command. Teaching and quizzing both close the loop around the cognition profile

## 7. The team turn

On 2026-10-02 the project switched from personal use to a team project. Collaboration red lines—data boundaries, git discipline, the commit process—see the "User requirements" section of AGENTS.md, whose authority always remains AGENTS.md itself. Development artifacts enter git; instance data never does. The framework is a universal product; real courses, grades, privacy, and credentials belong to the deployment instance.

## 8. Lineage and map

A minimal chronology: 2026-08 the personal vault founded; 09-08 the prototype landed, plugins plus commands; 09-12 the validate-by-use ruling; 09-19 to 09-30 domainization and connectors; 10-02 the team turn and governance rules; 10-04 the cognition consumer side established and mechanism documentation opened. For the full stream see `log.md` and git history.

| Want to know | Go read |
|---|---|
| Constitution and collaboration red lines | `AGENTS.md` |
| Mechanics overview | the kernel reference skill |
| How the mechanics work | `.owfa/docs/mechanics.md` |
| Daily usage | `.owfa/docs/usage.md` |
| Using the sandbox | `.owfa/docs/sandbox.md` |
| Why a plugin is designed this way | that plugin's `PLUGIN.md` |
| Research basis | `.owfa/docs/research-*.md` |
| Deployment guide | `.owfa/docs/deployment.md` (five-minute path: `.owfa/docs/quickstart.md`) |
| Run history and current state | `log.md` |
