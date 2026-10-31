"""Backup plan (F10). No AI.

Runway order: OR-Tools CP-SAT when optimise=True (see cpsat.py), else first come first served.
Then metering: each flight is held (engines off) until it can
taxi straight to its runway slot. Holds that the gate can't take go to a remote stand, and stands go
first to the flights with the least fuel slack. The CP-SAT order is kept only if it passes every hard
rule and burns no more taxi fuel than the first-come-first-served order.
"""
from src.checker.rules import NO_HOLD_FLIGHT, active, check, hard_failures
from src.config import CFG
from src.schemas import GATE_TARGET, PlanItem, PlanLine, Plan, Scenario, hhmm
from src.sim.timing import simulate
from src.solver.cpsat import runway_order

BUFFER_MIN = 2   # arrive at the runway queue this long before the slot


def _runway_order(s: Scenario) -> list[str]:
    """FCFS by ready time, then bubble up any flight that would miss its crew duty end."""
    order = [f.flight for f in sorted(s.flights, key=lambda f: f.ready)]
    duty = {f.flight: f.duty_end for f in s.flights}
    for _ in range(len(order) ** 2):
        t = {x.flight: x for x in simulate(s, _slots(order))}
        late = next((i for i, fid in enumerate(order) if i and t[fid].wheels_off > duty[fid]), None)
        if late is None:
            break
        order[late - 1], order[late] = order[late], order[late - 1]
    return order


def _slots(order: list[str]) -> list[PlanItem]:
    return [PlanItem(flight=fid, action="PUSH", runway_slot=i) for i, fid in enumerate(order, 1)]


def solve(s: Scenario, constraints=None, source="BACKUP", blocked_by=None, optimise=False) -> Plan:
    no_hold = {c.flight for c in active(constraints) if c.type in NO_HOLD_FLIGHT}
    greedy = _plan(s, _runway_order(s), constraints, source, blocked_by)
    order = runway_order(s, no_hold) if optimise else None
    if not order:
        return greedy
    best = _plan(s, order, constraints, source, blocked_by, solver="OR-Tools CP-SAT")
    fuel = lambda p: sum(t.fuel_kg for t in p.timing)  # noqa: E731
    if hard_failures(best.checks) or (not hard_failures(greedy.checks) and fuel(best) > fuel(greedy)):
        return greedy
    return best


def _plan(s: Scenario, order: list[str], constraints, source, blocked_by, solver="first come first served") -> Plan:
    cons = active(constraints)
    no_hold = {c.flight for c in cons if c.type in NO_HOLD_FLIGHT}
    turb = {c.flight for c in cons if c.type == "TURBULENCE"}
    bad_gates = {c.gate for c in cons if c.type in GATE_TARGET}
    fl = {f.flight: f for f in s.flights}

    base = {t.flight: t for t in simulate(s, _slots(order))}
    items, need_stand = {}, []
    for slot, fid in enumerate(order, 1):
        f, t = fl[fid], base[fid]
        hold = int(t.wheels_off - s.normal_taxi - BUFFER_MIN - f.ready)
        if fid in turb:
            hold = max(hold, CFG["turbulence_wait_min"])
        hold = min(hold, f.ramp_shift_end - f.ready)          # CREW-01
        item = PlanItem(flight=fid, action="PUSH", runway_slot=slot)
        if hold > 0 and fid not in no_hold:
            gate_ok = f.gate_power and f.gate not in bad_gates
            if gate_ok and (f.inbound_at is None or f.ready + hold <= f.inbound_at):
                item = PlanItem(flight=fid, action="GATE_HOLD", until=hhmm(f.ready + hold), runway_slot=slot)
            else:
                need_stand.append((fid, hold))
        items[fid] = item

    slack = lambda fid: (fl[fid].fuel_kg - fl[fid].trip_reserve_kg) / fl[fid].burn_kg_min  # noqa: E731
    stands = list(s.remote_stands)
    for fid, hold in sorted(need_stand, key=lambda x: slack(x[0])):
        f, slot = fl[fid], items[fid].runway_slot
        if stands:
            items[fid] = PlanItem(flight=fid, action="REASSIGN_GATE", gate=stands.pop(0),
                                  until=hhmm(f.ready + hold), runway_slot=slot)
        elif f.gate_power and f.gate not in bad_gates and f.inbound_at and f.inbound_at > f.ready:
            items[fid] = PlanItem(flight=fid, action="GATE_HOLD", until=hhmm(f.inbound_at), runway_slot=slot)

    lines = [PlanLine(**items[fid].model_dump(), line_id=f"BK-{i:02d}", proposed_in="BACKUP")
             for i, fid in enumerate(order, 1)]
    timing, checks = check(s, lines, constraints)
    fails = hard_failures(checks)
    return Plan(source=source, lines=lines, timing=timing, checks=checks, blocked_by=blocked_by or [],
                note=f"no safe improvement found: {', '.join(fails)}" if fails else f"runway order: {solver}")


def first_come_first_served(s: Scenario, constraints=None) -> Plan:
    """B0: today's order. Everyone pushes when ready, runway in push order."""
    lines = [PlanLine(flight=f.flight, action="PUSH", line_id=f"B0-{i:02d}", proposed_in="B0")
             for i, f in enumerate(sorted(s.flights, key=lambda f: f.ready), 1)]
    timing, checks = check(s, lines, constraints)
    return Plan(source="B0", lines=lines, timing=timing, checks=checks)
