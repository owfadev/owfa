# 部署

> 读者：任何把 OWFA 装进某个目录（Obsidian vault、笔记文件夹、任意工作区）的人，或替你做这件事的 agent。这是完整指南——组件、通道、首次运行、package、升级、排障。五分钟路径见 [quickstart.md](quickstart.md)；发布 runbook 见 [releasing.md](releasing.md)。自 v0.4.1 起，原 distribution 页中属于装机面的内容——通道命令、`init`/`upgrade` 行为——并入本文；吸收段落标注 *（吸收自 distribution.md）*。

## 1. 装下去的是什么

OWFA 分层，其中只有一层被「安装」：

| 层 | 是什么 | 住在哪 | 被安装？ |
|---|---|---|---|
| **OWFA CLI** | 安装器 / 升级器（`init`、`upgrade`、`doctor`、`add`、`list`、`pkg`） | npm 包，经 `npx` 或全局安装运行 | 否——留在工作区之外 |
| **OWFA Core** | 框架本体：plugin、命令、协议、kernel、skill 副本 | `.owfa/` + `.agents/skills/` | 是——拷进工作区 |
| **kernel** | 确定性 Python 引擎（`validate`、`inject`、`registry`、`deploy`、`install`） | `.owfa/scripts/owfa_kernel.py` | 否——随 Core 分发；没有独立的 kernel 安装 |
| **package** | 可选 domain 扩展（cuhksz、lark、email、bili、project…） | `.owfa/plugins/domains/<pkg>/` | 按需 |
| **instance** | 你拥有的工作区：`vault/`、`wiki/`、`AGENTS.md`、框架本体 | 你的目录 | — |

调用链是单向的：

```
OWFA CLI  →  拷贝 OWFA Core  →  调 kernel  →  kernel 收敛 Core + package
```

部署后的工作区长这样：

```
my-workspace/
├── AGENTS.md                  # 身份/布局（你的）+ 注入区（kernel 管理）
├── vault/                     # 真实资产，任意格式
├── wiki/                      # markdown 世界
│   ├── notes/  sessions/  vault/
│   └── index.md  tags.md  hot.md  log.md   # 派生层，流水线重建
├── .owfa/                     # OWFA Core（v0.4 拆分后仅 kernel 树）
│   ├── VERSION                # 框架锚点——部署版本的唯一事实源（别信任何硬编码数字）
│   ├── scripts/               # kernel + wikilib（pipeline 归套件；弃用宿主垫片最后一次种下是 0.5.0 之前的通道）
│   ├── plugins/domains/       # 已安装 package——init 时内嵌 personal 套件（21 成员）落此；通道本身不带 plugin
│   ├── command/               # 框架命令母本（套件自有命令随包分发）
│   └── docs/                  # 本指南及同伴
└── .agents/skills/            # deploy 出的命令/connector skill 副本
```

kernel **不是**服务、守护进程或 pip 包。它是纯标准库 Python 脚本，由 CLI（和 agent）按需调用。Core 的唯一运行时要求是 Python 3.9+。

## 2. 前置条件

| 项 | 要求 | 用途 |
|---|---|---|
| Python | **3.9+**，纯标准库 | Core 与 kernel |
| Node | **16.7+** | 仅 npm 通道（CLI 是 Node） |
| agent | 会读 `AGENTS.md` 与 `.agents/skills/` 的编码助手（如 ZCode、Claude Code、Cursor、dsh） | 日常使用 |
| git | 建议 | 实例快照与升级回滚 |
| Obsidian | 可选 | 查看 wiki；永不必需 |

框架本身零包管理器依赖：不 `pip install`、无 Python venv、tarball 内无 npm 依赖。`npm` 是投递工具，不是运行时。

## 3. 选通道

所有通道部署同一棵 Core 树；按环境选，不按功能选。

