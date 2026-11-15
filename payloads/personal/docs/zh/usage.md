# 使用指南

> 读者：安装完成之后的 vault 主人——`owfa init` 的下一步——以及想理解协作形态的人。命令细节的权威披露在各 `.agents/skills/` 下的 SKILL.md；本文讲的是工作流的串联：单条命令如何连成循环。示例统一用套件包内的 pipeline 路径 `.owfa/plugins/domains/personal/pipeline.py`（框架树里的弃用宿主副本 `.owfa/scripts/pipeline.py` 保留至 0.5.0）。

> 安装与部署见框架仓 [quickstart](https://github.com/owfadev/owfa/blob/master/.owfa/docs/quickstart.md) / [deployment](https://github.com/owfadev/owfa/blob/master/.owfa/docs/deployment.md)。

## 循环一：vault 日常经营

通用循环；每天几分钟。

**输入**：把文件丢进 `vault/`，对 agent 说「map」——得到带 SHA-256 与元数据的 `wiki/vault/` 代理页；index、tags、hot 自动更新。当一段对话产出值得留存的洞见，说「save」，它落为 `wiki/notes/` 的原生页——`type` 做分类，`tags` 做归组。珍贵草稿及时从 `wiki/tmp/` 提升出去；提升即删除草稿。

**检索**：说「query」。agent 先读 hot 与 index，再综合作答；答案带 wikilink 引用，可以一路追下去。index 的逐级下钻本身就是一个指针结构。

**委托与提醒**：委托给 agent 的任务落进 `wiki/todo.md`；一条 = 触发条件加一句话。新会话开始时 agent 先读这页；到期项主动提出；完成即结清——历史进 log。

**健康**：定期说「check」做机械与语义的全面审计。随时说「profile」，把关于你的新认知收敛进 `wiki/profile.md`：断言带证据，偏好会过期。个性化决策之前——称呼、文风——agent 先读它。

一句话纪律：wiki 收蒸馏物，不收过程。过程产物归 vault、tmp 与各 domain 工作区；只有沉淀下来的结论进 notes。

## 循环二：课程学习

bb domain 循环（本协议之上的一个域示例）；一个学期的节奏。需要 **owfa-cuhksz** 包——经 `kernel install` 另行安装，随之带来 **cuhksz-cli** connector（聚合 bb | sis；旧的 bb-cli / sis-cli 包装保留兼容）。

**课程接入**，每学期开学一次：cuhksz-cli 拉取，凭据只存本机；`cuhksz/bb/<term>/<course>/` 工作区落地——文档类内容全量，媒体走指针；bb-map 把 wiki 侧 territory 投影为四个桶：info 课程信息、courseware 知识点、assessments 作业档案、attachments 附件；domain 根的 inbox.md 摘要页——公告蒸馏加临近截止加未交提醒，由两个来源合成。

**每日**、每周：

1. 读 inbox，取公告与截止日的近窗视图
2. 「讲解」「出题 / 考我」bb-teach 与 bb-quiz：哪里不懂问哪里，或者给个范围自测。agent 先读认知档案；未知的讲透，已知的略过。重要讲解以 ai notes 落进 notes/；测验批改经你确认回流认知档案
3. 「认知档案」bb-track：读档案与缺口分析。知识点全集减去已锚定集即缺口；答错可回溯到 assessments 复盘

**闭环**：teach 讲解，ai notes 作弱证据；track 收敛；quiz 按档案出题；批改作为机器证据回流；下一轮 teach 对着新档案调整。素材在 bb 侧——笔记、试卷、批改过程；结论在 wiki 侧——认知读数。学期结束，一切随 term_status 冻结。

## 循环三：协作开发

改包或改框架的标准流程——细节见实例 AGENTS.md 的「commit flow」：从最新 master 切分支；动 manifest 或命令前先读 `wiki/log.md` 对齐现状与下一步；`kernel all` 全绿；小步 commit，`module: summary` 格式；push 开 PR；评审合并。开发产物进 git；实例数据永不进。

**装新 domain**，把外部来源接进来：`kernel list-remote` 看目录；`kernel install <pkg> --yes` 一步落地——plugin、命令与仓内 connector 随包到达（connector 随各包分发：**owfa-cuhksz** 带 cuhksz-cli；**owfa-email** 带 mail-cli；**owfa-bili** 带 bili-cli；lark domain 声明的是外部 lark-cli，不随框架分发）。凭据留在本机；首次使用先读 connector skill 披露。

**实验**一律落沙盒或本地；沙盒实验内容永不进历史——结论经对话报告或文档流转。

## 节律

- calendar 来源经部署侧 cron 无人值守会话每日刷新；bb 数据 TTL 默认 1 天，agent 即同步器——过期意味着现在就拉
- 课程开学接、期末冻；每周一次 check 加缺口分析；其余按使用触发。命令即自然语言触发——没有仪式
