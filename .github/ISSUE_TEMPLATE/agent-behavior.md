---
name: Agent behavior analysis (agent-behavior)
about: Standardized agent behavior analysis attached to plugin-improvement issues (#34 ruling — mandatory, the evidence base for any change; protocol in .owfa/docs/agent-behavior.md)
labels: agent-behavior
---

## Scene
<!-- plugin@version / session date / one line on where the deviation happened -->

## User-layer instruction, verbatim
<!-- quote the user's instruction word for word; later key corrections likewise -->

## Actual behavior chain (fact layer, verifiable)
<!-- step by step; only steps with verifiable traces; speculation does not enter this layer -->
| # | Action | Constraint/pointer relied on (verbatim quote) | Owning plugin | Verifying trace |
|---|---|---|---|---|
| 1 | | | | |

## Expected behavior
- **Declared expectation** (L-layer behavior contract / injection-line quote; if none, write "undeclared"):
- **User expectation** (the correction, verbatim):

## Deviation
<!-- actual vs expected, item by item; vs declared = compliance diff, vs user expectation = demand signal — list separately -->

## Attribution (interpretation layer: hypothesis + confidence)
<!-- five classes, multiple allowed; each with a verbatim constraint quote and the minimal fix if it holds -->
- [ ] a constraint defect (wrong / ambiguous / over-executed)
- [ ] b constraint conflict (which two, quotes side by side)
- [ ] c not delivered (tier / dependency-chain check)
- [ ] d execution deviation (constraint present, not followed)
- [ ] e spec vacuum (no constraint covers the behavior)

## Suggested change
<!-- minimal fix + blast radius (other scenes depending on this constraint); the agent proposes, developers weigh -->
