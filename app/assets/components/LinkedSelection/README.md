LinkedSelection is how one click on a flight shows everything that touches it: the flight's strip, the messages that mention it, the notes that name it and the rule rows that covered it. The screen reads stored trace links (PRD F10.4); it computes nothing. You supply the selected flight and the set of linked ids per object type from the `trace_links` table.

## Markup

Put `is-linked` on every linked object: a `hs-strip`, `hs-bubble`, `hs-note`, a `tr` in `hs-table`, or a `hs-chip`. Above the lists, one `hs-linkbar` states what is selected and counts what is linked, with a Clear button.

```html
<div class="hs-linkbar">
  <span class="hs-label">Selected</span><span class="hs-linkbar__flight">AA1234</span>
  <span class="hs-linkbar__counts">1 strip · 2 messages · 1 note · 2 rule rows</span>
  <button class="hs-btn hs-btn--quiet hs-btn--sm" type="button">Clear</button>
</div>
```

## Rules

- Selection is a 2px ink outline, not a new colour. Agent colours, yellow and red already mean something; a highlight hue would collide with them and fail in greyscale.
- Do not dim unlinked objects. Dimming lowers contrast on text the supervisor may still need; the outline is enough.
- Table rows use the inset top and bottom lines in the stylesheet (`tr.is-linked`), because outlines on `tr` are unreliable.
- The linkbar always says how many objects it found. "0 messages" is information: a plan line with no message is a broken trace, and `TraceChain` shows it.
- Selecting must work from the keyboard: the flight picker is a real control with the focus ring. Add `aria-current="true"` to the strip that was picked.
- The count must match the log. Do not highlight anything by text search; only by stored links.
- Selecting again, or Clear, removes every outline at once.
