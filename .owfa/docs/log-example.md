# log.md — instance seed example

> The run log of an instance (the framework repo itself keeps none — its change trail is git history + PRs + issues). Created by the log command on first write; the agent never rewrites old entries.

```markdown
# 运行日志

> 置顶追加、只增不删；条目 = `- YYYY-MM-DD <类型> [<域>]：一句话`（域标可缺省——无域事务，log 桥）。规则见 `.owfa/plugins/core/log/`，写走 `pipeline.py log`。

- 2026-10-12 other：<one sentence: what happened, from which domain, with what outcome>
- 2026-10-12 map：<one sentence per mapping transaction>
- 2026-10-11 save：<one sentence per note landed, with the page name>
```

Shape rules:

- **Prepend at the top, never rewrite** — the log is append-only history; window overflow is archived mechanically to `wiki/archive/<month>/log.md`, never trimmed by hand
- **One transaction, one line** — type (`map/save/query/check/plugin/todo/profile/other`) + optional `[domain]` tag + one sentence; evidence and detail live on pages, the log records that they happened
- Write through the pipeline (`pipeline.py log <type> <text>`), which enforces the window and the archive; hand edits are legitimate for humans but keep the format
