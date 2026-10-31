# HoldShort — Product Requirements (PRD)

*Engines off, queue on time.*

Autonomous SG 2026 · Airbus Challenge #2 · v0.3 · 31 Oct 2026
Full background: `holdshort-brief.md` in the project knowledge base.

**v0.3 changes:** trace links stored by code (plan line ↔ message ↔ note ↔ rule check); linked selection, "Why this line" and note banners on the supervisor screen; code-assigned IDs; design system adopted for the app; interface references added.

**v0.2 changes:** revised arrival times + gate reassignment; free-text ops notes; calibration and same-calculator baselines; positioned against NASA ATD-2 / FAA TFDM metering; Streamlit instead of FastAPI + React; reply cache and cheaper batch model; configurable round limit; stated data limits.

## 1. Summary

HoldShort helps a tower supervisor clear a weather-delayed departure queue. Three AI agents (Tower, Pilot, Ground) read the situation, including free-text ops notes, and negotiate pushback order, engines-off gate holds, gate moves and runway order in at most 3 rounds. Plain code checks every plan against safety rules. If the agents don't agree, a solver makes a backup plan. A human approves every final plan, which includes revised departure and arrival times. Everything is logged, and every line of the final plan can be traced back to the messages, notes and rule checks behind it.

## 2. Problem

During weather disruptions, aircraft push back in order and wait in long taxi queues with engines running. Tower, airline ops and ramp sort out exceptions (crew duty limits, gate conflicts, connections, broken ground equipment) by radio and phone, one flight at a time. This wastes fuel, adds controller workload and spreads delays to later flights.

## 3. Prior work and our addition

Departure metering (gate holds timed by an algorithm) is proven: NASA's ATD-2 trial at Charlotte reported over 1M gallons of fuel saved in its first four years, and the FAA is rolling out surface metering in TFDM. Metering decides *when* aircraft leave the gate. It does not negotiate trade-offs between organisations or read unstructured ops information. HoldShort adds that. Our solver without notes (B1) stands in for metering and is the baseline to beat.

### Interface references

We ranked nine related interfaces and borrow from the top three. The pictures we looked at were schematics drawn from each source's text, not screenshots; we link the sources.

| Rank | Interface | What we borrow |
|---|---|---|
| 1 | ATD-2 tower display | Linked selection: pick a flight and it highlights everywhere (F9.9) |
| 2 | AgentCoord | Messages marked by type; a line from each plan line back to the message that proposed it (F9.10, F9.11) |
| 3 | FAA electronic flight strips | Memory-aid banners, for example a note that a gate has no ground power (F9.12) |
| 4 | ATD-2 ramp console | Hold countdown on held strips (F9.13, optional) |

The ATD-2 human-factors study is small (4 to 13 survey responses per condition), so we cite it as context, not proof.

## 4. Users

| User | Needs |
|---|---|
| **Tower supervisor for the departure queue** (primary) | A safe, ready-to-approve plan and the reasons behind it |
| Airline dispatch (represented by Pilot agent) | Fuel, crew duty limits and connections protected |
| Ramp/station manager (represented by Ground agent) | Gates freed for inbound aircraft, ramp crew not pushed into overtime |
| Hackathon judges | Clear AI/plain-code split, honest numbers, visible failure cases |

## 5. Goals and non-goals

**Goals**
- G1. Produce a safe plan for a real disrupted hour, agreed by round 2 where possible, round 3 at most.
- G2. Zero safety-rule violations in any approved plan.
- G3. Fewer excess taxi-out minutes than B0 (today) and B1 (metering-style solver).
- G4. Every decision traceable to messages, notes, rule checks and data source.
- G5. Every plan states revised departure and arrival times per flight.
- G6. From any plan line, the supervisor reaches the proposing message, the agreeing agents, the notes used and the rule results in one click, with no recomputation in the UI.

**Non-goals**
- Arrivals sequencing, en-route rerouting, multi-airport networks.
- Live data feeds.
- Replacing the controller. The tool advises; a human approves.

## 6. User stories

1. As a supervisor, I pick a disrupted hour from the flight data and see the queue and the ops notes.
2. As a supervisor, I watch the three agents negotiate, round by round, as named characters.
3. As a supervisor, I see which proposals were blocked and by which rule.
4. As a supervisor, I see which notes each agent relied on, and how it read them.
5. As a supervisor, I get one final plan (agreed or backup) with revised departure/arrival times and a plain-English summary.
6. As a supervisor, I approve or reject the plan; nothing counts until I do.
7. As an auditor, I export the full log as JSON.
8. As a judge, I see results across many scenarios versus B0 and B1, including failures.
9. As a supervisor, I click one flight and see its strip, its messages, the notes about it and its rule checks highlighted together.
10. As a supervisor, I ask "why this line?" on any plan line and see what produced it.

