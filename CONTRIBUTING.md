# Contributing

SkyQueue was built for Autonomous SG 2026. Issues and pull requests are welcome.

## Setup

Follow the quick start in the [README](README.md). You need `data/flights.csv` from the challenge drive for anything that builds a scenario. Recorded runs need no API key.

Check a change end to end with the three demo scenarios:

```bash
python -m src.coordinator demo1
python -m src.coordinator demo2
python -m src.coordinator demo3
```

## Rules for changes

- AI never decides legality and never does arithmetic. Safety rules, timing and the backup plan stay in plain Python.
- Agents never invent IDs. Code assigns `msg_id`, `line_id` and `note_id`.
- Every made-up value is labelled `synthetic` in data, UI and exports.
- A new safety rule needs an ID, an entry in `HARD` or `SOFT` in `src/checker/rules.py`, and a row in the README's safety rules table.
- Never commit `data/flights.csv`, `.env`, `runs.sqlite`, `cache/` or any API key.
- Commits are written and authored by people. Don't add AI attribution or Co-Authored-By lines for tools.

## Pull requests

Keep each pull request to one change, say which demo scenarios you ran, and update the README if behaviour or rules change. Report security problems privately, as described in [SECURITY.md](SECURITY.md).
