# OWFA — One Workspace For All (agents)

> [English](README.md) | 简体中文

**OWFA** 是一个开源的、基于本体论、为 agent 服务的工作区框架。工作区是你自己的一个目录：你用的每一个 agent 都反复进入它，而不必每次重新介绍背景；agent 零先验地读写，一切留在本地纯文件里，任何能读 `AGENTS.md` 与技能的 harness 都能运行它。

工作区的性质由**协议**决定：

- **personal**（默认，`vaultwiki`）——面向个人信息处理的协议：真实资产放 `vault/`，Markdown 知识放 `wiki/`，配 map / save / query / check 命令。设计思想源自 llm-wiki，既有工作流几乎零成本接入。
- **project**——工作区本身就是一个项目时使用。要开发 owfa 本身，加装可选 `owfadevelop` 包。
- 其他——协议与域包（cuhksz、lark、email、bili、qq……）按需从[注册表](https://github.com/owfadev/owfa-registry)安装。

## 安装

```bash
npx owfadev init my-workspace   # 内核 + 默认 personal 协议；--core none 得裸工作区，--core <pkg-id> 选其他协议
cd my-workspace
npx owfadev doctor              # 健康检查
npx owfadev add cuhksz          # 可选域包
npx owfadev upgrade             # 之后：更新框架，实例数据不动
```

前置：Node 16.7+（安装器）、Python 3.9+ 纯标准库（内核）、一个会读 `AGENTS.md` 的 agent；git 推荐；Obsidian 可选（仅作查看器）。npm 包名是 `owfadev`——`npx owfa` 不可用（名字被 npm 冻结），详见[命名](.owfa/docs/zh/naming.md)。`init` 是加法式的：既有内容永不触碰。

首次使用：在工作区根目录开一个 agent 会话，丢一个文件进去，说「map」。

## 默认 personal 协议下

- 资产丢进 `vault/`，任意格式——**map** 为每份登记 SHA-256 与 Markdown 代理页；**query** 带引用作答（热缓存 → 索引 → 全文 → 原文）；**check** 体检健康
- 对话经 **save** 蒸馏为原生笔记；用户画像驱动个性化；索引、标签与运行日志自动维护
- 外部信息源以域接入：cuhksz 拉课件、作业与成绩；lark / email / bili / qq 把各自平台变成可检索领地——按需安装，卸载不伤数据

命令分三层：**owfa-check / owfa-docs / owfa-kernel / owfa-plugin** 是框架自带（任何工作区都在，协议不预设）；其余随协议套件或包到达——缺哪个命令，就说明缺哪一层。

## 核心概念

| 概念 | 定义 |
|---|---|
| workspace（工作区） | 你拥有的目录；每一个 agent 都把它当作常驻上下文反复进入 |
| protocol（协议） | 决定工作区的性质——领地、页面与工作循环是什么（personal、project……） |
| package（包） | 一切能力的交付形态：协议套件、域适配器、工具——整体装卸，注册表列出 |
| kernel（内核） | 包机制：清单、依赖图、投影、安装升级——不认识任何内容协议 |
| SASU-L | 披露范式：agent 只经 system prompt、AGENTS.md、Skills、用户话语、循环获知信息 |

## 布局

| 目录 | 内容 |
|------|------|
| `.owfa/` | 内核树：`owfa_kernel.py`（纯标准库）、`VERSION`、`protocol/`、`docs/`、`command/`（4 个框架命令母本） |
| `payloads/personal/` | personal 套件的内嵌副本——默认 `init` 离线安装的就是它 |
| `.agents/skills/` | 命令与连接器技能的部署副本 |
| `bin/` + `templates/` | npm 通道（`owfadev` CLI、AGENTS 种子） |

域包住在 [owfadev](https://github.com/owfadev) 组织各自的 `owfa-*` 仓里；注册表的一行 PR 就是人审收录门。自 0.4.8 起另有**用户级内核**通道（`init --user-level`、`adopt`）——内核每机一份，工作区打标登记（见 [deployment](.owfa/docs/zh/deployment.md)）。

## 参与贡献

面向包贡献：一个 connector 技能、一个域包、或一次内核改进——三路径表与开发循环见 [`developer.md`](.owfa/docs/zh/developer.md)。开发 owfa 本身，推荐在 project 协议工作区加装 `owfadevelop` 包进行。缺陷与行为问题走 issue；框架 PR 需一枚批准评审（规则见 [CONTRIBUTING.md](CONTRIBUTING.md)）。

## 文档索引

- [快速上手](.owfa/docs/zh/quickstart.md) 五分钟路径 · [部署](.owfa/docs/zh/deployment.md) 组件、通道、升级
- [包机制](.owfa/docs/zh/packages.md) · [开发者](.owfa/docs/zh/developer.md) 插件落位 · [发布](.owfa/docs/zh/releasing.md) 发版手册
- [内核](.owfa/docs/zh/kernel.md) 内核机制 · [命名](.owfa/docs/zh/naming.md) 名字、层次、撞名政策
- [personal 协议](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/protocol.md) 默认协议自己的章程

## 许可

MIT——见 [LICENSE](LICENSE)。
