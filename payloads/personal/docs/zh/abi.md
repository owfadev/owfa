# vaultwiki 协议 ABI——寻址、词汇、精度

> 契约面：`proto_query.py`（包根，pipeline.py 先例）。信封与语义由框架 ABI 规范
> （abi-spec v2 §2）定义；本页持有协议主权部分：寻址规则、kind 词汇、recent 的
> op 精度，以及错误信封速览。

## 寻址（addr）

`addr` = **wiki 全名**：页面在 `wiki/` 下的路径去掉尾部 `.md`
（与 `[[...]]` 链接语法同文法——见 link 插件）。示例：
`notes/idea`、`vault/a.pdf`（vault 资产的 md 代理）、`sessions/2026-11-15-topic`。
地址区分大小写，且绝不在此规则之外另行发明——不存在中间寻址层。

`wiki/tmp/` **不在 ABI 面上**（tmp 插件对派生层不可见的语义）：草稿既不被
list、不被 search，也不进 recent；对 `wiki/tmp/` 地址做 `get` 得到
`not_found`。`get` 也从不对存在性撒谎：存在但无法按 UTF-8 解码的页面
（listing 遍历会跳过）依然返回——只读，用替换字符解码。

## kind 词汇

`kind` = 页面 frontmatter 的 `type` 字段（开放词汇——原生笔记默认值见 notes
插件；域插件自带其类型）。无 `type` 的页面上报空串。`list --kind K` 按全等
过滤；未知 kind 返回**空结果而非报错**（ABI 冒烟测试依赖此行为）。

## search 语义

`search <expr>`：全名**前缀**匹配（`notes/` 命中 `wiki/notes/` 下全部页面）
或页面正文（不含 frontmatter）的**子串**匹配。匹配**区分大小写**。仅纯子串
——无正则、无操作符。

## recent：op 精度（尽力声明）

窗口 = `--window <N>d|m`（默认 7d；一个月按 30 天计——扫描窗口，不是日历
承诺）。收录以 **mtime 落入窗口**为准。`op`：

- `create`——仅当窗口内 `wiki/log.md` 或 `wiki/hot.md` 的一行带日期记录
  （全名或末段）伴随创建动词（create/created/新建/建立/创设）提到该页面。
- `update`——窗口**之前**的 log/hot 提及证明页面早已存在，故窗口内的触碰是
  更新。
- `unknown`——两个方向都无证据（常见情形；仅 mtime 无法判定）。

已知 mtime 扰动源：`git checkout`/切分支与整树拷贝会批量改写 mtime——这类
窗口会出现虚假的 `update`/`unknown` 条目。绝不从年轻 mtime 猜测创建
（不谎报 `create`）。

## 错误信封

查询级失败以 **0** 退出并带 `{"ok": false, "error_code": ..., "message": ...}`；
只有进程崩溃才非零退出。

| error_code | 何时 |
|---|---|
| `not_found` | `get` 一个无页面的地址，或 `wiki/tmp/` 之下的地址 |
| `bad_request` | 参数缺失/非法（`--window` 非法、缺 `<addr>`/`<expr>`） |
| `unsupported_semantic` | 首参数不是 list/get/search/recent 之一 |
| `internal` | 本包无法服务该查询（如 PKG.yaml 不可读） |

每一条目中的 `proto_ver` 从本包 `PKG.yaml` 的 `version` 实时读取。
