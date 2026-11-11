# AGENTS.md — instance seed example

> The framework repo itself carries no AGENTS.md (library posture — dev rules live in README/CONTRIBUTING). This is the seed an instance drafts at deployment step ③ of the deployment guide. Keep it short: one identity paragraph, one layout paragraph, the injection region verbatim.

```markdown
# <vault name> — personal/instance library

<One paragraph: what this instance is for, whose, what lives here. Written by the human,
rewritten freely — the agent never edits outside the injection region.>

## Layout

<vault root>: `vault/` real assets · `wiki/` the md world
· `.owfa/` + `.agents/skills/` the framework body (packages under `.owfa/plugins/domains/`).

## Git

Instance snapshots follow the instance-git plugin (core) — the agent commits at transaction close (`type: summary`); beyond that contract, git usage is the human's own.

<!-- wiki-inject:start -->

## wiki 注入区

> 本区为插件注入的投影，装卸插件时同步增删对应标记块；手写内容不进此区。

<!-- wiki-inject:end -->
```

Rules of thumb:

- The **injection region markers** (`<!-- wiki-inject:start -->` … `<!-- wiki-inject:end -->`) are copied verbatim; everything inside is kernel-managed — hand-writing there is lost on the next `kernel all`
- Everything **outside** the region is yours; the agent treats it as constitution-level context
- After the mechanical run, the region fills with one `<!-- plugin:<id> v<x.y> -->` block per full-tier plugin — that is the structural contract surfaces to every future session
- The injection region has a hard byte budget (kernel-checked): if a package's roster line overflows it, re-tier members rather than trimming the region by hand
