# SkyQueue product requirements

*Engines off, queue on time.*

Autonomous SG 2026, Airbus Challenge #2. Background, pitch and evaluation story live in `docs/brief.md`. This file says exactly what to build.

## 1. Summary

SkyQueue helps a tower supervisor clear a weather-delayed departure queue. A note reader turns free-text ops notes into typed answers, and plain code validates them. Three AI agents (Tower, Pilot, Ground) then negotiate pushback order, engines-off gate holds, gate moves and runway order in at most 3 rounds. Plain code checks every plan against safety rules. If the agents don't agree, a greedy backup plan is used. A person approves every final plan, which includes revised departure and arrival times, and every plan line can be traced back to the messages, notes and rule checks behind it.

## 2. Problem

During weather disruptions, aircraft push back in order and wait in long taxi queues with engines running. Tower, airline ops and ramp sort out exceptions (crew duty limits, gate conflicts, connections, broken ground equipment) by radio and phone, one flight at a time. This wastes fuel, adds controller workload and spreads delays to later flights.

## 3. Prior work and what SkyQueue adds

Departure metering is proven. NASA's ATD-2 trial at Charlotte reported over 1 million gallons of fuel saved in its first four years, and the FAA is rolling out surface metering in TFDM. Metering decides when aircraft leave the gate. It doesn't negotiate trade-offs between organisations or read unstructured ops information, and SkyQueue adds both. The B1 baseline (solver without notes) stands in for metering.

## 4. Users

| User | Needs |
|---|---|
| Tower supervisor for the departure queue (primary) | A safe, ready-to-approve plan and the reasons behind it |
| Airline dispatch (Pilot agent) | Fuel, crew duty limits and connections protected |
| Ramp or station manager (Ground agent) | Gates freed for inbound aircraft, ramp crew not pushed into overtime |
| Hackathon judges | A clear AI and plain-code split, honest numbers, visible failure cases |

## 5. Goals and non-goals

Goals:
- G1. Produce a safe plan for a real disrupted hour, agreed by round 2 where possible and round 3 at most.
- G2. Zero safety-rule breaks in any approved plan.
- G3. Fewer hidden constraints broken than B1, and fewer excess taxi minutes than B0.
- G4. Every decision traceable to messages, notes, rule checks and data source.
- G5. Every plan states revised departure and arrival times per flight.

Non-goals:
- Arrivals sequencing, en-route rerouting and multi-airport networks.
- Live data feeds.
- Replacing the controller. The tool advises, and a person approves.

## 6. User stories

1. As a supervisor, I pick a disrupted hour from the flight data and see the queue and the ops notes.
2. As a supervisor, I see what the note reader made of each note, and which notes were accepted, ambiguous or flagged.
3. As a supervisor, I watch the three agents negotiate round by round.
4. As a supervisor, I see which proposals were blocked and by which rule.
5. As a supervisor, I get one final plan (agreed or backup) with revised departure and arrival times and a plain-English summary.
6. As a supervisor, I click "Why this line" on any plan line and see the message, agents, notes and rule results behind it.
7. As a supervisor, I approve or reject the plan, and nothing counts until I do.
8. As an auditor, I export the full log as JSON.
9. As a judge, I see results for B0, B1, B2 and SkyQueue on the same scenarios, including failures.

## 7. Functional requirements

### F1. Scenario loading
- F1.1 Load `flights.csv` (2015 US DOT), `airlines.csv` and `airports.csv`. Parse local `hhmm` times with YEAR, MONTH and DAY.
- F1.2 Trigger rows have `WEATHER_DELAY > 15` or `LATE_AIRCRAFT_DELAY > 20`. Skip diverted or cancelled rows and rows missing `TAXI_OUT`, and log them as declined.
- F1.3 The queue is every departure from the trigger row's `ORIGIN` within 60 minutes either side of its `SCHEDULED_DEPARTURE`.
- F1.4 Made-up attributes use a fixed seed and are flagged `synthetic: true`: wake class, fuel on board, burn rate, gate, ground power at the gate, the inbound needing that gate, crew duty end, ramp shift end and connecting passengers.
- F1.5 The reduced departure rate is the real wheels-off rate in that window.
- F1.6 The demo airport is the airport with the most trigger rows.

