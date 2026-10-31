"""Timing calculator (F8). No AI.

push = ready, or the hold-until time. Runway order follows runway_slot when given, else push order.
wheels_off = max(push + normal taxi, previous wheels_off + max(15 / rate, wake gap)).
"""
import math

from src.config import CFG
from src.schemas import FlightTiming, PlanItem, Scenario, minutes


def wake_gap(leader: str, follower: str) -> float:
    return CFG["wake_gap_min"][leader][follower]


def rate_gap(s: Scenario) -> float:
    return 15 / max(1, math.floor(s.rate_per_15))


def simulate(s: Scenario, lines: list[PlanItem]) -> list[FlightTiming]:
    by = {ln.flight: ln for ln in lines}

    def push_of(f):
        ln = by.get(f.flight)
        if ln and ln.until and ln.action in ("GATE_HOLD", "REASSIGN_GATE"):
            return max(f.ready, minutes(ln.until))
        return f.ready

    def slot_of(f):
        ln = by.get(f.flight)
        return ln.runway_slot if ln and ln.runway_slot is not None else None

    order = sorted(s.flights, key=lambda f: (slot_of(f) is None, slot_of(f) or 0, push_of(f), f.ready))
    out, prev = [], None
    for pos, f in enumerate(order, 1):
        push = push_of(f)
        wo = push + s.normal_taxi
        if prev:
            wo = max(wo, prev[1] + max(rate_gap(s), wake_gap(prev[0].wake, f.wake)))
        prev = (f, wo)
        taxi = wo - push
        fuel = taxi * f.burn_kg_min
        arrival = round(wo + f.air_time + f.taxi_in)
        ln = by.get(f.flight)
        out.append(FlightTiming(
            flight=f.flight, gate=ln.gate if ln and ln.action == "REASSIGN_GATE" and ln.gate else f.gate,
            push=push, hold_min=push - f.ready, wheels_off=round(wo, 2), taxi_min=round(taxi, 1),
            fuel_kg=round(fuel, 1), co2_kg=round(fuel * CFG["co2_per_kg_fuel"], 1),
            dep_delay=push - f.sched_dep, arrival=arrival, arr_delay=arrival - f.sched_arr, runway_pos=pos))
    return out
