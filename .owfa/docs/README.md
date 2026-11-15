# OWFA Documentation

Reader: anyone approaching OWFA — first-time users, operators of existing instances, and plugin/package authors.

This documentation set covers the **kernel and the channel** (protocol-agnostic). It is layered: [quickstart.md](quickstart.md) gets you running in five minutes; [kernel.md](kernel.md) goes into how the kernel actually operates (packages, capabilities, projections, budgets, lifecycle); [packages.md](packages.md) and [developer.md](developer.md) serve those who extend the system; [deployment.md](deployment.md) and [releasing.md](releasing.md) cover installation operations and the release pipeline; [conversion.md](conversion.md) handles the 0.3 → 0.4 migration. The **default protocol** (the llmwiki-descended organization scheme, shipped as the personal suite) documents itself in the [owfa-personal repo](https://github.com/owfadev/owfa-personal/blob/master/docs/protocol.md) — protocol.md, usage.md, and the 21 member PLUGIN.md files. Chinese mirrors live under [zh/](zh/README.md).

## Where to go

| I want to… | Read |
|---|---|
| Use it — get a workspace running fast | [quickstart.md](quickstart.md) |
| Understand how it works — kernel, packages, capabilities, projections | [kernel.md](kernel.md) |
| The default protocol: lineage, slots, vocabulary, member roster | [owfa-personal docs](https://github.com/owfadev/owfa-personal/blob/master/docs/protocol.md) |
| Day-to-day usage loops (default protocol) | [owfa-personal usage](https://github.com/owfadev/owfa-personal/blob/master/docs/usage.md) |
| Write plugins or packages | [packages.md](packages.md) + [developer.md](developer.md) |
| Call a protocol from outside — the ABI: four semantics, compat intervals | [abi.md](abi.md) |
| Install or upgrade an instance (manual path, channels) | [deployment.md](deployment.md) |
| Publish the framework or a package | [releasing.md](releasing.md) |
| Migrate a 0.3-era instance to 0.4 | [conversion.md](conversion.md) |

## Topics

- [naming.md](naming.md) — the naming history: OWFA, `owfadev`, the frozen `owfa` npm name.
- [sandbox.md](sandbox.md) — the sandbox: what runs where, and what is never touched.
- [agent-behavior.md](agent-behavior.md) — agent behavior self-checks.
- [abi.md](abi.md) — the protocol ABI: the four-semantics calling contract, compat intervals, and the R11 qualification line.
- [map.md](map.md) — the map mechanism: vault assets → wiki proxy pages.
