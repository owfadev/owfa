# 内核参考

> 读者：需要精确理解内核机制的任何人或 agent——`.owfa/scripts/owfa_kernel.py` 强制什么、投影什么、拒绝什么，以及每条规则住在源码的哪几行。脚本本身是权威；本文与源码冲突时以源码为准。下列每条机制均附源码行号（对 v0.4.2 内核，共 2335 行）。初稿 2026-11-15，吸收原 `mechanics.md` 的内核半边。

## 1. 内核是什么

内核是**单个 Python 文件** `.owfa/scripts/owfa_kernel.py`，**Python 3.9+、纯标准库**即可运行——模块级导入只有 `ast / importlib / os / re / shutil / sys / types`（`owfa_kernel.py:131-137`）；联网（`urllib`）与进程执行（`subprocess`）在用到它们的函数内惰性导入（`1205`、`1253-1254`）。零第三方依赖、零额外解释器。这是一条部署保证：装得起安装器后置步骤的机器，就跑得起内核。

章程写在模块 docstring 里：确定性结构操作归脚本，语义判断归 LLM；且脚本**只碰四个地方**——插件目录进出、AGENTS.md 注入区标记块、registry 插件节、`.agents/skills/` 命令副本。协议工件、保留节、手写区永不触碰（`owfa_kernel.py:5-9`）。

子命令面已收敛为两组：

- **收敛 7 子命令**——`ls / validate / audit / inject / registry / deploy / all`（`owfa_kernel.py:12-18`；分发 `2277-2330`）
- **包生命周期 8 子命令**——`plan / install / uninstall / list-remote / migrate / upgrade / pkg / residual`（`19-27`；分发 `2205-2270`）

另有一个只读辅助视图补全面：`provides`——离线、纯读盘地报告每个已装包的能力 provides 与每条 needs 的满足状态（`26`、`1677-1704`）。

**协议无关性。** 内核认识的是包、插件清单、依赖图、能力、投影——仅此而已。它不认识任何内容协议：一「页」该装什么、有哪些领地、工作区维护哪些派生工件——都不在内核词表里。最干净的证明是 v0.4.2 的产权分家：`pipeline.py`（vault-wiki 协议一侧的数据区派生层工具，如 index/tags/hot/log 重建）**已离开框架树、归入协议的 suite 包**——自 suite 0.1.1 起它随 owfa-personal 的包根分发（实例路径 `.owfa/plugins/domains/personal/pipeline.py`），框架树里的那份是一次性弃用 shim，0.5.0 退役；内核从不调用它（shim 头注，`.owfa/scripts/pipeline.py:3-6`）。凡内核刻意不解释的，都归协议所有。

## 2. 包模型

自 v0.4 起插件随**包**分发。安装单元就是目录：一个包 = `.owfa/plugins/domains/<pkg>/` 下一个内含 `PKG.yaml` 的目录（`load_packages`，`877-893`；安装落点 `1454`）。目录边界 == 包边界；布局遍历器同时容忍旧的平铺与 `core/` 布局（`_plugin_dirs`，`252-273`）。一个插件至多归一个包——被两个 PKG 同时声明的成员是错误（`936-939`）。

`PKG.yaml` 由专门的极小解析器读取（标量、flow 列表、块式 dict 列表、一层嵌套 mapping——`parse_pkg`，`817-874`）。逐字段的完整参考、suite 与 domain-family 的语义之别、撰写指引都在 [packages.md](packages.md)；本节只钉住内核机械读取的部分：

| 字段 | 内核用途 | 源码 |
|---|---|---|
| `id` | 必须等于目录名（`889-890`） | |
| `kind` | `suite`（rootless：无家族根、免闭包法则）与 `domain-family`（默认）；present/compat/平坦图/id 法则两者同守（`916-979`）；`protocol` 另加 step2 形状法则与（0.4.6 起）R11 两态 ABI 合格线（[abi.md](abi.md)） | |
| `version` | A.B.C；安装时对 INDEX 行核验（`1421-1424`），`upgrade` 比对 | |
| `compat` | `>= X.Y` 下限，对 `.owfa/VERSION` 锚点核验（`framework_version`，`896-908`；检查 `973-979`、安装 `1409-1414`） | |
| `members` | 插件花名册；子集安装必须依赖封闭（`948-969`） | |
| `skeleton` | 安装时机械 mkdir 的实例目录——内核不硬编码任何布局；带路径逃逸守卫（`1559-1564`） | |
| `connectors` | 仓内目录安装时复制进 `connectors/`（`1510-1519`），卸载时移除（`1616-1627`） | |
| `needs` / `provides` | 包级能力（第 3 节） | |
| `uninstall` | `anchors`（残留扫描面，第 7 节）、`retains` / `credentials` / `processes`（卸载时打印的 teardown 披露，`1664-1670`） | |
| `menu` / `disclosure` / `migrations/` | 由 `plan`（`2123-2161`）与第 7 节的迁移 staging 消费 | |

