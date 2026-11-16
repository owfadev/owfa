# 包（Packages）

读者：包作者、实例维护者，以及一切想弄清 `install` / `uninstall` 到底做了什么的人。

package 是分发与安装的单元。本页是合并后的参考：包布局、`PKG.yaml` 全字段、suite 与 domain-family 的语义差异、能力（capability）机制、三安装通道与信任级、装卸与残留契约、版本与 tag、registry 行格式。kernel（`.owfa/scripts/owfa_kernel.py`）与各 `PKG.yaml` 声明是权威；本页解释机制与理由。本页吸收了原 `plugin-lifecycle.md`（develop → publish → be found → install → update → uninstall 全程）与命名治理规则。

## 包布局：目录 == package

v0.4 框架发布树**不带任何plugin**——只有kernel、6 个框架命令母本（`.owfa/command/`）、协议工件（`.owfa/protocol/`）、以及内嵌的 blessed 套件副本 `payloads/personal/`。connector 随各包分发（cuhksz-cli 在 owfa-cuhksz、mail-cli 在 owfa-email、bili-cli 在 owfa-bili）；其 SKILL.md 经 kernel deploy 落入 `.agents/skills/`。

实例中，已安装的包位于 `.owfa/plugins/domains/` 之下——一个目录一个包，目录边界 == 安装单元：

```
.owfa/plugins/domains/
 ├── personal/    # blessed 套件（kind: suite）—— 默认 init 即安装
 ├── cuhksz/      # PKG.yaml + plugin母本 + connectors/cuhksz-cli
 ├── email/  bili/  project/  ...
```

## 命令分层 —— 哪些命令从哪来

| 层 | 命令 | 出现在 |
|---|---|---|
| 框架自带（`.owfa/command/`） | asset-read、owfa-check、owfa-docs、owfa-kernel、owfa-plugin、owfa-query | **任何工作区、任何协议都在**——这就是「project 工作区里为何有 asset-read」的答案 |
| 协议套件 | personal：owfa-map、owfa-save、owfa-profile · project：套件本身不带命令 | 运行该协议的工作区 |
| 包命令 | 随包到达——如 owfa-develop ← 可选 `owfadevelop` 包；connector 技能同样随包走 | 装了该包的工作区 |

投影保持按 id 索引、扁平（`.owfa/command/`、`.agents/skills/`、registry、AGENTS 注入区）：package 重组的是母本而非投影，因此 deploy/inject/registry 无需重设计。

| 包（仓库） | kind | 成员 | connector |
|---|---|---|---|
| framework（发布树） | — | 无 —— 仅kernel + 框架命令 | — |
| personal（**owfadev/owfa-personal**） | suite | 21 个plugin（原 core，含 vault/mapping/structure 启动例外）+ 3 个自有命令（owfa-map / owfa-save / owfa-profile） | — |
| owfa-cuhksz | domain-family | cuhksz · bb · bb-map · bb-track · bb-teach · bb-quiz · sis · registry | cuhksz-cli（聚合 bb\|sis） |
| owfa-lark / owfa-email / owfa-bili / owfa-project / owfa-github / owfa-diary / owfa-qq | domain-family | 见各自 PKG.yaml | lark-cli / mail-cli / bili-cli / — / gh / — / qq-cli |

vault 例外的意义：天真的"所有 domain 都是包"式拆分会把默认 domain 赶出框架——但任何实例在任何其他包存在之前都要靠 vault/mapping/structure 启动。v0.4 拆分后这些启动plugin作为内嵌 personal 套件的成员随行（例外被声明，而非作为框架文件分发）。框架侧副本由 `scripts/sync-blessed.sh` 保持同步：按 tag 模式 `personal-v[0-9]*` 从 owfa-personal 拉取并刷入 `payloads/personal/`。

## PKG.yaml —— 全字段

blessed 套件原文（`payloads/personal/PKG.yaml`）：

```yaml
schema_version: 1
id: personal
kind: suite
version: 0.1.0
compat: ">= 0.4"
members: [calendar, cron, device, domain, hot, index, instance-git, language, link, log, mapping, notes, sessions, structure, tag, tmp, todo, trust, user-profile, vault, wiki]
depends: [framework]
skeleton: [vault/, wiki/notes/, wiki/sessions/, wiki/vault/]
uninstall:
  anchors: [wiki/profile.md, wiki/language.md, wiki/calendar.md, wiki/todo.md, wiki/cron/]
  retains: [vault/, wiki/]
  credentials: []
  bridges: []
  processes: []
disclosure: "Purely local information organization (calendar / todo / notes / sessions / vault proxies / tags / index / logs / cron intents); no network services, no credentials, no external data sources — all content stays on this machine's repository."
```

