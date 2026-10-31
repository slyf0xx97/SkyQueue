# Using HoldShort in Streamlit

Streamlit controls colours and one font through its theme settings, and anything finer through injected CSS. Use both: the theme for the frame, the injected `bundle.css` for the components.

## 1. Theme file

Save as `.streamlit/config.toml`. These values are the Apron theme.

```toml
[theme]
base = "light"
primaryColor = "#0e1a28"
backgroundColor = "#e9edf1"
secondaryBackgroundColor = "#f6f8fa"
textColor = "#0e1a28"
font = "sans serif"
```

`primaryColor` is `ink`, not yellow: Streamlit uses it for buttons and sliders, and yellow means "held" in HoldShort. Newer Streamlit releases also accept custom font files in the theme section; check the docs for your installed version. If yours does not, the injected CSS below sets the fonts.

## 2. Inject tokens and components

Copy `tokens.css`, `components/bundle.css` and the `fonts/` folder into `app/assets/`, then load them once at the top of `streamlit_app.py`.

```python
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).parent / "assets"

def load_holdshort():
    css = (ASSETS / "tokens.css").read_text() + (ASSETS / "components" / "bundle.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_holdshort()
```

Font files do not load from relative paths inside injected CSS. Serve them with `enableStaticServing = true` under `[server]` and put them in `app/static/`, then point the `@font-face` URLs at `/app/static/<file>`. Without this the app falls back to system fonts, which is acceptable for a demo but loses the data face.

## 3. Render components as HTML

Each component is plain HTML with `hs-` classes. Build strings in small Python helpers and pass them to `st.markdown(..., unsafe_allow_html=True)`.

```python
def agent_bubble(agent: str, round_no: int, msg_id: str, kind: str, text: str) -> str:
    glyph = {"tower": "T", "pilot": "P", "ground": "G"}[agent]
    return f'''
    <article class="hs-bubble hs-bubble--{agent}">
      <header class="hs-bubble__head">
        <span class="hs-agent hs-agent--{agent}"><span class="hs-agent__glyph">{glyph}</span>
        <span class="hs-agent__name">{agent}</span></span>
        <span class="hs-bubble__meta">R{round_no} · {msg_id}</span>
        <span class="hs-chip hs-chip--{agent}">{kind}</span>
      </header>
      <p class="hs-bubble__text">{text}</p>
    </article>'''

st.markdown(agent_bubble("tower", 1, "R1-TOWER-01", "PROPOSE", "Release DL455 first; hold AA1234 until 14:20."), unsafe_allow_html=True)
```

Escape agent text before it goes in (`html.escape`). Agent output and ops notes are data: never render them as HTML.

## 4. Dark theme

Streamlit cannot switch `data-theme` from Python. To show Tower night, wrap the markup in `<div data-theme="dark" class="hs">…</div>`; `tokens.css` re-declares every variable inside it. Run the live demo in light: projectors wash out dark screens.

## 5. Linked selection and "Why this line"

Streamlit reruns the script on every interaction and plain HTML cannot send a click back, so selection goes through a native control. Keep the picked flight in `st.session_state`, read the stored trace links, and add `is-linked` to every object the links name.

```python
def linked_ids(selected: str | None) -> dict[str, set[str]]:
    # trace_links rows: (from_type, from_id, to_type, to_id). Code wrote them; read only.
    if not selected:
        return {}
    ids = {"flight": {selected}}
    for ft, fid, tt, tid in trace.links_touching("flight", selected):
        ids.setdefault(tt, set()).add(tid)
    return ids

flights = [l.flight for l in plan.lines]
selected = st.segmented_control("Flight", flights, key="selected_flight")
linked = linked_ids(selected)

def cls(kind: str, id_: str) -> str:
    return " is-linked" if id_ in linked.get(kind, set()) else ""

# e.g. in the strip helper: f'<div class="hs-strip hs-strip--hold{cls("flight", line.flight)}">'
# in the bubble helper:     f'<article class="hs-bubble hs-bubble--{agent}{cls("message", msg_id)}">'
```

`st.segmented_control` needs a recent Streamlit; on older releases use `st.radio(..., horizontal=True)`. Both give a keyboard-reachable control with a focus ring. Print the `hs-linkbar` counts from `len(linked.get(kind, ()))`, never from searching text.

"Why this line" is a `st.button` per line that opens `st.dialog` (or an `st.expander` on older releases) containing the `TraceChain` markup built from that line's stored fields. Escape every string that came from a model or a note with `html.escape`. If a field is missing, render the `hs-chain__step--missing` step and disable Approve.

I have not run these helpers in Streamlit; check them against the version you have installed.

## 6. What Streamlit will not do

- Rounded or notched speech bubbles in native `st.chat_message`. Use the HTML bubble above instead.
- Hatched or dashed cell backgrounds in `st.dataframe`. Render the provenance-aware tables as HTML (`RuleTable`, `FlightStrip`).
- Click events from injected HTML. A strip cannot be clicked to select it; use the picker above. The `Why this line` button in a strip footer is decorative in static HTML; in the app, put a real `st.button` next to the strip.
- Keyboard focus rings on injected HTML buttons. Use `st.button` for Approve and Reject, and style them with the theme; keep the `Button` component for slides and static pages.
