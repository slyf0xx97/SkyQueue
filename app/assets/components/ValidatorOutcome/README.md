ValidatorOutcome shows what plain code did with a note reading. The validator is the trust boundary: a reading becomes a rule only if the type is allowed, the flight or gate exists, confidence clears the threshold, and it is not a request to break a rule. You supply the outcome the validator returned; the screen never decides it.

## Variants

| Class | Word | Meaning |
|---|---|---|
| `hs-outcome hs-outcome--accepted` | ✓ ACCEPTED | Passed every check. Goes to the agents, to the rules as an extra hard rule, and to the backup plan. |
| `hs-outcome hs-outcome--single` | ✓ 1 OF 2 READERS | Only one reader found it, and it passed the checks. Accepted, and marked for the supervisor. Dashed outline. |
| `hs-outcome hs-outcome--ambiguous` | ? AMBIGUOUS | Low confidence. Never a rule; shown to the supervisor. Yellow tint. |
| `hs-outcome hs-outcome--differ` | ≠ READERS DIFFER | Readers disagree. Each reading that passes is accepted; the mismatch is logged and counted. Double outline. |
| `hs-outcome hs-outcome--flagged` | ✕ FLAGGED | The note asks to skip a safety rule. Never a rule; logged as an injection attempt. Solid fail fill. |

## Rules

- Mark and word together: ✓, ?, ≠, ✕. The outline style (solid, dashed, double) is a second cue, so the five stay apart in greyscale.
- Only FLAGGED is loud. Ambiguous and differ ask a person to look; they do not say anything went wrong.
- An outcome sits in the head of its `OpsNote`. A note with outcome AMBIGUOUS or FLAGGED must also show a verdict sentence.
- Do not invent a sixth outcome in the UI. If the validator adds one, add it here first.
- Counts of each outcome belong in the results page ("Notes ambiguous / flagged / mismatched").
