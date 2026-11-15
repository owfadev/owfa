# OWFA 文档

读者：所有接触 OWFA 的人——新用户、已有实例的运维者、plugin/package 作者。

这套文档覆盖**内核与通道**（协议无关）。分层：[quickstart.md](quickstart.md) 五分钟跑起来；[kernel.md](kernel.md) 深入内核机制（包、能力、投影、预算、生命周期）；[packages.md](packages.md) 与 [developer.md](developer.md) 面向扩展系统的人；[deployment.md](deployment.md) 与 [releasing.md](releasing.md) 管装机运维与发布流水线；[conversion.md](conversion.md) 处理 0.3 → 0.4 迁移。**默认协议**（源自 llmwiki 的组织法，随 personal 套件分发）在 [owfa-personal 仓](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/protocol.md)自成文档——protocol.md、usage.md 与 21 个成员 PLUGIN.md。英文正本在[上一级目录](../README.md)。

## 读者分流

| 我想…… | 读 |
|---|---|
| 用起来——五分钟建好一个 workspace | [quickstart.md](quickstart.md) |
| 懂原理——kernel、包、能力、投影 | [kernel.md](kernel.md) |
| 默认协议：谱系、槽位、词汇、成员名册 | [owfa-personal 文档](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/protocol.md) |
| 日常使用循环（默认协议） | [owfa-personal usage](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/usage.md) |
| 写plugin或包 | [packages.md](packages.md) + [developer.md](developer.md) |
| 装机 / 升级实例（手动路径、各通道） | [deployment.md](deployment.md) |
| 发版——框架或包 | [releasing.md](releasing.md) |
| 把 0.3 旧实例迁到 0.4 | [conversion.md](conversion.md) |

## 专题

- [naming.md](naming.md) —— 命名史：OWFA、`owfadev`、被冻结的 `owfa` npm 名。
- [sandbox.md](sandbox.md) —— 沙盒：什么在哪里运行、什么永不被触碰。
- [agent-behavior.md](agent-behavior.md) —— agent 行为自检。
- [map.md](map.md) —— map 机制：vault 资产 → wiki 代理页。
