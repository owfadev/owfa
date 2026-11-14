# 机制详解

> 读者：将要修改框架或撰写 package 的成员与贡献者。机械规则的权威来源是kernel（`.owfa/scripts/owfa_kernel.py`）及其读取的清单文件。本文档在总纲之下展开一层——原则、实例走查、上手流程——不复写规则原文；与源码冲突时以源码为准。初稿 2026-10-04；为 v0.4 包时代重写于 2026-11-14。

## 0. 一个源，五投影

v0.4 拆分之后，plugin随**包**分发：发布树本身不带任何plugin（kernel、`.owfa/command/` 下六个框架命令母本、协议工件、以及内嵌的 `payloads/personal/` 套件副本）。在已安装的实例里，plugin母本住在 `.owfa/plugins/domains/<pkg>/<id>/` ——包是分发与安装单元（`PKG.yaml`，`kind: suite | domain-family`），且目录边界 == 层级边界 == 包边界。

无论母本住在哪个目录，`PLUGIN.yaml` 始终是机器可读的本体——清单。kernel脚本从清单机械投影到五处：

| 投影 | 落点 | 源键 | 谁读它 |
|---|---|---|---|
| AGENTS 注入区 | `<!-- plugin:<id> v<x> -->` 标记块 | `inject` | 每个会话的 agent；章程级披露 |
| check 检查块 | owfa-check 命令内的 `check-inject` 块 | `checks` | check 命令；语义项 |
| 命令用法块 | 各命令内的 `cmd-inject` 块 | `usage`，按 consumes 顺序 | 命令执行点；写侧规则 |
| registry plugin节 | `.owfa/protocol/registry.yaml` | `fields` | 写页前查询字段词表的命令 |
| skill 副本 | `.agents/skills/<command>/` | 命令与connector母本 | 部署侧 agent |

关键性质是幂等重建。标记块内部禁止手改——重建即覆盖；块外的文字归人所有。不存在第二真相源：改规则就是改清单，随后一条 `all` 收敛一切。整类文档漂移问题被连根消除——投影与本体不可能不一致，因为它们本就不是两样东西。

走一个真实样本：cuhksz 域基的清单里，`inject:` 是一行式披露，声明校域的领地、connector与红线。`all` 跑完后，这行原样出现在 AGENTS 注入区的 `<!-- plugin:cuhksz v0.3 -->` 块里。agent 日常读的是投影；清单本体只在装卸与升级包时被触碰。

## 1. plugin形状

一plugin一目录三件套——如今位于其所属包内：

- `PLUGIN.yaml` ——清单，本体
- `PLUGIN.md` ——纯文档：设计摘要、Structure、Invariants、Changelog。设计的「为什么」住在这里；机械共性归kernel参考
- `scripts/check.py` ——可选的附带审计。定义 `check(ctx)` 返回 `[{level, message}]`，只读零副作用；形状经 AST 静态校验

七个必填清单键，以 bb-quiz 的真值举例（v0.8，owfa-cuhksz 包成员，位于 `.owfa/plugins/domains/cuhksz/bb-quiz/`）：

| 键 | 语义 | 实例 |
|---|---|---|
| `id` / `version` / `updated` | 身份与版本；沿 changelog 递进不跳号 | `bb-quiz` / `0.8` |
| `depends` | 依赖表 | `[bb-track, bb-map]` |
| `attachment` | 领地声明：拥有即写入，借用即只读消费 | 见下 |
| `fields` | plugin自有页面字段；进入 registry 全局词表 | `quiz`，试卷块映射 |
| `inject` | 注入区行的来源；章程级披露 | 由 cuhksz 家族承载（member 层，见下） |

四个可选键。`commands` 声明plugin驱动的命令；`usage` 是写侧规则表；`checks` 是检查规则；`bridge` 是桥声明，仅全局件可持有。

