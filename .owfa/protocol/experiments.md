# Disclosure paradigm: SASU-L and the zero-contamination discipline

> Ruling of 2026-09-12: with the project positioned for personal use, the test-set matrix and cross-validation protocol were abolished (never executed; the design is preserved in git history). This document retains the SASU-L disclosure paradigm and the zero-contamination discipline, as a mirror for writing skills / docs and for self-review.
> Basis (two rounds of empirical work on 2026-09-12: cold start on a fictional vault, migration of 25 items in a real vault): in real deployments the agent knows things only in SASU-L order, with zero priors; every "assumed known" in the framework is non-portable knowledge-layer leakage (an extension of the principle-2 touchstone). Empirical regularities—wrong-guess points = where the spec lacks examples; behavioral divergence points = where rules are absent from the execution site; silent rot = where formal-layer feedback is missing.

## SASU-L: the environment's only disclosure channel

1. **S** (system prompt) — the harness base: identity, toolset, general behavioral rules. Outside the framework's control; treat it as the given environment; differences in S across harnesses are not charged to the framework's account (including whether AGENTS.md is auto-injected at all—that too is an S-layer property)
2. **A** (AGENTS.md) — the workspace constitution: system-injected, including the plugin injection region—identity, principles, structural map
3. **S** (Skills) — the capability surface: skill **descriptions** are available at session start; bodies load on trigger—the actual reading happens inside L
4. **U** (user prompt) — the user's own words: the sole legitimate source of task semantics
5. **L** (loop) — the execute-observe cycle: reading anchors, reading pages, calling tools, post-write feedback. Anchors and pages (registry, vocabulary, PLUGIN.md, hot, index, pre-existing pages) are **resources accessed within L, not standalone stages**; **pre-existing pages are part of the spec**—the agent uses existing pages as format references (empirically: multiple sessions in the migration experiment consulted precedent pages to align format), hence gold-sample quality is disclosure quality

The first four links are a static availability ordering; all actual reading happens in L. Any information beyond this—training priors, spec restatements stuffed into prompts, verbal conventions—counts as nonexistent on the agent side.

## Zero-contamination discipline (also used for comparisons and spot checks)

- Cold-start subagent: no conversation history; the prompt contains only two things—what the environment supplies (role positioning + working directory) and the **U-layer original user task text**
- **U-layer purity**: no restating any S / A layer content (e.g. do not write "remember to reuse the vocabulary" or "remember to run the pipeline"—that is the Skills layer's job; restating it inflates the measurement)
- Interaction steps (confirmations / questions) declare their proxy approach under an "experiment protocol" statement, but must not slip in format answers along the way
- When a comparison is needed: run the same type of task before and after the change and compare friction points; running them simultaneously contaminates both

## Validate by use (since 2026-09-12)

Whether a change works is judged by real-use feedback: friction points (guessing formats, missed steps, repeatedly explaining the same thing) are spec voids; fix one spot, use one spot—no matrix thresholds.

## Layer content & capacity discipline (2026-10-06, issue #12)

Supplement distilled from the inject-region overrun incident (instance AGENTS.md at 39 KB, 97% injection region, silently truncated on four of five mainstream harnesses). SASU-L ordered *when* each channel becomes available but never stated *what each layer may carry and how much*—so the one channel with no norm, the A-layer injection region, became the dumping ground. The paradigm's own empirical rule had already located the fix: behavioral divergence points sit where rules are absent from the **execution site**—and the execution site is L (skill bodies, pages, anchors read at the moment of use), not A. A is the constitution, not the execution site.

**Content contract—what each layer stores:**

- **A (AGENTS.md)**—task-independent orientation only: identity and positioning, principles, the structural map (top-level layout, territory roots), red lines, entry pointers. Injection projections are **pointer-dense, not disclosure-complete**: a plugin's line states what it is, where its territory sits, its red lines, and where the full disclosure lives. Procedures, formats, field semantics and per-plugin mechanisms are **forbidden in A**—they belong to S or L.
- **S (skills)**—the capability surface. Descriptions are one-line trigger surfaces (the skill catalog is also always-on session context—the same tax as A, so the same leanness applies). Bodies carry the procedures and the constitutional constraints that travel with the operation (append-only, no-regeneration zones): a skill may be slimmed, never below its constitutional clauses.
- **U (user prompt)**—task semantics only; the purity rule above stands.
- **L (loop)**—the full-disclosure home: plugin manifests (the `inject` field stays the single source of a plugin's disclosure text whether or not it projects into A), PLUGIN.md design docs, wiki declaration pages, precedent pages—read at the moment of use.

**One home per fact.** The same disclosure is not carried in parallel across layers (inject region ↔ PLUGIN.md ↔ skill body): with three copies, one silently rots. Each fact is stated once, in the layer the contract assigns; the other layers hold pointers to it.

**Capacity is structural, not disciplinary.** The kernel enforces a byte budget on the projected injection region (manifest `inject_tier`: `full` projects, `member` exits; a member must reach a full-tier domain root through depends—validate checks, else it exits into invisibility). **Exposure ladder for exited members**: the family root's line must name every member (id + one phrase—the roster floor for members with no skill surface), the skill catalog carries trigger-surface awareness, and L-layer reads resolve the full contract on demand. Overrun blocks mechanical actions (a validate error since the 2026-10-06 tier migration landed the region at ~13.5 KB against the 15 KiB budget).