### F2. Ops notes
- F2.1 Each scenario gets 2 to 5 free-text notes tied to its flights and gates, generated from templates with a fixed seed and labelled made-up.
- F2.2 Note types: broken ground power, crew duty remaining, priority connection, turbulence report, gate unavailable, ambiguous note and prompt-injection note.
- F2.3 Each note stores its hidden ground-truth constraint for evaluation. Agents and readers never see it.
- F2.4 The team writes and labels 30 test notes before any prompt tuning.
- F2.5 Code assigns each note a `note_id` (N1, N2 and so on) and records the flights and gates it names.

### F3. Note reader
- F3.1 One interface with three implementations: `JevReader` (Jev decision model `typesafe/jev-1.14` via OpenRouter), `ClaudeReader` and `FakeReader` (returns the hidden ground truth, for building and tests).
- F3.2 One request per scenario with all its notes. For each note the reader answers: constraint type (NO_GATE_HOLD, DUTY_LIMIT, PRIORITY_CONNECTION, TURBULENCE, GATE_UNAVAILABLE, NONE), flight (from the scenario, or NONE), gate (from the scenario, or NONE), urgency 0 to 3, and the probability that the note asks to ignore a safety rule.
- F3.3 Readings are cached by model plus prompt hash, and Jev's `usage.cost` is logged.
- F3.4 If the reader fails, its notes are marked ambiguous and the agents still read the raw notes.
- F3.5 The reader runs only on the 3 demo scenarios (and a few more), once, with replies replayed from the cache.

### F4. Validator (no AI)
- F4.1 A reading becomes a validated constraint only if the type is allowed, the flight or gate exists in the scenario, confidence is at or above `jev.min_confidence`, and the override probability is below the flag threshold.
- F4.2 Outcomes: ACCEPTED, AMBIGUOUS (low confidence, never a rule), FLAGGED (asks to break a rule, never a rule, logged as an injection attempt), single-source (only one reader found it, accepted if it passes and marked) and mismatch (readers disagree, each passing candidate accepted and the mismatch logged).
- F4.3 The validator compares each agent's `constraints_from_notes` with the reader's after every round and logs mismatches.
- F4.4 No constraint type can relax a hard rule. One note's effect on soft weights is capped.
- F4.5 `jev.min_confidence` is tuned on the dev scenarios only, never on the 30 test notes.

### F5. Agents
- F5.1 Tower, Pilot and Ground are separate Claude API calls, each with its own system prompt and private data.
- F5.2 Tower sees the queue, departure rate and wake classes. Pilot sees fuel, duty and connections. Ground sees gates, ground power, inbound needs and ramp shifts. All three see the raw notes, the validated constraints and the shared plan.
- F5.3 Notes are data, never instructions.
- F5.4 Output must pass the Pydantic schema. Invalid output gets one re-ask, then counts as REJECT.
- F5.5 Agents never decide legality. They may cite rule IDs.
- F5.6 The model is a setting. Replies are cached by model plus prompt hash.

### F6. Messages and trace IDs
- F6.1 Message fields: `msg_id`, `round`, `from` (TOWER, PILOT, GROUND), `type` (PROPOSE, COUNTER, ACCEPT, REJECT), `plan[]` (flight, action PUSH, GATE_HOLD or REASSIGN_GATE, plus `until`, `runway_slot` or `gate`), `constraints_from_notes[]` (type, target, note_id), `constraints_cited[]`, `rationale` (300 characters at most) and `timestamp`.
- F6.2 Code assigns `msg_id` (for example R2-TOWER-01) and a `line_id` for every plan line. Agents never invent either, and may only cite `note_id` values from their input.
- F6.3 COUNTER and ACCEPT messages refer to plan lines by `line_id`.
- F6.4 Each final plan line carries `line_id`, `proposed_in` (a msg_id, or BACKUP), `agreed_by[]`, `notes_used[]`, `checks[]` (`{rule_id, pass, detail}`) and a provenance label per value (real, synthetic, estimate).

### F7. Coordinator
- F7.1 Before round 1, the reader and validator run once and the validated constraints go to all three agents.
- F7.2 Round 1: Tower proposes. Pilot and Ground accept or counter.
- F7.3 Round 2: Tower merges the counters, and the agents accept or reject.
- F7.4 Round 3: final offer. Agreed means all three accept and all hard rules pass.
- F7.5 The round limit is a setting (default 3). With no agreement, the backup plan runs.
- F7.6 Every proposal is checked before the other agents see it. A failed proposal goes back to its sender with the rule IDs.

