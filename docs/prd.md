# HoldShort — Product Requirements (PRD)

*Engines off, queue on time.*

Autonomous SG 2026 · Airbus Challenge #2 · v0.1 · 31 Oct 2026
Full background: `holdshort-brief.md` in the project knowledge base.

## 1. Summary

HoldShort helps a tower supervisor clear a weather-delayed departure queue. Three AI agents (Tower, Pilot, Ground) negotiate pushback order, engines-off gate holds and runway order in at most 3 rounds. Plain code checks every plan against safety rules. If the agents don't agree, a solver makes a backup plan. A human approves every final plan, and everything is logged.

## 2. Problem

During weather disruptions, aircraft push back first-come-first-served and wait in long taxi queues with engines running. Tower, airline ops and ramp coordinate by radio and phone, one flight at a time. This wastes fuel, adds controller workload and spreads delays to later flights.

## 3. Users

| User | Needs |
|---|---|
| **Tower ground controller / ramp tower supervisor** (primary) | A safe, ready-to-approve queue plan and the reasons behind it |
| Airline dispatcher (represented by Pilot agent) | Fuel reserves, crew duty limits and connections protected |
| Ramp/station manager (represented by Ground agent) | Gates freed for inbound aircraft, ramp crew not pushed into overtime |
| Hackathon judges | Clear AI/plain-code split, honest numbers, visible failure cases |

## 4. Goals and non-goals

**Goals**
- G1. Produce a safe departure plan for a real disrupted hour in ≤ 3 negotiation rounds.
- G2. Zero safety-rule violations in any approved plan.
- G3. Reduce excess taxi-out minutes against first-come-first-served (B0).
- G4. Every decision traceable to messages, rule checks and data source.

**Non-goals**
- Arrivals sequencing, en-route rerouting, multi-airport networks.
- Real-time live data feeds.
- Replacing the controller. The tool only advises; a human approves.

## 5. User stories

1. As a supervisor, I load a disrupted hour from the flight data and see the departure queue.
2. As a supervisor, I watch the three agents negotiate, round by round, as named characters.
3. As a supervisor, I see which proposals were blocked and by which rule.
4. As a supervisor, I get one final plan (agreed or backup) with a plain-English summary.
5. As a supervisor, I approve or reject the plan; nothing counts until I do.
6. As an auditor, I export the full log as JSON.
7. As a judge, I see results across many scenarios versus the baselines, including failures.

## 6. Functional requirements

### F1. Scenario loading
- F1.1 Load `flights.csv` (2015 US DOT), `airlines.csv`, `airports.csv`.
- F1.2 Select trigger rows where `WEATHER_DELAY > 15` or `LATE_AIRCRAFT_DELAY > 20`. Skip diverted/cancelled rows and rows missing `TAXI_OUT`.
- F1.3 Build the queue: all departures from the trigger row's `ORIGIN` within ±60 min of its `SCHEDULED_DEPARTURE`.
- F1.4 Add made-up attributes with a fixed seed: wake class, fuel on board, burn rate, gate, inbound needing that gate, crew duty end, ramp shift end, connecting passengers. Each field flagged `synthetic: true`.
- F1.5 Reduced departure rate = observed wheels-off rate in that window.

### F2. Timing calculator (no AI)
- F2.1 Given pushback order, gate holds and runway order, compute per flight: pushback time, taxi minutes, wheels-off, fuel used, departure delay.
- F2.2 Unimpeded taxi time per airport = 10th percentile `TAXI_OUT` for that airport.
- F2.3 Fuel = taxi minutes × burn rate; CO₂ = fuel × 3.16.

### F3. Agents
- F3.1 Three agents: Tower, Pilot, Ground. Each is a separate Claude API call with its own system prompt and private data.
- F3.2 Tower sees: queue, runway rate, wake classes. Pilot sees: fuel, duty times, connections. Ground sees: gates, inbound needs, ramp shifts. All see the shared plan.
- F3.3 Agents output only schema-valid messages (Pydantic). Invalid output → re-ask once → treat as REJECT.
- F3.4 Agents never compute legality. They may cite rule IDs.

### F4. Message schema
Fields: `msg_id`, `round`, `from` (TOWER|PILOT|GROUND), `type` (PROPOSE|COUNTER|ACCEPT|REJECT), `plan[]` (flight, action PUSH|GATE_HOLD, `until` or `runway_slot`), `constraints_cited[]`, `rationale` (≤ 300 chars), `timestamp`.

### F5. Negotiation coordinator
- F5.1 Round 1: Tower proposes. Pilot and Ground ACCEPT or COUNTER.
- F5.2 Round 2: Tower merges counters. Agents ACCEPT or REJECT.
- F5.3 Round 3: final offer. Consensus = all ACCEPT and all hard rules pass.
- F5.4 Hard cap of 3 rounds. No consensus → backup plan (F7).
- F5.5 Every proposal goes through the checker (F6) before other agents see it. Failed proposals return to the sender with rule IDs.