插件层，每份清单携带七个必填键——`id / version / depends / updated / attachment / fields / inject`（`REQUIRED_KEYS`，`155`）——及可选键（`commands`、`usage`、`checks`、`bridge`、`inject_tier`、`usage_routes`、`transports`）。内核要求 `attachment` 与 `fields` **在场**但不解释其条目：一条 attachment 声明在实例数据模型上意味着什么，是协议语义；内核对插件内容的权威是机械的，不是编辑的。

### 2.1 插件本体论——owner 终裁（2026-11-15）

「插件是什么」的词条级定义，owner 于 2026-11-15 终裁。它是机制各节之上的词条：下文一概不修——R1–R10 各线、ABI、包/能力机器均照原文成立。

- **动机。** OWFA 走插件化，是因为信息是无限的、且无限可塑——插件是为方便 agent 而做的。一个插件就是把一「被定义的信息」打包，让 agent 拿得动。
- **四件套公式。** owfa 插件（包）＝**插件文档＋暴露机制**（注入、skill 等）**＋信息获取方式**（connector，或用户自己输入，如 vault）**＋信息处理方式**。插件本质上对应一种被定义的信息。
- **领土不在公式里。** 领土是**某些**信息种类的存放形式需求，绝不是插件身份的条件。树中先例即为证明：`trust` 无目录领土，`bridge` 0.3 零领土运行。插件恰在其信息种类需要该存放形式时才握有领土——那是存放，不是身份。
- **处理受协议约束。** 信息如何被处理受协议约束，约束强度有谱：弱→强——`bridge` 是满格一端，约束在那里硬化为拓扑完备法则（第 4 节）。

## 3. 能力引擎

自 v0.4 起包在 PKG.yaml 里声明能力——`needs: [ … ]` / `provides: [ … ]`——刻意限于包级；插件级声明在设计上不支持（`owfa_kernel.py:982-984`）。（多协议世界里成员级能力意味着什么，是台阶 2 的设计议题，不在本文。）内核强制四条法则：

- **语法**：`^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$`（`CAPABILITY_RE`，`991`；检查 `1016-1025`）。`owfa.*` 命名空间归框架所有；其他能力的首段名必须等于声明包 id（`1023-1024`）——内核查语法，registry 审查门管 `owfa.*` 特批。
- **精确名匹配**：need 只被同名 provides 满足；v2 供给者满足不了 v1 需求，且与能力完全缺失分开报告（`_cap_base` 版本变体测试，`1011-1013`、`1059-1063`）。
- **独占槽**：一个能力至多一个已装包供给；第二个供给者是错误（`1045-1047`）。
- **信任门控满足**：只有受信包——按 registry INDEX 行为 `framework-bundled` 或 `reviewed-3rd-party`（`TRUSTED_PROVIDERS`，`995`）——的 provides 满足 needs。同名供给者若信任未验证，是**软拒绝**：`--yes` 可越权，越权即记 journal（`1052-1057`、`1493-1502`）。语法、独占槽、缺失、版本失败则直接拒绝——不可越权。

收敛点：**install** 在任何文件与投影变更之前，把检查作为预检跑在「前瞻包图」上——已装 provides，减去升级路径上被换版的旧 provides，加 incoming 版的 provides（`1460-1502`；前瞻棋盘的理由，`1776-1783`）。**validate** 对全装成图跑同样法则记为错误，单包 `--scope` 模式降为警告（`validate_capabilities`，`1071-1091`；分发 `2299-2301`）。**uninstall 刻意不是收敛点**：拆走某能力最后一个供给者会留下红色 validate，而卸载本身照常成功——有意的不对称（`1655-1658`）。

