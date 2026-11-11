# User Profile Research Distillation (design basis for user-profile)

> Development-side design archive (2026-09-13, distilled from four rounds of web research): the selection basis for the user-profile plugin. Not a runtime artifact of any instance; framework behavior is sourced from `.owfa/plugins/user-profile/`.

"User profiling" has two practice lines with different semantics: the product-design line draws **representative fictional target users** (personas), serving design decisions; the agent-memory line maintains **a continuous cognition profile of the real user** (user profile), serving personalization. vault-wiki's profile plugin belongs to the latter—borrowing the dimension framework from the former and the update mechanism from the latter.

## The dimension framework from product methodology

Mainstream persona template fields converge on: basic attributes, role/background, goals, pain points, behavioral habits, motivations. Chinese-language material commonly distinguishes **static dimensions** (demographic attributes, low-frequency change) from **dynamic dimensions** (behavioral preferences, continuously evolving). The construction process is a three-step frame: acquire and research user information → segment user groups → build and enrich profiles.

Two practical disciplines:

- **Details that serve no decision should be discarded**—a profile is not better for being more complete; details you cannot act on are unwanted
- **Profiles have a durability requirement**—they go stale and must be maintained continuously; the static/dynamic layering maps neatly onto different update frequencies and expiry policies

## The update mechanism from agent memory

The core patterns of the agent memory field: a profile consists of two layers, **static identity facts + real-time behavioral signals**; user-scoped persistent memory underpins cross-session continuity; profiles update incrementally with user feedback. Behavioral signals and self-reported signals complement each other—what the user did (which assets were placed in) is often harder evidence than what the user said.

## vault-wiki's selection

The profile page is a convergent cognition profile: a static identity layer + a dynamic preference layer, with open-ended sections and unenumerated dimensions. Assertions must carry evidence wikilinks (guarding against hallucination pile-up), and the preference layer carries stale_after (knowledge that can go stale explicitly declares its expiry moment). Signals have two channels: conversation saves (self-reported signals) and asset mapping (behavioral signals). Zero proprietary fields; trust provenance fully reuses trust semantics.

## Sources

- Zhihu column 「数据分析之用户画像方法与实践」 (user-profiling methods and practice in data analysis), 人人都是产品经理 「构建用户画像的流程与方法」 (the process and methods of building user profiles), boardmix 「persona 的 8 个内容维度」 (8 content dimensions of a persona)—the dimensions-and-process line
- Supermemory "How AI User Profiles Drive Personalization", Mem0 "Build an AI Agent That Actually Remembers Your Users", Microsoft Foundry user-scoped persistent memory—the agent-memory line
