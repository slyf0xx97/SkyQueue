# Taxi-Out Negotiator

Autonomous SG 2026 · AI & Aerospace Track · Airbus Challenge #2

When weather backs up a departure queue, three independent AI agents (ATC, Pilot, Ground) negotiate pushback order, engines-off gate holds and runway sequence. A deterministic safety checker vets every proposal, a rule-based solver is the fallback, and a human supervisor approves the final plan.

## Layout

| Path | Purpose |
|---|---|
| `data/` | 2015 US DOT flight data (`flights.csv` not committed — download from the challenge Drive) |
| `src/sim/` | Scenario builder + queue simulator (no LLM) |
| `src/agents/` | ATC, Pilot and Ground agents — separate prompts and private state |
| `src/checker/` | Deterministic constraint checker (WAKE-01, RATE-01, FUEL-01, GATE-01, ...) |
| `src/solver/` | Non-AI fallback solver (baseline B1) |
| `eval/` | Batch evaluation vs baselines B0 (FCFS) and B1 |
| `ui/` | Supervisor UI: agent characters, message thread, consensus log, approve |
| `docs/` | Project brief |

## Rules of the build

- No LLM does arithmetic or legality checks.
- Max 3 negotiation turns, then fallback.
- Every number is labelled real (DOT) or synthetic.
