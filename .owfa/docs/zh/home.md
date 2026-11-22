# 机器级 substrate：`~/.owfa` — 连接器家目录

> 状态：0.5.x ABI。取代 pre-0.4 的散落目录习惯（`~/.bb-cli`、`~/.sis-cli`、
> `~/.bili-cli`、`~/.config/mail-cli`、`~/.qq-cli` …）。
> 实现：`.owfa/scripts/owfa_home.py`（纯标准库，无依赖）。

一台机器承载多个 OWFA 工作区。连接器的凭据、会话与 spool 属于**机器**，不属于任何单一工作区树——但两个工作区也不能悄悄共用一个状态目录。substrate 同时回答这两个要求。

## 布局

```
~/.owfa/                                   # 机器级 substrate（env: OWFA_HOME）
├── kernel/<X.Y.Z>/                        # 用户级内核多版本（+ current 指针）
├── journal/events.log                     # 机器日志
├── workspaces.yaml                        # 工作区注册表
└── connectors/<name>/
    ├── bindings.json                      # [{id, root, home, bot?, installed_at}]
    └── homes/<id>/                        # 每个绑定一个状态目录（0600/0700）
        └── <component>/                   # 可选：多目录连接器
```

- `<name>` 是**连接器名**（发行物/仓库名：`cuhksz-cli`、`bili-cli`、`mail-cli`、`qq-cli` …），不是工作区自取的标签。
- `<id>` 是人类别名 + 2 字节哈希（`repo-a1b2`）；单工作区机器的单例就是 `default`。
- **组件**：一个有多个状态目录的连接器把它们放在同一家的组件下（`cuhksz-cli` → `bb/`、`sis/`），而不是长出第二个家。`component_dir()` 是访问器，`migrate_legacy_home(..., component="bb")` 把一个旧目录迁进一个组件。

## 解析顺序

```
显式 --root / --home 参数
> OWFA_ROOT 环境变量
> cwd 在 bindings.json 中的反查
> homes/default
```

多绑定机器上匹配不到的工作区仍回落 `homes/default`（降级但健康），但会在 stderr 大声警告——两个未匹配工作区共用 `default` 对排他检查是隐形的。绑定该根或设 `OWFA_ROOT` 消除歧义。

## 连接器 bootstrap ABI

连接器在**导入/运行时**解析状态，绝不用构建期常量。规范 bootstrap（各连接器保持逐字节一致）：

```python
import importlib.util
import os
from pathlib import Path

HELPER_ENV = "OWFA_HOME_HELPER"   # 指向 owfa_home.py 的显式路径


def _candidates():
    out = []
    env = os.environ.get(HELPER_ENV)
    if env:
        out.append(Path(env).expanduser())
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for parent in (start, *start.parents):
            out.append(parent / ".owfa" / "scripts" / "owfa_home.py")
    return out


def load_owfa_home():
    """导入机器级 substrate helper；在工作区之外运行时返回 None。"""
    seen = set()
    for helper in _candidates():
        if helper in seen or not helper.is_file():
            continue
        seen.add(helper)
        spec = importlib.util.spec_from_file_location("owfa_home", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None
```

规则：

1. **不许猜布局。** 所有路径来自 helper（`resolve_home`、`component_dir`、`migrate_legacy_home`）。连接器不得手拼 `~/.owfa/connectors/...`。
2. **回退就是旧目录，而且必须出声。** 找不到 helper（连接器装在工作区外）时继续用旧散落目录，并在 stderr 打一行带迁移命令的提示。helper 出现但状态尚未迁移时同理：只要旧目录还有数据就继续用它（出声、点名 `home migrate`），不得悄悄切到空的 substrate 家。绝不能造出第二个"静默优先"的家。
3. **显式覆盖仍然显式。** 现有各连接器覆盖变量（`BB_CLI_HOME`、`SIS_CLI_HOME` …）优先，语义是"就用这个目录"，属兼容逃生口，不是默认路径。
4. **迁移是显式命令，不是副作用。** `migrate_legacy_home` 只移动不复制，并在旧路径留符号链接，让旧的绝对路径继续可解析。连接器以 `home status` / `home migrate [--dry-run]` 暴露它。

## 交付给连接器

`owfa_home.py` 随通道载荷（`.owfa/scripts/`）发布，落到工作区的方式取决通道：

| 通道 | helper 位置 |
|---|---|
| legacy（树内内核） | 随载荷树复制：`<ws>/.owfa/scripts/owfa_home.py` |
| 用户级内核（0.5.x） | `owfa init` / `owfa adopt` 植入 `<ws>/.owfa/scripts/owfa_home.py`（内核本体在 `$OWFA_HOME/kernel/<ver>/`）；已存在的工作区用幂等的 `owfa plant-helper <ws>` 修复 |

marker 工作区缺 helper 时 `owfa doctor` 失败并点名 `owfa plant-helper`；legacy 的 `owfa upgrade` 按设计拒绝 marker 工作区（M1 防踩），修复路径就是 `plant-helper`。连接器因此只需上面的上溯查找；`OWFA_HOME_HELPER` 留给非常规布局与测试。

## 不变量

1. **一家一绑定生效。** 两个工作区排干同一 spool 是语义错误（`exclusivity_violations`），不是健康警告。
2. **未绑定工作区 = 降级但健康。** 连接器照常应答，什么也不排干；要隔离就显式绑定根。
3. **解绑只脱钩，不删除。** `homes/<id>/` 持有凭据——删除是人的动作，需确认。
4. **陈旧绑定**（工作区根已消失）由 `stale_bindings` 报告，仅在确认后清理。
5. **任何仓库都不存状态。** 家目录是机器级的；仓库可以放连接器代码，永远不放家目录。

## 从 pre-0.4 散落目录迁移

```bash
# 先看
python3 .owfa/scripts/owfa_home.py status cuhksz-cli
# 一个旧目录一次调用；<id> 默认取该根的绑定
python3 .owfa/scripts/owfa_home.py migrate cuhksz-cli --legacy ~/.bb-cli  --component bb
python3 .owfa/scripts/owfa_home.py migrate cuhksz-cli --legacy ~/.sis-cli --component sis
```

同一卷上移动是原子的；留下的符号链接是人的清理项，内核永不删除。连接器发现旧目录且没有 substrate 家时，打印的也是同样两条命令。

## 健康

- `exclusivity_violations(connector)` → 错误级（substrate 里唯一的错误态）。
- `stale_bindings(connector)` → 报告，确认后清理。
- `connector_status(connector)` → 只读视图，供连接器 `home status` 与检查使用：家、组件、绑定、上面两类风险。

## 版本

helper 随内核版本化（`$OWFA_HOME/kernel/<X.Y.Z>/`）。bootstrap 导入的是**工作区实际植入的那份**，所以钉在旧内核上的工作区保留旧 ABI；连接器只可依赖 `component` 落地（0.5.2+）以来存在的函数。新增保持向后兼容；破坏性 ABI 变更需要升内核版本并抬连接器的 `compat` 下限。