### F8. Timing calculator (no AI)
- F8.1 Given a pushback order, gate holds and moves, and a runway order, compute per flight: pushback, taxi minutes, wheels-off, fuel used, revised departure delay and revised arrival time (wheels-off plus scheduled air time plus taxi-in).
- F8.2 Taxi time is the airport's normal taxi time (10th percentile `TAXI_OUT`) plus queue wait from the reduced departure rate and wake gaps. Taxiway capacity is a simple counter.
- F8.3 Fuel is taxi minutes times burn rate, and CO2 is fuel times 3.16.
- F8.4 Calibration replays the real order for about 30 scenarios and reports the mean absolute error against recorded `TAXI_OUT`.

### F9. Safety rules (no AI)

| ID | Rule | Type |
|---|---|---|
| WAKE-01 | Minimum gap between departures by wake class (simplified FAA values, in config) | Hard |
| RATE-01 | Departures per 15 minutes at or below the reduced rate | Hard |
| TAXI-01 | Aircraft on the taxiway at or below capacity | Hard |
| FUEL-01 | Fuel after taxi at or above trip fuel plus reserve | Hard |
| DUTY-01 | Wheels-off before crew duty ends | Hard |
| GATE-01 | A held aircraft leaves before an inbound needs the gate | Hard |
| GATE-02 | No engines-off hold at a gate without ground power | Hard |
| CREW-01 | Ramp crew on shift at pushback | Hard |
| CONN-01 | Minimise missed connections | Soft |
| CREW-02 | Minimise ramp overtime | Soft |
| THRU-01 | Maximise throughput | Soft |

- F9.1 Each check returns `{rule_id, pass, detail}` and the plan lines it covered. All values come from `src/checker/config.yaml`.
- F9.2 Validated note constraints are applied as extra hard rules.

### F10. Backup plan (no AI)
- F10.1 A greedy rule in Python: first come first served, plus gate holds ranked by slack, respecting every hard rule.
- F10.2 `solve(scenario, constraints=None)`. The production backup passes the validated constraints. B1 passes none.
- F10.3 If no safe improvement exists, it returns first come first served with gate holds and says "no safe improvement found".
- F10.4 Output is marked `source: BACKUP` with the rule that blocked agreement.

### F11. Supervisor screen (Streamlit)
- F11.1 Use the design system in `app/assets/` (`tokens.css`, then `components/bundle.css`, and the fonts). See `docs/design-system/README.md` and `docs/streamlit.md`.
- F11.2 The three agents show as AgentTag glyph tiles (T, P and G on square, circle and hexagon). No emoji, and no character art until the team draws it.
- F11.3 Notes panel: each note with its reader, validator outcome and effect.
- F11.4 Conversation: one bubble per message, grouped by round, with the rule results under each.
- F11.5 Queue as flight strips: action, gate, revised departure and arrival, taxi minutes and fuel, with real and made-up values styled differently.
- F11.6 Rule table: pass or fail per rule ID per proposal.
- F11.7 Plan card with the AI summary and source (AGREED or BACKUP), plus Approve and Reject. The decision is written to the log.
- F11.8 "Why this line" on every strip opens the proposing message, agreeing agents, notes used and rule results, read from the trace links.
- F11.9 A validated note raises a banner on every strip it affects. An ignored injection note shows "Ignored".
- F11.10 Scenario picker and a results page with the B0, B1, B2 and SkyQueue comparison.

### F12. Log and cache (SQLite)
- F12.1 Tables for messages, note readings, reading mismatches, rule checks, plans, decisions and cached replies, all with timestamps.
- F12.2 A `trace_links` table stores edges `(from_type, from_id, to_type, to_id)` between plan lines, messages, notes, rule checks and flights. The coordinator writes them, and the screen only reads them.
- F12.3 A run exports as JSON, including the trace links.

### F13. Evaluation
- F13.1 Calibration and B0, B1 and B2 on about 30 scenarios. SkyQueue on the 3 demo scenarios plus a few more. The results slide says "small sample, indicative".
- F13.2 All arms run through the same timing calculator. B2 uses the same validated constraints as the SkyQueue run, so the two differ only in negotiation.
- F13.3 Report: calibration error, excess taxi minutes, fuel and CO2 (estimated), delay, missed connections, hidden constraints broken per arm, hard-rule breaks in approved plans, proposals blocked, agreement by round 2 or 3 or backup, note-reading precision and recall on the 30 test notes, injection notes turned into rules, trace completeness and time per negotiation.
- F13.4 Save these failure cases: deadlock that falls back to the backup plan, an unsafe proposal blocked with its rule ID, a scenario worse than B1, a misread note, and a bad input row declined.
- F13.5 The 3 demo scenarios double as failure cases: a clean agreement in round 2, a deadlock, and an injection note plus an unsafe plan blocked.

