# 默认协议

> 读者：使用这套套件的一切人——vault 主人、在 OWFA 实例里工作的 agent，以及想理解这套信息组织法到能写出第二协议的人。本文是默认协议在今天的完整章程；只写已实现的事实，本页不包含对任何未来语法的承诺。

## 谱系

**llmwiki → vault-wiki → OWFA 默认协议。**「给 agent 经营的信息库配一套 wiki over 纯文件 vault」的想法源于 llmwiki，在 vault-wiki 框架中成形（2026-08 个人 vault 建立；09-08 插件原型落地），自 OWFA v0.4 起以独立包发布——即本套件 **personal**，该组织原则的第一个、目前也是唯一的一个实现。

先说清一个用语：自框架 0.4.3 起，内核已支持 `kind: protocol`（随 `protocol:` 字段与 org 能力声明），本包即为首个协议包——`protocol: vaultwiki`、`provides: vaultwiki.org.v1`。协议 ABI 与按协议分变体仍是未裁决的想法，不是在位的机器。本文描述的是 21 个成员加 `pipeline.py` 实际实现的东西。

## 协议是什么

协议同时是三件事：

1. **信息成形规则**——每类信息落在哪、以什么形状、归什么写模型。vault/wiki 二分、territory 语法、页面类型、链接语法、红线。
2. **自足基线**——零额外装包，workspace 即完整：map、save、query、check 全线可用。各 domain（cuhksz、lark、email、bili……）是租用这套基线结构的加装件，不是它的前提。
3. **服务面**——全体成员共用的横切服务：派生层（index、tags、hot、log）、检索惯例、提炼区（notes、sessions）、check 规则集。

### 协议 vs 域 vs 内核——三测试

域内规约可以长得非常像协议（课程域的四桶布局就是一部微型组织法）。三个测试把它们分开：

| 测试 | 协议 | 域内规约 |
|---|---|---|
| **约束谁？** | workspace 里的一切落法，含各域的内侧领土语法 | 只约束自己领土内的成员与数据 |
| **可否拆除？** | 拆了它，workspace 就不再是这个 workspace | 卸载该域，workspace 毫发无伤 |
| **提供横切服务吗？** | 派生层、检索、check 规则、提炼区——全 workspace 共用 | 不提供；域内派生借协议服务落地（结论经桥进 notes，用协议的 index 检索） |

