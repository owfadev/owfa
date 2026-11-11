# OWFA — One Workspace For All (agents)

> [English](README.md) | 简体中文

> **OWFA** 是项目名；**OWFA Core** 是框架本体（原 `vault-wiki`）；**OWFA CLI** 是安装器。公开主页为 **`owfadev/owfa`**——`github.com/owfa` 是无关组织。npm 包名 `owfa` 正在申请中，详见[「关于命名」](#关于命名)。

**OWFA**（One Workspace For All agents）是一个开源的 agent 工作区：开箱即用、可持续维护、端到端插件化。一个工作区——你拥有的那个目录，装着 `vault/`（真实资产）、`wiki/`（md 投影与原生笔记）和 `AGENTS.md`（章程）——是你所有 agent 反复进入的常驻上下文，而不是每次会话重新自我介绍。agent 按 SASU-L 披露次序零先验地读写；md 与纯文本文件是地基，Obsidian 等只是可替换的查看器。行为通过一份活的用户画像个性化，新能力以插件落地——每个插件都经 registry 的人工审核门发布，欢迎贡献：为你使用的信息源写一个域插件，向 registry 提一行 PR 即可上架（见[参与贡献](#参与贡献)）。

> 状态：**alpha**——能力面是经六周真实日常使用打磨出的原型（生于 2026-09-08，经两轮实际运营与一次冷启动披露审计检验，bb 课程家族在四门课真实运行）；分发面 v0.3 是首个可安装形态——经一次全新实例验收，尚无外部用户。Beta 门槛：行为契约（#34）落地 · 两位成员真实装机 · 旧实例转换走通 · 验收脚本可重放绿。`.owfa/VERSION` 锚定的是内核契约而非产品成熟度——阶段标签在这里与 release notes。2026-10-02 转为团队项目。文档语言 2026-10-06 起切换为英文。2026-10-25：框架本体有了自己的分发通道——npm CLI `owfa`（`init` / `upgrade` / `doctor` / `add`），补上「clone + 拷两棵树 + 手写 AGENTS.md」的缺口（issues #45/#46）；npm 名 `owfa` 因相似性策略冻结，申请中，`owfadev` 为兜底命名空间。
## 为什么是 OWFA

两重便利，一条原则。

**别再用手指数路。** 没有工作区时，每次会话你都在重新解释：文件在哪、那门课的页面什么意思、哪个视频看过了、上周定了什么。OWFA 把这个方向倒过来——信息自己登记进 wiki（map、save、域包），agent 自己去找。价值就是最朴素的那种便利：原本需要你手动指向的信息，变成 agent 自己能找到的答案。

**任意 harness，你的上下文。** OWFA 以 AGENTS.md + 技能的形态交付，不是一项服务——所以它不挑哪个 agent harness 来读。今天在一个 harness 里跑，明天换一个，或者同时跑两个：工作区、记忆与插件都跟着你走。插件线把这点说得最具体：`bili` 包（含其自主 agent 成员）把 B 站变成可查询的档案——在一个 harness 里养起来的东西，在任何读 AGENTS.md 的 harness 里同样养得起来。你租用的是 harness，不是投进一座围墙花园。


## 关于命名

**OWFA — One Workspace For All (agents)。** 一个工作区——你拥有的目录，装着 `vault/`、`wiki/`、`AGENTS.md` 与框架本体——你使用的每一个 agent 都重新进入它，而不是每次会话重新认识它。*All* 指的是*你的*所有 agent，不是所有人，也不是托管服务；人始终是所有者与审计锚点。`vault-wiki` 退出公开面：公开文案称 **OWFA**（或 **OWFA Core**），GitHub 家在 **`owfadev/owfa`**，CLI 以 `owfa` 之名发布。npm 地址尚未空闲——npm 以「与 `ow`/`ora` 过于相似」冻结了 `owfa`，申诉进行中，`owfadev` 为兜底包。完整的理据、分层与撞名对策：[`.owfa/docs/naming.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/naming.md)。

## 它做什么

让 AI 编码 agent 替你经营一座「个人 wiki」：

- 资产随手丢进 `vault/`，任何格式——md、txt、csv、pdf、图片。**map** 命令把每件资产登记为 `wiki/vault/` 下的 md 投影页，带 SHA-256、元数据与链接
- 对话中的洞见与决策由 **save** 命令蒸馏为 `wiki/notes/` 下的原生笔记；会话骨架页进 `wiki/sessions/`
- **query** 命令先读热缓存与索引，再以 wikilink 引用作答
- 索引、标签、热缓存与运行日志由派生层自动维护；**check** 命令体检库健康；**plugin** 命令装卸结构插件
- 外部信息源以域接入：lark 与 email 落为指针或归档页；calendar 管时间线；project 管项目容器；bb 经 bb-cli 拉课件、作业与成绩；bilibili 经 bili-cli 按需应答（搜索/详情/收藏/UP 追更；视频摘要与评审经显式请求归档；低风险写白名单须用户显式动词）。翻译发生在域外；域内一切互链
- **profile** 命令维护一份关于用户的活认知档案：断言带证据，偏好会过期；任何个性化决策前先读它
- **teach** 命令按认知档案讲解——熟点略讲或抽测，生点拆解；重要问答沉淀进 ai notes
- **quiz** 命令按范围加可选样本出题；批改结果回流认知档案
- **track** 命令读写每门课的 user.md 学习状态；teach 与 quiz 的使用挂载于此

## 核心概念

| 概念 | 定义 |
|---|---|
| wiki | md 世界，内外之分的内侧：各域投影 + 原生笔记 + 派生层 |
| domain | wiki 之外信息源的适配器契约。vault 是默认域；lark、project、email、bb、bili 也是域 |
| vault | 默认域——真实资产仓库；命令侧只增不删，删除与修改的自由属于人 |
| SASU-L | 披露范式：agent 只经系统提示、AGENTS.md、Skills、用户的话与循环来学习 |

## 目录结构

| 目录 | 内容 |
|------|------|
| `.owfa/` | 原型核心，两级插件布局：`plugins/core/`（20 个框架插件——domain 与 wiki 两个概念根、横切件，以及 vault/mapping/structure 的明示章程例外）+ `plugins/domains/<pkg>/`（一包一目录：`PKG.yaml` + 家族母本——cuhksz 8、lark 4、email、bili、project）。目录边界 == 层级边界 == 包边界；`PKG.yaml` 声明名册，内核对账家族闭包；`.owfa/VERSION` 锚定框架版本（包 `compat` 下限对它校验）。注入次序 = 依赖拓扑 + 字典序；AGENTS 注入区分层——成员级域件退出注入区（家族名册 + 技能 + 按需 manifest 读取承担曝光），受内核字节预算约束；全局插件可声明桥，必依桥由内核校验。另有 13 个命令母本、协议工件（registry、actions、experiments）与机械脚本 owfa_kernel、pipeline、wikilib——纯标准库零依赖 |
| `connectors/` | 连接器母本：部署侧 CLI 事实接口 + 技能使用披露。`connectors/*/SKILL.md` 经内核 deploy 落入 `.agents/skills/`；现有 bb-cli、sis-cli、mail-cli、bili-cli。连接器随各自包的 `PKG.yaml` 走 |
| Packages | 索引在 [registry](https://github.com/owfadev/registry)（Obsidian 模式：包自托管于各自仓，一行 PR 即上架门）。`kernel install`/`list-remote` 对它解析；未入索引的仓 `--yes` 可装（trust: unknown）。组织仓 `pkg-cuhksz` / `pkg-lark` / `pkg-email` / `pkg-bili` / `pkg-project` / `pkg-github` 承载各包，带完整文件谱系拆分 |
| `.agents/skills/` | 命令与连接器技能的部署副本（拆分后框架命令在此；连接器技能随包到达） |
| `bin/` + `templates/` + `package.json` | npm 通道：`owfa` CLI、AGENTS 种子、包清单。`test/` 与 `scripts/` 仅供开发，不随包发布 |
| `test-repo/` | 本地测试沙盒——2026-10-13 起不入 git（owner 裁定；全新 clone 不含它）。需要 AGENTS.md 上下文的实验用临时部署；设置与规则见 [`.owfa/docs/sandbox.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/sandbox.md)。框架仓自身不带 AGENTS.md——库姿态；开发规则在 [CONTRIBUTING.md](https://github.com/owfadev/owfa/blob/master/CONTRIBUTING.md) |
| `.owfa/docs/` | 人读文档：`intro.md` 导论、`mechanics.md` 机制、`usage.md` 使用指南、`deployment.md` 全指南 / `quickstart.md` 五分钟路径、`instance-git.md` 实例侧 git 最小契约、`research-*.md` 研究文件——文末直链。权威机制在内核参考 skill；文档不复写机制 |

## 参与贡献

欢迎贡献，插件是预定贡献面：新能力是新插件，不是 fork 框架。三条路径，由小到大——为你使用的 CLI 写一个连接器技能；写一个把外部信息源适配进 wiki 的域插件（三路径表与开发循环见 [`developer.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/developer.md)）；或改进 core。域包自托管于各自仓；上架 = 向 [registry](https://github.com/owfadev/registry) 提一行 PR，那是人工审核的信任门。Bug 与行为问题走 issues；框架本体收 PR。

## 协作

本仓是团队项目：三名成员有写权限，一切经 PR（1 个 approving review 可合，`enforce_admins` 开启）；owner 对仓库设置、权限与章程/内核变更有最终决定权。数据红线、提交流程与版本纪律 summarized 在 [CONTRIBUTING.md](https://github.com/owfadev/owfa/blob/master/CONTRIBUTING.md)——权威开发规则；变更轨迹是 git 历史 + PR + issues（本仓不留运行日志）。

## 快速开始

两条入口。**通道（推荐）：** `npx owfa init my-workspace`——安装器要 Node 16.7+，Core 要 Python 3.9+；无需 clone（npm 名申请期间用 `npx owfadev init` 兜底）。**手动：** clone 本仓并按 [quickstart.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/quickstart.md) 的五步走，然后 `python .owfa/scripts/owfa_kernel.py all`。含包与升级的全指南：[deployment.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/deployment.md)。

前提：Python 3.9+，纯标准库，框架本身免安装（连接器自带依赖）；仅 npm 通道要 Node 16.7+；推荐 git（实例快照）；一个会读 AGENTS.md 与 skills 的 agent 环境，如 ZCode；Obsidian 可选，仅查看器。

在仓库根开一个 agent 会话。AGENTS.md 是章程，含插件注入区；十三个命令经自然语言触发：**owfa-map / owfa-save / owfa-profile / owfa-query / owfa-check / owfa-plugin / lark-map / bb-map / asset-read / 内核参考 / teach / quiz / track**——owfa-map、owfa-save、owfa-profile、owfa-query、owfa-check、owfa-plugin、lark-map、bb-map、asset-read、owfa-kernel、bb-teach、bb-quiz、bb-track；母本在 `.owfa/command/`。丢一个文件进 `vault/`，对 agent 说「owfa-map」——这就是第一次使用。

## 部署

OWFA 有三层：**OWFA CLI**（安装器，绝不拷入工作区）、**OWFA Core**（`.owfa/` + `.agents/skills/`，被安装之物）与 **kernel**（Core 内的纯标准库 Python 脚本——没有单独的内核安装；Python 3.9+ 即可运行）。`.owfa/plugins/domains/<pkg>/` 下的域包是可选的。

```bash
npx owfa init my-workspace        # 目标名；申请期间用 npx owfadev init
cd my-workspace
npx owfa doctor                   # 体检：python / 框架 / 标记 / kernel validate（兜底用 npx owfadev doctor）
npx owfa list                     # registry 目录
npx owfa add cuhksz               # 可选包
npx owfa upgrade                  # 日后：替换框架树，保留实例状态
```

名字申请期间，把上面每条 `npx owfa` 换成 `npx owfadev` 即可（或全局安装任一包；两者都暴露 `owfa` 命令）。

`init` 是加法的：既有内容不动，已有 `AGENTS.md` 保留、只追加注入区。`upgrade` 替换 `.owfa/` 与 `.agents/skills/`（实例数据永不触碰），保留内核迁移台账、journal 与 registry 缓存。

- 全部署指南（组件、通道、包、升级、故障）：[`.owfa/docs/deployment.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/deployment.md)
- 五分钟路径：[`.owfa/docs/quickstart.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/quickstart.md)
- 通道设计与发布手册：[`.owfa/docs/distribution.md`](https://github.com/owfadev/owfa/blob/master/.owfa/docs/distribution.md)

## 文档索引

- [.owfa/docs/deployment.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/deployment.md) — 部署指南：组件、通道、首跑、包、升级、故障
- [.owfa/docs/naming.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/naming.md) — 命名：本义展开、每个词的承诺、两名两职、异议与撞名对策
- [.owfa/docs/distribution.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/distribution.md) — npm 通道：命令、工件、版本不变量、发布手册、安全姿态
- [.owfa/docs/packages.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/packages.md) — 包机制与设计理据：布局、PKG.yaml、不变量、版本、卸载契约、决策台账
- [.owfa/docs/developer.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/developer.md) — 开发者指南：插件落位三路径表、开发循环、注册与发现
- [.owfa/docs/agents-example.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/agents-example.md) / [.owfa/docs/log-example.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/log-example.md) — AGENTS.md 与 log.md 的实例种子（框架仓自身两者都不带）
- [.owfa/docs/intro.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/intro.md) — 导论：为什么是这个框架，叙事与谱系
- [.owfa/docs/mechanics.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/mechanics.md) — 机制：每个机制再深一层，附 bb 家族走查；动框架前先读
- [.owfa/docs/usage.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/usage.md) — 使用指南：三种工作循环（库务、课程学习、协作开发）
- [.owfa/docs/quickstart.md](https://github.com/owfadev/owfa/blob/master/.owfa/docs/quickstart.md) — 五分钟路径：一条命令或手动五步，然后首跑
- `.owfa/protocol/` — 字段注册表、行动纪律、披露范式

## 许可

MIT——见 [LICENSE](https://github.com/owfadev/owfa/blob/master/LICENSE)。
