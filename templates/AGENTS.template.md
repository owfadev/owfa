# {{name}}

This is an OWFA workspace — a `vault/` of real assets plus a `wiki/` the agent can re-enter without being re-introduced. `vault/` holds files in any format, `wiki/` holds the markdown pages the agent reads and writes, and `.owfa/` + `.agents/skills/` are the framework body. Rewrite this paragraph freely: everything outside the injection region is yours, and the agent never edits it.

## Layout

`vault/` real assets · `wiki/` the md world · `.owfa/` + `.agents/skills/` the framework body (domain packages under `.owfa/plugins/domains/`).

## Git

Instance snapshots follow the instance-git plugin (core) — the agent commits at transaction close (`type: summary`); beyond that contract, git usage is the human's own.

<!-- wiki-inject:start -->

## wiki 注入区

> 本区为插件注入的投影，装卸插件时同步增删对应标记块；手写内容不进此区。

<!-- wiki-inject:end -->
