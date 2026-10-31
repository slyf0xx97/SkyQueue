RuleTable lists every rule the checker ran against one proposal, with its owner, a plain-English description, hard or soft, and the result. The supervisor reads it next to the AI summary, so it must show everything, not only failures. You supply the checker's rows: `{rule_id, pass, detail}` plus the owner and description from config.

## Markup

A `hs-table-wrap` around a `hs-table`. Columns: Rule, Owner, What it checks, Covers, Type, Result. "Covers" lists the plan line IDs the check ran against (`L1, L3`), straight from the checker's output; these are the links that attach the result to each line's `checks[]`. A failed row gets `class="is-fail"` and a `hs-table__detail` line inside the description cell with the numbers.

## Rules

- Show passed and failed rules in the same table, in checker order. Do not sort passes away.
- Every failed row carries the detail string returned by the checker, in mono. If the checker gave none, show "no detail returned".
- Under the table say what happened to the proposal ("Blocked: sent back to Tower with GATE-02").
- On narrow screens the wrapper scrolls horizontally; do not hide columns.
- In Streamlit render this as HTML, not `st.dataframe`, so the FAIL badge keeps its form.
- Note-derived rules appear in the same table, with the note ID in the description ("from N1"). They are extra hard rules, so they use the same PASS and FAIL badges.
- Add `is-linked` to a row when `LinkedSelection` has a flight picked and that row's lines include it.
