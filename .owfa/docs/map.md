# Docs map — what to read when

> The routing table for `.owfa/docs/` (framework) and package-repo docs. The entry index for agents; skills point here, the documents stay the source of truth.

| Situation | Read |
|---|---|
| User reports dissatisfaction with agent behavior; behavior self-audit | [agent-behavior.md](agent-behavior.md) — feedback handling (consent gate) → routing → the seven-step standard |
| Filing feedback — which repo owns it | [agent-behavior.md](agent-behavior.md) §Routing |
| How packages / install / upgrade / migrations work (design + decision ledger) | [packages.md](packages.md) |
| Deploying an instance; components (CLI/Core/kernel); channels; packages; upgrades; troubleshooting | [deployment.md](deployment.md) |
| Five-minute install path | [quickstart.md](quickstart.md) |
| Installing/upgrading the framework body; npm channel | [deployment.md](deployment.md) |
| Release runbook (version invariant, publish pipeline, merge discipline) | [releasing.md](releasing.md) |
| The name: OWFA expansion, two names two jobs, collision policy | [naming.md](naming.md) |
| Converting a legacy (pre-split flat) instance to the package era | [conversion.md](conversion.md) — one command (`npx owfadev upgrade`), with the staging-resume warning |
| Instance git usage (snapshots, red lines, recovery) | the instance-git plugin (personal suite member; canonical repo [owfa-personal](https://github.com/owfadev/owfa-personal), embedded copy at `payloads/personal/instance-git/`) |
| Kernel mechanics: packages, capabilities, projections, injection, lifecycle | [kernel.md](kernel.md) |
| (Un)install history, package lifecycle | [kernel.md](kernel.md) §7 + [packages.md](packages.md) |
| Third-party view: develop → publish → install → update → uninstall; name governance | [packages.md](packages.md) (consolidated) + [developer.md](developer.md) |
| Experiments: sandbox or local | [sandbox.md](sandbox.md) |
| Development rules, commit flow, template + instance workflow | [CONTRIBUTING.md](../../CONTRIBUTING.md) — template-repo root (an instance reads it there, never keeps a copy) |
| Day-to-day usage loops (default protocol) | [owfa-personal: usage.md](https://github.com/owfadev/owfa-personal/blob/master/docs/usage.md) |
| What the default protocol is: lineage, slots, vocabulary | [owfa-personal: protocol.md](https://github.com/owfadev/owfa-personal/blob/master/docs/protocol.md) |
| Package-side plugin docs (bb family, lark family, …) | the owning `owfa-*` repo's plugin masters |
| AGENTS.md seed / log seed examples | [agents-example.md](agents-example.md), [log-example.md](log-example.md) |
