# 使用沙盒

> 读者：需要拿真实数据做实验的团队成员。沙盒治理红线的权威来源是 AGENTS.md 的「User requirements」一节；本文只讲操作。成文于 2026-10-04；2026-10-13 更新——仓内沙盒脱离 git 跟踪（owner 裁定），仅存本地；2026-11-14 更新——建法与镜像同步行为对齐 v0.4 两阶段树。

## 它是什么

test-repo 是住在开发仓库内部的草稿部署实例——**自 2026-10-13 起仅存本地、不入 git**：框架的新克隆不带它的任何内容，它内部的一切（镜像在内）都进不了历史。它的 `.owfa/` 与 `.agents/` 树是框架的镜像，批次收尾时从根侧整树重拷；其余是沙盒自己的数据区。沙盒内部对项目无感知：在沙盒根打开的会话读的是沙盒自己的 AGENTS.md 与 skills。

## 启用

新克隆里沙盒未初始化。v0.4 拆分后框架树只带 kernel——没有 plugin——所以手工建法与 `owfa init` 同为两阶段（kernel 自举，再装内嵌 personal 套件——第②阶段即协议选择，默认 `vaultwiki`；给别的协议做沙盒就装那个协议）：

1. 在框架根 `mkdir test-repo`
2. 拷入框架树：根侧的 `.owfa/` 与 `.agents/`
3. 在内部建 `AGENTS.md` 壳：一段身份描述加一段布局描述，插入注入区标记块——从 `<!-- wiki-inject:start -->` 到 `<!-- wiki-inject:end -->`，保留区头与说明行（见 [agents-example.md](agents-example.md)）
4. 在沙盒根离线安装内嵌 personal 套件并收敛：

```bash
python3 .owfa/scripts/owfa_kernel.py install personal --path <框架根>/payloads/personal
python3 .owfa/scripts/owfa_kernel.py all
```

套件 `PKG.yaml` 的 `skeleton:` 声明会机械地建出四个实例目录（`vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/`）——不要手工 mkdir；kernel 不再硬编码任何实例布局。validate 全绿即成可用实例。

## 跑实验

在沙盒根打开 agent 会话，照常用命令：map、save、query、check 与课程全家都可用。数据区自然生长——wiki 派生页首跑即建，课程数据落 bb 侧。一切产物与衍生品都按本地临时材料对待。

## 红线

此处摘要三条；权威在 AGENTS.md：

- `test-repo/` 内部的一切永不 commit——整树 gitignore；镜像、数据、派生页，全部
- 镜像更新只走根侧重拷。沙盒侧可以为框架实验改镜像文件，但下次重拷会覆盖；框架级改动应在根侧分支上做，走评审合并
- 结论经对话报告或文档流转，绝不经沙盒档案

## 收尾与重置

实验数据去留随你；重置 = 删除镜像树之外的一切——`bb/`、`wiki/`、镜像内的 `__pycache__`——然后把「启用」再走一遍，得到干净沙盒。

## 镜像同步

根侧批次收尾时发生重拷。想自己触发：删掉沙盒两个镜像树，从根侧整树拷入，再跑一次 kernel 收敛。v0.4 树的 deploy 行为：根侧**没有 `connectors/`**（connector 随各包安装、按实例到达），所以全新重拷后 deploy 只从 `.owfa/command/` 部署六个框架命令 skill，**不报 connector 孤儿**——已在框架树上跑 `kernel deploy` 验证（"all in sync"，零 plugin）。`[warning] orphan copy .agents/skills/<name>/` 只在某个 skill 副本的母本在两侧都消失时出现——典型是被移除的包未做沙盒侧清理的残留——且仅报告：删除权在人。

## 沙盒 vs 本地

章程与使用指南都说「实验落沙盒或本地」。两者是同一件事的两个尺度：test-repo 是模板检出的就地共享沙盒；在别处开自己的本地沙盒就是一次手工部署（见 [deployment.md](deployment.md)）——克隆（或拷两棵树）、写壳、装内嵌 personal 套件（其 `skeleton:` 建目录）、收敛——目标 vault 自选。选择标准：需要与手头模板镜像保持同步用 test-repo；长期私用或接近真实 vault 的场景另部署。
