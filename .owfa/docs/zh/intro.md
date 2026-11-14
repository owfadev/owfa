# 引言

> 读者：团队成员、贡献者，以及任何想理解这套设计的人。机制「是什么」的权威来源是 kernel 参考 skill 与 AGENTS.md 注入区；本文讲的是「为什么走到今天」——叙事与谱系，不是机制的镜像。成文于 2026-10-04。

## 1. 出发点的问题

每个会话里，agent 按 SASU-L 顺序获取信息：system prompt、AGENTS.md、Skills、用户自己的话、loop。system prompt 不携带任何 vault 信息；用户以为 agent 记得上次，这不可能。跨会话的信息获取只能靠 agent 主动去读，而真实部署中 agent 对 vault 零先验。用 AI 助手之痛往往不是不够聪明，而是每次都要自我介绍一遍：资产在哪、在学什么、上次的决策停在哪。

## 2. 文件地基

Markdown 加纯文件是地基。没有工具私有的格式；Obsidian 与 WebUI 只是可替换的查看器。现在 agent 能读 vault 了——但「能读」不等于「知道该读什么」。没有路标的阅读是盲读：全读则 context 爆炸，漏读则信息失明。框架解决的不是存储，而是信息披露的结构。

## 3. 指针机制

指针是常驻 context 的低成本路标：位置与摘要恒在，摘要就是全部过滤效率的来源；触发条件与触发后动作按需配对。渐进披露分三层：指针以最小 context 代价常驻；被指向的目标按需读取；被引用的材料再往下钻。index 逐级下钻正是这个结构。

两条推论贯穿整个框架：

- **凡可派生的绝不手写**。手写的指针会腐烂——目标挪了、描述过期了；派生指针由机械重建，天然免疫腐烂。这是「一源五投影」的哲学起点。
- **披露的终极目的不是「找得到」，而是「该想起来时想得起来」**。todo 是时间维度指针的显式实例，指向某个未来时刻应被想起的东西；带「何时先读」条件的注入行是主动指针；consumes 在命令触发时把规则带到现场——同一个思想。

## 4. 插件化

架构不做穷举。文件格式与笔记类型不进章程——类型是 frontmatter 字段；结构由各 plugin 自行规定。一 plugin 一目录：manifest 是机器可读的本质；PLUGIN.md 记录设计理由；附带的 audit 脚本可选。plugin 持有一个 territory——哪片路径归谁、写模型是什么——并持有面向外部的字段与纪律。

domain 是核心抽象。wiki 只认内与外；外部 domain 是一份适配器契约，落实为六个问题：外部 territory、落地策略、身份凭证、wiki 侧 territory、写模型、信任模型。落地本质上是写模型的选择：终态资产进 append-only 存储；过程容器拿到完整读写权；真相在别处时用指针。借用 vault 或指针是默认姿态，自立容器是例外。

## 5. 投影

一套 manifest 由机械投影到五处：AGENTS 注入区；check 的检查块；命令 usage 块（按 consumes 排序）；registry 的字段区；deploy 出去的 skill 副本。全部幂等重建，(un)install 时自动同步，在场即注册。没有第二事实源：改契约就是改 manifest，一条命令全部收敛。一个部署出去的实例只带注入区与 skills 即可自足——机制文档活在运行时可见面上，不另写一套会漂移的架构文档。

## 6. 分层与桥

- **素材层 vs 归档层**：过程产物住在 domain workspace——拉取的素材、笔记、批改过的测验都算；蒸馏出的结论住进 wiki。wiki 收的是蒸馏物，不是过程。
- **全局组件 vs domain 组件**：横切服务及其归宿是全局组件——trust、log、todo、calendar、notes、user-profile——它们可以声明桥；domain 组件经 depends 传递地归属某 domain。桥承载校验与声明——必经桥完备、可选桥宽容；披露分布归投影管。
- **采集通道**：消费侧 plugin 可以取最薄形态——零 territory、纯工作流，usage 挂在源侧、在枢纽命令处现场汇总。教学与测验都围绕认知档案闭环。

## 7. 团队转向

2026-10-02，项目从个人使用转为团队项目。协作红线——数据边界、git 纪律、commit 流程——见 AGENTS.md 的「User requirements」一节，其权威永远是 AGENTS.md 本身。开发产物进 git；实例数据永不进。框架是通用产品；真实的课程、成绩、隐私与凭据属于部署实例。

## 8. 谱系与地图

一段极简编年：2026-08 个人 vault 创建；09-08 原型落地，plugin 加命令；09-12 「以用为验」裁决；09-19 至 09-30 domain 化与 connector；10-02 团队转向与治理规则；10-04 认知消费侧确立、机制文档开写。完整流见 [log.md](https://github.com/owfadev/owfa/blob/main/log.md) 与 git 历史。

| 想知道 | 去读 |
|---|---|
| 章程与协作红线 | [AGENTS.md](https://github.com/owfadev/owfa/blob/main/AGENTS.md) |
| 机制总览 | kernel 参考 skill |
| 机制怎么运转 | [zh/mechanics.md](mechanics.md) |
| 日常使用 | [zh/usage.md](usage.md) |
| sandbox 的使用 | [zh/sandbox.md](sandbox.md) |
| 某 plugin 为什么这样设计 | 该 plugin 的 `PLUGIN.md` |
| 研究依据 | `.owfa/docs/research-*.md`（英文，无 zh 镜像） |
| 部署指南 | [zh/deployment.md](deployment.md)（五分钟路径：[zh/quickstart.md](quickstart.md)） |
| 运行历史与现状 | [log.md](https://github.com/owfadev/owfa/blob/main/log.md) |