## 7. Functional requirements

### F1. Scenario loading
- F1.1 Load `flights.csv` (2015 US DOT), `airlines.csv`, `airports.csv`. Parse local `hhmm` times with YEAR/MONTH/DAY.
- F1.2 Trigger rows: `WEATHER_DELAY > 15` or `LATE_AIRCRAFT_DELAY > 20`. Skip diverted/cancelled rows and rows missing `TAXI_OUT` (logged as declined).
- F1.3 Queue: all departures from the trigger row's `ORIGIN` within ±60 min of its `SCHEDULED_DEPARTURE`.
- F1.4 Made-up attributes, fixed seed, each flagged `synthetic: true`: wake class, fuel on board, burn rate, gate, ground power at gate, inbound needing that gate, crew duty end, ramp shift end, connecting passengers.
- F1.5 Reduced departure rate = real wheels-off rate in that window.
- F1.6 Demo airport = airport with the most trigger rows.

### F2. Ops notes
- F2.1 Each scenario gets 2–5 free-text notes, tied to its flights and gates, generated from templates with a fixed seed and labelled made-up.
- F2.2 Note types: broken ground power, crew duty remaining, priority connection, turbulence report, gate unavailable, ambiguous note, prompt-injection note.
- F2.3 Each note stores its hidden ground-truth constraint for evaluation (never shown to agents).
- F2.4 30 notes hand-written and hand-labelled before any prompt tuning.
- F2.5 Each note has a code-assigned `note_id` (`N1`, `N2`, …) and the flights and gates it names, so the UI can show it on every affected strip.

### F3. Timing calculator (no AI)
- F3.1 Given pushback order, gate holds/moves and runway order, compute per flight: pushback, taxi minutes, wheels-off, fuel used, revised departure delay, **revised arrival time** (wheels-off + scheduled air time + taxi-in).
- F3.2 Normal taxi time per airport = 10th percentile `TAXI_OUT`.
- F3.3 Fuel = taxi minutes × burn rate; CO₂ = fuel × 3.16.
- F3.4 **Calibration:** replay the real order for every test scenario and report mean absolute error vs recorded `TAXI_OUT`.

### F4. Agents
- F4.1 Tower, Pilot, Ground: separate Claude API calls, own system prompt, own private data.
- F4.2 Tower sees queue, rate, wake classes. Pilot sees fuel, duty, connections. Ground sees gates, ground power, inbound needs, ramp shifts. All see the notes and the shared plan.
- F4.3 Agents convert relevant notes into structured constraints (`constraints_from_notes`), each citing a `note_id`.
- F4.4 Notes are data, never instructions. A note asking to break a rule must be flagged and ignored.
- F4.5 Output must be schema-valid (Pydantic). Invalid → re-ask once → treated as REJECT.
- F4.6 Agents never decide legality; they may cite rule IDs.
- F4.7 Model is a setting: stronger model for the live demo, cheaper fast model for batch runs.

### F5. Message schema
`msg_id`, `round`, `from` (TOWER|PILOT|GROUND), `type` (PROPOSE|COUNTER|ACCEPT|REJECT), `plan[]` (flight, action PUSH|GATE_HOLD|REASSIGN_GATE, plus `until` / `runway_slot` / `gate`), `constraints_from_notes[]` (type, target, note_id), `constraints_cited[]`, `rationale` (≤ 300 chars), `timestamp`.

- F5.1 **Code assigns IDs.** The coordinator sets `msg_id` (for example `R2-TOWER-01`) and a `line_id` for every plan line. Agents never invent either. Agents may only cite `note_id` values that were in their input; code rejects any other.
- F5.2 A COUNTER or ACCEPT refers to the plan lines it changes or agrees with by `line_id`. The coordinator records which message first proposed each line and which agents accepted it.
- F5.3 Each plan line in an agreed or backup plan carries: `line_id`, `proposed_in` (msg_id; `BACKUP` for solver lines), `agreed_by[]`, `notes_used[]` (note_ids), `checks[]` (`{rule_id, pass, detail}` for every rule run against that line) and a `provenance` label per value (`real`, `synthetic`, `estimate`).

### F6. Negotiation coordinator
- F6.1 Round 1: Tower proposes. Pilot and Ground ACCEPT or COUNTER.
- F6.2 Round 2: Tower merges counters. Agents ACCEPT or REJECT.
- F6.3 Round 3: final offer. Agreed = all ACCEPT and all hard rules pass.
- F6.4 Round limit is a setting (default 3). No agreement → backup plan (F8).
- F6.5 Every proposal is checked (F7) before other agents see it. Failed proposals return to the sender with rule IDs.