第五个可选键 `inject_tier`（full|member，默认 full）承载**层级法则**（issue #12 分层纪律）：member 退出 AGENTS 注入区——曝光搭家族根的花名册行、skill 目录与清单的按需读取；validate 要求 member 经 depends 可达某个 full 层域根。cuhksz 包里除域基本身外全员 member 层：bb 家族的披露由 cuhksz 的花名册行承载，而非五个独立 AGENTS 块。投影区带字节预算（16 KiB），保 A 层指针致密：指针与红线，绝无流程或格式（契约在 `protocol/experiments.md`）。每条 full 层注入行另有 256 B 指针密度准则（issue #49）——超了 validate 警告：一行只留路径 + 读写触发 + 最易破的一条不变量 + 指向 PLUGIN.md 的指针。

attachment 值得细看。bb-quiz 声明三条：

- `cuhksz/bb/<term>/<course>/notes/testing/` 是试卷子区，本plugin拥有。每次自测新增一套题与答案；批改追加在答案页
- `wiki/cuhksz/bb/<term>/<course>/user.md` 是认知档案，bb-track 拥有。本plugin只读；批改回流走 bb-track 的写规则
- `wiki/cuhksz/bb/<term>/<course>/courseware/` 与 `assessments/` 归 bb-map。本plugin只读，取 sm-N 锚点、术语表与已知作业

第一条是拥有；后两条是借用：领地属于别的plugin，写路径必须过它的规则。attachment 是框架的物权登记——谁拥有哪些路径、谁只读消费谁，一目了然，机械可查。

## 2. 依赖与注入顺序

`depends` 声明依赖。validate 查两件事：依赖存在、无环——环经 DFS 检出。

域件是 depends 链可达 `domain` 的plugin。与 domain 直连的是域基——现有七个：vault（内嵌 personal 套件的成员）、lark、project、email、cuhksz、bili、github；域内件经传递归属，不必直连。bb-quiz 不直连 domain：它经 `bb-quiz → bb-track → bb-map → bb → cuhksz → domain` 到达，因而是域件。cuhksz 包内，bb（sis、registry 同理）同时直连 cuhksz 与 domain——域内治理成员，各自在域基之下统治一块子领地。

注入顺序 = 依赖拓扑 + 同批按字母序：被依赖者先注入；同批按名排序。看 cuhksz 家族的 depends 与实际顺序：

| plugin | depends | 效果 |
|---|---|---|
| cuhksz | `[domain, wiki, trust, log]` | 域基，最先注入；家族中唯一的 full 层块 |
| bb | `[cuhksz, domain, wiki, trust, log]` | 课程运营子基，在 cuhksz 后 |
| bb-map | `[bb, wiki]` | 映射法则，在 bb 后 |
| bb-track | `[bb, bb-map, trust, wiki]` | 认知档案，在 bb-map 后 |
| bb-quiz / bb-teach | `[bb-track, bb-map]` | 采集通道；同批按字母序——quiz 先于 teach |

这保证一件事：消费侧plugin被投影时，它消费的披露已在场。bb-teach 的用法写着「纪律见 bb-track 块」——该块必在其上。另有一条域纪律：domain 必须在 wiki 内可发现——经声明页或注入行；域件不建根容器。

## 3. 投影走查

假设你想给 bb-quiz 的写侧规则加一条纪律——流程如下：

1. 编辑 `.owfa/plugins/domains/cuhksz/bb-quiz/PLUGIN.yaml` 的 `usage:` 列表加一行。顺手 bump `version`、刷新 `updated`；在 PLUGIN.md 的 Changelog 加一行。（这一切的上游是包：改动在 owfa-cuhksz 仓库里撰写，经 PKG 版本 bump + tag 发布，经 `kernel upgrade` 到达实例——见 [packages.md](packages.md)）
2. 跑 `python .owfa/scripts/owfa_kernel.py all`。顺序：validate 先行——失败即阻断，修好重跑；bb-quiz 与 bb-track 两个命令母本的 cmd-inject 块被重建——用法出现在每个 consumes 含 bb-quiz 的命令里；registry plugin节重建；skill 副本同步
3. 自查 diff。改动应只落在清单、受影响的命令母本与 `.agents/skills/` 副本；若 inject 或 fields 变了，AGENTS 与 registry 随之而变。超出此范围的改动都是异常
4. 以 `plugin: bb-quiz …` 格式提交；一次提交一件事

