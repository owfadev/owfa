<!-- docs-lint: historical — narrates the 0.3→0.4 conversion; paths describe layouts of that era -->
# 转换：0.3 旧实例 → 0.4 包时代

> 读者：现有 OWFA 0.3 实例的主人——框架本体还在 `.meta/`，或已是 0.4 目录形状但 core plugin仍长在框架树里——想在不触碰实例数据的前提下升到 v0.4。全新安装不需要本页：`npx owfadev init` 直接落地拆分后的布局。已跟上当前版本的实例，常规升级机制见 [deployment.md](deployment.md)。

## 哪些实例需要转换

两种 pre-split 形态，一次 `upgrade` 全部处理：

- **`.meta/` 布局** —— 框架树在 `.meta/` 下（无 `.owfa/VERSION` 但能读到版本文件即为该形态）。
- **in-tree core** —— 存在 `.owfa/plugins/core/` 目录。v0.4 起发布通道不再随树携带任何plugin；这批母本已是实例状态，转换时被收编为 `personal` suite 包。

两条都不命中（无 `.meta/`、无 `plugins/core/`）的实例，`upgrade` 只是普通框架刷新，见 [deployment.md](deployment.md)。

## 一条命令

```bash
npx owfadev upgrade
```

写 `npx owfadev`，不要写 `npx owfa` —— `owfa` 这个 npm 名被相似性策略冻结，`npx owfa` 不可用（包本身同时暴露 `owfa` 与 `owfadev` 两个 bin，已全局装过的 `owfa upgrade` 继续可用）。

常用旗标：`--check`（只读演练）、`--backup`（把换下的树备份到 `.owfa-backup/`）、`--force`。

## 背后的流程分解

1. **框架换树，旧树停入 attic。** 旧框架树（`.meta/` 或 `.owfa/`）被整体改名为 `.owfa-migrate/replace/`，通道的新树拷入，包自有状态按差集搬回（包命令母本、非框架 skills、kernel状态文件）。这一步失败会回滚——停入的旧树绝不会被隐式丢弃。
2. **core 母本的 attic 救援。** 若停入的旧树带 `.owfa/plugins/core/` 而新树不再携带，这批母本就是唯一副本——包括你所有**未入 git 的 core 本地改动**。它们在 attic 被删除前先移到 `.owfa-migrate/convert/core/`。
3. **staging 出 `personal` 包。** 被救援的母本拷入 `.owfa-migrate/convert/personal/`，manifest 里 0.3 时代的旧命令 id（`map`、`save`、`profile`……）改写为 v0.4 的 `owfa-*` 后继名，suite 的命令母本随通道内嵌的 blessed 副本一并带上，再合成一份 `PKG.yaml`（`id: personal`、`kind: suite`，skeleton 与 uninstall anchors 沿袭 pre-0.4 通道契约）。
4. **安装。** `kernel install personal --path .owfa-migrate/convert/personal --yes` —— 这里的 `--yes` 是对通道自己昔日 payload 的机械收编，不是信任决定。
5. **收敛。** 创建（或自愈）`.meta` → `.owfa` 布局 shim，0.3 时代的绝对路径在 0.5 退役前继续可解析；随后跑 `kernel all`：validate、inject、registry、deploy。

产物是一个 **rootless suite**：`kind: suite` 完全跳过kernel的 family-root/闭包法——没有合成根plugin，也没有合成的 `personal` 依赖边。转换出的包与正式仓 `owfa-personal` 的形状一致（21 个成员、无根），之后可经 `kernel upgrade personal` 正常替换。

> **⚠ 重跑失败的转换前必读**
>
> 断点续传**按设计就是复用**：救援出的母本 `.owfa-migrate/convert/core/` 有意跨次保留（转换从它续跑），staging 目录同样被复用——重跑是往已存在的 `.owfa-migrate/convert/personal/` 里**叠加拷贝**，不会先清空。
>
> **`kernel install` 一步失败后，重跑前必须先删掉旧 staging：**
>
> ```bash
> rm -rf .owfa-migrate/convert/personal
> ```
>
> 否则重跑会在旧 staging 之上安装，收敛出两次尝试的脏混合物——两次运行的plugin母本、manifest、投影搅在一起。这不是理论风险：真实事故里，一个被转换的实例因此注入预算溢出，排查了两轮才追到复用的 staging 目录。与之相反，`convert/core/` 的救援存留是安全且有意为之的。

## 转换后自检

```bash
python3 .owfa/scripts/owfa_kernel.py validate   # 全绿
npx owfadev doctor                              # ok
```

再确认**实例数据原位不动**：换树只替换框架树（`.owfa/`、`.agents/skills/`）——`wiki/` 页面、`vault/` 资产、各 domain 数据目录、connectors、`AGENTS.md`、`.gitignore` 一概不碰。抽查几页 wiki 和资产：应当逐字节原样在位。随后一次提交收尾事务（`git add -A && git commit`）；跑 `upgrade` **之前**也先打一个基线提交，那是你的回滚锚点。

若 0.4 之前实例 git 跟踪过 `.meta/`，一次性清一遍：`git rm -r --cached .meta`（upgrade 的输出会提醒）。

## 手动逃生口

若机械路径不合适（core 改动太多、不信任自动转换）：`npx owfadev init` 一个全新工作区（两阶段：kernel自举，再离线安装内嵌 `personal` suite），然后手工把数据区（`vault/`、`wiki/`、domain 数据、connectors）搬过去，跑 `kernel all`。完整流程——组件、通道、首跑核验——见 [deployment.md](deployment.md)。

## 旧 migrations 页面的去向

pre-split 的 `migrations/init.md`（手动八步转换走查与手动首跑配方）已被取代：它描述的流程如今由 `npx owfadev upgrade` / `init` 机械完成，部署侧指引归 [deployment.md](deployment.md)。唯一未覆盖的是 **git 通道手动安装**——从模板仓库拷 `.owfa/` + `.agents/skills/` 而不走 npm——即 deployment.md 通道表里的 git 通道一行。
