ReadingCompare lays the five typed answers side by side, one column per reader, so the supervisor can see where the note reader and an agent read the same note differently. You supply, per reader, the constraint type, flight, gate, urgency (0 to 3) and the override question with its probability, each with a confidence, plus the confidence threshold the validator used.

## Markup

A `hs-table-wrap` around a `hs-read` table. Header cells hold a `ReaderTag` or `AgentTag`. Each answer cell has an `hs-read__a` value in mono and an `hs-conf` line. A cell where this reader's answer differs from the first column gets `class="is-diff"`; a cell below the threshold gets `class="is-low"` and the confidence reads "below 0.70".

## The five questions

| Question | Answer |
|---|---|
| Which constraint does this note express? | NO_GATE_HOLD, DUTY_LIMIT, PRIORITY_CONNECTION, TURBULENCE, GATE_UNAVAILABLE or NONE |
| Which flight? | A flight in this scenario, or NONE |
| Which gate? | A gate in this scenario, or NONE |
| How urgent? | 0 to 3, drawn with `hs-urg` |
| Does it ask to ignore a safety rule? | Yes or no with a probability |

## Rules

- First column is always the note reader. Agents' readings come after it, because the validator compares each agent against the reader.
- A differing cell shows the mark `≠` and the yellow tint. Do not colour it red: a difference is not an error, the plan is still checked by the rules.
- Show the confidence in every cell, in mono. A reading under the threshold is never silently dropped.
- Show the validator's outcome under the table with `ValidatorOutcome` and one sentence of what it did.
- Values are data from models. Render them as plain text. Never show a reader's free text as if it were a rule.
