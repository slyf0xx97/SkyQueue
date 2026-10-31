RoundTimeline shows where a negotiation is: the note-reading step before round 1, rounds 1 to 3, and the result. It tells the supervisor at a glance whether agents agreed in round 2 or the backup plan took over. You supply the round limit, the round reached and the source of the final plan.

## Markup

An `ol.hs-steps` with one `li.hs-steps__item` per step:

1. `hs-steps__mark--reader` diamond, label "Notes read".
2. One round mark per round (numbers 1 to 3, or up to the setting), label "Round 1" and so on.
3. A last item with the result, as the plan card's source tag (`hs-plan__source--agreed` or `--backup`).

Completed steps get `is-done` (filled mark). Rounds that were never needed get `is-skipped` (dashed mark with a dash), so "agreed in round 2" shows round 3 as skipped, not missing. Say why in the label of the group ("round 3 not needed"), not in every item.

## Rules

- The reader step comes first and is always shown, even when every note was ambiguous.
- Rounds are numbered dots, the reader is a diamond, the result is a word. Never rely on colour to tell done from skipped: filled versus dashed carries it.
- The round limit is a setting. Draw as many round marks as the limit, not always three.
- Put the timeline above the first bubble. The dots in `hs-round` headings inside the conversation stay as they are.
- A backup result reads "Backup plan" with the blocking rule ID beside it.