这就是「一个源，五投影」的日常体感：你写了一处，五处自动一致。

## 4. 命令绑定

owner 与 commands 互为声明。命令 SKILL.md 的 frontmatter 写 `owner: <plugin-id>`，或 `framework` 表示显式无主；plugin清单写 `commands: [命令名]`。任一侧单边声明都是 validate 错误——既防无主命令，也防plugin冒领命令。

用法经两条路落在命令上。**拉侧**：命令 frontmatter 写 `consumes: [plugin表]`，声明拉取哪些plugin的用法；owner 驱动的命令必填且须含全部 owner。**源侧路由**：plugin清单写 `usage_routes: [命令名表]`，声明其用法额外落在哪些命令上——装上plugin投影即达，无需编辑目标命令。推送侧同样贯彻「在场即注册」：装卸单文件即生效。validate 检查路由目标在场、路由plugin带 usage、与 consumes 重复为错。

披露顺序即呈现顺序：owner 块在前（按 consumes 序）；路由块居中（按依赖拓扑 + 字母序）；其余 consumes 殿后。

首例走查：bb-track 命令，这个认知枢纽。bb-track 命令只声明 `consumes: [bb-track, trust, log]`；bb-teach 与 bb-quiz 各在清单里写 `usage_routes: [bb-track]`。`all` 之后，bb-track 命令的 SKILL.md 含五个 `<!-- usage:<id> -->` 子块：bb-track 自己的写规则、两条采集通道 bb-quiz 与 bb-teach 的完整用法、trust 与 log 的写侧规则。效果：任何 agent 踏入 bb-track 命令点，一处即得、零检索——教学与自测怎么用、批改怎么回流、写后做什么。日后要立第三条采集通道，新plugin只需写好 usage 加一条路由声明；投影自动到达，枢纽命令一字不改。

用法路由随时可经 `ls` 查验：每个带 usage 的plugin列出它落点的命令；无落点者标记为契约文档面——如 email 的写侧契约，先用后致。

## 5. 桥法则

全局件是横切服务与归宿：trust、log、todo、calendar、notes、user-profile。它们可声明桥；域件持桥为错。

必依桥在清单里写作 `bridge: 必依`：每个域基必须有一条指向该件的 depends 边；缺边是 validate 错误。log 是一例——第 2 节表中 cuhksz depends 里的 `log` 边即必依桥所迫：任何 domain 的活动必须留痕。这是拓扑完备不变量，不是风格建议。

按需桥写作 `bridge: 按需`：缺席可容忍。user-profile 的认知桥是一例——bb-track 建档案时若 profile 在场则登记一行；不在场则跳过，不代建、不报错。

consumes 为何替代不了桥——2026-10-04 裁决给出两条硬理由：

1. 必依完备性检查是拓扑约束。「所有域基，一个不能缺边」是全图不变量；consumes 是单个命令的列表，表达不了全局完备
2. 跨领地的写入发生在每次命令执行里。todo 派生、calendar 派生、notes 涌现——都不经过某个单点命令容器；consumes 无处可挂

分工：桥管校验与声明——谁可挂、基数、完备检查、缺席容忍；披露分发归投影——集成格式的权威源是 usage，经 cmd-inject 到达消费点。

## 6. 能力机制

自 v0.4 起，包在 PKG.yaml 里声明能力——`needs: [ … ]` / `provides: [ … ]`，刻意限于包级（能力绝不在plugin级声明）。kernel强制：

