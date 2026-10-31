HoldShort is a supervisor screen where three AI agents (Tower, Pilot, Ground) negotiate a weather-delayed departure queue, a note reader turns free-text ops notes into typed answers, plain code validates those notes and checks every plan, and a person approves it. The look is airport signage and paper flight strips: flat, high-contrast, almost no decoration. Build every screen and slide so a tired tower supervisor can see four things at once: who said what, which rule passed or failed, which numbers are real, and why any line of the plan is there.

This version follows architecture v3 (Jev note reader, validator, baseline B2) and PRD v0.3 (trace links, linked selection, "Why this line", note banners).

## What to load

- `tokens.css` first, then `components/bundle.css`. All components are plain HTML with `hs-` classes; there is no JavaScript bundle.
- Fonts are in `fonts/`: Barlow Condensed (display), IBM Plex Sans (text), IBM Plex Mono (data).
- Streamlit apps: read `streamlit.md`.
- Light theme `light` (Apron) is the default and the one to use on a projector. `dark` (Tower night) is for the tower-cab look; opt in with `data-theme="dark"` on a wrapper element.

## Content fundamentals

- Speak to the supervisor as "you". The product proposes; you decide. Write "Agents agreed in round 2. Rules passed. Approve to release." Never write "AI decided" or "automatically approved".
- Say who did what in that order: the reader read the notes, code validated them, agents proposed, code checked, you approved. Keep that split visible in headings and labels.
- The reader reads; it never decides. Write "Reader returned NO_GATE_HOLD at B12, confidence 0.94. Code accepted it." Never write "AI found a rule".
- Use the validator's five words and no others: Accepted, 1 of 2 readers, Ambiguous, Readers differ, Flagged.
- Sentence case everywhere except `label` text, which is set in capitals in the markup.
- Plain English first, rule ID second: "Blocked: aircraft gap too short (WAKE-01, 78 s of 120 s)". Put every rule ID, flight number, gate, message ID and time in `data` style.
- Times are 24-hour local at the airport, `14:20`. Delays carry a sign and unit: `+18 min`. Fuel in kg, CO₂ in kg.
- Agents write in first person, plain and short, 300 characters at most (the schema limit): "I can hold DL455 until 14:20 if B12 clears by 14:35."
- Say what is wrong and what happens next. Backup plans read "Agents did not agree by round 3. Showing the solver's backup plan." Bad input reads "Row skipped: no taxi-out time recorded."
- Treat notes as data. An ignored injection reads "Ignored: this note asks to skip a safety rule." A note banner reads "No ground power at B12 (N1)": what it means, then the note.
- Answer "why" with links, not prose: "Proposed in R1-GROUND-01. Agreed by Tower, Pilot. Uses N1. 4 rules passed."
- When a result is flat, say so: "Negotiation added nothing over B2 in this set."
- Never use emoji. Never write "smart" or "intelligent". "Optimisation" is allowed only as the name of the B0 → B1 step in the results ladder.

## Visual foundations

