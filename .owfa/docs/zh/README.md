# OWFA 文档

读者：所有接触 OWFA 的人——新用户、已有实例的运维者、plugin/package 作者。

这套文档是分层的。[quickstart.md](quickstart.md) 让你五分钟跑起来；[intro.md](intro.md) 讲 OWFA 是什么；[usage.md](usage.md) 覆盖日常使用；[mechanics.md](mechanics.md) 深入机制（manifest、投影、bridge）；[packages.md](packages.md) 与 [developer.md](developer.md) 面向扩展系统的人；[deployment.md](deployment.md) 与 [releasing.md](releasing.md) 管装机运维与发布流水线；[conversion.md](conversion.md) 处理 0.3 → 0.4 迁移。英文正本在[上一级目录](../README.md)。

## 读者分流

| 我想…… | 读 |
|---|---|
| 用起来——五分钟建好一个 workspace | [quickstart.md](quickstart.md) |
| 懂原理——kernel、plugin、投影、bridge | [mechanics.md](mechanics.md) |
| 写插件或包 | [packages.md](packages.md) + [developer.md](developer.md) |
| 装机 / 升级实例（手动路径、各通道） | [deployment.md](deployment.md) |
| 发版——框架或包 | [releasing.md](releasing.md) |
| 把 0.3 旧实例迁到 0.4 | [conversion.md](conversion.md) |

## 专题

- [naming.md](naming.md) —— 命名史：OWFA、`owfadev`、被冻结的 `owfa` npm 名。
- [sandbox.md](sandbox.md) —— 沙盒：什么在哪里运行、什么永不被触碰。
- [agent-behavior.md](agent-behavior.md) —— agent 行为自检。
- [map.md](map.md) —— map 机制：vault 资产 → wiki 代理页。