逐字段说明（示例均取 personal 行）：

| 字段 | 含义 | personal 值 |
|---|---|---|
| `schema_version` | manifest 格式版本（1）——只版本化一次，与后续 behavior contracts 共用 | `1` |
| `id` | 包 id；必须等于目录名与 registry 键 | `personal` |
| `kind` | `suite` \| `domain-family`（缺省即 domain-family） | `suite` |
| `version` | 包自身 `A.B.C` 发布语义——随 `<pkg>-vA.B.C` git tag 走，与框架永不锁步，也不绑成员版本 | `0.1.0` |
| `compat` | 框架版本下限，对照 `.owfa/VERSION` 机检 | `">= 0.4"` |
| `members` | 声明的plugin名册；domain-family 下必须等于最大家族闭包（见下） | 21 个 id |
| `depends` | v1 扁平依赖图——`[framework]`，包与包之间没有边 | `[framework]` |
| `skeleton` | 包需要的实例目录；install 机械 mkdir（kernel不再硬编码任何布局——默认 init 的四个目录就来自这一行） | `vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/` |
| `uninstall.anchors` | 除kernel基线（AGENTS.md 手写区）外追加的 teardown 锚面，供残留扫描用；只做加法，目录锚会展开为其中 .md 文件 | `wiki/profile.md` … `wiki/cron/` |
| `uninstall.retains` | kernel永不触碰的数据区——卸载时报告、永不删除 | `vault/`, `wiki/` |
| `uninstall.credentials` | 凭据位置——提示、绝不自动删除 | `[]` |
| `uninstall.bridges` | 卸载时需检查的语义注册点 | `[]` |
| `uninstall.processes` | 需停止的长驻执行器 | `[]` |
| `needs` / `provides` | 包级能力声明（刻意不支持plugin级）——见下节 | ——（其 registry 行声明 `provides: owfa.org.v1`） |
| `disclosure` | `plan` 在征求同意前展示的一行隐私/行为披露 | 上引原文 |

随包分发 connector 的包另加 `connectors:` 列表（三态）：in-repo（`name` + `path: connectors/<id>`——代码随包走）、external（`external: true`——仅声明）、system（`system: true` + `expect: ">= 2.0"`——预装二进制，只有能力与版本期望，不带代码）。例：owfa-cuhksz 的 `cuhksz-cli` 为 in-repo；owfa-lark 的 `lark-cli` 为 external；`gh` 为 system。

`uninstall:` 块是**声明，绝非可执行钩子**——安全模型拒绝在特权时刻运行第三个执行面（前两个是 inject 文本与 connector）；删除知识因此成为可评审的数据。

PKG.yaml 是**最小 YAML 子集**——顶层标量、`key: []`、block list、一层 block mapping；更复杂的结构会被静默丢弃，声明务必保持扁平。

## kind: suite —— rootless 语义

`kind: suite` 声明一个**无根**（rootless）包：N 个并列成员，没有、也不需要家族根plugin（owfa-personal 的形状）。后果：

- **无合成根**——kernel不为包发明根plugin；
- **无合成依赖边**——成员不会被连向幻影根；`depends` 仍是 v1 扁平图；
- **家族根/闭包法则不适用**：家族闭包法（members == 到达包根的 depends 链闭包）是 **domain-family** 专属不变量。suite 的 `members` 名册只做在场检查（subset 纪律），不做闭包 diff。

缺省 `kind` = 经典 domain-family 行为（默认）：kernel计算家族闭包并与 `members` 双向 diff——漂移即 validate 错误。既然闭包可算，为何还要声明？因为 depends 图是活的、而 package 是版本化锚点：闭包推导的包会随图演化悄悄改变内容，声明名册把内容钉死在版本上。

实例侧 v1 要求全员在场——每个成员都在盘上；subset 语法（`installed ⊆ members`、非空、依赖闭包、domain-family 根强制）定死，`--without` 因此永不破坏校验器：`kernel install <pkg> --without a,b`（及 `owfa add <pkg> --without a,b`）今天就能装入经校验的子集——已装成员在 validate 里带 `suite subset install` 注记。它的承诺是语义的——零注入、零 skill 面、零凭据——而非物理的。

## kind: protocol —— step2 形状裁定（R1–R11）

`kind: protocol` + `protocol: <id>` 成对声明即构成**协议包**（protocol package）——一个工作区协议的持有者。形状裁定自 step2（0.4.5/0.4.6）起生效（正文以 step2-spec v2 为准），因 kernel.md 与 abi.md 按编号引用，此处一次性列举：

