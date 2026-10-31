"""Runway order for the backup plan with OR-Tools CP-SAT. No AI.

CP-SAT only chooses the take-off order. The holds, the stands, the timing and the safety checks are
still worked out by backup.py, simulate() and the rule checker, exactly as for any other plan.

Model: each flight gets a wheels-off time no earlier than ready + normal taxi; every pair of flights
is kept apart by max(storm rate gap, wake gap) in whichever order they go; crew duty end is a hard
limit. The objective is total wheels-off delay, with a minute counted NO_HOLD_WEIGHT times for flights
that can't wait with engines off, because their wait is spent burning fuel on the taxiway.
"""
from src.sim.timing import rate_gap, wake_gap

SCALE = 100          # CP-SAT works in integers: hundredths of a minute
NO_HOLD_WEIGHT = 5
TIME_LIMIT_S = 2.0


def runway_order(s, no_hold: set[str]) -> list[str] | None:
    """Return flight IDs in take-off order, or None if OR-Tools is missing or finds no answer."""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return None

    fl = s.flights
    n = len(fl)
    if n < 2:
        return [f.flight for f in fl]
    rg = rate_gap(s)
    sep = lambda a, b: round(max(rg, wake_gap(a.wake, b.wake)) * SCALE)  # noqa: E731
    earliest = [round((f.ready + s.normal_taxi) * SCALE) for f in fl]
    horizon = max(earliest) + n * max(sep(a, b) for a in fl for b in fl) + SCALE

    m = cp_model.CpModel()
    wo = [m.NewIntVar(e, horizon, f"wo_{i}") for i, e in enumerate(earliest)]
    for i, f in enumerate(fl):
        if f.duty_end is not None:
            m.Add(wo[i] <= round(f.duty_end * SCALE))
    for i in range(n):
        for j in range(i + 1, n):
            i_first = m.NewBoolVar(f"b_{i}_{j}")
            m.Add(wo[j] >= wo[i] + sep(fl[i], fl[j])).OnlyEnforceIf(i_first)
            m.Add(wo[i] >= wo[j] + sep(fl[j], fl[i])).OnlyEnforceIf(i_first.Not())
    m.Minimize(sum((NO_HOLD_WEIGHT if f.flight in no_hold else 1) * (wo[i] - earliest[i]) for i, f in enumerate(fl)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT_S
    solver.parameters.num_workers = 8
    if solver.Solve(m) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [fl[i].flight for i in sorted(range(n), key=lambda i: (solver.Value(wo[i]), fl[i].ready))]
