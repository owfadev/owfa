# OWFA Documentation

Reader: anyone approaching OWFA — first-time users, operators of existing instances, and plugin/package authors.

This documentation set is layered. [quickstart.md](quickstart.md) gets you running in five minutes; [intro.md](intro.md) explains what OWFA is; [usage.md](usage.md) covers day-to-day work; [mechanics.md](mechanics.md) goes into how the machinery actually operates (manifests, projections, bridges); [packages.md](packages.md) and [developer.md](developer.md) serve those who extend the system; [deployment.md](deployment.md) and [releasing.md](releasing.md) cover installation operations and the release pipeline; [conversion.md](conversion.md) handles the 0.3 → 0.4 migration. Chinese mirrors live under [zh/](zh/README.md).

## Where to go

| I want to… | Read |
|---|---|
| Use it — get a workspace running fast | [quickstart.md](quickstart.md) |
| Understand how it works — kernel, plugins, projections, bridges | [mechanics.md](mechanics.md) |
| Write plugins or packages | [packages.md](packages.md) + [developer.md](developer.md) |
| Install or upgrade an instance (manual path, channels) | [deployment.md](deployment.md) |
| Publish the framework or a package | [releasing.md](releasing.md) |
| Migrate a 0.3-era instance to 0.4 | [conversion.md](conversion.md) |

## Topics

- [naming.md](naming.md) — the naming history: OWFA, `owfadev`, the frozen `owfa` npm name.
- [sandbox.md](sandbox.md) — the sandbox: what runs where, and what is never touched.
- [agent-behavior.md](agent-behavior.md) — agent behavior self-checks.
- [map.md](map.md) — the map mechanism: vault assets → wiki proxy pages.
