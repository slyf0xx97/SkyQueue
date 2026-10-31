FlightStrip is one row of the departure queue, styled after a paper flight strip: an action band on the left, then flight, gate, departure, arrival, taxi minutes and fuel. You supply the plan line for one flight (action, slot or hold-until time, gate move) and the calculator's output (revised departure and arrival times, taxi minutes, fuel).

## Variants

| Class | Action band |
|---|---|
| `hs-strip` | PUSH with the runway slot, ink band. |
| `hs-strip hs-strip--hold` | GATE_HOLD with the hold-until time, yellow `hold` band, `on-hold` text. |
| `hs-strip hs-strip--move` | REASSIGN_GATE with the new gate, outlined band. |

## Banner and trace footer

Two optional rows sit under the cells and span the whole strip.

| Class | What |
|---|---|
| `hs-strip__banner` | Memory-aid banner raised by a validated note: "! No ground power at B12" plus the note chip. Yellow tint. One banner per note that affects this flight. |
| `hs-strip__banner hs-strip__banner--ignored` | An injection note that names this flight: "✕ Ignored · N5". Fail tint. |
| `hs-strip__foot` | Trace footer: the plan line ID (`L3`), the rule count, and the "Why this line" button, which opens `TraceChain`. |

Add `is-linked` to the strip when the flight is picked in `LinkedSelection`.

## Rules

- Show the action as a word in the band, not only by colour: PUSH, HOLD, MOVE.
- Show departure and arrival as `scheduled → revised` with a signed delta beneath. Every plan must show both revised times.
- Style each value by source: gates are made-up (`hs-val--synthetic`), fuel is an estimate (`hs-val--estimate`), recorded times and taxi minutes are plain. Put the matching `Provenance` tags in the table header.
- Flight numbers and gates are in mono; keep the cell order identical in every strip so columns line up.
- Under 760px wide the strip folds to three columns and the action band spans two rows. Do not truncate flight numbers.
- Do not colour the whole row. The band is the only strong colour in a strip.
- A banner says what the note means for this flight in plain words, then cites the note. It is a memory aid, not a rule: the rule row lives in `RuleTable`.
- Banners come only from notes the validator accepted. Never raise one from a raw reading, an ambiguous note or a reader mismatch that was not applied.
- Every strip in a plan has the trace footer, so the "Why this line" button is always in the same place.
