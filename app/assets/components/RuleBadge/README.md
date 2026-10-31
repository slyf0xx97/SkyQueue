RuleBadge shows the result of one safety rule for one proposal: the rule ID and PASS, FAIL or MISS. You supply the rule ID from `config.yaml` (for example `WAKE-01`) and the pass flag the plain-code checker returned. Agents never set this value.

## Variants

| Class | Meaning |
|---|---|
| `hs-rule` | Rule passed. Tint fill, check mark, the word PASS. |
| `hs-rule hs-rule--fail` | Hard rule failed. Solid `fail` fill, cross mark, the word FAIL. The plan is blocked. |
| `hs-rule hs-rule--soft` | Soft rule missed (CONN-01, CREW-02, THRU-01). Yellow tint, "! MISS". The plan is not blocked. |

## Rules

- Always show the word and the mark with the colour. Pass and fail must read in greyscale.
- Show the ID in `data-sm` mono exactly as in the checker output. Do not rename rules for display.
- Put the numbers behind a fail in the rule table's detail line ("gap 78 s, minimum 120 s"), not inside the badge.
- Never show a green badge for a rule the checker did not run.
