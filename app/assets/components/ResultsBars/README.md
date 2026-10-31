ResultsBars compares the arms of the evaluation on one metric, using the same timing calculator for all of them: B0 first-come-first-served, B1 metering-style solver, B2 solver with the validated notes but no negotiation, and HoldShort. You supply the metric name, the direction that is better, each arm's median with its spread, and the bar length as a percentage of the largest value.

## Markup

A `hs-results` wrapper with one `hs-results__metric` per metric. Each has four `hs-bar` rows: `hs-bar--b0` (grey fill), `hs-bar--b1` (hatched grey), `hs-bar--b2` (dotted) and `hs-bar--hs` (yellow fill with a 2px ink outline). An optional fifth row `hs-bar--oracle` (dashed empty track) shows B2-oracle, the solver with the hidden true constraints, as the best any note reader could do. Set the length with `style="--w:52%"`.

After the metric bars, one `ul.hs-ladder` says what each step added:

| Step | Reads as |
|---|---|
| B0 → B1 | Optimisation: what a solver alone adds |
| B1 → B2 | Notes: what the validated ops notes add |
| B2 → HoldShort | Negotiation: what the agents add on top |

A step with no gain gets `hs-ladder__step--zero` and the words "no gain over B2". If B2 matches HoldShort, say so on the page.

## Rules

- Draw all bars on one scale per metric, starting at zero. A zero-length bar is a real result; keep the row and print the 0.
- Print the value in mono at the end of every bar. Add the spread there too ("6.3 min, IQR 4.1–9.0") once the real run exists.
- Keep the arms in the order B0, B1, B2, HoldShort in every metric so the eye finds them without a legend. Each arm differs in fill pattern (solid, hatched, dotted, yellow), not just grey level.
- The yellow outline carries the HoldShort bar on any surface; never remove the ink outline.
- Estimated metrics (fuel, CO₂) carry an Estimate tag. Paired comparisons only: say "per scenario, same calculator".
- Show the scenarios where HoldShort is worse than B1. Add a row or a note; do not drop them from the bars.
- The preview values are placeholders, labelled as example data. Replace them with output from `eval/results/` before showing them to anyone.
- Include "Hidden true constraints broken, per arm" as its own metric. B1 never sees the notes, so it breaks many by design; showing that is what proves the notes matter.
- Name the step in the ladder with a plain word (optimisation, notes, negotiation) and print the paired difference per scenario, same calculator.
- B2-oracle is optional. Draw it only if the run exists, and never in HoldShort's colours.