内核则拥有**机制**（manifest 语法、投影、[包/能力引擎](https://github.com/owfadev/owfa/blob/master/.owfa/docs/packages.md) / [内核机制](https://github.com/owfadev/owfa/blob/master/.owfa/docs/kernel.md)、check 机器），且协议无关：它执行已装包声明的任何规则。一句话——**内核是机器，协议是法，域是带章程、受法约束的成员；插件是一「被定义的信息」，不是土地的租户**（插件本体论——owner 2026-11-15 终裁——见[内核机制](https://github.com/owfadev/owfa/blob/master/.owfa/docs/zh/kernel.md) §2.1）。

## 槽位的形状

**槽位**——存储、检索、提炼、检查——是阅读本套件的理解框架，不是已声明的语法。每个协议在相同槽位上填自己的形状；本协议的填法如下。

### 存储

- **vault/wiki 二分**。`vault/` 收任意格式的真实资产——一切的落地库，对 agent 只增不删（删除与修改归人）。`wiki/` 收 md 世界：territory 页、原生写作、派生投影。一切是 Markdown 加纯文件；没有工具私有格式；查看器（Obsidian、Web UI）皆可替换。
- **territory 语法**。`wiki/` 下每条路径都属于某个插件的领土：`wiki/notes/`（原生笔记）、`wiki/sessions/`（会话主干）、`wiki/vault/`（`vault/` 的代理镜像）、`wiki/tmp/`（临时区，派生层不可见）、`wiki/cron/`（延迟触发），各域领土（`wiki/<domain>/…`），以及单页领土（`hot.md`、`log.md`、`index.md`、`tags.md`、`todo.md`、`profile.md`、`language.md`、`structure.md`、`calendar.md`）。

### 检索

- `wiki/index.md`（溢出时加子树 index.md）——全部可达页面按全路径列出，派生、永不手编。
- `wiki/tags.md`——tag 反向索引。
- 其余靠对 `wiki/` 的全文 grep。
- **热缓存** `wiki/hot.md`——agent 进入仓库先读的最近变更摘要：≤25 条、<5 日、每条 ≤200 字。

### 提炼

- `wiki/notes/`——生于 wiki 的知识；命令只增不改。`wiki/sessions/`——会话主干页；高价值主题提升进 notes 并带回链。
- **桥与回链**：域内派生必须回链来源；跨领土的结论走声明过的桥（必经或按需）；wiki 收蒸馏物，不收过程。

### 检查

每个成员在 `checks:` 里带自己的规则集（见下方名册）；附带 audit 脚本（`scripts/check.py`）在 audit 发现时机械执行，语义项走 check 命令。全体规则集合成协议的健康面：hot/log 的窗口界、派生页漂移、链接完整性、trust 字段合法性、领土落位、`vault/` 与 `wiki/vault/` 的镜像差——每个成员的 PLUGIN.yaml 逐字列着自己的条目。

## 词汇表

| 词条 | 含义 |
|---|---|
| **wiki** | md 世界（`wiki/`）：territory 页、原生写作、派生投影 |
| **vault** | 真实资产库（`vault/`），任意格式，对 agent 只增不删 |
| **domain** | 有适配器契约的有界真相区域；wiki 只认内与外 |
| **territory** | 某些信息种类需要的存放形式：某插件握写权的路径片（借用即只读消费）。领土服务于信息种类，绝不是插件身份——trust 无目录领土，bridge 0.3 零领土 |
| **派生层** | 机械再生的页面（index / tags / hot / log）——手编无效，下次重建即覆盖 |
| **页面类型** | 开放的 `type` frontmatter 词汇；结构由各插件自行声明，协议不做穷举 |
| **红线** | 硬纪律：对 `vault/` 与 log/历史只增不删；派生页绝不手编再生；命令对 notes/sessions 只增不改；实例数据永不入 git |

## 派生机器：pipeline.py

[pipeline.py](../../pipeline.py) 位于包根（0.1.1 起）——派生层机器随套件走，内核从不调用它。实例路径：`.owfa/plugins/domains/personal/pipeline.py`（框架树保留一版弃用宿主副本至 0.5.0）。确定性的结构操作归此脚本，语义判断归 LLM；各命令以调用它收尾，不手写派生页。

| 命令 | 效果 |
|---|---|
| `index` | 重建 `wiki/**/index.md`（纯函数、幂等；减负合并回父级后的多余索引一并删除） |
| `tags` | 重建 `wiki/tags.md`（幂等） |
| `hot <type> <一句话>` | 先逐出窗外条目，再置顶追加一条热缓存 |
| `log <type> <一句话> [--domain <域>]` | 容量归档后置顶追加一行日志（域标可缺省） |
| `verify` | 写后自证：内核 audit + 派生区漂移检查 |

窗口参数（脚本源码即权威规则表）：hot ≤ **25** 条 / **5** 日 / **200** 字；log 主文件 ≤ **100** 条（溢出按月归档进 `wiki/archive/<month>/log.md`）；单份索引清单 ≤ **25** 条，溢出以子目录自立索引化解。概念页 = `wiki/` 下全部 `.md`，排除保留名、根级派生页、`archive/` 与 `tmp/`。

## 成员名册

21 个成员（版本逐字取自各自 PLUGIN.yaml；包 `personal` v0.1.2、`kind: protocol` / `protocol: vaultwiki`、`compat: ">= 0.4"`）：

| id | 一句话 | 版本 |
|---|---|---|
| calendar | 时间领土：`wiki/calendar.md` 源键 + 月页（`## Schedule` 整体刷新，`## Manual Notes` 只增） | 0.5 |
| cron | 延迟触发 `wiki/cron/`，一任务一页（`cron` 块 + 只增的运行注记） | 0.5 |
| device | 设备页在 `wiki/notes/`；`device` 块 + 工具环境登记；保修到期审计 | 0.5 |
| domain | 声明 wiki 内/外：各域的适配器契约，成员继承 | 0.3 |
| hot | 最近变更摘要 `wiki/hot.md`（≤25 条、<5 日、≤200 字）；进入仓库先读 | 0.11 |
| index | 派生 `wiki/index.md`（溢出加子树索引）；`pipeline.py index` 重建 | 0.15 |
| instance-git | 实例 git = 真实使用的快照账本：事务收尾 agent 提交；凭据永不入库 | 0.2 |
| language | 写作声明 `wiki/language.md`：语言规则与统一术语，写工件前先读 | 0.6 |
| link | 链接语法 `[[全名]]` = `wiki/` 内路径去掉 `.md`；永不截断；断链/孤页分级 | 0.15 |
| log | 运行日志 `wiki/log.md`：置顶追加、永不改写；走 `pipeline.py log`；超 100 条自动归档 | 0.17 |
| mapping | 代理层 `wiki/vault/`：`vault/` 的 1:1 镜像，页带 `raw_file` / `raw_sha256` | 0.8 |
| notes | 原生笔记 `wiki/notes/`：生于 wiki 的知识，开放 `type` 词汇；命令只增不改 | 0.16 |
| sessions | 会话主干 `wiki/sessions/`（`type: session`、`participants` 必填）；提升进 notes 带回链 | 0.11 |
| structure | vault 布局声明 `wiki/structure.md`；放资产前先读，人重整后同步 | 0.5 |
| tag | 页面 `tags`：YAML 列表、每页 ≤5 个、层级 ≤2；语义开放，不复述 `type` | 0.13 |
| tmp | 临时区 `wiki/tmp/`：草稿与中间物，无保留承诺，派生层不可见 | 0.4 |
| todo | 工作集 `wiki/todo.md`：会话开始先读；条目 = 触发条件 + 一句话 + by/at | 0.6 |
| trust | trust 字段（`generated`/`verified`/`stale_after`/`sources`）；级别是派生的，从不存储 | 0.10 |
| user-profile | 对用户的持续认知 `wiki/profile.md`；只经 profile 命令写；断言带证据 | 0.8 |
| vault | 默认域 `vault/`：真实资产，对 agent 只增；其他域的落地库 | 0.7 |
| wiki | wiki 容器 `wiki/`：territory 页形状、frontmatter 约束、派生投影 | 0.8 |

包还自带三条命令（`command/owfa-map`、`owfa-save`、`owfa-profile`），并声明骨架目录（`vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/`）。

## 换协议的路径

协议是一个包，所以离开它就是一次包卸载——而卸载契约保住你的数据：

- **数据存活**。`uninstall.retains: [vault/, wiki/]`——真实资产与整个 md 世界原地不动。
- **锚点受尊重**。声明的锚点（`wiki/profile.md`、`language.md`、`structure.md`、`calendar.md`、`todo.md`、`wiki/cron/`）是内核拒绝清扫的实例内容。
- 照常装新协议包（`kernel install <pkg>`），把新组织法能消化的部分迁移过去。
- **重装本套件即复活 workspace**：派生层（`index`、`tags`）从存留页面机械重建——`wiki/` 里的任何东西都不依赖套件在场才可读。