| # | 裁定（除注明外均由 validate 强制） |
|---|---|
| R1 | `kind: protocol` ⇔ `protocol:` 字段在场——这对要么一起声明，要么都不声明 |
| R2 | 协议包恰供给一个 `<protocol>.org.v<N>` org 能力（普通能力允许，前缀按 R4 = 协议 id 或包 id） |
| R3 | 协议包无根（完整继承 kind:suite 纪律：无根、跳过闭包法则、全员在场） |
| R4 | 能力前缀只有两个合法来源：包 id 或该包的 `protocol:` id；协议 id 不得为 `owfa`（保留） |
| R5 | uninstall：retains 必须覆盖每个数据 skeleton 目录（未覆盖 validate 警告）；「工作区无协议——空壳」提示落在 uninstall 输出 + doctor，不在 validate |
| R6 | 全有或全无：`--without` 或成员级 needs 剪枝触及协议成员即拒绝整个包（子集安装只属于 domain family） |
| R7 | members 非空；协议 id 与已装包 id 及其他协议 id 均不冲突；协议 id ≠ owfa |
| R8 | org 能力演化：每个协议任意时刻恰有一个 `<proto>.org.v<N>`（v1+v2 并存 = 错误）；upgrade = 原位替换，无共存窗口 |
| R9 | org 能力（`*.org.v*`）为协议包专属：非协议包供给任何 org 能力即 validate 错误；一工作区一协议随之自动成立 |
| R10 | 成员级 needs 受信任门控（只有 trust ≥ reviewed 的供给满足；不受信 = 不满足 → R6 语义）；文法 = CAPABILITY_RE；`owfa.*` 保留 |
| R11 | 两态 ABI 合格线（0.4.6 起强制；0.5.0 起为错误）——见 [abi.md §4](abi.md) |

## 能力（capability）

包级 `needs` / `provides`（v0.4）。语法，由 `validate` 机检：

```
<namespace>.<capability>.v<ordinal>     例如 owfa.org.v1
^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*\.v\d+$
```

- **前缀必须等于声明包 id**——非 `owfa.*` 能力的第一段名字必须等于包 id（`validate` 拒绝其余一切）；非声明者的名字空间被拒绝。
- **`owfa.*` 为框架保留**——这些名字只在框架仓库定义；registry 评审门在 index PR 时执法所有权。框架特批例外存在：personal 的 `owfa.org.v1`。
- **精确名匹配**——`needs: owfa.org.v1` 只被 `provides: owfa.org.v1` 满足，绝不被姊妹能力或不同 ordinal 满足；v2 供给者满足不了 v1 需求（单独报告为版本不匹配）。
- **独占槽**——每个精确能力名最多一个已安装供给者；两个已安装包供给同名即 validate 错误。
- **跨 ordinal 双供给合法**——同一基础能力的不同 ordinal（`x.cap.v1` 与 `x.cap.v2`）可同时在场；精确名匹配使它们各占各的槽。
- **needs 受信任门控**——只有 trust ≥ reviewed 的 provides 才算数（`framework-bundled`、`reviewed-3rd-party`）；**registry INDEX 行是信任来源**，因此 `--path` 与 owner-repo 直装（trust: unknown）的 provides 保持未验证，被它们覆盖的 needs 仍是红的。
- **`--yes` 在安装时越权并记 journal**——越权记入kernel journal，但不改写信任。

收敛点：install preflight（前瞻集合——upgrade 时按 已安装 − 旧 + 新 provides 组盘）、`validate`（全图错误，`--scope` 降为警告）、`upgrade`（前瞻）。**卸载刻意不是收敛点**：移走最后一个供给者会让 `validate` 保持红，而卸载本身照常成功（有意的不对称）。

命名治理总体上靠三层机械闸挡住碰撞：(1) plugin id——重复 id 是 validate 错误，install preflight 拒绝与已装成员同 id 的来包；(2) 包 id——registry `INDEX.yaml` 以包 id 为键，所有权在 index PR 上裁定；(3) 命令名——owner × commands 双向互检，两个包无法悄悄发布同名命令。

## 三安装通道与信任级

| 通道 | 形式 | 信任 |
|---|---|---|
| A —— registry | `kernel install <pkg>`（可带 `<pkg>@<tag>`） | 取自 index 行：`framework-bundled` / `reviewed-3rd-party` 免提示安装；其余需 `--yes` |
| B —— 未收录仓库 | `kernel install <owner>/<repo> --yes` | unknown——`--yes` 即信任门；registry PR 是包挣得 reviewed 信任的途径 |
| C —— 本地路径 | `kernel install <pkg> --path ./dir` | 你亲手审过；不经 registry |

