"""Safety rules (F9). No AI. Every check covers one plan line (flight) or the whole plan."""
import math

from src.config import CFG
from src.schemas import (GATE_TARGET, Check, FlightTiming, Note, PlanItem, ReadingDecision,
                         Scenario, hhmm, minutes)
from src.sim.timing import simulate, wake_gap

HARD = ["PLAN-01", "WAKE-01", "RATE-01", "TAXI-01", "FUEL-01", "DUTY-01", "GATE-01", "GATE-02", "CREW-01"]
SOFT = ["CONN-01", "CREW-02", "THRU-01"]
NO_HOLD_FLIGHT = {"DUTY_LIMIT", "PRIORITY_CONNECTION"}
EPS = 1e-6


def truth_constraints(notes: list[Note]) -> list[ReadingDecision]:
    """Hidden ground truth as decisions, for scoring 'hidden constraints broken'."""
    return [ReadingDecision(note_id=n.note_id, type=n.truth.type, flight=n.truth.flight, gate=n.truth.gate,
                            source="READER", status="ACCEPTED")
            for n in notes if n.truth.type != "NONE" and not n.truth.injection]


def active(constraints) -> list[ReadingDecision]:
    return [c for c in (constraints or []) if c.status == "ACCEPTED" and c.type != "NONE"]


def _structure(s: Scenario, lines: list[PlanItem]) -> list[Check]:
    ids = {f.flight for f in s.flights}
    out, seen, stands = [], set(), set()
    for ln in lines:
        problems = []
        if ln.flight not in ids:
            problems.append("unknown flight")
        if ln.flight in seen:
            problems.append("duplicate line")
        seen.add(ln.flight)
        if ln.action == "REASSIGN_GATE":
            if ln.gate not in s.remote_stands:
                problems.append(f"{ln.gate} is not a free remote stand")
            elif ln.gate in stands:
                problems.append(f"{ln.gate} already used")
            stands.add(ln.gate)
        if ln.until:
            try:
                minutes(ln.until)
            except ValueError:
                problems.append(f"bad time {ln.until}")
        if ln.action == "GATE_HOLD" and not ln.until:
            problems.append("GATE_HOLD needs until")
        out.append(Check(rule_id="PLAN-01", passed=not problems, flight=ln.flight,
                         detail="; ".join(problems) or "line is well formed"))
    return out


def check(s: Scenario, lines: list[PlanItem], constraints=None) -> tuple[list[FlightTiming], list[Check]]:
    checks = _structure(s, lines)
    if not all(c.passed for c in checks):
        return [], checks
    timing = simulate(s, lines)
    fl = {f.flight: f for f in s.flights}
    moved = {ln.flight for ln in lines if ln.action == "REASSIGN_GATE"}
    seq = sorted(timing, key=lambda t: t.runway_pos)
    cap, limit = CFG["taxiway_capacity"], math.floor(s.rate_per_15)

    for i, t in enumerate(seq):
        f = fl[t.flight]
        add = lambda rid, ok, detail, hard=True: checks.append(  # noqa: E731
            Check(rule_id=rid, passed=ok, detail=detail, flight=t.flight, hard=hard))
        if i:
            p = seq[i - 1]
            need = wake_gap(fl[p.flight].wake, f.wake)
            gap = t.wheels_off - p.wheels_off
            add("WAKE-01", gap >= need - EPS, f"{gap:.1f} min after {p.flight} ({fl[p.flight].wake}->{f.wake}), needs {need}")
        else:
            add("WAKE-01", True, "first departure")
        n15 = sum(1 for u in seq if t.wheels_off - EPS <= u.wheels_off < t.wheels_off + 15 - EPS)
        add("RATE-01", n15 <= limit, f"{n15} departures in the 15 min from {hhmm(t.wheels_off)}, limit {limit}")
        on_taxi = sum(1 for u in seq if u.push <= t.push < u.wheels_off - EPS)
        add("TAXI-01", on_taxi <= cap, f"{on_taxi} aircraft taxiing at {hhmm(t.push)}, capacity {cap}")
        left = f.fuel_kg - t.fuel_kg
        add("FUEL-01", left >= f.trip_reserve_kg, f"{left:.0f} kg after taxi vs {f.trip_reserve_kg:.0f} kg trip+reserve")
        add("DUTY-01", t.wheels_off <= f.duty_end, f"wheels-off {hhmm(t.wheels_off)}, duty ends {hhmm(f.duty_end)}")
        leave = f.ready if t.flight in moved else t.push
        if f.inbound_at is None:
            add("GATE-01", True, f"no inbound needs {f.gate}")
        else:
            add("GATE-01", leave <= f.inbound_at, f"leaves {f.gate} at {hhmm(leave)}, inbound needs it {hhmm(f.inbound_at)}")
        gate_hold = t.hold_min > 0 and t.flight not in moved
        add("GATE-02", not (gate_hold and not f.gate_power),
            f"{t.hold_min} min hold at {f.gate}, ground power {'yes' if f.gate_power else 'no'}")
        add("CREW-01", t.push <= f.ramp_shift_end, f"push {hhmm(t.push)}, ramp shift ends {hhmm(f.ramp_shift_end)}")
        if f.connecting_pax:
            add("CONN-01", t.arr_delay <= CFG["missed_connection_min"],
                f"{f.connecting_pax} connecting pax, arrival delay {t.arr_delay} min", hard=False)
        late = f.ramp_shift_end - CFG["ramp_overtime_window"] < t.push <= f.ramp_shift_end
        add("CREW-02", not late, f"push {f.ramp_shift_end - t.push} min before ramp shift end", hard=False)

        for c in active(constraints):
            if c.type in GATE_TARGET and c.gate == f.gate:
                add(f"NOTE-{c.note_id}", not gate_hold, f"{c.type} at {c.gate}: hold here {t.hold_min} min")
            elif c.type in NO_HOLD_FLIGHT and c.flight == t.flight:
                add(f"NOTE-{c.note_id}", t.hold_min == 0, f"{c.type}: {t.flight} held {t.hold_min} min")
            elif c.type == "TURBULENCE" and c.flight == t.flight:
                w = CFG["turbulence_wait_min"]
                add(f"NOTE-{c.note_id}", t.hold_min >= w, f"TURBULENCE: {t.flight} waits {t.hold_min} of {w} min")

    last = max(t.wheels_off for t in seq)
    checks.append(Check(rule_id="THRU-01", passed=True, hard=False,
                        detail=f"{len(seq)} departures, last wheels-off {hhmm(last)}"))
    return timing, checks


def hard_failures(checks: list[Check]) -> list[str]:
    return sorted({c.rule_id for c in checks if c.hard and not c.passed})


def rule_summary(checks: list[Check]) -> dict[str, bool]:
    """Rule table row: rule_id -> passed, for one proposal."""
    out: dict[str, bool] = {}
    for c in checks:
        out[c.rule_id] = out.get(c.rule_id, True) and c.passed
    return out
