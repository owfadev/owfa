# log.md —— 实例种子示例

> 实例的运行日志（框架仓自身不保有——它的变更轨迹是 git 历史 + PR + issue）。首次写入时由 log 命令创建；agent 永不改写旧条目。

```markdown
# 运行日志

> 置顶追加、只增不删；条目 = `- YYYY-MM-DD <类型> [<域>]：一句话`（域标可缺省——无域事务，log 桥）。规则见 personal 套件（owfa-personal，内嵌副本 `payloads/personal/log/`）的 log plugin，写走 `pipeline.py log`。

- 2026-10-12 other：<one sentence: what happened, from which domain, with what outcome>
- 2026-10-12 map：<one sentence per mapping transaction>
- 2026-10-11 save：<one sentence per note landed, with the page name>
```

形态规则：

- **置顶追加、永不改写**——log 是 append-only 历史；窗口溢出由机械归档到 `wiki/archive/<month>/log.md`，绝不手工裁剪
- **一事务一行**——类型（`map/save/query/check/plugin/todo/profile/other`）+ 可选 `[domain]` 标 + 一句话；证据与细节住在页面上，log 只记录它们发生过
- 写入走 pipeline（`pipeline.py log <type> <text>`），由它强制窗口与归档；人手编辑是合法的，但保持格式
