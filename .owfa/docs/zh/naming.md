# 名字

> **OWFA — One Workspace For All (agents)。**
> 公开框架：**OWFA Core** · 安装器：**OWFA CLI** · GitHub：**owfadev/owfa** · npm：`owfadev`（bin `owfa` + `owfadev`）。

这页存在，是因为名字是与敲它的人签的契约。它记录每个词承诺了什么、哪些层不可合并、名字实际解析到哪里。

## 那句话

按原样使用展开式。任何公开文本中不得展开为 *One Wiki For All* 或 *One Web For All*——前者是另一个（更小的）主张，后者属于一个无关的 GitHub 组织。缩写需要独立出现时，每份文档配一次括号注，之后用 `OWFA`。

- 中文：**一个工作区，装下你所有的 agent。**
- 一句话：OWFA gives every agent you use one workspace to re-enter — your assets, your wiki, your instructions — instead of re-introducing yourself every session.
- 对 agent：「这是一个 OWFA 工作区：`vault/` 放真实资产，`wiki/` 放 md 世界，`.owfa/` + `.agents/skills/` 是框架本体。先读 AGENTS.md，再从各 index 干活。」

## 每个词的承诺

**One**——一个目录，一个新会话重新进入的地方。不是一个吞下所有工具的应用，也不是一个厂商账号。单位是人拥有、每个 agent 都读的工作区。

**Workspace**——外层对象：`vault/` + `wiki/` + `AGENTS.md` + 框架本体。wiki 是*内层*的 markdown 世界；workspace 是用户真正拥有、搬运、备份、指向 agent 的东西。给 workspace 而不是 wiki 命名是有意的：贡献在重入面，不在 markdown 这个格式。

**For all (agents)**——所有*你的* agent：跨 harness（ZCode、Claude Code、Cursor、dsh……）、跨会话、跨时间。**不**指所有人、所有数据或托管服务。括号是名字的一部分，不是脚注——它让主张为真。人始终是所有者与审计锚；agent 是零先验重入的那一方。

名字回答的是项目真实的起点之痛：每个会话都要被重新介绍的 agent。「One workspace for all agents」就是那个痛的反面。

## 分层——不可合并

| 层 | 名字 | 住在哪 | 职责 |
|---|---|---|---|
| 产品 | **OWFA** | README、npm 页、文档 | 品牌 |
| 框架 | **OWFA Core** | `.owfa/` + `.agents/skills/` | 被装进工作区的本体 |
| 安装器 | **OWFA CLI** | `bin/owfa.js`（npm 包 `owfadev`） | 取树；子命令：`init / install-kernel / adopt / workspaces / upgrade / doctor / add / list / pkg / version` |
| 引擎 | **kernel** | `.owfa/scripts/owfa_kernel.py` | validate / inject / registry / deploy / install 机制 |
| plugin 层 | **core** | owfa-personal 套件包（通道内嵌于 `payloads/personal/`） | 原 21 个框架 plugin |
| 扩展 | **package** | `.owfa/plugins/domains/<pkg>/` | domain 家族（cuhksz、lark、email、bili、project……） |
| 单位 | **instance** | 用户的目录 | 一个已部署的工作区 |

调用链正是名字必须分立的理由：

```
npx owfadev init
  └─ bin/owfa.js            CLI：取载荷、拷树、写 AGENTS.md、调引擎
       └─ kernel             validate → inject → registry → deploy
            └─ core plugin   投影进 AGENTS.md 的结构契约
```

由此两条规则：

- **CLI ≠ kernel。** CLI 是可替换的投递（今天是 npm，明天可以 pipx 或 curl）；kernel 是契约固定的确定性机制。把 kernel 改叫「OWFA CLI」会把两者合并，让 npm 通道显得拥有它并不拥有的语义。
- **`core` 是 plugin 层。** 框架公开称 *OWFA Core*，仓库则是 `owfadev/owfa`——一个词两个所指靠「永不把仓库命名为 `core`」避免。若将来拆分，`owfadev/core`（框架本体）与 `owfadev/cli`（安装器）可以拿走这个词，也只有那时 `core` 才指仓库。

`vault-wiki` 已从公开面退役：公开文案说 OWFA（或 OWFA Core），仓库是 `owfadev/owfa`。旧字符串存于历史、旧链接与技术标识符；kernel、plugin 目录、包 id 不做任何大爆改。

## 两个名字，两份职——定局格局

| 名字 | 职责 | 出现在哪 |
|---|---|---|
| `vault-wiki` | 历史/技术别名——代码曾用名 | 旧链接、commit 历史 |
| OWFA / OWFA Core | 公开名——项目是什么 | README 首行、npm 页、文档 |
| `owfadev` | namespace——名字解析之处 | GitHub 组织与 npm 包（双 bin `owfa` + `owfadev`） |
| `owfa` | CLI bin 名，兼仓库名（`owfadev/owfa`） | 全局安装后的 `PATH`；GitHub 主页 |

只活在幻灯片里的名字是口号；能在包管理器里解析的名字是地址。地址层必须机械地落定，而非修辞地主张——如今已落定：`npx owfadev` 是一切安装示例所用的命令。

## OWFA 不是什么

- 不是 SaaS 或托管产品；每个工作区都在本地，框架无遥测。
- 不是「为所有人」，也不主张触及所有数据；范围是*你的*工作区与*你的* agent。
- 不是 GitHub 上名为 `owfa` 的组织，与「One Web For All」无关联。
- 不是对 kernel、CLI、`core` plugin 层这三个独立概念的替代。

## 质疑与回答

1. **「主张过大——听着像通用产品。」**
   范围被限了两次：*你的*工作区，*你的* agent。文档从不说所有数据或所有人。不能被证伪的口号会失败；这一个有机械测试——装上它，看一个全新 agent 是否无需重新自我介绍就能重入。

2. **「『workspace』含混；这东西是 wiki。」**
   wiki 是媒介；workspace 是被拥有的重入单位。产品的价值在于新会话知道去哪看，而不在于文件以 `.md` 结尾。

3. **「那就改仓库名和所有包名。」**
   不。仓库是 `owfadev/owfa`；包 id、plugin 目录与 kernel 维持原状。`core` 仍是 plugin 层。这是 namespace 层的 `ripgrep`/`rg` 模式。

## 名字在哪里被强制

- `package.json`——`"name": "owfadev"`，`"bin": { "owfa": …, "owfadev": … }`
- `README.md`——首行、*Name* 一节、安装注记（永不宣布 registry 不供的命令）
- `templates/AGENTS.template.md`——新实例起手的身份段
- [releasing.md](releasing.md)——通道的版本不变式与发布 runbook
- `scripts/verify-release.js`——release gate（名字/bin 一致、版本骑 `.owfa/VERSION`、tag 匹配）

---

**结局注记（2026-10-26）：** 项目入驻 **`owfadev`** 组织（组织自 `AIE3905-Wuwa` 改名，仓库自 `vault-wiki` 改名 `owfa`）。npm 依相似性政策冻结 `owfa`，定局答案是包 **`owfadev`**、双 bin `owfa` + `owfadev`——已带 provenance 发布（v0.4.0 与 v0.4.1，均 2026-11-14）。名字问题就此关闭；本页保留的是理据，不是追过程。
