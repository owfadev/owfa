# AGENTS.md —— 实例种子示例

> 框架仓自身不带 AGENTS.md（库姿态——开发规则住在 README/CONTRIBUTING）。这是实例在部署指南第 ③ 步起草的种子。保持短：一段身份、一段布局、注入区逐字保留。

```markdown
# <vault name> — personal/instance library

<One paragraph: what this instance is for, whose, what lives here. Written by the human,
rewritten freely — the agent never edits outside the injection region.>

## Layout

<vault root>: `vault/` real assets · `wiki/` the md world
· `.owfa/` + `.agents/skills/` the framework body (personal suite members land via `kernel install`).

## Git

Instance snapshots follow the instance-git plugin (personal suite member, owfa-personal) — the agent commits at transaction close (`type: summary`); beyond that contract, git usage is the human's own.

<!-- wiki-inject:start -->

## wiki 注入区

> 本区为插件注入的投影，装卸插件时同步增删对应标记块；手写内容不进此区。

<!-- wiki-inject:end -->
```

经验法则：

- **注入区标记**（`<!-- wiki-inject:start -->` … `<!-- wiki-inject:end -->`）逐字复制；区内一切归 kernel 管——手写的内容会在下一次 `kernel all` 时丢失
- 区**外**的一切归你；agent 把它当作章程级上下文
- 机械跑完后，区内会为每个全量层 plugin 填入一个 `<!-- plugin:<id> v<x.y> -->` 块——那就是暴露给每个未来会话的结构契约
- 注入区有硬性字节预算（kernel 检查）：某 package 的名单行溢出预算时，正确做法是给成员降层（re-tier），而不是手工裁剪注入区