内核 journal（`.owfa/kernel-journal.log`）记录每次机械操作——install、uninstall、upgrade、信任越权、sweep、迁移 clear——一次一行，留最后 500 行（`JOURNAL`，`152`；`_journal`，`1863-1871`）。

## 4. 依赖图与注入顺序

`depends` 声明行为性或语义性依赖。validate 查依赖在场（`440-446`），查无环——经 DFS 三色标记检出（`447-464`）。

**注入顺序 = 依赖拓扑（被依赖者先注入）+ 同批按字母序**（`ordered_plugins`，`174-191`）。遇环或悬空依赖，投影器退回字母序输出，保证投影可建，错误由 validate 另行报告（`177-179`）。保证的是一件事：消费侧插件被投影时，它消费的披露已在它上方。

两个内核硬编码的图概念：

- **`domain` 概念插件**。depends 链可达 `domain` 的是域件；直连 `domain` 的是域基（`reaches_domain`，`298-305`）。这是内核的图论概念——「域」在实例数据上意味着什么，归协议语义。
- **桥**（`bridge: 必依 | 按需`）。仅全局件（depends 链不可达 `domain`）可持桥；必依桥要求**每个**域基都有一条指向该件的 depends 边——拓扑完备不变量，不是风格建议（`validate_bridges`，`551-567`）。

**层级法则**（`inject_tier: full | member`，默认 full）：member 层插件退出 AGENTS.md 注入区——曝光搭家族根的花名册行、skill 目录与清单的按需读取。validate 要求每个 member 层插件经 depends 可达某个 full 层域根，否则它退进不可见（`INJECT_TIERS`，`165`；`build_inject_blocks`，`371-381`；层级检查 `419-429`）。

**字节预算**：投影注入区带 16 KiB 预算（`INJECT_BUDGET = 16 * 1024`，`168`）；超预算是 validate 错误，阻断机械动作（`430-434`）。**行准则**：每条 full 层注入行有 256 B 指针密度准则（`INJECT_LINE_GUIDE`，`171`）——超出只警告、不阻断（`435-438`）：一行是路由指针（路径 + 读写触发 + 最易破的一条不变量 + 指向 PLUGIN.md 的指针），细节住在 PLUGIN.md。

## 5. 投影：一个源，五个落点

内核从清单机械投影到五处。全部幂等重建；标记块内手改是徒劳（重建即覆盖），块外文字归人。不存在第二真相源：改规则就是改清单，随后一条 `all` 收敛一切。

| 投影 | 落点 | 源键 | 源码 |
|---|---|---|---|
| AGENTS 注入区 | AGENTS.md 的 `wiki-inject:start/end` 标记区，每个 full 层插件一个 `<!-- plugin:<id> v<x> -->` 块 | `inject` | `do_inject`，`613-633` |
| check 检查块 | check 命令母本内的 `check-inject` 块 | `checks` | `do_check_inject`，`636-666` |
| 命令用法块 | 各命令 SKILL.md 内的 `cmd-inject` 块 | `usage` | `do_cmd_inject`，`669-721` |
| registry 插件节 | `.owfa/protocol/registry.yaml` 的 `plugins:` 节（保留节不动） | `fields` | `do_registry`，`724-748` |
| skill 副本 | 从命令与连接器母本同步到 `.agents/skills/<name>/SKILL.md` | 母本 | `do_deploy`，`751-780` |

命令绑定是第三个投影的地基。`owner` 与 `commands` **互为声明**：命令 SKILL.md 的 frontmatter 写 `owner: <plugin-id>`（或 `framework` 表示显式无主）；插件清单写 `commands: [命令名]`。任一侧单边声明都是 validate 错误——缺 owner、owner 指向未装插件、`framework` 与其他 owner 并列，同错（`validate_bindings`，`476-533`）。

用法经两条路落在命令上：

- **拉侧**：命令 frontmatter 写 `consumes: [插件表]`——写侧契约的拉取声明；owner 驱动的命令必填且须含全部 owner（`492-507`）。
- **源侧路由**：插件清单写 `usage_routes: [命令名表]`——装上插件投影即达，无需编辑目标命令。推送侧贯彻「在场即注册」。validate 检查路由目标在场、路由插件带 `usage`、既被路由又被 consumes 为重复路由错（`534-548`）。