### F6. Safety rules (no AI)
| ID | Rule | Type |
|---|---|---|
| WAKE-01 | Min gap between departures by wake class (simplified FAA, configurable) | Hard |
| RATE-01 | Departures per 15 min ≤ reduced rate | Hard |
| TAXI-01 | Aircraft on taxiway ≤ capacity | Hard |
| FUEL-01 | Fuel after taxi ≥ trip fuel + reserve | Hard |
| DUTY-01 | Wheels-off before crew duty end | Hard |
| GATE-01 | Gate-held aircraft leaves before inbound needs the gate | Hard |
| CREW-01 | Ramp crew on shift at pushback | Hard |
| CONN-01 | Minimise missed connections | Soft |
| CREW-02 | Minimise ramp overtime | Soft |
| THRU-01 | Maximise throughput | Soft |

Each check returns `{rule_id, pass, detail}`. All values come from config, not code constants.

### F7. Backup plan (no AI)
- F7.1 OR-Tools CP-SAT: all hard rules as constraints; minimise weighted excess taxi minutes + missed connections + overtime.
- F7.2 Time limit 5 s. If no feasible plan, fall back to FCFS with gate holds and flag "no safe improvement found".
- F7.3 Output marked `source: BACKUP` with the rule(s) that blocked consensus.

### F8. Supervisor screen
- F8.1 Three agent characters (original illustrations) with speech bubbles per message.
- F8.2 Queue table: flight, action, times, taxi minutes, fuel; real vs made-up values visually distinct.
- F8.3 Rule-check panel: pass/fail per rule ID per proposal.
- F8.4 Final plan card with AI summary + source (AGREED or BACKUP).
- F8.5 Approve / Reject buttons; decision written to the log.
- F8.6 Scenario picker (airport, date, trigger row).

### F9. Log
- F9.1 Store every message, check result, plan and decision with timestamps in SQLite.
- F9.2 Export a run as JSON.

### F10. Evaluation
- F10.1 Batch-run N scenarios (target 100–300), fixed seed; dev set of ~20 kept separate.
- F10.2 Baselines: B0 = actual FCFS order with observed `TAXI_OUT`; B1 = backup solver alone.
- F10.3 Report: excess taxi minutes, fuel/CO₂ (estimated), delay, missed connections, hard-rule violations in approved plans, unsafe proposals blocked, % consensus, % backup, gap vs B1, latency.
- F10.4 Save four failure cases: deadlock → backup; unsafe proposal blocked; worse than B0; out-of-scope input declined.
- F10.5 Sensitivity check on burn rate and departure rate.

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | One negotiation (3 rounds) finishes in < 30 s |
| N2 | Same seed + same cached LLM replies = same result |
| N3 | Works if the LLM API is down: backup plan still runs; a recorded demo run is cached |
| N4 | No API keys in git; `.env` only |
| N5 | `flights.csv` not committed |
| N6 | Rule checker and timing calculator covered by pytest |
| N7 | Commits authored by the team only, no AI co-author lines |

## 8. Tech stack

Python 3.11 · pandas · Claude API · Pydantic · OR-Tools (CP-SAT) · FastAPI · React + Vite · SQLite · pytest

## 9. Repo layout

```
data/            airlines.csv, airports.csv (flights.csv ignored)
src/sim/         scenario builder, timing calculator
src/agents/      tower.py, pilot.py, ground.py, prompts/
src/checker/     rules.py, config.yaml
src/solver/      backup.py (OR-Tools)
src/api/         FastAPI app, coordinator.py, log.py
ui/              React + Vite supervisor screen
eval/            run_batch.py, baselines.py, results/
docs/            prd.md
```

## 10. API (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| GET | `/scenarios?airport=&limit=` | List trigger rows |
| POST | `/runs` `{scenario_id}` | Start a negotiation; returns `run_id` |
| GET | `/runs/{id}` | Messages, checks, final plan, status |
| POST | `/runs/{id}/decision` `{approve, note}` | Supervisor decision |
| GET | `/runs/{id}/export` | JSON log |

## 11. Acceptance criteria

- [ ] A scenario from a real trigger row runs end to end in the UI.
- [ ] Three separate LLM calls per round, visible in the log.
- [ ] Negotiation stops at round 3 every time.
- [ ] A deliberately unsafe proposal is blocked with its rule ID.
- [ ] Approved plans have zero hard-rule violations across the full test set.
- [ ] Backup plan appears and is labelled when there is no consensus.
- [ ] Results table vs B0 and B1 is generated by script.
- [ ] Four failure cases are saved and shown.
- [ ] Every made-up value is labelled in UI and exports.

## 12. Milestones (today)

| # | Deliverable | Done when |
|---|---|---|
| M1 | Data + scenario builder + timing calculator + B0 | B0 numbers for 1 scenario |
| M2 | Rules + backup solver + tests | pytest green, B1 runs |
| M3 | Agents + coordinator + log | 3-round run in terminal |
| M4 | API + UI | Run and approve in browser |
| M5 | Batch eval + failure cases | Results table generated |
| M6 | Slides + 3-min recording | Submitted |

Feature freeze after M4.

## 13. Open questions

- Which demo airport? (Pick the one with most qualifying rows.)
- Taxiway capacity and wake intervals: agree the simplified values and document them.
- Character art: who draws the three original agent characters?