### F7. Safety rules (no AI)
| ID | Rule | Type |
|---|---|---|
| WAKE-01 | Min gap between departures by wake class (simplified FAA, in config) | Hard |
| RATE-01 | Departures per 15 min ≤ reduced rate | Hard |
| TAXI-01 | Aircraft on taxiway ≤ capacity | Hard |
| FUEL-01 | Fuel after taxi ≥ trip fuel + reserve | Hard |
| DUTY-01 | Wheels-off before crew duty end | Hard |
| GATE-01 | Held aircraft leaves before inbound needs the gate | Hard |
| GATE-02 | No engines-off hold at a gate without ground power | Hard |
| CREW-01 | Ramp crew on shift at pushback | Hard |
| CONN-01 | Minimise missed connections | Soft |
| CREW-02 | Minimise ramp overtime | Soft |
| THRU-01 | Maximise throughput | Soft |

- Each check returns `{rule_id, pass, detail}`. All values come from `config.yaml`.
- Constraints extracted from notes are validated (type, target exists) and then applied as extra hard rules.
- F7.1 Each check also reports which plan lines it covered, so results can be attached to `checks[]` on those lines (F5.3).

### F8. Backup plan (no AI)
- F8.1 OR-Tools CP-SAT over all hard rules, minimising weighted excess taxi minutes + missed connections + overtime. Greedy rule-based version if time runs short.
- F8.2 Does **not** see the notes (this is B1).
- F8.3 Time limit 5 s; if infeasible, fall back to first-come-first-served with gate holds and flag "no safe improvement found".
- F8.4 Output marked `source: BACKUP` with the rule(s) that blocked agreement.

### F9. Supervisor screen (Streamlit)
- F9.1 Three original agent characters with speech bubbles per message.
- F9.2 Ops notes panel; each note shows which agent used it and how.
- F9.3 Queue table: flight, action, gate, revised departure/arrival, taxi minutes, fuel; real vs made-up values visibly different.
- F9.4 Rule table: pass/fail per rule ID per proposal.
- F9.5 Final plan card with AI summary and source (AGREED or BACKUP).
- F9.6 Approve / Reject buttons; decision written to the log.
- F9.7 Scenario picker (airport, date, trigger row).
- F9.8 Results page: tables and charts from the latest evaluation run.
- F9.9 **Linked selection.** Selecting a flight highlights its strip, its plan line, every message that mentions it, every note that names it and every rule row that covered it. The screen reads the stored trace links (F10.4); it computes nothing.
- F9.10 **Message type marks.** Every message shows its type (PROPOSE, COUNTER, ACCEPT, REJECT) as a chip with a mark (✓ for ACCEPT, ✕ for REJECT), not by colour alone.
- F9.11 **Why this line.** Each plan line has a "Why this line" action. It opens the proposing message, the agents that agreed, the notes used and the rule results for that line, in that order.
- F9.12 **Note banners.** A validated note constraint raises a banner on every strip it affects (for example "No ground power at B12, note N1"). An ignored injection note shows "Ignored" and is logged.
- F9.13 (Could, before the feature freeze only) Held strips show the hold-until time as a countdown.
- F9.14 The screen uses the HoldShort design system (`tokens.css`, `components/bundle.css`, fonts) from `app/assets/`. Real, made-up and estimated values use the Provenance styles.

### F10. Log and cache
- F10.1 SQLite: every message, note reading, rule check, plan and decision with timestamps.
- F10.2 Export a run as JSON.
- F10.3 Cache AI replies keyed by model + prompt hash, so reruns are identical and cheap.
- F10.4 **Trace links.** A `trace_links` table stores edges `(from_type, from_id, to_type, to_id)` between plan lines, messages, notes, rule checks and flights, written by the coordinator when each message and check is recorded. The UI's linked selection and "Why this line" (F9.9, F9.11) query this table.
- F10.5 The JSON export includes the trace links, so an auditor can follow the same paths offline.

### F11. Evaluation
- F11.1 Batch-run 100–300 scenarios across several airports/months, fixed seed, parallel calls; ~20-scenario dev set kept separate.
- F11.2 All three arms through the same timing calculator: B0 (real order), B1 (solver without notes), HoldShort.
- F11.3 Report: calibration error; excess taxi minutes; fuel/CO₂ (estimated); delay; missed connections; hard-rule breaks in approved plans; proposals blocked; % agreed by round 2 / 3 / backup; note-reading precision/recall; injection notes refused; latency. Medians with spread, paired per scenario.
- F11.4 Save five failure cases: deadlock → backup; unsafe proposal blocked; worse than B1; misread note; bad input declined.
- F11.5 Sensitivity check on burn rate and departure rate.
- F11.6 Trace completeness: in approved plans, 100% of plan lines have a proposing message, `agreed_by`, `checks[]` and provenance labels. Reported as a metric.

