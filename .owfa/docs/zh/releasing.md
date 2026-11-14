# 发布

> 读者：OWFA Core 与各 owfa-* 包的维护者。本页取代旧 distribution.md 的维护者面（装机与升级内容见 [deployment.md](deployment.md)）。文中每一步都与实件核对过——.github/workflows/publish.yml、scripts/verify-release.js、scripts/sync-blessed.sh、bin/owfa.js——不是理想化流程。

## 发布不变量

一次框架发布是五个载体的严格相等：

```
.owfa/VERSION  ==  package.json "version"  ==  git tag vA.B.C  ==  npm owfadev@A.B.C  ==  GitHub Release vA.B.C
```

守门的是 [scripts/verify-release.js](https://github.com/owfadev/owfa/blob/master/scripts/verify-release.js)。它在本机、`npm publish`（prepublishOnly）与 CI 首步各跑一遍，任何漂移都**fail closed**：

- package version 必须与 `.owfa/VERSION` 完全相等（VERSION 载完整 `A.B.C`）；
- CI 中（`GITHUB_REF_TYPE=tag`）tag 必须等于 `v${version}`；
- 包名必须是 `owfa` 或 `owfadev`，且 `bin.owfa` 与 `bin.<pkg.name>` 都指向 `bin/owfa.js`；
- 不得有 `preinstall`/`install`/`postinstall` 脚本；
- 实际 packlist（`npm pack --dry-run --json`）必须含必备载荷——`.owfa/VERSION`、kernel、`payloads/personal/PKG.yaml`、内嵌 suite 母本等——且不得混入开发/本机状态（`test/`、`scripts/`、`.github/`、`__pycache__`、`pending.json`、`kernel-journal.log`、`registry-cache.yaml`、实例 `vault/`/`wiki/`、`.owfa/plugins/core/`、以及 suite 自有命令母本出现在 `.owfa/command/` 下）。

会打破等式的发布在 publish 之前被拒，而不是事后修补。现行版本 0.4.1（tags v0.4.0 与 v0.4.1，均 2026-11-14）。

## 框架发布流程

1. **改动先落地。** 一切经 PR 进 `master`（合并纪律见下文）。不直接 push，不养长命 release 分支。
2. **同步 blessed suite**（见下节），让 `payloads/personal/` 带上本版要内嵌的套件内容。
3. **同一 commit 双载体 bump**：`.owfa/VERSION` 与 `package.json` 的 `"version"`——同一个完整 `A.B.C`，如 `0.4.1` → `0.4.2`。
   ```bash
   node scripts/verify-release.js   # 在工作树上先过一遍门
   node test/smoke.js               # 端到端通道冒烟（init / doctor / upgrade）
   npm pack --dry-run               # 亲眼看一下 tarball
   ```
4. **打 tag `vX.Y.Z`——打之前必须核对 tag 指向的 commit 内容。** 这条纪律是吃了亏写进来的：tag 推错 commit，整条流水线就对着错误内容跑完，而 npm 版本不可变。`git tag` 之前：
   - `git log --oneline -5`——bump commit 是 tip，其后没有混入别的提交；
   - `git show <commit>:package.json | grep version` 与 `git show <commit>:.owfa/VERSION`——即将打 tag 的那个 commit 确实带着新版本号；
   - `git status`——工作树干净，tag 命名的是已提交内容而非工作目录。

   教训的出处：本项目自己的会话史里就有一次没核对目标 commit 内容直接打 tag，错位直到下游才被发现。先核对——tag 是扳机，不是草稿。
   ```bash
   git tag v0.4.2
   git push origin v0.4.2
   ```
5. **tag 驱动流水线**——[publish.yml](https://github.com/owfadev/owfa/blob/master/.github/workflows/publish.yml) 以 `push: tags: v*` 触发，依次执行：
   1. `node scripts/verify-release.js`——release gate（CI 环境下复检 version/tag/packlist）；
   2. `node test/smoke.js`——通道冒烟：对 tarball 跑 init / doctor / upgrade；
   3. `npm publish --provenance --access public`——发布 **owfadev**（依赖仓库 secret `NPM_TOKEN`；`id-token: write` 提供 npm provenance）；
   4. 创建 GitHub Release（`softprops/action-gh-release@v2`，`generate_release_notes: true`，正文链接 `owfadev@<tag>`）。

   GitHub Release 由同一次运行创建，因此 Release 集合永远与 npm 版本集合一致。Release notes 是占位——精心写的说明放 tag/commit message 里。

手动 `npm publish --provenance` 只是 CI 本身坏掉时的兜底；gate 仍会经 `prepublishOnly` 跑一遍。

## 套件同步（payloads/personal/）

默认 `owfa init` 是两阶段自举：先 kernel 树，再从内嵌副本**离线**装 personal suite——`kernel install personal --path payloads/personal`（bin/owfa.js 的 cmdInit）。内嵌副本由 [scripts/sync-blessed.sh](https://github.com/owfadev/owfa/blob/master/scripts/sync-blessed.sh) 刷新：

- 数据源：`owfadev/owfa-personal`，取匹配 `personal-v[0-9]*` 的最新 tag（按版本排序取第一）；
- 下载该 tag 的 tarball，仓库根没有 `PKG.yaml` 即拒收；
- `rm -rf payloads/personal/` 整体替换；`README.md` 归通道所有——套件仓的副本被丢弃，由脚本重写一份通道 README；
- 末尾打印 tag 名与 plugin 母本计数。

时机：框架流程第 2 步之前跑。内嵌副本随框架版本走：suite 发新版，用户要么等下一次框架发布的 tarball，要么 `kernel upgrade personal`——套件仓自己打 tag 并不改变 `owfa init` 装到的东西。注意 gate 的推论：verify-release 发现没有 `payloads/personal/PKG.yaml` 会拒绝发布，所以「忘了同步」是发布失败，而不是发出一个无法自举的 tarball。

## 包发布流程（各 owfa-* 包）

对 suite/domain 包（owfa-personal、owfa-cuhksz、owfa-lark……）流程有意拆成**两个小步、彼此分离**：

1. **在包仓库**：bump `PKG.yaml` 的 `version`（A.B.C），打 tag `<pkg>-vA.B.C`（如 `personal-v0.1.1`），push。tag 模式正是 sync-blessed.sh 与 registry 工具所依赖的。
2. **在 `owfadev/owfa-registry`**：提 PR 更新该包在 `INDEX.yaml` 的行（repo / version / compat / trust / members / summary、needs/provides、commit SHA pin）。

为何分离：registry 不与框架冻结。包的 tag 是「一个仓库在一个 commit 上」的事实；registry 行是把这个事实经人工审核后的晋升（一行一包，好审）。这两步都不会触发 publish.yml——那条 workflow 只属于框架的 npm 通道。强行绑在一起，会让 registry 改动被裹进框架发布 commit，一条坏 INDEX 行也会连坐阻塞或搭车进入框架发布。

## 合并与分支保护纪律

- 一切改动——代码、文档、发布 bump——走 PR：**1 个 approving review** 可合，`enforce_admins` 开启。维护者不豁免于自己定的门，这正是这个开关的意义。
- 因此 `gh pr merge --admin` 被挡是设计行为。确属必须（时间敏感的修复、没有第二个醒着的 reviewer）时，标准动作是：
  1. 经 API 暂时下调保护——`gh api -X PUT repos/owfadev/owfa/branches/master/protection`，只动 `enforce_admins` 这一个开关（或在仓库设置里精确改这一处）；
  2. 合并；
  3. **立即精确恢复原保护状态**，并在 PR/commit 轨迹里说明。

  例外是那次暂停，不是新常态；保护挂一夜没开回来就算事故。
- 发布 bump 的 PR 与普通 PR 同规——runbook 说的「同一 commit」指两个版本文件一起动，不是免审。

## npm 命名现状（一段话）

`owfa` 被 npm 的名称相似性策略冻结（太近 `ow`/`ora`），`npx owfa` 不存在，一切安装示例必须写 `npx owfadev`。**`owfadev` 是现实包名**（gate 仍接受 `owfa`，只为冻结解除的那天留门）；一个包、两个 bin——`owfa` 与 `owfadev`——verify-release 两者都强制。详见 [naming.md](naming.md)。
