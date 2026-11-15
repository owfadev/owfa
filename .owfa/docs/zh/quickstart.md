# 快速上手

读者：想在五分钟内拥有一个能用的 OWFA workspace 的新用户。

## 前提

- **Node 16.7+** —— 安装器 CLI 是 Node 的（`npx owfadev`）。
- **Python 3.9+** —— kernel是纯标准库，不需要 pip，也不需要 venv。
- **一个会读 `AGENTS.md` 与 `.agents/skills/` 的 agent**（Claude Code、Cursor、dsh、Zcode…）。

## 五分钟路径

```bash
npx owfadev init my-workspace
cd my-workspace
```

npm 包名是 **`owfadev`**（`owfa` 这个名字被 npm 相似性策略冻结，`npx owfa` 不可用——一律写 `npx owfadev`）。

`init` 是两阶段的：第 ① 阶段自举 kernel（`.owfa/` 树加 `AGENTS.md` 种子——加法式，已有内容不动），第 ② 阶段离线安装内嵌的 personal 套件（`kernel install personal --path payloads/personal`），由套件的 `skeleton:` 声明创建 workspace 目录（`vault/`、`wiki/notes/`、`wiki/sessions/`、`wiki/vault/`）。

然后在 workspace 根目录开一个 agent 会话，随便丢一个文件进 `vault/`，说一句 **"owfa-map"**——agent 会把这个资产登记成 wiki 代理页（SHA-256、镜像路径、index/hot/log 联动）。首次运行同时会建好派生页。再跟一句 "owfa-check" 审计实例健康状态。

至此 workspace 已经活了。日常用法见默认协议的[使用指南](https://github.com/owfadev/owfa-personal/blob/master/docs/zh/usage.md)。

## 手动部署

想走手动路径（git clone、离线、或嵌入既有 vault）？一句话：拷贝框架树、装套件、写 `AGENTS.md` 外壳、收敛投影——逐步操作见 [deployment.md](deployment.md)。
