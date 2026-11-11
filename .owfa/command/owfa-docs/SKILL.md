---
name: owfa-docs
owner: framework
description: "Docs thin-router: points to the documentation map and the behavior/feedback protocol — no norms live in this skill. Fire when the user reports dissatisfaction with agent behavior (possible plugin/kernel cause), asks where something is documented, or how to file feedback. Triggers on: docs, 查文档, 文档在哪, 框架问题, 行为自检, agent-behavior, 怎么提issue."
---

# owfa-docs: thin router to the documentation layer

S-layer pointer only — the norms live in the documents (L layer). Re-read what you cite; never quote from memory.

## 1. User dissatisfaction → triage first, consent before any self-audit

When the user reports dissatisfaction with your behavior, do **not** launch an analysis on your own:

- **Not a plugin/kernel matter** (pure conversation, execution slip)? Ignore the rest of this skill — respond to the user directly, fix in-session.
- **Possibly a plugin or kernel problem?** First ask the user whether to run a behavior self-audit (**recommended** — it produces the evidence base for a real fix). Only on consent, follow the protocol: [`.owfa/docs/agent-behavior.md`](../../docs/agent-behavior.md) — feedback handling → routing → the seven-step standard.

## 2. "Where is X documented?" / "how does X work?"

Read [`.owfa/docs/map.md`](../../docs/map.md) — the routing table (what to read when), framework docs and package-repo docs both.

## 3. Filing feedback / issues

The routing table lives in [`.owfa/docs/agent-behavior.md`](../../docs/agent-behavior.md) §Routing: framework → owfa; package members → the matching `pkg-*` repo; new-plugin proposals → incubation on owfa.