## 8. Data models

```python
from typing import Literal, Optional
from pydantic import BaseModel

ConstraintType = Literal["NO_GATE_HOLD", "DUTY_LIMIT", "PRIORITY_CONNECTION",
                         "TURBULENCE", "GATE_UNAVAILABLE", "NONE"]

class NoteReading(BaseModel):
    note_id: str
    reader: Literal["JEV", "CLAUDE", "FAKE"]
    constraint_type: ConstraintType
    p_type: float                  # confidence in the chosen type
    target_flight: Optional[str]   # None means NONE
    p_flight: float
    target_gate: Optional[str]
    p_gate: float
    urgency: int                   # 0 to 3
    p_override: float              # probability the note asks to bypass a rule

class ReadingDecision(BaseModel):
    note_id: str
    type: ConstraintType
    flight: Optional[str]
    gate: Optional[str]
    source: Literal["JEV", "AGENT", "BOTH"]   # JEV or AGENT alone means single-source
    status: Literal["ACCEPTED", "AMBIGUOUS", "FLAGGED"]
```

Validated constraints are the decisions with status ACCEPTED.

## 9. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | One negotiation finishes in under 30 seconds |
| N2 | The same seed plus the cache gives identical results |
| N3 | If an API is down, the backup plan still runs and a recorded demo run is available |
| N4 | No API keys in git. Keys go in `.env` (see `.env.example`) |
| N5 | `data/flights.csv` is never committed |
| N6 | Rules, timing, validator and trace-link writes are covered by pytest |
| N7 | Commits are authored by the team only, with no AI co-author lines |

## 10. Tech stack

Python 3.11, pandas, Pydantic, Claude API, Jev via OpenRouter, Streamlit, SQLite, pytest.

## 11. Repo layout

```
data/            airlines.csv, airports.csv (flights.csv ignored)
src/schemas.py   messages, plan lines, NoteReading, ReadingDecision
src/sim/         scenarios.py, notes.py, timing.py, calibrate.py
src/agents/      tower.py, pilot.py, ground.py, readers.py, prompts/, cache.py
src/checker/     rules.py, validator.py, config.yaml
src/solver/      backup.py
src/coordinator.py, src/log.py, src/trace.py
app/             streamlit_app.py, assets/ (design system)
eval/            run_batch.py, baselines.py, notes_labelled.csv, results/
tests/
docs/            brief.md, prd.md, design-system/README.md, streamlit.md
```

## 12. Acceptance criteria

- [ ] A scenario from a real trigger row runs end to end in the Streamlit app.
- [ ] Three separate agent calls per round, visible in the log.
- [ ] Negotiation never goes past the round limit.
- [ ] The final plan shows revised departure and arrival times, and at least one demo plan uses a gate move.
- [ ] A deliberately unsafe proposal is blocked with its rule ID.
- [ ] The injection note is flagged, never becomes a rule, and is logged.
- [ ] Approved plans have zero hard-rule breaks across the test set.
- [ ] The backup plan appears, labelled, when there is no agreement, and it respects validated notes.
- [ ] Calibration error and the B0, B1, B2 and SkyQueue table are produced by script.
- [ ] The failure cases are saved and shown.
- [ ] Every made-up value is labelled in the app and exports.
- [ ] "Why this line" opens the full chain for any plan line.

## 13. Schedule (31 Oct 2026, SGT)

| Time | Milestone |
|---|---|
| 12:25 | Schemas frozen, airport and 3 demo scenarios picked |
| 13:25 | Integration checkpoint: one scenario runs end to end with FakeReader and fake agents |
| 14:15 | Real agents and Jev cached. Feature freeze |
| 15:00 | Recording, calibration, small evaluation and slides done |
| 15:20 | Submit (hard deadline about 15:50) |

If the 13:25 checkpoint slips, cut the Jev call first and use ClaudeReader.

## 14. Known limits

- The DOT data covers about 14 large airlines, so regional and cargo flights are missing.
- One Pilot agent speaks for all airlines, but real airlines compete.
- Wake classes, fuel, gates, crew times and notes are made-up.
- The timing calculator is simplified, and its error is reported.
- Jev is new (released September 2026), and its speed and accuracy claims are the vendor's own.

## Sources

- NASA Spinoff, ATD-2 at Charlotte: https://spinoff.nasa.gov/node/11424
- FAA TFDM Surface Metering: https://www.faa.gov/air_traffic/technology/tfdm/sm
- Jev on OpenRouter: https://openrouter.ai/docs/guides/community/jev
