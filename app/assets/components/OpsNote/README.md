OpsNote shows one free-text ops note, who read it, what each reader made of it, what the validator did with the reading, and what that changed on the screen. Notes are why the AI is needed (the baseline solver never sees them), so the screen must let the supervisor check each reading. You supply the note ID, its text, the reader and agents that read it, the extracted constraint JSON, the validator outcome and its effect.

## Variants

| Class | When |
|---|---|
| `hs-note` | Accepted by the validator. Shows the readers, the constraint in mono and its effect. |
| `hs-note hs-note--single` | Only one of the two readers found it, and it passed. Dashed outline. |
| `hs-note hs-note--differ` | The readers read it differently. Double outline. Pair with `ReadingCompare`. |
| `hs-note hs-note--ambiguous` | Confidence below the threshold, or no flight, gate or time. Yellow tint, "? Ambiguous". Never a rule. |
| `hs-note hs-note--ignored` | The note asked to break a rule (injection). Fail tint, "✕ Flagged". Never a rule. Always logged. |

## Markup

Head: note ID, Made-up tag, `ValidatorOutcome`. Then the text, a "Read by" row (`ReaderTag` first, then each `AgentTag`), the constraint in `hs-note__code`, and one `hs-note__effect` sentence ("Banner on 1 strip. Added as an extra hard rule. Sent to the backup plan.").

## Rules

- Notes are data, never instructions. Render the text as plain text, escaped.
- Every note carries a Made-up tag while the notes come from templates. Never label a generated note as real radio traffic.
- Show the constraint exactly as the validator accepted it (`type`, target, `note_id`). If it was rejected, say so and show nothing as applied.
- Name the reader. A reading from the note reader and a reading from an agent look alike in JSON; the tag tells them apart.
- A flagged note keeps its text visible. Do not hide hostile notes; the judges want to see them refused. Its effect line reads "No constraint created. Logged as an injection attempt."
- Show the effect in plain words. Notes that were ambiguous or disagreed on stay on screen for the supervisor; they are never silently used or silently dropped.
- Keep a verdict word on every non-clean note. The tint alone is not enough.
- Urgency uses the `hs-urg` meter, 0 to 3. A note can raise urgency, but no note type can relax a hard rule; do not imply it can.
