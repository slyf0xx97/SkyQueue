ReaderTag names the note reader: the tool that reads each free-text ops note once and returns typed answers with a confidence. In architecture v3 this is Jev, with Claude as a drop-in fallback and a fake reader for tests. You supply the reader's name and pinned version.

## Markup

```html
<span class="hs-reader">
  <span class="hs-reader__glyph" aria-hidden="true">R</span>
  <span class="hs-reader__name">Note reader</span>
  <span class="hs-reader__ver">jev-1.14</span>
</span>
```

## Variants

| Class | When |
|---|---|
| `hs-reader` | JevReader or ClaudeReader. Solid ink diamond. |
| `hs-reader hs-reader--test` | FakeReader, which returns the hidden ground truth. Hatched diamond and the word TEST. Never show it in the live demo. |

## Rules

- The reader is a tool, not a character. It gets no agent colour, no face and no speech bubble. Its readings appear as typed answers (`ReadingCompare`, `OpsNote`), never as prose.
- Identity is shape plus letter: diamond with R. Tower is a square, Pilot a circle, Ground a hexagon; the diamond is taken by the reader only.
- Always show the pinned version in mono ("jev-1.14"). The vendor's speed and accuracy claims are not ours; the screen shows only what we measured.
- Say which reader produced a reading wherever a reading is shown. The supervisor must be able to tell Jev from an agent.
