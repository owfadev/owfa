# Usage Guide

> Audience: the vault owner after deployment completes — the next step after deployment — plus members who want to understand the collaboration shape. Command details are authoritatively disclosed in each SKILL.md under `.agents/skills/`. This document is about chaining workflows: how single commands connect into loops. Written 2026-10-04.

## Loop One: Vault Stewardship

The general loop; a few minutes a day.

**Input**: drop files into `vault/` and tell the agent "map" — you get `wiki/vault/` proxy pages carrying SHA-256 and metadata; index, tags, and hot cache update automatically. When a conversation yields an insight worth keeping, say "save" and it settles into `wiki/notes/` as a native page — type for classification, tags for grouping. Promote precious drafts out of `wiki/tmp/` promptly; promotion deletes the draft.

**Retrieval**: say "query". The agent reads the hot cache and the index first, then answers synthetically; answers carry wikilink citations you can follow all the way down. Drilling down through index levels is itself a pointer structure.

**Delegation and reminders**: tasks delegated to the agent land in `wiki/todo.md`; one entry = a trigger condition plus one sentence. At the start of a new session the agent reads this page first; due items are proactively raised; completion closes the entry — history goes to log.

**Health**: periodically say "check" for a full audit of mechanical and semantic items. Say "profile" anytime to converge new knowledge about you into `wiki/profile.md`: assertions carry evidence, preferences expire. Before personalization decisions — forms of address, style — the agent reads it first.

The discipline in one sentence: the wiki takes distillates, not process. Process products belong to vault, tmp, and the domain workspaces; only settled conclusions enter notes.

## Loop Two: Course Study

The bb domain loop; one semester's rhythm.

**Onboarding a course**, once at term start: bb-cli pulls, with credentials stored only on the local machine; the `bb/<term>/<course>/` workspace materializes — document-type content in full, media as pointers; bb-map projects the wiki-side territory into four buckets: info for course information, courseware for knowledge points, assessments for assignment dossiers, attachments for attachments; the domain-root inbox.md digest page — announcement distillation plus approaching deadlines plus unsubmitted reminders, synthesized from both sources.

**Daily**, weekly:

1. Read inbox for a near-window view of announcements and deadlines
2. "Explain and answer" bb-teach: ask about whatever is unclear. The agent reads the cognition profile first; the unknown is explained thoroughly, the known skimmed — or met with a question back at you. Significant explanations settle as ai notes into notes/
3. "Quiz me" bb-quiz: give a scope, optionally samples. English questions with Chinese annotations land in notes/testing/; after you answer, grading flows back into the cognition profile with your confirmation
4. "Cognition profile" bb-track: reading the profile and gap analysis. The knowledge-point universe minus the anchored set is the gap; wrong answers trace back to the assessments review

**Closed loop**: teach explains, with ai notes as weak evidence; track converges; quiz generates questions by the profile; grading flows back as machine evidence; the next round of teach flexes against the new profile. Material lives on the bb side — notes, exam papers, the grading process; conclusions live on the wiki side — cognition readings. When the semester ends, everything freezes with term_status.

## Loop Three: Collaborative Development

The standard flow for changing the framework — see AGENTS "commit flow" for details: branch off the latest master; before touching manifests or commands, read `log.md` to align with current state and next steps; `kernel all` green; small commits in the `module: summary` format; push and open a PR; the manager reviews and merges.

**Installing a new domain**, bringing an external source in: `kernel list-remote` shows the catalog; `kernel install <pkg> --yes` lands the package — plugins, commands, and in-repo connectors arrive in one step (the bb course domain brings bb-cli with it; lark declares the external lark-cli; email mail-cli). Credentials stay on the local machine; on first use read the connector skill disclosure, e.g. bb-cli's credentials and usage. The domain growth path and its decision criteria are in the mechanics doc, "How Domains Grow" section.

**Experiments** always land in the test-repo sandbox or locally. Sandbox usage is in `.owfa/docs/sandbox.md`; sandbox experiment content never enters history — conclusions travel via conversation reports or docs.

## Rhythm

- calendar sources refresh daily via deployment-side cron unattended sessions — built into lark-calendar's design; bb data TTL defaults to 1 day, the agent is the synchronizer — stale means pull now
- Onboard courses at term start, freeze at term end; a weekly check plus gap analysis; everything else triggers on use. Commands are natural-language triggered — no ceremony
