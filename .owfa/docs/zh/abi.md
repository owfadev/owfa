# 协议 ABI

> 读者：协议包作者、bridge/connector 作者，以及任何在 OWFA 实例上做跨协议检索的人。本页固定**调用契约**（abi-spec §2）与 **compat 区间语法**（abi-spec §4），自框架 0.4.6 起实装。内核只做在位校验（R11），不实现任何检索——机制归各协议包。英文正本在[上一级目录](../abi.md)。

## 1. ABI 是什么

ABI 是协议对外**唯一合法访问面**：连接器、bridge 与（将来的）联邦检索不许读他协议内部结构，只许走四语义。机制归协议包（实现随包携带），内核只定**调用契约**与**在位校验**——通用适配器类法则的又一次应用：内核（标准件）不预设结构，检索的实实现由协议包携带。

执行通道是**包根脚本 `proto_query.py`**（pipeline.py 先例：包根脚本整树随包装入、按路径调用，绕过 command 绑定系统——那是 agent 技能面，不是机器调用面）。`command/proto-query` 技能是可选便利层，不属于合格线。

## 2. 四语义

统一入口：`proto_query.py <semantic> [args]`。**JSON-lines 输出是唯一契约面**；`--pretty` 是尽力而为的便利层，不属契约。

| 语义 | 输入 | 输出（归一化元组） | 约束 |
|---|---|---|---|
| `list` | `--kind <k>`（可选过滤；**参数名归一化，词汇归协议主权**） | 每项 `{addr, title, kind, mtime}` | addr = 协议**原生编址**，永不发明中间编址；未知 kind → 空结果不报错（smoke 依赖此语义） |
| `get` | `<addr>` | `{addr, title, kind, mtime, content}` | content = 原文全文，不截断；只读，绝不触发写 |
| `search` | `<expr>`（协议原生语法） | 同 list 元组 | 语义随协议；协议须在 `abi:` 块中写一句检索语义说明 |
| `recent` | `--window <N><d\|m>`（正整数 + 单位，默认 7d；非法值 → `bad_request`） | `{addr, title, kind, mtime, op}` | op ∈ `create\|update\|unknown`，尽力而为；协议在自己的 abi.md 中声明判定精度 |

**归一化的边界**：只归一化信封与字段名及 `--kind` / `--window` 两个参数名；addr 语法、search 语法、kind 词汇是协议主权。

**共同信封**：每条输出携带 `protocol`（协议 id）+ `proto_ver`（= **PKG.yaml 的 `version`**，单一取值源；org 能力位的 vN 是无关的能力租约词汇）。批量结果 `{ok, semantic, count, items}`。

**错误信封**：查询级失败 **exit 0** + `{ok: false, error_code, message}`，error_code ∈ `not_found / bad_request / unsupported_semantic / internal`；exit ≠ 0 表示命令本身死了——消费方（如 bridge stale 三步）以 `ok:false` 与 exit 码分流「查询失败」与「命令死了」。

## 3. compat：唯一版本词汇与区间语法

`proto_ver` = PKG.yaml `version`（X.Y.Z）。破坏性判定：major ≥ 1 时 **major 变更即破坏性推定**；0.x 期间 **minor 兼作 major**（0.1 → 0.2 即破坏性推定；patch 永不破坏）。信封字段只增不删不改语义，删改即破坏性变更。

区间语法（bridge 连接声明 / 落位模板版本锚 / 注册表引用——该词汇只用于 bridge 三处；PKG `compat` 字段维持 `>= X.Y` 单下限不动）：

```
interval   := comparator { " " comparator }        ; 空格分隔 = AND
comparator := op version                            ; op 紧贴 version，无空格
op         := ">=" | "<=" | ">" | "<" | "="
version    := major [ "." minor [ "." patch ] ]     ; 数字段
```

缺位语义（逐 op）：

| op | 缺位解释 | 示例 |
|---|---|---|
| `>=` / `>` / `<=` / `<` | 取该精度**最低值**（1 = 1.0.0；2.0 = 2.0.0） | `<2.0` ⇔ 排除 2.0.0 及以上；`>=0.8` ⇔ 含 0.8.0 |
| `=` | **前缀匹配** | `=1.2` ⇔ 1.2.* |

canonical 示例：`>=1.0 <2.0`、`=1.2.3`、`>=0.8`。模板版本锚可窄于声明的 compat，不得宽于。Python 侧 `compat_match(version, interval)`（`owfa_kernel.py`）是 interval 的**唯一解析**——bridge、模板校验、注册表引用一律调它；禁止第二套 Python 实现。

## 4. R11：合格线（两态校验）

`kind: protocol` 包在 PKG.yaml 中声明：

```yaml
abi:
  semantics: [list, get, search, recent]   # 恰好四者
  search_lang: "全名前缀 + grep 子串"       # 一句检索语义说明（给人看）
  addr_doc: docs/abi.md                    # 编址规则文档指针（可选但建议）
```

自 0.4.6 起两态校验：

- **块缺位** → 0.4.x 全周期 warning（存量协议包与未升级工作区不受影响）；**0.5.0 起升 error**——无 grandfather 条款。
- **块在位但** semantics 不齐 / 包根 `proto_query.py` 缺失 / 块字段非法 → **error**（写了就是承诺，写错即错）。

内核 `audit` 另对已装且声明了 abi 块的 `kind:protocol` 包跑 **ABI smoke**：`proto_query.py list --kind __abi_smoke`，期待 exit 0（空结果合法——未知 kind 永不报错）。不可运行或超时 = check 失败项。

## 5. 各协议交付什么

实现归包：包根 `proto_query.py`（自包含——协议包不得假设他协议的机器在位）、abi.md（编址规则与 recent 的 op 判定精度声明）、包内最小自测，以及上面的 `abi:` 块。框架侧（本页）只交付契约与校验。
