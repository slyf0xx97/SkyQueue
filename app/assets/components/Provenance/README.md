Provenance labels where a number came from: real (2015 US DOT data), made-up (synthetic, fixed seed) or estimated (computed from made-up assumptions). It exists because judges score trust and traceability, and a made-up value that looks real is a lie. You supply the class for every value you show and, in headers, a tag with the source.

## Forms

| Source | Tag | Value style |
|---|---|---|
| Real | `hs-prov` (solid dot) | plain `hs-val` |
| Made-up | `hs-prov hs-prov--synthetic` (dashed, hatched, hollow dot) | `hs-val hs-val--synthetic` (dashed box with hatch) |
| Estimate | `hs-prov hs-prov--estimate` (≈) | `hs-val hs-val--estimate` (≈ prefix, dotted underline) |

## Rules

- Every number on screen is one of the three. If you cannot say which, do not show it.
- The classes use neutral colour on purpose. The difference is in the form (solid, dashed, dotted), so it survives greyscale and projectors.
- Put a tag in each table and card header, and `hs-val--*` on individual cells where a table mixes sources.
- Name the seed or source in the tag text: "Real · DOT 2015", "Made-up · seed 42".
- Exports carry the same label: JSON fields get a `provenance` key with `real`, `synthetic` or `estimate`.
- Never use the yellow `hold` colour for made-up data. Yellow means held or needs a person.
