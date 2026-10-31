AgentTag names one of the three agents with a glyph tile and an uppercase name, and the message-type chip carries what that agent just did. You supply the agent key (`tower`, `pilot`, `ground`) and, for the chip, the schema type: PROPOSE, COUNTER, ACCEPT or REJECT.

## Markup

```html
<span class="hs-agent hs-agent--tower">
  <span class="hs-agent__glyph" aria-hidden="true">T</span>
  <span class="hs-agent__name">Tower</span>
</span>
<span class="hs-chip hs-chip--tower">PROPOSE</span>
```

## Rules

- Identity is colour, letter and shape together: Tower is a square with T, Pilot a circle with P, Ground a hexagon with G. Never drop the name or the glyph.
- Use the agent colours for agents only. Do not reuse blue, violet or orange for status, charts or buttons.
- Prefix ACCEPT with ✓ and REJECT with ✕ inside the chip. The chip keeps the sender's colour; the mark carries the meaning.
- When the character artwork arrives (`assets/Characters/`), show it beside the tag in bubbles, not instead of the tag.
