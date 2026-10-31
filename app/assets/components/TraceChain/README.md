TraceChain is the "Why this line" panel: for one plan line, the chain from the message that proposed it, through the agents that agreed and the notes it relied on, to every rule it passed. You supply the line's stored trace: `line_id`, `proposed_in`, `agreed_by`, `notes_used`, `checks[]` and a provenance label per value. Code wrote these links; the panel only reads them.

## Markup

An `ol.hs-chain` with a head (`hs-chain__title` and a trace-complete mark) and one `li.hs-chain__step` per link, always in this order:

| # | Step | Shows |
|---|---|---|
| 1 | Proposed in | The message chip, the `AgentTag`, and the rationale as a quote. For a backup line: "Backup solver. No negotiation." |
| 2 | Agreed by | One `AgentTag` per agent that accepted, with the ACCEPT message ID. |
| 3 | Notes used | Each note as a chip plus its `ValidatorOutcome`. "No notes" if none. |
| 4 | Rules checked | A `RuleBadge` for every check on this line, passes included. |
| 5 | Values | `Provenance` tags: which of the line's numbers are real, made-up or estimated. |

## Rules

- Never skip a step. If a link is missing, keep the step and give it `hs-chain__step--missing` with the sentence "No <thing> recorded for this line." A line with a missing link cannot be approved; say so in the head.
- The head shows "Trace complete" with ✓ only when all five steps resolve. Trace completeness is a reported metric; the panel must agree with the log.
- IDs are the ones code assigned (`L3`, `R1-TOWER-01`, `N1`). Agents never invent them, so never show an ID the log does not hold.
- Open it from the strip's "Why this line" button. It opens in a dialog or expander next to the strips, so the supervisor keeps the queue in view.
- Quote the agent's rationale as plain text. It is model output.
- A backup plan's lines still have a chain: the proposer is the solver, agreed-by is empty, and notes used are the validated ones the solver received.
