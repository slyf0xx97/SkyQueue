# SkyQueue build guide for Claude Code

SkyQueue is our Autonomous SG 2026 entry for Airbus Challenge #2. When weather backs up a departure queue, three AI agents (Tower, Pilot, Ground) negotiate gate holds, gate moves and runway order in at most 3 rounds. Plain code checks every plan against safety rules, and a supervisor approves it.

## Read these first

1. `docs/brief.md` is the source of truth. Its "Time-boxed build plan" section overrides anything older.
2. `docs/prd.md` (v0.3) has the detailed requirements. Where it disagrees with the time-boxed plan, follow the plan.
3. `docs/architecture-v3.md` explains the Jev note reader, the validator and the B2 baseline, with the Pydantic models for `NoteReading` and `ReadingDecision`.
4. `docs/design-system/README.md` and `docs/streamlit.md` explain how the screen should look and how to use the design system in Streamlit.

Overrides from the time-boxed plan:
- The backup plan is a greedy rule in Python (first come first served, plus gate holds ranked by slack). Don't use OR-Tools or CP-SAT.
- Evaluation is small: about 30 scenarios for calibration and for B0, B1 and B2, plus SkyQueue on the 3 demo scenarios and a few more. Skip the 100 to 300 scenario batch and the sensitivity check.
- Jev (note reader, via OpenRouter) and the Claude agents run only on the 3 demo scenarios, once, with replies cached and replayed.
- Skip linked selection and character art. Use the glyph tiles from the AgentTag component for the three agents.
- The backup plan takes validated note constraints. B2 is the solver plus the same validated notes, with no negotiation.

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
6. Real Claude agents and JevReader, both cached. If Jev isn't working by 13:40, use ClaudeReader.
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

Python 3.11, pandas, Pydantic, Claude API (`anthropic`), Jev via OpenRouter, Streamlit, SQLite, pytest.
