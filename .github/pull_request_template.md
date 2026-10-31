## What this changes


## How I checked it
- [ ] `python -m src.coordinator demo1`, `demo2` and `demo3` run
- [ ] Checked on the Streamlit screen (if the UI changed)

## Project rules
- [ ] Legality, timing and the backup plan are still plain Python, not AI
- [ ] Code, not agents, assigns `msg_id`, `line_id` and `note_id`
- [ ] New made-up values are labelled `synthetic`
- [ ] No `data/flights.csv`, `.env`, `runs.sqlite`, `cache/` or keys in the diff
- [ ] README updated if behaviour or rules changed
