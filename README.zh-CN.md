# OWFA — One Workspace For All (agents)

> [English](README.md) | 简体中文

> **OWFA** 是项目名；**OWFA Core** 是框架本体（原 `vault-wiki`）；**OWFA CLI** 是安装器。公开主页为 **[`owfadev/owfa`](https://github.com/owfadev/owfa)**——`github.com/owfa` 是无关组织。见[「关于命名」](#关于命名)。

**OWFA**（One Workspace For All agents）是一个开源的 agent 工作区：开箱即用、可持续维护、端到端插件化。一个工作区——你拥有的那个目录，装着 `vault/`（真实资产）、`wiki/`（md 投影与原生笔记）和 `AGENTS.md`（章程）——是你所有 agent 反复进入的常驻上下文，而不是每次会话重新自我介绍。agent 按 SASU-L 披露次序零先验地读写；md 与纯文本文件是地基，Obsidian 等只是可替换的查看器。新能力以 package 落地——每个 package 经 registry 的人工审核门上架，欢迎贡献：为你使用的信息源写一个域 package，向 registry 提一行 PR 即可上架（见[参与贡献](#参与贡献)）。

> 状态：**alpha**——能力面经真实日常使用打磨；分发面仍年轻，外部用户尚少。**现行版本 v0.4.1**（v0.4.0 与 v0.4.1 均发布于 2026-11-14）。v0.4 完成核心拆分：发布树只含内核与内嵌 **personal** 套件（21 个插件成员）——域包（cuhksz、lark、email、bili、project……）迁入各自的 `owfa-*` 仓，按需经 [registry](https://github.com/owfadev/owfa-registry) 安装。npm 包名为 **`owfadev`**（`owfa` 之名被 npm 相似性策略冻结；包同时暴露 `owfa` 与 `owfadev` 两个 bin）。`.owfa/VERSION` 锚定的是内核契约，不是产品成熟度。

## 为什么是 OWFA

两重便利，一条原则。

**别再用手指数路。** 没有工作区时，每次会话你都在重新解释：文件在哪、那门课的页面什么意思、哪个视频看过了、上周定了什么。OWFA 把这个方向倒过来——信息自己登记进 wiki（map、save、域 package），agent 自己去找。价值就是最朴素的那种便利：原本需要你手动指向的信息，变成 agent 自己能找到的答案。

**任意 harness，你的上下文。** OWFA 以 AGENTS.md + 技能的形态交付，不是一项服务——所以它不挑哪个 agent harness 来读。今天在一个 harness 里跑，明天换一个，或者同时跑两个：工作区、记忆与插件都跟着你走。package 这条线把这点说得最具体：`bili` 包（含其自主 agent 成员）把 B 站变成可查询的档案——在一个 harness 里养起来的东西，在任何读 AGENTS.md 的 harness 里同样养得起来。你租用的是 harness，不是投进一座围墙花园。

## 关于命名

**OWFA — One Workspace For All (agents)。** 一个工作区——你拥有的目录，装着 `vault/`、`wiki/`、`AGENTS.md` 与框架本体——你使用的每一个 agent 都重新进入它，而不是每次会话重新认识它。*All* 指的是*你的*所有 agent，不是所有人，也不是托管服务；人始终是所有者与审计锚点。`vault-wiki` 退出公开面：公开文案称 **OWFA**（或 **OWFA Core**），GitHub 家在 **`owfadev/owfa`**，npm 包名是 **`owfadev`**——npm 以「与 `ow`/`ora` 过于相似」冻结了 `owfa`，`npx owfa` 不可用，因此一切安装示例写 `npx owfadev`（包装好后暴露 `owfa` bin）。完整的理据、分层与撞名对策：[`.owfa/docs/zh/naming.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/naming.md)。

## 它做什么

让 AI 编码 agent 替你经营一座「个人 wiki」：

- 资产随手丢进 `vault/`，任何格式——md、txt、csv、pdf、图片。**map** 命令把每件资产登记为 `wiki/vault/` 下的 md 投影页，带 SHA-256、元数据与链接
- 对话中的洞见与决策由 **save** 命令蒸馏为 `wiki/notes/` 下的原生笔记；会话骨架页进 `wiki/sessions/`
- **query** 命令先读热缓存与索引，再以 wikilink 引用作答
- 索引、标签、热缓存与运行日志由派生层自动维护；**check** 命令体检库健康；**plugin** 命令装卸 package
- 外部信息源以 domain 接入：lark 与 email 落为指针或归档页；calendar 管时间线；project 管项目容器；cuhksz 经 cuhksz-cli 拉课件、作业与成绩；bilibili 经 bili-cli 按需应答。翻译发生在域外；域内一切互链
- **profile** 命令维护一份关于用户的活认知档案：断言带证据，偏好会过期；任何个性化决策前先读它

## 核心概念

| 概念 | 定义 |
|---|---|
| wiki | md 世界，内外之分的内侧：各域投影 + 原生笔记 + 派生层 |
| domain | wiki 之外信息源的适配器契约。vault 是默认域；lark、project、email、cuhksz、bili 也是域 |
| vault | 默认域——真实资产仓库；命令侧只增不删，删除与修改的自由属于人 |
| SASU-L | 披露范式：agent 只经系统提示、AGENTS.md、Skills、用户的话与循环来学习 |

## 目录结构

v0.4 发布树（核心拆分，option B）——**没有** `.owfa/plugins/`，也没有 `connectors/`：

| 目录 | 内容 |
|------|------|
| `.owfa/` | 内核树：`scripts/owfa_kernel.py`（另有 pipeline、wikilib——纯标准库零依赖）、`VERSION`（框架锚点，包 `compat` 下限对它校验）、`protocol/`（字段注册表、行动纪律、披露范式）、`docs/`（人读文档——见文末索引） |
| `.owfa/command/` | 6 个框架命令母本：asset-read / owfa-check / owfa-docs / owfa-kernel / owfa-plugin / owfa-query（套件自有命令——owfa-map / owfa-save / owfa-profile——随 personal 套件走） |
| `payloads/personal/` | 内嵌的 blessed **personal** 套件副本（正仓 `owfadev/owfa-personal`，经 `scripts/sync-blessed.sh` 刷新）。21 个插件成员 + 3 个套件命令；默认 init 从此路径离线安装 |
| Packages | 域 package 各居组织仓——`owfa-cuhksz`（cuhksz-cli 聚合 bb\|sis）、`owfa-lark`、`owfa-email`（mail-cli）、`owfa-bili`（bili-cli）、`owfa-project`、`owfa-github`、`owfa-diary`、`owfa-qq`——连接器随各自的包分发；SKILL.md 经 kernel deploy 落 `.agents/skills/`。索引在 [registry](https://github.com/owfadev/owfa-registry)（`owfadev/owfa-registry`）：一行一包，人工审核的 PR 即上架门；`kernel install`/`list-remote` 对它解析，未入索引的仓 `--yes` 可装（trust: unknown） |
| `.agents/skills/` | 命令与连接器技能的部署副本（init 落框架命令；连接器技能随包到达） |
| `bin/` + `templates/` + `package.json` | npm 通道：`owfa`/`owfadev` CLI、AGENTS 种子、包清单（`owfadev`，已启用 provenance）。`test/` 与 `scripts/` 仅供开发，不随包发布 |

## 安装

```bash
npx owfadev init my-workspace   # 两阶段：内核自举，再离线安装内嵌 personal 套件
cd my-workspace
npx owfadev doctor              # 体检：python / 框架 / 标记 / kernel validate
npx owfadev list                # registry 目录
npx owfadev add cuhksz          # 可选域包
npx owfadev upgrade             # 日后：替换框架树，保留实例状态
```

npm 包名是 `owfadev`——`npx owfa` 不可用（名字被 npm 相似性策略冻结）。包同时暴露 `owfa` 与 `owfadev` 两个 bin，全局安装后即得 `owfa` 命令。前提：安装器要 Node 16.7+，内核要 Python 3.9+（纯标准库）；一个会读 AGENTS.md 与 skills 的 agent 环境；推荐 git；Obsidian 可选，仅查看器。

`init` 是加法的（既有内容不动；已有 `AGENTS.md` 保留原文，只追加注入区）。从 0.3 升级：`npx owfadev upgrade` 走核心拆分转换（attic 救援 → staging → rootless personal 套件）。框架升级替换 `.owfa/` 与 `.agents/skills/`——实例数据永不触碰；迁移台账、journal 与 registry 缓存保留。

第一次使用：在工作区根开一个 agent 会话，丢一个文件进 `vault/`，对 agent 说「owfa-map」。

## 参与贡献

欢迎贡献，package 是预定贡献面：新能力是新 package，不是 fork 框架。三条路径，由小到大——为你使用的 CLI 写一个连接器技能；写一个把外部信息源适配进 wiki 的域 package（三路径表与开发循环见 [`developer.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/developer.md)）；或改进 core。域 package 自托管于各自的 `owfa-*` 仓；上架 = 向 [registry](https://github.com/owfadev/owfa-registry) 提一行 PR，那是人工审核的信任门。Bug 与行为问题走 issues；框架本体收 PR（1 个 approving review 可合，`enforce_admins` 开启；开发规则见 [CONTRIBUTING.md](https://github.com/owfadev/owfa/blob/master/CONTRIBUTING.md)）。

## 文档索引

- [quickstart.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/quickstart.md) — 五分钟路径：一条命令或手动步骤，然后首跑
- [deployment.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/deployment.md) — 部署指南：组件、通道、首跑、包、升级、故障
- [packages.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/packages.md) — 包机制：布局、PKG.yaml、能力语法、安装通道、信任级、卸载契约
- [developer.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/developer.md) — 开发者指南：插件落位三路径表、开发循环、注册与发现
- [releasing.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/releasing.md) — npm 通道与发布手册：流水线、五载体版本不变量、合并纪律
- [conversion.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/conversion.md) — 0.3→0.4 转换与迁移：staging、续传注意事项、转换代数
- [mechanics.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/mechanics.md) — 机制：每个机制再深一层，附域家族走查；动框架前先读
- [usage.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/usage.md) — 使用指南：三种工作循环（库务、课程学习、协作开发）
- [intro.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/intro.md) — 导论：为什么是这个框架，叙事与谱系
- [naming.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/naming.md) — 命名：本义展开、每个词的承诺、两名两职、撞名对策

## 许可

MIT——见 [LICENSE](https://github.com/owfadev/owfa/blob/master/LICENSE)。
