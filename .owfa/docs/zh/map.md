# 文档地图——什么情况读什么

> 这是 `.owfa/docs/`（框架侧）与各包仓库文档的路由表。agent 的入口索引；skills 指向这里，文档本身始终是事实源。

| 情形 | 去读 |
|---|---|
| 用户报告对 agent 行为的不满；行为自检 | [zh/agent-behavior.md](agent-behavior.md) —— 反馈处理（同意门）→ 路由 → 七步标准 |
| 提反馈——归哪个仓 | [zh/agent-behavior.md](agent-behavior.md) §路由 |
| 包 / 安装 / 升级 / 迁移如何运转（设计 + 决策台账） | [zh/packages.md](packages.md) |
| 部署实例；组件（CLI/Core/kernel）；通道；包；升级；排障 | [zh/deployment.md](deployment.md) |
| 五分钟安装路径 | [zh/quickstart.md](quickstart.md) |
| 框架本体的安装/升级；npm 通道；发布 runbook | [zh/releasing.md](releasing.md) |
| 名字：OWFA 展开、两名两职、撞名政策 | [zh/naming.md](naming.md) |
| 把存量（拆分前扁平）实例转入包时代 | [zh/conversion.md](conversion.md) —— 真实实例上走过的八步演练 |
| 实例 git 用法（快照、红线、恢复） | instance-git plugin（personal 套件成员；正仓 [owfa-personal](https://github.com/owfadev/owfa-personal)，内嵌副本 `payloads/personal/instance-git/`） |
| 框架机制：投影、桥、注入、inject 层级 | [zh/mechanics.md](mechanics.md) |
| (un)install 历史、包生命周期 | [zh/mechanics.md](mechanics.md) §7 + [zh/packages.md](packages.md) |
| 第三方视角：开发 → 发布 → 安装 → 更新 → 卸载；名称治理 | [zh/packages.md](packages.md) |
| 试验：sandbox 或本地 | [zh/sandbox.md](sandbox.md) |
| 开发规则、commit 流、模板 + 实例工作流 | [CONTRIBUTING.md](https://github.com/owfadev/owfa/blob/main/CONTRIBUTING.md) —— 模板仓根部（实例去那里读，不自留副本） |
| 日常使用循环 | [zh/usage.md](usage.md) |
| 框架是什么、入门 | [zh/intro.md](intro.md) |
| 包侧 plugin 文档（bb 家族、lark 家族……） | 归属 `owfa-*` 仓的 plugin 母本 |
| AGENTS.md 种子 / log 种子示例 | [zh/agents-example.md](agents-example.md)、[zh/log-example.md](log-example.md) |
