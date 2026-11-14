# 机器基座：`~/.owfa` —— connector 归宿与工作区绑定

> v0.4 工单 #56（B1–B3）。一台机器可以承载多个 OWFA 工作区；connector
> 状态在它们之间绝不能相撞。这是每个 OWFA connector 通过 import
> `.owfa/scripts/owfa_home.py` 继承的共享契约——任何 connector 不得
> 自行发明布局。

## 布局

```
~/.owfa/                                  # 机器基座（环境变量 OWFA_HOME）
└── connectors/<name>/
    ├── bindings.json                     # registry：[{id, root, home, bot?, installed_at}]
    └── homes/<id>/                       # 每个绑定一个状态目录——凭据、
                                           # spool、日志；0600/0700，永不进任何仓库
```

- `<id>` = 人类别名 + 2 字节哈希（`repo-a1b2`）；单例情形就叫
  `default`。
- home 是**机器全局、非按实例**的：connector 不读工作区；只有它的绑定
  记录哪个工作区在消费它。

## 解析顺序

`--root/--home` 参数 → `OWFA_ROOT` 环境变量 → cwd 在 registry 里反查
→ `homes/default`（单工作区机器：零配置）。

在有**两个及以上绑定**的机器上，哪个都不匹配的工作区仍会落到
`homes/default`（降级但健康），但会发出响亮的 stderr 警告：default 在
那里未注册，两个未匹配的工作区共用它时 `exclusivity_violations` 会看
不见。要么显式绑定 root、要么设置 `OWFA_ROOT`，消掉这个歧义。

## 不变量

1. **一个 home，一个活跃绑定。** 两个工作区消费同一个 spool 是语义错误
   （`exclusivity_violations` → error，基座中唯一的 error 级健康态）。
2. **未绑定工作区 = 降级但健康**（domain check 里的 warning）：
   domain 已装、skill 带指引应答、没有谁在消费。
3. **解绑是摘除，不是删除。** `homes/<id>/` 装着凭据与 spool 数据——
   删除是人的动作，须确认。
4. **过期绑定**（工作区 root 已消失）会被报告，经确认后清理——与 tmp
   区 stale_after 同一节奏。

## 从 0.4 前散落 home 迁移

`owfa_home.migrate_legacy_home("qq-cli", "~/.qq-cli")` 把旧目录**移动**
进 `homes/<id>`（移动、绝不复制——凭据不得同时存在于两处），并在旧路径
留一个 symlink 让旧的绝对引用继续可解析；该 symlink 是 0.5 的清理项。
按 connector 版本门控：首次运行发现自己旧 home 的 connector 会提议迁移，
而不是悄悄创建第二个 home。

## Harness 范围

connector manifest（PKG.yaml `connectors[]`）可为状态在本基座之外的
外部 connector 声明 `home:`（声明，不迁移）。registry 逐包镜像
`harness:` —— `universal` connector 是一等公民；被 harness 锁定的如实
注册，健康检查把不匹配暴露出来。
