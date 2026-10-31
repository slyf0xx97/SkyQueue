PlanCard is the decision point: one final plan, where it came from (AGREED or BACKUP), a short summary, the headline facts, and the Approve and Reject buttons. You supply the source, the plain-English summary, the rule count from the checker, the trace count from the log, the measured differences and the supervisor's decision state.

## Markup

A `hs-plan` section with a head (`hs-plan__title` and `hs-plan__source--agreed` or `--backup`), a summary, an optional `hs-plan__facts` list, the `hs-holdline` divider, and `hs-plan__actions` with two Buttons and a status line.

## Rules

- This is the only card with a shadow. Do not stack plan cards on top of each other.
- A BACKUP plan says why: "Agents did not agree by round 3" plus the rule that blocked agreement. A backup is never styled as agreed. In architecture v3 the backup solver uses the validated notes, so say "made with the validated notes, without negotiation", never "without the notes".
- Show "Lines traced" next to the rule count, from the log (`11 / 11`). Approve stays disabled while any line has a broken trace; the card says which line (`L5`) and links to its `TraceChain`.
- Show `RoundTimeline` above the card when there is room.
- The summary is AI-written and sits beside the raw rule table. Show both; never show the summary alone. "N / N pass" must come from the checker, not from the summary text.
- Facts show provenance. Fuel and excess taxi minutes are estimates (`hs-val--estimate`). Compare against B0 and say so in the label when you show a delta.
- Show the hold-short line once, above the buttons.
- After a click the buttons stop and the status line records who decided and when. Approved cards keep the same layout so the log and the screen match.
