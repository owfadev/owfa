# Docs map — what to read when

> The routing table for `.owfa/docs/` (framework) and package-repo docs. The entry index for agents; skills point here, the documents stay the source of truth.

| Situation | Read |
|---|---|
| User reports dissatisfaction with agent behavior; behavior self-audit | [agent-behavior.md](agent-behavior.md) — feedback handling (consent gate) → routing → the seven-step standard |
| Filing feedback — which repo owns it | [agent-behavior.md](agent-behavior.md) §Routing |
| How packages / install / upgrade / migrations work (design + decision ledger) | [packages.md](packages.md) |
| Deploying an instance; components (CLI/Core/kernel); channels; packages; upgrades; troubleshooting | [deployment.md](deployment.md) |
| Five-minute install path | [quickstart.md](quickstart.md) |
| Installing/upgrading the framework body; npm channel; release runbook | [distribution.md](distribution.md) |
| The name: OWFA expansion, two names two jobs, collision policy | [naming.md](naming.md) |
| Converting a legacy (pre-split flat) instance to the package era | [conversion.md](conversion.md) — the eight-step drill walked on a real instance |
| Instance git usage (snapshots, red lines, recovery) | the instance-git plugin (personal suite member; canonical repo [owfa-personal](https://github.com/owfadev/owfa-personal), embedded copy at `payloads/personal/instance-git/`) |
| Framework mechanics: projections, bridges, injection, inject tiers | [mechanics.md](mechanics.md) |
| (Un)install history, package lifecycle | [mechanics.md](mechanics.md) §7 + [packages.md](packages.md) |
| Third-party view: develop → publish → install → update → uninstall; name governance | [plugin-lifecycle.md](plugin-lifecycle.md) |
| Experiments: sandbox or local | [sandbox.md](sandbox.md) |
| Development rules, commit flow, template + instance workflow | [CONTRIBUTING.md](../../CONTRIBUTING.md) — template-repo root (an instance reads it there, never keeps a copy) |
| Day-to-day usage loops | [usage.md](usage.md) |
| What the framework is, intro | [intro.md](intro.md) |
| Package-side plugin docs (bb family, lark family, …) | the owning `owfa-*` repo's plugin masters |
| AGENTS.md seed / log seed examples | [agents-example.md](agents-example.md), [log-example.md](log-example.md) |