cmd-inject 区内的披露顺序即呈现顺序：owner 块在前（按 consumes 序）；路由块居中（依赖拓扑 + 字母序）；其余 consumes 殿后（`702-707`）。`ls` 呈现完整用法路由表——每个带 usage 的插件列出落点命令；无落点即契约文档面（`791-814`）。

`all` 是收敛命令：validate 先行——失败即阻断——随后 inject、check-inject、cmd-inject、registry、deploy（`converge`，`1278-1304`；分发 `2318-2330`）。install 与 uninstall 收尾时自动跑同一收敛。

## 6. check 机制

附带审计契约（每插件可选的 `scripts/check.py`）里，**机制**归内核；各条规则查什么，是协议的内容。一句话点到分工：内核定义并强制契约的形状；每条规则的语义由协议定义。

- **契约**：脚本必须定义 `check(ctx)`，返回问题表 `[{level: error|warning|info, message}]`；`ctx.root` 是仓库根，`ctx.pages` 是实例页面语料（路径、frontmatter、正文），单次扫描共享；只读零副作用——修复归命令与人（`owfa_kernel.py:124-129`）。
- **静态门**：形状经 AST 校验、不执行文件——语法错误与缺失的 `check(ctx)` 都是 validate 错误（`409-418`）。
- **发现式执行**：`audit` 以发现方式运行每个在场的 check 脚本——契约合规的脚本出现在插件目录即自动列入，卸载时目录搬走即自动除名。在场即注册，与注入区同构，但不做文本拼接（`do_audit`，`570-610`）。单个插件的脚本失败记为该插件的错误，不拖垮其他插件（`596-600`）；错误计数非零即非零退出（`610`）。

内核自己的 validate 是硬结构层（字段、图、绑定、预算）；附带审计是叠在其上的语义层。

## 7. 装卸契约与迁移代数

流程叙事（同意向导、通道、发布）见 [packages.md](packages.md) 与 [deployment.md](deployment.md)；本节钉住机制。

**install**（`do_install`，`1342-1581`）落包：对前瞻图做能力预检（第 3 节——硬失败在任何变更之前拒绝，`1460-1502`）；staging 的母本对已装集做清单图预检——插件 id 重复即拒（`_preflight_install`，`1307-1339`）；母本复制到 `.owfa/plugins/domains/<pkg>/`（`1507-1508`）；仓内连接器复制进 `connectors/`，已有目录保留（`1510-1519`）；包携命令母本落 `.owfa/command/`，已有文件绝不覆盖，被剪成员的命令随行出局（`1520-1534`）；PKG 声明的 `skeleton:` 目录带逃逸守卫机械 mkdir（`1559-1564`）；迁移 staging（见下）；投影经 `all` 收敛（`1575`）。

**uninstall**（`do_uninstall`，`1584-1674`）必须 `--yes`（`1589-1591`），执行机械**四清**：包携命令连同其 skill 副本从 `.owfa/command/` 移除（`1603-1615`）；声明的连接器从 `connectors/` 与 `.agents/skills/` 移除（`1616-1627`）；包目录本身（`1641`）；空容器目录不留残迹（`1671-1673`）。数据区永不触碰。PKG 的 teardown 披露只打印、不执行：`retains`（永不触碰）、`credentials`（留本机，人工移除）、`processes`（如有长驻执行器则停掉）——`1664-1670`。

**anchors 与残留。** 残留扫描面 = 内核下限（AGENTS.md——注入区跳过；手写区永不删除）+ 各包 `uninstall.anchors` 的加法并集；目录 anchor 展开为其内 `.md` 文件（`_anchor_files`，`1109-1135`）。`residual <pkg>` 在这些面上、内核管理区之外，grep 对包及其成员的引用——默认的 teardown 门（`_residual_hits`，`1138-1167`；`do_residual`，`1170-1186`）。声明的 anchors 内核永不删除——安装时明确披露（`1571-1573`）。

**迁移代数。** 语义迁移以 `migrations/` 声明随包走，staging 进内核区（`.owfa/migrations/`，即用即删；`1906-1937`）：