- **语法**：`^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$` ——如 `owfa.org.v1`。`owfa.*` 命名空间归框架所有（特批除外）；其他能力的首段名必须等于声明包的 id
- **精确名匹配**：need 只被同名 provides 满足——v2 供给者满足不了 v1 需求，与能力完全缺失分开报告
- **独占槽**：一个能力至多一个已安装包供给；第二个供给者是 validate 错误
- **信任门控满足**：只有受信包（framework-bundled、reviewed-3rd-party——registry INDEX 行是信任源）的 provides 满足 needs；同名供给者若信任未验证是软拒绝，`--yes` 可越权，越权即记 journal。语法、独占槽、缺失、版本失败则直接拒绝——不可越权

安装时该检查作为预检跑在「前瞻包图」（prospective graph）上，先于任何文件与投影变更；validate 时同样的法则跑全图（单包 `--scope` 模式降为警告）。能力模型的设计缘由见 [packages.md](packages.md)；本节只钉住机制。

## 7. 派生层

kernel管机制与投影——plugin图、清单合规、及由其派生的一切（v0.4 拆分后plugin*内容*随包走；kernel对它的权威是机械的，而非编辑的）；pipeline 管数据区——wiki 派生页。命令是 `python .owfa/scripts/pipeline.py index / tags / hot / log / verify`：

- **index / tags**：目录索引与标签倒排索引。纯函数重建，只聚合、不发明结构；索引列表溢出窗口时把子目录拆出自己的索引——药方是更多子目录，不是编辑索引
- **hot**：近期变更热缓存。至多 25 条、5 天内、每条 200 字符以内；agent 进库先读它
- **log**：运行日志行写入与滚动归档。窗口至多 100 条；溢出机械归档到 `wiki/archive/<month>/log.md`
- **verify**：写后一致性检查。map、save 等命令的写后流水以它收尾

派生页与投影是同一哲学的两个应用：投影派生自清单——框架侧无第二源；派生页派生自 vault 内容——数据侧无第二源。手改派生页是徒劳的；下次重建即覆盖。

## 8. 装卸生命周期

自拆分（2026-10-12）起，**包是安装单元，生命周期由kernel驱动**——权威记述在 [packages.md](packages.md)（包模型、迁移代数、卸载契约）与 owfa-plugin 命令 skill（向导协议）。此处只给机制层的视图。

`kernel install <pkg>` 五步落包：能力预检（第 6 节——硬失败在任何变更之前拒绝）；plugin母本复制到 `.owfa/plugins/domains/<pkg>/`；connector随行落进实例的 `connectors/`；包携命令母本落 `.owfa/command/`（已有文件保留、绝不覆盖）；PKG 声明的 `skeleton:` 目录被机械 mkdir——kernel不硬编码任何实例布局。随后投影经 `all` 收敛。安装通道：registry、直装 `owner/repo`（需 `--yes`，trust: unknown）、本地 `--path`。

卸载是包级 `kernel uninstall <pkg> --yes`（四清 + 残留扫描 + teardown staging——见 packages.md）。升级在重装之上叠加语义迁移 staging。

如今撰写新plugin意味着在包仓库里撰写：在包树下备好三件套，`validate`、`all`、冒烟（`audit <id>` 加按 PLUGIN.md 走查关键流程）、记一行日志——然后经包的版本 bump 与 registry 行发布。纪律始终如一：脚本错误必阻断、警告只报告；版本沿 changelog 递进——不预占号、不跳号。

## 9. domain 如何生长

框架不为 wiki 之外的信息源设白名单。集成就是回答同一份契约，生长走同一条路径。走一遍 cuhksz 包——其 bb 家族是树内最完整的样例。

### 契约六问

设计一个 domain 就是逐题作答。答案落在域基的领地声明与注入行里：

