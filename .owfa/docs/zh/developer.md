# 开发者指南：写插件与包

读者：任何想为 OWFA 生态贡献 plugin 或 package 的人。

插件落在哪里由它的 `depends` 决定，而非个人口味——而且无论落在哪里，开发循环都一样：clone → 分支 → 修改 → `--path` 装进沙箱 → PR。机制细节（PKG.yaml 字段、能力机制、通道与信任、装卸契约、版本、registry 行格式）都在 [packages.md](packages.md)——本页只有落位表、开发循环与发现机制。

## 你的插件落在哪里？

| 你的插件是…… | 落在…… | 信任门 |
|---|---|---|
| **domain 成员**（depends 链到达某个 domain 根，如 bb 家族） | 该 domain 包的仓库——往那里提 PR。没有选择余地：家族闭包会机械地认领你（`PKG.members` 必须包含你，否则 validate 报错） | 包维护者 |
| 一个独立的**新 domain** | 你自己的仓库作为一个包（`PKG.yaml`，见 [packages.md](packages.md)）+ 向 [registry](https://github.com/owfadev/owfa-registry) 提一行 PR | registry PR——人工评审门（inject 文本与 connector 是安全面） |
| **横切 / 非 domain**（全局件） | blessed 套件包仓库（**owfadev/owfa-personal**）——往那里提 PR | 所有者评审（章程级，门槛最高） |

单个插件从不裸发货——package 才是分发单元。孤插件就是单成员包（十几行 PKG.yaml，参见 owfa-email / owfa-bili / owfa-project）。

## 开发循环

1. **clone 目标仓库**（domain 工作克隆包仓库，core 克隆框架）并开分支：`module/topic`
2. **修改**——按既有模式写 manifest（PLUGIN.yaml）+ PLUGIN.md + skills；版本沿 changelog 前进
3. **没有 monorepo 也照样集成测试**：在沙箱（或任意实例）里
   ```
   cd test-repo
   python3 .owfa/scripts/owfa_kernel.py install <pkg> --path /path/to/your/clone
   python3 .owfa/scripts/owfa_kernel.py validate --scope <pkg>
   ```
   `--path` 安装本地 clone（通道 C）；随意迭代——卸了重装，或直接重拷
4. **PR**——一次一事一提交，`模块: 概述`；按 [CONTRIBUTING](https://github.com/owfadev/owfa/blob/master/CONTRIBUTING.md) 自检（框架根：`validate`；沙箱：`all`）
5. **发布**（包仓库）：bump PKG.yaml `version`，打 tag `<pkg>-vA.B.C`，然后提 registry 行 PR——刻意分成两个小步：registry 永不与框架冻结在一起

## 发现机制：人们（和 agent）怎么找到你的作品

- **收录之前**：你的仓库已经可装（`kernel install <owner>/<repo> --yes`，trust: unknown），且经 GitHub topics 可被发现——给仓库打上 `owfa-package` topic
- **registry PR 之后**：进入 `kernel list-remote`（agent 侧界面），安装免 `--yes`，trust: reviewed-3rd-party
- **summary 写给 agent 看**——registry 的 `summary` 行与你 SKILL.md 的 `description` 字段才是 agent 实际匹配的东西；含混的 summary 等于不可发现