| 通道 | 命令 | 状态 |
|---|---|---|
| npm | `npx owfadev init my-workspace` | **已上线**——包名 `owfadev`（双 bin `owfa` + `owfadev`，provenance 已启用）；现行版本以 npm 页面为准 |
| npm，冻结名 | `npx owfa init …` | **不可用**——npm 以相似性政策（太近 `ow`/`ora`）冻结了 `owfa`；`npx owfa` 解析不到 |
| git，克隆即实例 | `git clone https://github.com/owfadev/owfa.git my-workspace` | 现在可用 |
| git，嵌入既有 vault | 在别处克隆模板，拷 `.owfa/` + `.agents/skills/` | 现在可用 |
| 模板 + 实例（开发者） | 模板克隆 + 独立实例 | 见 [CONTRIBUTING.md](https://github.com/owfadev/owfa/blob/master/CONTRIBUTING.md) |

> npm 通道由 registry 以 `owfadev` 之名供给；一切安装示例必须写 `npx owfadev`。组织改名于 2026-10-26 执行（`AIE3905-Wuwa` → `owfadev`，`vault-wiki` → `owfa`）；旧仓库 URL 重定向，旧组织/API 路径 404。

## 4. 安装

### 4.1 npm 通道——一条命令 *（吸收自 distribution.md）*

```bash
npx owfadev init my-workspace
cd my-workspace
npx owfadev doctor            # python、框架、标记、kernel validate——只读不写
```

**命令形态。** `npx owfadev <verb>` 无需全局安装。全局安装（`npm i -g owfadev`）会把 `owfa` 与 `owfadev` **两个** bin 都放上 `PATH`。CLI 完整命令面：

```
owfa init [dir] [--name NAME] [--packages a,b] [--force]
owfa upgrade [dir] [--check] [--backup] [--force]
owfa doctor [dir]
owfa add <pkg> [--yes] [--without a,b]
owfa list
owfa pkg
owfa version
```

本文余下部分 CLI 一律写 `owfa <verb>`、Python 引擎一律写 `kernel …`；未全局安装时替换为 `npx owfadev`。该包零依赖、无生命周期脚本——`npm install` 不执行包内任何脚本；框架唯一的运行时依赖仍是 Python（Node 用于*装*，不用于*用*）。

`init` 默认两阶段（v0.4 定局形态——通道只发这一种）：

1. 从 tarball 拷 `.owfa/` 与 `.agents/skills/`，对仅 kernel 树跑 `python .owfa/scripts/owfa_kernel.py all`（validate → inject → registry → deploy）；
2. 离线安装内嵌 **personal 套件**（原 21 个框架 plugin，即 **owfa-personal** 包的审定副本，在 `payloads/personal/`）——其 `PKG.yaml` 的 `skeleton:` 声明建出 `vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/`，命令母本（`owfa-map`、`owfa-profile`、`owfa-save`）随包 deploy；
3. 从种子写 `AGENTS.md`；已存在则只追加**注入区**（手写部分保留；标记残缺一半则拒绝）；
4. 可选装 package（`--packages cuhksz,lark`），停在第一个 stage 语义迁移的包。

`--core none` 跳过第 2 阶段（仅 kernel 实例：无 skeleton、无套件）；`--core <pkg-id>` 改从 registry 取套件而非内嵌副本。

常用 flag：

- `--name NAME`——写进 AGENTS 种子的工作区名；
- `--packages a,b`——init 期间从 registry 装 package；
- `--force`——在既有实例上重拷框架树，保留 kernel 的迁移台账、journal 与 registry 缓存。实例数据（`vault/`、`wiki/`）永不触碰。

目录已有 `.owfa/` 时 `init` 拒绝；改用 `owfa upgrade`（或有意 `--force`）。

### 4.2 git 通道——五个手工步骤

**克隆即实例**（克隆*就是*你的工作区）：

```bash
git clone https://github.com/owfadev/owfa.git my-workspace
cd my-workspace
# 不想要框架的历史就自己接管：
rm -rf .git && git init
```

**嵌入既有 vault**：在别处克隆模板，把两棵树拷进目标根：

```bash
cp -R /path/to/owfa/.owfa          /path/to/my-workspace/
cp -R /path/to/owfa/.agents/skills /path/to/my-workspace/.agents/
```

v0.4 拆分后拷来的树只带 kernel——没有 plugin。装内嵌套件（随克隆在 `payloads/personal/`）及其 skeleton：

```bash
python3 .owfa/scripts/owfa_kernel.py install personal --path /path/to/owfa/payloads/personal
```

然后在目标根：

1. **写 `AGENTS.md`**——一段身份、一段布局，注入标记照抄 [agents-example.md](agents-example.md)。已有 `AGENTS.md` 则只贴标记块（或让 `owfa init` 追加）。
2. **收敛**：

```bash
python .owfa/scripts/owfa_kernel.py all
```

预期：personal 套件 21 成员 validate 通过，package 名册对账，注入区重建，命令副本同步。四个 skeleton 目录（`vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/`）随套件安装而来——其 `PKG.yaml` 的 `skeleton:` 声明它们；通道不硬编码任何实例布局。

### 4.3 「安装 kernel」

没有独立可装的东西。kernel 就是 Core 里的文件 `.owfa/scripts/owfa_kernel.py`；Python 3.9+ 即可跑。验证：

```bash
python3 .owfa/scripts/owfa_kernel.py validate   # 结构检查，只读
python3 .owfa/scripts/owfa_kernel.py ls         # personal 套件 21 成员（框架树本身一个不带）
python3 .owfa/scripts/owfa_kernel.py pkg        # 已装 package + 未认领残余
```

Windows 上 `python` 可能是 `py -3`；CLI 依次探测 `python3`、`python`、`py -3`。设 `OWFA_PYTHON=/path/to/python3` 可覆盖。kernel 缺失说明 Core 拷贝不完整——重拷树，不要去「pip install」任何东西。

### 4.4 用户级内核与机器注册表

自 0.4.8 起，内核可以**每台机器装一份**，而非每个工作区一份——用户级内核通道（kernel-home spec v2）：

```bash
owfa init <dir> --user-level   # 在用户级通道上新建工作区
owfa install-kernel            # 把本通道的 kernel master 装进 $OWFA_HOME/kernel/<X.Y.Z>/
owfa adopt <path>              # 把既有 legacy 树迁上该通道（幂等）
owfa workspaces list           # 机器工作区注册表
owfa workspaces rescan [--under DIR]   # 从盘上标记重建注册表索引
```

- **`init --user-level`** 把内核装进 `$OWFA_HOME/kernel/<ver>/`（一版一目录、多版共存、对通道 master 做 sha256 校验），写工作区标记 `.owfa/WORKSPACE.yaml` 并登记工作区——工作区树**不再**携带 `scripts/` 载荷，也没有树内 `VERSION`。缺省（不带旗标）仍是 legacy 每树一份的通道。
- **`adopt <path>`** 迁移 legacy 树：停泊树内 `scripts/`、写标记、登记、经新内核 validate——全有或全无；已 adopt 的工作区是 no-op。
- **`$OWFA_HOME`**（默认 `~/.owfa`）是用户级基座根：`kernel/<ver>/` 放已装内核，`kernel/current` 指向最新，`workspaces.yaml` 是机器注册表。设 `OWFA_HOME` 环境变量可让 CI 容器或测试沙箱各用各的根。
- **`.owfa/WORKSPACE.yaml` 是事实源**——极简标记（`kernel_compat` 下限；协议身份永不写入，由已装协议包推导）。**`~/.owfa/workspaces.yaml` 只是索引**（路径、uuid、kernel/compat 快照）。`owfa workspaces rescan` 扫盘上 `WORKSPACE.yaml` 标记重建索引（有界扫描，默认在用户主目录下）；自 0.4.8 起，rescan 还会从盘上刷新每行的 kernel/compat 快照。`list` 对悬空路径惰性注销并提示重新 adopt。
- **垫片退役（0.5.0）。** 自 0.5.0 起，通道不再向用户级工作区种弃用宿主转发器，legacy 通道也不再分发 pipeline 宿主垫片（`.owfa/scripts/pipeline.py`）——直接调用内核：`python3 $OWFA_HOME/kernel/<current>/owfa_kernel.py --root <工作区>`（或 `owfa` CLI）；pipeline 一律走 personal 套件包（`.owfa/plugins/domains/personal/pipeline.py`）。已有文件在升级时**永不删除**：0.5.0 之前的工作区保留其仍在工作的转发器（它与版本无关）；`owfa doctor` 与升级输出会打印弃用提示行，附同样的迁移建议。
- **嵌套工作区与父区名册（声明式实践，2026-11-16）。** 已登记的工作区目录内可以再容纳其他已登记工作区（如个人库在 `projects/` 下托管独立项目工作区）：机器注册表本身是扁平无层级的——嵌套条目一律平等列出。两个现行限度，如实记录：`workspaces rescan` 碰到已发现的标记即停止下探（不会继续扫父区子树里的更多标记——嵌套子区需显式登记，或用 `--under <子区子树>` 定点重扫）；CLI 绑定精确 cwd（尚无向上标记走查——kernel-home 规格v2 的 F2 最近标记者胜解析未实装，列为 0.6.0 候选）。父区以**自己的协议**决定如何披露子区（笔记页/索引页——父区实践，非内核法）；披露行文法：`路径 · 协议（org 能力）· compat 区间 · git 根 · 桥引用（如有连接）`。指向子区的桥就是普通桥——父区上下文只读，写仅在子区法域在场时（见 agent-behavior.md § 法域纪律）。父区不追踪子区内部——名册是指针，不是镜像。

## 5. 首次运行

```bash
cd my-workspace
git init && git add -A && git commit -m "init: OWFA workspace"   # 建议
```

1. 随便放一个文件进 `vault/`——`memo.txt`、PDF、图片。
2. 在工作区根打开 agent 会话，说 **map**。
3. agent 写 `wiki/vault/memo.txt.md`（SHA-256 + 元数据），流水线接着建 `wiki/index.md`、目录 index、`tags.md`、`hot.md`、`log.md`。
4. 说 **check**——审计全绿即部署健全。

`AGENTS.md` 的注入区此刻每个 full-tier plugin 一块；agent 把它读作结构契约。标记之外的一切是你的。

## 6. 怎么用

在工作区根打开 agent；它读 `AGENTS.md` 与 `.agents/skills/`。日常命令即自然语言：

| 你说 | 发生什么 |
|---|---|
| map | 把 vault 资产登记为 wiki 代理页（哈希、元数据、链接） |
| save | 把当前对话蒸馏成原生笔记 |
| query | hot → index → grep 作答，带 wikilink 引用 |
| check | 仓库健康审计（结构 + 语义检查） |
| plugin | 安装 / 卸载 / 列出结构 plugin |
| profile | 维护用户认知档案 |
| 讲解 / 出题 / 认知档案 | 课程学习全家（需课程 domain，如 cuhksz） |
| kernel 参考 | kernel 用法与机制 |

日常循环——库务、课程学习、协作开发——见默认协议文档（[owfa-personal: usage](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/usage.md)）。内核机制见 [kernel.md](kernel.md)；flag 以 kernel 参考 skill 为权威。

## 7. package——查找与安装

v0.4 起 Core 本身两阶段：kernel 载荷先落，`init` 默认再装内嵌 **blessed 套件**——原框架 plugin，现以 **owfa-personal** 包分发（tarball 内的审定副本）（`--core none` 跳过，`--core <pkg>` 改装别的 core 包）。外部系统以同样方式到达，即 **package**：一个目录 `.owfa/plugins/domains/<pkg>/`，带 `PKG.yaml` 名册、plugin 母本、命令与 connector。

### 7.1 查有什么

在实例内跑：

```bash
owfa list                    # registry 目录：版本、compat 下限、已装标记
owfa pkg                     # 本实例装了什么：成员、connector、core 残余
# 经 kernel 同样可以：
python3 .owfa/scripts/owfa_kernel.py list-remote
python3 .owfa/scripts/owfa_kernel.py pkg
```

registry 是 GitHub 索引 `owfadev/owfa-registry`；装前也可直接读该仓库的 `INDEX.yaml`。每行给出 package 版本、框架 compat 下限、成员 plugin 与信任级。

### 7.2 装 package

```bash
owfa add cuhksz              # 包装 kernel install + 收敛
# 等价且更明确：
python3 .owfa/scripts/owfa_kernel.py install cuhksz --yes
```

这也是 agent 的 **plugin** 命令做的事：你可以按名让 agent 装 package，它驱动同一个 kernel。CLI 是人/脚本侧的等价物。

落了什么：`.owfa/plugins/domains/<pkg>/` 下的 plugin 母本、命令母本、仓内 connector、skill 副本、注入块、registry 行。随后 kernel 收敛。若 package 声明了**首跑语义迁移**（如 `project` 这类根包），安装即 stage，`validate` 保持红，直到 agent 做完语义步骤：

```bash
python3 .owfa/scripts/owfa_kernel.py migrate <pkg>
# 读打印页，建声明/身份页，然后：
python3 .owfa/scripts/owfa_kernel.py migrate <pkg> --clear
```

CLI 会停下并如实报告，不假装收敛。该状态下 `owfa add` 非零退出。

其他形态：

- `kernel install <pkg>@<tag>`——钉住发布 tag；
- `kernel install <owner>/<repo> --yes`——未入索引的仓库（trust: unknown；`--yes` 即信任闸）；
- `kernel install <pkg> --path ./local-pkg`——本地 package（通道 C，不经 registry）；
- `--without a,b`——子集语法保留；v1 报「未开放」。离线替代：把 `domains/<pkg>/` 拷进 `.owfa/plugins/domains/` 重跑 `all`。

信任级在 `owfa list` 可见：`framework-bundled` 与 `reviewed-3rd-party` 免确认安装；其余需 `--yes`，报 unknown。

### 7.3 升级与卸载 package

```bash
python3 .owfa/scripts/owfa_kernel.py upgrade            # 对账报告（只读）
python3 .owfa/scripts/owfa_kernel.py upgrade <pkg> --yes # 静默重装，按包，永不级联
python3 .owfa/scripts/owfa_kernel.py uninstall <pkg> --yes
```

- package 版本是骑在自己 tag 上的发布序数；成员 plugin 版本不联动。
- 升级在新版本落地时 stage 语义迁移；做下一个机械动作前先清掉。
- 卸载做机械四清（母本、命令、connector、skill）加残余扫描；**数据区与凭据永不自动删除**。声明的 teardown 会 stage 语义删除警告与残余闸。见 [packages.md](packages.md)。

## 8. 升级框架

### npm 通道 *（吸收自 distribution.md）*

```bash
npx owfadev upgrade            # 以通道版本替换 .owfa/ + .agents/skills/
# 自 v0.4.3 起升级顺序按形状定：先框架、后包。
# PKG 形状旧内核解析不了的包（0.4.3 起 kind: protocol、能力命名空间）在旧内核上跑
# kernel upgrade <pkg> 必失败——失败升级不得留下中间态（真实事故见 issue #72）。
# 「套件先行」是 v0.4.1–0.4.2 的事实惯例（当时文档未明示顺序，垫片注释为证），仅适用于旧内核可解析的包。
npx owfadev upgrade --check    # 只读报告
npx owfadev upgrade --backup   # 在 .owfa/backup/<version>-<timestamp>/ 留一份副本
```

`upgrade` 比对实例 `.owfa/VERSION` 与 tarball 版本（非 `--force` 拒绝降级），保留实例本地 kernel 状态（`.owfa/migrations/pending.json`、`.owfa/kernel-journal.log`、`.owfa/registry-cache.yaml`），替换两框架树下的本地改动（实例热修属于实例 git），重跑 `all`。待清的语义迁移会阻塞收敛，并给出确切的 `migrate` 命令。

### git 通道

从新模板修订重拷 `.owfa/` 与 `.agents/skills/`（先看 diff，勿在待迁移之上盲拷），然后 `kernel all`。实例 git 快照即回滚路径。

框架版本锚在 `.owfa/VERSION`——读文件本身，别信文档里引用的数字；升级可能 stage 目标侧语义迁移，同样的三面警告与 `kernel migrate` 流程。五载体等式（`.owfa/VERSION` == `package.json` == git tag == npm == GitHub Release）由 release gate 强制——见 [releasing.md](releasing.md)。

## 9. 卸载

- **一个 package**：`kernel uninstall <pkg> --yes`；数据区留下，凭据只提醒、绝不删。
- **整个框架**：删 `.owfa/`、`.agents/skills/`、`AGENTS.md` 注入区块。`vault/` 与 `wiki/` 是你的，随意处置。别无所装。

## 10. 排障

| 症状 | 原因 / 处理 |
|---|---|
| `Python 3.9+ not found` | 装 Python 3，或设 `OWFA_PYTHON`；安装器纯 Node，运行时是 Python |
| `already contains .owfa/` | 这已是实例——`owfa upgrade`；`--force` 重拷两树 |
| `npx` 跑了旧版本 | `npx owfadev@latest …`；npm 按版本范围缓存 |
| `npx owfa` 失败 / 404 | 名字被 npm 相似性政策冻结、解析不到；用 `npx owfadev`（双 bin）——一切安装示例都用它 |
| 升级被待迁移卡住 | 跑 `kernel migrate <pkg>`，做完语义步骤再 `--clear` |
| AGENTS 标记缺失 | 壳丢了 `wiki-inject:start/end` 一对；补齐两行，再 `kernel all` |
| Windows：`python` 弹商店 | 装 Python 3 并确保 `py -3` 或 `python3` 可用；`OWFA_PYTHON` 覆盖探测 |
| kernel `list-remote` 失败 | 网络/raw 访问；registry 索引取自 GitHub raw。框架本身离线仍可用 |

## 11. 安装后文件地图

| 路径 | 用途 | 可手改？ |
|---|---|---|
| `AGENTS.md` | 身份/布局（你的）+ 注入区（kernel） | 标记之外，可以 |
| `vault/` | 真实资产 | 可以——人所有 |
| `wiki/` | markdown 世界、代理、笔记、会话 | 可以，经命令；派生页会被重建 |
| `wiki/index.md`、`tags.md`、`hot.md`、`log.md` | 派生层 | 否——流水线重写 |
| `.owfa/plugins/` | Core plugin + 已装 package | 否——框架作者面 |
| `.owfa/scripts/` | kernel、wikilib（pipeline 归套件；弃用垫片最后一次种下是 0.5.0 之前——既有副本继续可用） | 否——框架作者面 |
| `.owfa/command/` | 命令母本 | 否 |
| `.agents/skills/` | deploy 出的 skill 副本 | 否——`kernel deploy` 同步 |
| `.owfa/migrations/` | stage 的语义迁移 + 台账 | 否——kernel 区 |
| `projects/` | project 容器（若装了 project 包） | 可以——project 自有 |

## 12. FAQ

- **已有内容的 vault？** 加法式：`init` 建/扩框架树，不碰你的文件。新资产走 `map`；旧内容是否代理由你增量决定。
- **能用 Obsidian 吗？** 能——它是查看器。框架写纯 markdown 加文件；无需任何插件。
- **能拷整个 `.agents/` 树吗？** 能；本仓库的 `.agents/` 只有 `skills/`。
- **Windows？** 纯标准库、无硬编码路径；CLI 探测 `py -3`。Git Bash 与 PowerShell 皆可。
- **离线？** 联网机上 `npm pack`，拷 `.tgz`，`npm install -g ./owfa-x.y.z.tgz`，再 `owfa init`。package 可拷 `domains/<pkg>/` 后用 `all` 收敛。
- **多工作区？** 一目录一实例，互相独立，且 `owfa workspaces list` 一览无余——用户级通道维护机器注册表（`~/.owfa/workspaces.yaml`），收录每个 adopt / `--user-level` init 的工作区，`rescan` 可从盘上重建索引。legacy 通道的工作区就是彼此独立的树；CLI 可 init/upgrade 任意路径。
- **plugin 从哪来？** registry 索引；未索引仓库可用 `--yes` 装（trust: unknown）。package 模型与 `PKG.yaml` 见 [packages.md](packages.md)。

## 附录——命令速查

| 目标 | 命令 |
|---|---|
| 安装 | `npx owfadev init <dir>` |
| 健康检查 | `npx owfadev doctor <dir>` |
| CLI / 通道版本 | `npx owfadev version` |
| 框架升级 | `npx owfadev upgrade <dir>`（或 `--check` / `--backup`） |
| package 目录 | `owfa list` / `kernel list-remote` |
| 已装 package | `owfa pkg` / `kernel pkg` |
| 装 package | `owfa add <pkg>` / `kernel install <pkg> --yes` |
| package 升级 | `kernel upgrade`（报告）/ `kernel upgrade <pkg> --yes` |
| package 卸载 | `kernel uninstall <pkg> --yes` |
| 待迁移 | `kernel migrate` / `kernel migrate <pkg> --clear` |
| 结构检查 | `kernel validate` |
| 全量收敛 | `kernel all` |
