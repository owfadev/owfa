# Usage Guide

> Reader: the vault owner after installation — the next step after `owfa init` — plus anyone who wants to understand the collaboration shape. Command details are authoritatively disclosed in each SKILL.md under `.agents/skills/`. This document is about chaining workflows: how single commands connect into loops. Usage examples run against the suite-package pipeline path `.owfa/plugins/domains/personal/pipeline.py` (a deprecated host copy remains at `.owfa/scripts/pipeline.py` until framework 0.5.0).

> Install & deploy: the framework's [quickstart](https://github.com/owfadev/owfa/blob/master/.owfa/docs/quickstart.md) / [deployment guide](https://github.com/owfadev/owfa/blob/master/.owfa/docs/deployment.md).

## Loop One: Vault Stewardship

The general loop; a few minutes a day.

**Input**: drop files into `vault/` and tell the agent "map" — you get `wiki/vault/` proxy pages carrying SHA-256 and metadata; index, tags, and hot cache update automatically. When a conversation yields an insight worth keeping, say "save" and it settles into `wiki/notes/` as a native page — `type` for classification, `tags` for grouping. Promote precious drafts out of `wiki/tmp/` promptly; promotion deletes the draft.

**Retrieval**: say "query". The agent reads the hot cache and the index first, then answers synthetically; answers carry wikilink citations you can follow all the way down. Drilling down through index levels is itself a pointer structure.

**Delegation and reminders**: tasks delegated to the agent land in `wiki/todo.md`; one entry = a trigger condition plus one sentence. At the start of a new session the agent reads this page first; due items are proactively raised; completion closes the entry — history goes to log.

**Health**: periodically say "check" for a full audit of mechanical and semantic items. Say "profile" anytime to converge new knowledge about you into `wiki/profile.md`: assertions carry evidence, preferences expire. Before personalization decisions — forms of address, style — the agent reads it first.

The discipline in one sentence: the wiki takes distillates, not process. Process products belong to vault, tmp, and the domain workspaces; only settled conclusions enter notes.

## Loop Two: Course Study

The bb domain loop (a domain example riding on this protocol); one semester's rhythm. Requires the **owfa-cuhksz** package — installed separately via `kernel install`, bringing the **cuhksz-cli** connector (aggregating bb | sis; the older bb-cli / sis-cli wrappers remain for compatibility).

**Onboarding a course**, once at term start: cuhksz-cli pulls, with credentials stored only on the local machine; the `cuhksz/bb/<term>/<course>/` workspace materializes — document-type content in full, media as pointers; bb-map projects the wiki-side territory into four buckets: info for course information, courseware for knowledge points, assessments for assignment dossiers, attachments for attachments; the domain-root inbox.md digest page — announcement distillation plus approaching deadlines plus unsubmitted reminders, synthesized from both sources.

**Daily**, weekly:

1. Read inbox for a near-window view of announcements and deadlines
2. "Explain" / "quiz me" bb-teach and bb-quiz: ask about whatever is unclear, or give a scope for self-testing. The agent reads the cognition profile first; the unknown is explained thoroughly, the known skimmed. Significant explanations settle as ai notes into notes/; quiz grading flows back into the cognition profile with your confirmation
3. "Cognition profile" bb-track: reading the profile and gap analysis. The knowledge-point universe minus the anchored set is the gap; wrong answers trace back to the assessments review

**Closed loop**: teach explains, with ai notes as weak evidence; track converges; quiz generates questions by the profile; grading flows back as machine evidence; the next round of teach flexes against the new profile. Material lives on the bb side — notes, exam papers, the grading process; conclusions live on the wiki side — cognition readings. When the semester ends, everything freezes with term_status.

## Loop Three: Collaborative Development

The standard flow for changing a package or the framework — details in the instance AGENTS.md "commit flow": branch off the latest master; before touching manifests or commands, read `wiki/log.md` to align with current state and next steps; `kernel all` green; small commits in the `module: summary` format; push and open a PR; review and merge. Development artifacts enter git; instance data never does.

**Installing a new domain**, bringing an external source in: `kernel list-remote` shows the catalog; `kernel install <pkg> --yes` lands the package — plugins, commands, and in-repo connectors arrive in one step (connectors ride with their packages: **owfa-cuhksz** brings cuhksz-cli; **owfa-email** brings mail-cli; **owfa-bili** brings bili-cli; the lark domain declares the external lark-cli, which is not distributed by the framework). Credentials stay on the local machine; on first use read the connector skill disclosure.

**Experiments** always land in a sandbox or locally; sandbox experiment content never enters history — conclusions travel via conversation reports or docs.

## Rhythm

- calendar sources refresh daily via deployment-side cron unattended sessions; bb data TTL defaults to 1 day, the agent is the synchronizer — stale means pull now
- Onboard courses at term start, freeze at term end; a weekly check plus gap analysis; everything else triggers on use. Commands are natural-language triggered — no ceremony
