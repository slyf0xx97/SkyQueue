Button is the only way a person makes a decision in HoldShort: Approve and Reject on a plan, plus quiet actions such as exporting the log. You supply the label and the click handler; the component supplies the height, colour and focus ring.

## Variants

| Class | Use when |
|---|---|
| `hs-btn hs-btn--approve` | The one action that writes the supervisor's approval to the log. One per screen. Ink fill, not yellow: yellow means held. |
| `hs-btn hs-btn--reject` | Sends the plan back. Outlined in `fail`, always paired with Approve. |
| `hs-btn hs-btn--quiet` | Everything else: export, show details, change scenario. |

Add `hs-btn--lg` (44px) for Approve and Reject on the plan card, `hs-btn--sm` (28px) inside tables.

## Rules

- Label with a verb and the object: "Approve plan", "Reject plan", "Export log (JSON)". Never "OK" or "Submit".
- Do not focus or enable Approve automatically. Nothing counts until the supervisor clicks it.
- Disabled buttons use `disabled`; they have no colour contrast requirement but must not hide why: say it in a caption beside them.
- Keep the 3px `focus` ring. Do not set `outline: none`.
- In Streamlit use `st.button` styled by the theme; use this markup for slides and static pages.