信任级：`framework-bundled` / `reviewed-3rd-party` / `unknown`。默认 init 的离线步骤就是通道 C：`kernel install personal --path payloads/personal`。

发布（包作者的全程）：写 PKG.yaml → bump `version` → 打 tag `<pkg>-vA.B.C` → 提一行 registry PR。tag、PKG 版本、registry 行三者必须一致——kernel在 install/upgrade 时拒绝漂移。后两步（tag 与 registry PR）刻意分成两个小 PR：registry 永不与框架冻结在一起。

## 装卸与残留 —— 契约

子命令（包生命周期共 8 个，含 `migrate`——见[conversion.md](conversion.md)）：

| 命令 | 作用 |
|---|---|
| `plan <pkg>` | 包落位前的依赖披露：信任级、包披露、基线/可选成员、connector、建议命令。一次性、绝不交互——同意对话由 *agent* 执行；kernel只披露 |
| `install <pkg>[@tag]` | 解析 registry index（成员对照 PKG.yaml 核对）→ 信任门 → clone → 前瞻 manifest/预算 preflight → 拷贝母本/connector/命令 → 收敛 |
| `uninstall <pkg> --yes` | 机械四清（母本 / 命令 / connector / skill）+ 收敛 + 残留扫描 + retains/credentials 提醒——数据永不触碰 |
| `residual <pkg>` | 独立残留扫描：在锚面（AGENTS 手写区 + 包的 `uninstall.anchors` 页——personal 套件即其 PKG.yaml 声明的 profile/language/calendar/todo/cron 等）中按词边界（刻意放宽）grep 成员引用；kernel管理的注入区跳过（已被机械清理） |
| `list-remote` | registry index 表，带已装标记 |
| `upgrade` / `upgrade <pkg> --yes` | 只读对账报告；执行为逐包**静默重装**（绝不级联）——成员增量、changelog 摘录、链式 migration staging |
| `pkg` | 包清单：成员、connector、未被任何包认领的plugin |

**安装失败处理。** 拷贝前，`install` 先在临时目录按真实安装过滤器 staging 前瞻母本，并对照合并集（已安装 + 来包）检查 manifest/依赖规则与既有 UTF-8 注入预算；拒绝即在任何文件改动**之前** exit 1（调用方的 `--path` 源保留；下载的临时源丢弃）。拷贝后收敛继续跑；此处失败*不是*事务回滚——检查、修复、`kernel validate`。声明了首跑语义 migration 的包会机械装好，但 `validate` 保持红、横幅常驻，直到语义步骤完成并清除（`kernel migrate <pkg> --clear`）。

**卸载契约。** kernel做机械四清，随后残留扫描输出即人类侧清理清单；agent 按声明在确认门后收尾语义（凭据提醒、进程停止、bridge 注册行）。**数据与凭据绝不自动删除**——删除的自由属于人；保留的数据区转入 deprecated 姿态。声明的 `teardown.md`（每次 install 都休眠 staging）在卸载时翻成待办警告——语义删除债，同样的三面横幅与残留门控的 `--clear`。

**migration：0 → x → y → 0 的代数。** 语义状态变化乘声明而非钩子：init（`migrations/init.md`，新装）、migrate（`x-to-y.md`，发布时冻结，升级跨 B 线时 staging）、teardown（`teardown.md`，每次 install 休眠 staging，卸载时消费）。kernel把它们 staging 到 `.owfa/migrations/<pkg>/` 并记账（`pending.json`），升起三面警告（每次调用的横幅 · 红 validate · kernel管理的 AGENTS 块），直到经作者的 AST 门控 `verify(ctx)`——只读、仅标准库——清除并删除文件（用后即删）。sweep 对称性让账本无需 cron 即保持诚实：migrate 类条目随包消亡，teardown 类随重装消亡；staging 里休眠的 PKG.yaml 副本兼任在场标记，因此即使手动 `rm -rf` 包目录，全套机械残留也能自愈。kernel journal（`.owfa/kernel-journal.log`，滚动上限 500 行，入 git）记录机械链——install / warn+ / clear / uninstall / sweep，以及 `--yes` 信任越权。

## 版本与 tag

版本分五层，一个原则：只有被 tag 或 registry 指称的层才携带发布语义（`A.B.C`）——其余层是回答"变了多少"的序数，而非"这是哪个发布"。