- **0 → x**：首次安装时 `init.md` 在场即 staging（`1912-1913`）。
- **x → y**：升级时 staging 线段落在 `[prev_line, new_line)` 内的每份声明——同线 patch 更新不 staging（`1916-1922`）；`upgrade <pkg> --yes` 即安静的重装（uninstall → 携旧 PKG 作前瞻上下文的 install，`1776-1787`），由它触发 staging。
- **x → 0**：卸载消费包内休眠的 `teardown.md/py` 声明——移除**之前**把 pending teardown 登进台账并立警告横幅（`1628-1640`）。
- 重装 sweep 掉 pending teardown（前提随包归来而消失，`1535-1541`）；卸载 sweep 掉 migrate 类状态（随包而死，`1642-1650`）；内核区里的孤儿包状态在任何一次内核运行时自愈（`2217-2256`）。

pending 迁移**三面可见**：台账（`pending.json`）、注入区顶部的 AGENTS 横幅块（`_banner_set`，`1890-1903`）、常驻 validate 错误——机械祝福被扣发，直到清除（`2307-2308`）。`migrate <pkg>` 打印 staged 声明；`--clear` 有门：作者提供的 `verify(ctx)` 脚本须通过（AST 门：准标准库、只读——禁用导入与写模式 `open` 一律拒绝，`1940-1962`；进程内对已装子集执行，`1965-1988`）；无脚本的 teardown 只在残留扫描干净时可清（`2062-2071`）；既无脚本又无残留门，`--force` 即显式人工断言（`2072-2074`）。清掉的条目即删除——永久不变量属于 `scripts/check.py`，不属于迁移（judgment split，`2088`）。

**空壳形态。** 卸掉所有包之后，实例恰是 kernel-only 实例：`.owfa/scripts/` + AGENTS.md 种子，无插件、无人建 skeleton 之外的目录——与 `init --core none` 产出的形状相同（见 [deployment.md](deployment.md)）。卸载协议不是特殊操作：同一条 `kernel uninstall` 机制，由协议包的 `retains` 覆盖其数据区，人拥有的东西一件不碰。

## 8. registry 解析

registry 是 owfadev/owfa-registry 仓库；目录文件为 `INDEX.yaml`，**一行一包**——每行一道人工审查门。行字段：`repo / version / compat / trust / members / summary`，加 v0.4 字段 `needs` / `provides`（'/' 分隔列表，承 members 先例）与可选的 `commit` SHA pin（`owfa_kernel.py:1201-1204`）。

**解析顺序**（`load_index`，`1196-1244`）：实例根的本地 `INDEX.yaml` 优先；次之 `.owfa/registry-cache.yaml` 缓存（600 s TTL 内新鲜）；否则拉取远端 master 并缓存；过期缓存是离线兜底；只读调用方（`validate`、`provides`）永不联网。行按 `  pkg: {key: value, …}` 极简单行文法解析（`1238-1243`）。

**commit pin。** 带 `commit: <sha>` 的行钉住预期 HEAD：浅克隆之后实际 HEAD SHA 必须等于 pin，否则拒绝克隆——对抗审查与取货之间 tag/路径漂移的供应链内容锚（`_clone_package`，`1247-1275`）。

**三安装通道**（`do_install`，`1342-1399`）：

1. **registry**——包在 INDEX.yaml 中查得；信任级不属于 `framework-bundled / reviewed-3rd-party` 的不可自动安装，须显式 `--yes`（`1384-1399`）。INDEX 行与 PKG.yaml 交叉核验：成员花名册漂移与版本漂移都拒绝（`1415-1424`）。
2. **直装** `owner/repo` 或 URL——未入册，按约定可达，必须 `--yes`，trust: unknown；registry PR 是包挣得受信的途径（`1371-1383`）。
3. **本地** `--path <dir>`——开发与内嵌副本用；完全没有信任上下文（`1366-1370`）。

信任级：`framework-bundled` / `reviewed-3rd-party` / `unknown`——INDEX 行是唯一信任源，供第 3 节的能力信任门取用。`list-remote` 呈现带安装标记的索引表（`1707-1721`）；`upgrade`（报告模式）把已装版本对索引、把框架锚点对模板远端各做一次对账（`1810-1850`）。发布纪律——PKG 版本 bump → tag `<pkg>-vA.B.C` → registry 行 PR——记述在 [packages.md](packages.md)；每一步的机制在此。