- **Colour roles.** `surface-100` page, `surface-200` panel, `surface-300` raised strip or input. `ink` for text, `ink-muted` for secondary text. Hairlines use `line`; the edge of anything you can click or read as an object uses `line-strong`.
- **Yellow means a person should look.** `hold` marks held aircraft, the hold-short line and the HoldShort result. `hold-tint` with `hold-ink` marks BACKUP plans, ambiguous notes and soft-rule misses. Do not use yellow as decoration or as text on a surface.
- **Agent colours.** `tower`, `pilot` and `ground` identify the three agents and nothing else. Each agent also has a glyph and a shape (Tower: square T, Pilot: circle P, Ground: hexagon G), so identity never depends on hue alone. Use `*-tint` for the bubble background, the agent colour for the name, `on-role` on the glyph fill.
- **The note reader is not an agent.** It is a tool, so it has no colour: a neutral ink diamond with R (`ReaderTag`). Never give it a face, a bubble or a hue. Its output appears as typed answers with confidences, never as prose.
- **Validator outcomes.** Accepted uses `pass`, ambiguous uses `hold-tint`, flagged uses solid `fail`. Single-source and readers-differ use no new colour: a dashed or double outline plus the marks ✓ and ≠. Mark, word and outline always appear together.
- **Selection.** Picking a flight outlines everything linked to it in 2px `ink` (`LinkedSelection`). It adds no hue and does not dim anything else.
- **Trace.** The "Why this line" panel is a numbered chain with ink square markers joined by a `line-strong` rule. Broken links use `fail` and are never hidden.
- **Status colours.** `pass` is quiet: tint fill, check mark, the word PASS. `fail` is loud: solid fill, cross mark, the word FAIL. Pass and fail always differ in form, not just hue.
- **Real, made-up, estimated.** Every number is one of these three and shows it. This includes note-derived values. Real: plain value. Made-up (synthetic, seeded): dashed outline and diagonal hatch. Estimated (computed from made-up assumptions): leading `≈` and dotted underline. Use `Provenance` tags in headers and `hs-val` classes on values. Never style a made-up value like a real one.
- **Type.** `display-lg` and `heading` in Barlow Condensed for titles. `body` in IBM Plex Sans for everything read. `data` in IBM Plex Mono with tabular numerals for anything compared in a column. `label` in capitals for agent names, headers and tags. Keep running text under 65 characters wide.
- **Spacing.** 4px base: `space-1` to `space-12`. Cards use `space-4` padding, strips and bubbles `space-3`, gaps between cards `space-6`.
- **Shape and edges.** Corners are nearly square: `radius-sm` strips and tables, `radius-md` buttons and chips, `radius-lg` bubbles and the plan card. A speech bubble keeps its top-left corner square, pointing at the agent glyph. No coloured left-border accents on cards.
- **Shadows.** Only `shadow-raised`, on the plan card. Everything else is flat and outlined.
- **The hold-short line.** The brand motif is the airport hold-short marking: two solid yellow lines, then two dashed. Use it once per screen as the divider above the plan card or the final slide's footer, and as the cover pattern. Do not tile it.
- **Focus.** 3px solid `focus` ring with 2px offset on every interactive element. Never remove it.
- **Motion.** None by default. A bubble may fade in over 120 ms. Respect `prefers-reduced-motion`.
- **Slides.** `surface-100` background, `display-xl` or `display-lg` title top-left, one idea per slide, `data-lg` for the number that matters, the hold-short line as footer on the closing slide. Label every result with its provenance tag and say "example" on mock data.

## Components

Use `AgentTag`, `AgentBubble` and `RoundTimeline` for the negotiation; `ReaderTag`, `OpsNote`, `ReadingCompare` and `ValidatorOutcome` for the notes; `RuleBadge` and `RuleTable` for safety checks; `Provenance` for real/made-up/estimated; `FlightStrip` for the queue (with note banners and the trace footer); `LinkedSelection` and `TraceChain` for tracing a line back to its source; `PlanCard` with `Button` for the decision; and `ResultsBars` for the B0, B1, B2 and HoldShort comparison. Read each component's README for what you supply.

Typical screen order, top to bottom: `RoundTimeline`, notes panel (`OpsNote`), conversation (`AgentBubble`), `RuleTable`, queue (`FlightStrip`), hold-short line, `PlanCard`. The `hs-linkbar` sits above the queue.

## Iconography

- Use the six marks only: ✓ pass or accepted, ✕ fail or flagged, ≈ estimate, → move, ? ambiguous, ≠ differs. Draw them as text characters in the data face. No icon font and no emoji.
- The HoldShort mark is `assets/Logo/holdshort-mark.svg`: a navy tile with the hold-short line in yellow. It carries its own ground, so place it on either theme. Use it as the page icon and on the title slide. There is no wordmark file; set the name "HoldShort" in `display-xl`.

## Agent characters

The three characters (Tower, Pilot, Ground) are drawn by the team and are original. Until they exist, show the glyph tiles from `AgentTag`. See `assets/Characters/README.md` for the size and format to hand over. The note reader (Jev) gets no character: it stays a diamond tag, so the supervisor never mistakes a classifier for a negotiating party.