## 8. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | One negotiation finishes in < 30 s with the demo model |
| N2 | Same seed + cache = identical results |
| N3 | If the API is down: backup plan still runs; recorded demo run available |
| N4 | No API keys in git; `.env` only |
| N5 | `flights.csv` not committed |
| N6 | Rules, calculator, note validation and trace-link writes covered by pytest |
| N7 | Commits authored by the team only, no AI co-author lines |
| N8 | Batch evaluation fits the team's API budget (estimate cost before running) |
| N9 | Selecting a flight updates the highlights in under 200 ms (reads stored links only) |

## 9. Tech stack

Python 3.11 · pandas · Claude API · Pydantic · OR-Tools (CP-SAT) · Streamlit · SQLite · pytest

## 10. Repo layout

```
data/            airlines.csv, airports.csv (flights.csv ignored)
src/sim/         scenarios.py, notes.py, timing.py, calibrate.py
src/agents/      tower.py, pilot.py, ground.py, prompts/, cache.py
src/checker/     rules.py, config.yaml
src/solver/      backup.py
src/coordinator.py, src/log.py, src/trace.py
app/             streamlit_app.py, assets/ (tokens.css, components/bundle.css, fonts/, character art)
eval/            run_batch.py, baselines.py, notes_labelled.csv, results/
tests/
docs/            prd.md, streamlit.md
```

## 11. Acceptance criteria

- [ ] A scenario from a real trigger row runs end to end in the Streamlit app.
- [ ] Three separate AI calls per round, visible in the log.
- [ ] Negotiation never exceeds the round limit.
- [ ] Final plan shows revised departure and arrival times; at least one demo plan uses a gate move.
- [ ] A deliberately unsafe proposal is blocked with its rule ID.
- [ ] The injection note is refused and logged in 100% of test runs.
- [ ] Approved plans have zero hard-rule breaks across the test set.
- [ ] Backup plan appears, labelled, when there is no agreement.
- [ ] Calibration error and the B0 / B1 / HoldShort table are produced by script.
- [ ] Five failure cases are saved and shown.
- [ ] Every made-up value is labelled in the app and exports.
- [ ] Every plan line in an approved plan has a proposing message, agreeing agents, notes used and rule results in the log.
- [ ] Selecting a flight highlights its strip, messages, notes and rule rows from stored trace links.
- [ ] "Why this line" opens the full chain for any plan line.
- [ ] A validated note constraint shows a banner on every strip it affects.

## 12. Milestones (today)

| # | Deliverable | Done when |
|---|---|---|
| M1 | Data + scenarios + timing calculator + calibration + B0 | Calibration error and B0 for 1 scenario |
| M2 | Rules + backup solver (B1) + tests | pytest green, B1 runs |
| M3 | Notes + agents + coordinator + cache + log + trace links | 3-round run in terminal; trace links readable for every plan line |
| M4 | Streamlit app with linked selection, "Why this line" and note banners | Run and approve in browser; the three interactions work |
| M5 | Batch evaluation + failure cases | Results table generated |
| M6 | Slides + 3-min recording | Submitted |

Feature freeze after M4.

## 13. Known limits (say these out loud)

- DOT data covers ~14 large airlines; regional and cargo flights are missing.
- One Pilot agent speaks for all airlines; real airlines compete.
- Wake classes, fuel, gates, crew times and notes are made-up.
- Timing calculator is simplified; its error is reported.
- Interface references were studied from text descriptions and schematics, not screenshots.

## 14. Open questions

- Simplified wake intervals and taxiway capacity values: agree and document.
- Who draws the three original agent characters? (Spec in the design system, `assets/Characters`.)
- API budget for the batch run.
- Brand font: the design system uses open-licence fonts (Barlow Condensed, IBM Plex). If the organisers supply licensed Airbus font files, we swap them in.

## Sources

- NASA Spinoff, ATD-2 at Charlotte: https://spinoff.nasa.gov/node/11424
- FAA TFDM Surface Metering: https://www.faa.gov/air_traffic/technology/tfdm/sm
- FAA Electronic Flight Strips: https://www.faa.gov/air_traffic/technology/tfdm/efs
- NASA ATD-2 Charlotte human-factors paper: https://ntrs.nasa.gov/api/citations/20205004241/downloads/Parke_CLT_HF_%20DASC_paper_final.pdf
- AgentCoord: https://arxiv.org/html/2404.11943v1