| 问题 | cuhksz 域的回答 |
|---|---|
| 外部领地在哪 | cuhk.edu.cn 校务系统族——bb 课程运营、sis 学籍、registry 学业规章；connector cuhksz-cli（聚合 bb 与 sis；旧 bb-cli / sis-cli 包装保留兼容），纯只读 |
| 落地策略 | 同构两侧：`cuhksz/` 数据区 + `wiki/cuhksz/` 领地 |
| 身份证明 | 域身份页 `wiki/cuhksz/identity.md`；学期名与课程码目录加 bb 块映射里的机器 id |
| wiki 侧领地 | `wiki/cuhksz/bb/<term>/<course>/`，bb-map 的四桶投影 |
| 写模型 | 拉取工件 append-only；notes/ 人主导，ai 产物追加不覆盖 |
| 信任模型 | machine-confirmed 上限；stale_after = 拉取日期 + TTL |

### 三种写模型

落地本质是写模型选择，三个原型：

- **终态资产 → append-only 库**。落地后本体不再变——如 vault 资产、bb 物化课件、sis 成绩单 PDF。命令侧 append-only；删改归人
- **过程容器 → 全读写**。agent 在其中工作——如 `projects/`、bb notes/ 里的 ai 产物
- **真相在别处 → 指针**。源会变、无需本地副本——如 lark 指针页、bb 媒体默认指针。stale_after 管新鲜度；agent 是同步器

### 投影密度

翻译成本越高，投影密度越低，三档。**镜像**：1:1 代理，如 mapping。**指针**：token + url + 快照摘录，如 lark。**仅披露**：一行注入 + 按需实拉，如 email 检索。默认姿态是借用 vault 或指针；自立容器是例外——当写模型分叉，或结构被源刚性规定。cuhksz 数据区因其刚性两侧结构而自立。

### 生长路径

契约之后：**域基**立领地——cuhksz 同构两侧加 notes/ 共居，声明为一个包；**域内治理成员**跟进——bb、sis、registry，各持一条直连基与 domain 的边统治子领地；再是**域内件家族**——bb-map 的投影法则、bb-track 的认知档案，形状渐重；**消费侧采集通道**收尾——bb-teach 与 bb-quiz，零领地、纯工作流，用法经源侧路由挂上枢纽命令。家族内依赖链 `bb-quiz → bb-track → bb-map → bb → cuhksz` 即这条路径的机械表达——见第 2 节。

### 素材与档案

域内二分。过程产物住域工作区：拉取工件、人笔记、ai 笔记、试卷与批改。沉淀结论住 wiki 领地：投影页、认知读数。wiki 收蒸馏物，不收过程。这条线与全局纪律同构，只是落在域内。

### connector

connector随包分发——各 PKG.yaml 声明自己的connector（仓内 `path`、仓外 `external`、预装二进制 `system`），`kernel install` 把仓内connector目录复制进实例的 `connectors/`。各connector的 `SKILL.md` 再经kernel `deploy` 落为 `.agents/skills/` 副本。与命令的区别：命令是纯 wiki 操作，母本在 `.owfa/command/`；connector是通外部系统的取数通道——凭据留在本机、永不入库、永不落盘。domain plugin声明领地与纪律；connector提供事实接口。纪律与工具分离。

## 10. 场景速查

| 你想 | 动作 |
|---|---|
| 改写侧规则 / 检查规则 / 注入行 | 编辑 `.owfa/plugins/domains/<pkg>/<id>/PLUGIN.yaml` 里对应清单键，跑 `all` |
| 把新plugin的用法挂上某命令 | plugin清单写 `usage`；命令 frontmatter 的 consumes 加 id；跑 `all` |
| 编辑connector skill | 编辑 `connectors/<name>/SKILL.md` 母本，跑 `deploy` 或 `all` |
| 快速健康检查 | `validate` 加 `audit`；全面审计走 check 命令 |
| 装卸或升级包 | owfa-plugin 命令管语义，`kernel install / uninstall / upgrade` 管机制——见 [packages.md](packages.md) |
| 重建数据区派生页 | `pipeline.py index` 或 `tags`；hot 与 log 随写维护 |
| 接入新外部源 | 回答契约六问，见第 9 节；撰写connector与 domain-family 包；owfa-plugin 向导走装 |
