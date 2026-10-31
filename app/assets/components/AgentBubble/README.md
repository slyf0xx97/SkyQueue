AgentBubble shows one schema message from one agent: who, which round, what type, the short rationale, and the notes and rules it cited. You supply the agent, round, `msg_id`, message type, rationale text (300 characters at most) and the cited note IDs and rule results.

## Markup

```html
<article class="hs-bubble hs-bubble--pilot">
  <header class="hs-bubble__head">
    <!-- AgentTag --> <span class="hs-chip hs-chip--pilot">COUNTER</span>
    <span class="hs-bubble__meta">R1-PILOT-01</span>
  </header>
  <p class="hs-bubble__text">Rationale in the agent's words.</p>
  <footer class="hs-bubble__foot"><!-- note chips and RuleBadges --></footer>
</article>
```

Group bubbles under a `hs-round` heading (round dot + label) and stack them in one column, in the order they were sent.

## Rules

- One bubble per message. Do not merge two agents into one bubble.
- Keep the top-left corner square; it points at the sender. Do not add a coloured left border.
- Show the rule results the checker returned for that message in the footer. A message that fails a hard rule shows its FAIL badge and the caption "blocked before it reached the other agents".
- Render rationale as plain text. It is model output and may repeat a note; never inject it as HTML.
- Text and notes the agent cited appear as chips (`N1`, `N2`). The full note lives in `OpsNote`.
- When the validator found that this agent read a note differently from the note reader, add an `hs-outcome hs-outcome--differ` chip in the footer ("≠ differs from reader on N3: gate"). It is information, not an error; the full comparison lives in `ReadingCompare`.
- Message IDs (`R1-TOWER-01`) and plan line IDs (`L3`) are assigned by code. The bubble shows them as given; add `is-linked` when the bubble belongs to the selected flight (`LinkedSelection`).
- A `.hs-chip` showing a note ID is a link target: selecting it highlights that note and the flights it affects.