| 层 | 版本 | 语义 |
|---|---|---|
| 框架 / 发布通道 | `A.B.C` —— `.owfa/VERSION` == `package.json` == tag `vA.B.C` == npm == GitHub release | **A** 项目状态（`0` = alpha）· **B** 架构线 · **C** 线内更新 |
| package | `A.B.C` | 域自身发布语义，独立于框架（永不锁步）——tag `<pkg>-vA.B.C`、registry 行、migration |
| 成员plugin（及 core plugin） | `X.Y` | 器官修订序数——契约或行为变化时 bump；自身无发布粒度，随包的 `A.B.C` 走 |
| connector | 仓内锚点 | 工程 changelog——不进 registry / tag / PKG 语义 |

包的 bump 规则：**A** 只在毕业时动（所有者裁决；kernel强制的适配不是 A 事件——那种耦合住在 `compat` 里）；**B** = 域契约变化（成员名册、披露/manifest 模式、数据或页面形状、信任模型、compat 下限）——语义 migration 的唯一载体，按 B 线对命名（`0.2-to-0.3`）；**C** = 架构线内的更新，绝不携带 migration——动了数据或页面形状的变化是 B 不是 C。树变了 ⇒ 必换号，永远如此；C 数发布而非器官变化（三个成员一起变是包的一次 C bump）。同步义务：`PKG.yaml` 版本 == `<pkg>-v` tag == registry 行，install/upgrade 拒绝漂移。

## registry 行格式

registry 是 **owfadev/owfa-registry**（一个仓库，不是组织）：`INDEX.yaml`，一行一包，以包 id 为键——人工评审门（inject 文本与 connector 是安全面，index 行是挣来的而非自领的；信任级也在这个 PR 上裁定）。每行字段：

- `repo` —— `owner/name`（组织仓全部 `owfa-*`）
- `version` —— `A.B.C`，必须等于包的 tag
- `compat` —— 框架下限
- `trust` —— `framework-bundled` / `reviewed-3rd-party`（能力的信任来源）
- `members` —— plugin名册（`/` 分隔）
- `summary` —— 一行，写给 agent 看（见[developer.md](developer.md)发现机制一节）
- `needs` / `provides` —— 可选能力列表（`/` 分隔，镜像 PKG.yaml 以供跨包发现）
- `commit` —— 可选 SHA pin，供应链内容锚：clone 的 HEAD ≠ pin 即拒绝

INDEX 行字符串按 `/` 切分（INDEX 行文法中逗号是值终结符，会静默截断列表）。

## Transport 契约（可选，按plugin）

domain 可声明一个与 connector 无关的能力，使任何合规 transport 都能服务它：

```yaml
transports:
  contract: qq.transport.v1      # 能力 id（必填）
  recommends: qq-cli             # 默认 connector（可选）
  declaration: qq/policy.md      # 以 frontmatter `transport:` 标记活跃第三方 transport 的 wiki 页（可选）
  providers: qq-cli, napcat-bridge   # 逗号分隔标量（嵌套 block list 会被静默丢弃）
```

`validate` 做结构检查：声明了 contract 但既未装推荐 connector、声明页又无 `transport:` 字段 → 警告。保证语义：未声明 = 无保证——agent 侧纪律是底线，transport 侧强制是加固。contract id 遵循上述能力语法。

## 附录：决策台账（仍然有效的条目）

| # | 决策 | 一句话理由 |
|---|---|---|
| D1 | 声明名册 + 闭包对账（仅 domain-family） | 活图 vs 版本化锚；漂移 → 提交期错误；suite 只做在场检查，不做闭包 diff |
| D2 | 包版本 ≠ 成员版本 | 分发单元 ≠ 语义单元；锁步是陷阱 |
| D3 | binding 轮引入 scope/容忍 validate | 只有各仓能脱离全图自检，拆分才安全 |
| D4 | 实例本地包同样住 `domains/` | 一个语义：包目录 == 安装单元；零索引私有包 |
| D5 | subset 语法定死，`--without` 已开放 | 校验器格式永不破坏；子集在 install 时校验 |
| D6 | 声明式卸载、无钩子 | 拒绝第三个执行面；删除知识成为可评审数据 |
| D7 | migration 是闭合 0→x→y→0 的声明；teardown 随每次 install 休眠随行 | 语义变化乘可评审文件；x→0 必须在包消失*之前*声明 |
| D8 | sweep 对称 + 休眠 PKG.yaml 在场标记 | 无 cron 的账本真实；手动 `rm -rf` 也能自愈（处处无钩子） |
| D9 | teardown 门 = 默认残留扫描，作者脚本可选 | D6 无钩子原则延伸到删除*验证*——零脚本包也有语义门 |
