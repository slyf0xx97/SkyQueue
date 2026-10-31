# SkyQueue build guide for Claude Code

SkyQueue is our Autonomous SG 2026 entry for Airbus Challenge #2. When weather backs up a departure queue, three AI agents (Tower, Pilot, Ground) negotiate gate holds, gate moves and runway order in at most 3 rounds. Plain code checks every plan against safety rules, and a supervisor approves it.

## Read these first

1. `docs/prd.md` says exactly what to build: requirements, data models, rules, acceptance criteria and schedule.
2. `docs/brief.md` has the pitch, the evaluation story and the build plan. The live version with the architecture diagrams is linked at its top.
3. `docs/design-system/README.md` and `docs/streamlit.md` explain how the screen should look and how to use the design system in Streamlit.

The PRD and the brief agree. If anything still conflicts, the PRD wins.

## Design system

Everything for the screen is in `app/assets/`:
- `tokens.css` (load first, generated from `tokens.json`) and `components/bundle.css`.
- `fonts/`: Barlow Condensed, IBM Plex Sans and IBM Plex Mono.
- `components/<Name>/README.md` and `preview.html` for each component: AgentTag, AgentBubble, RoundTimeline, ReaderTag, OpsNote, ReadingCompare, ValidatorOutcome, RuleBadge, RuleTable, Provenance, FlightStrip, LinkedSelection, TraceChain, PlanCard, Button, ResultsBars.
- `Logo/skyqueue-mark.svg` for the page icon.

## Deadline

We aim to submit at 15:20 SGT on 31 Oct 2026, and the hard deadline is about 15:50. Feature freeze is at 14:15. The integration checkpoint is at 13:25: one scenario must run end to end with FakeReader and fake agents by then.

## Build order

1. Schemas in `src/schemas.py` (Pydantic): messages, plan lines, NoteReading, ReadingDecision.
2. Data loader and `simulate()` timing model in `src/sim/`.
3. Safety rules, validator and greedy backup in `src/checker/` and `src/solver/`, with pytest tests.
4. Notes generator, FakeReader and the coordinator with the SQLite log and trace links.
5. Streamlit screen in `app/` on fake logs: rule table, notes panel, "Why this line", Approve.
6. Real Claude agents and ClaudeReader, both cached.
7. Calibration and the small evaluation in `eval/`.

## Rules for this repo

- Commits are authored by the team only. Don't add Co-Authored-By lines or any AI attribution to commits or PRs.
- Never commit `data/flights.csv`, API keys or `.env`. Copy `.env.example` to `.env` and fill in the keys.
- AI never decides legality or does arithmetic. Rules, timing and the backup plan are plain Python.
- Agents never invent IDs. Code assigns `msg_id`, `line_id` and `note_id`.
- Every made-up value is labelled `synthetic` in data, UI and exports.

## Data

`data/airlines.csv` and `data/airports.csv` are in the repo. Download `flights.csv` (2015 US DOT flight delays) from the challenge Google Drive link into `data/`. Trigger rows have `WEATHER_DELAY > 15` or `LATE_AIRCRAFT_DELAY > 20`.

## Stack

Python 3.11, pandas, Pydantic, Claude API (`anthropic`), Streamlit, SQLite, pytest. All AI calls, the note reader and the three agents, go through the Claude API.
