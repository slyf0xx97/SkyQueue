from src.checker.rules import hard_failures, truth_constraints
from src.sim.demo import demo_scenario
from src.solver.backup import solve


def test_cpsat_backup_is_safe_and_never_burns_more_than_greedy():
    s = demo_scenario("demo2", "ORD")
    c = truth_constraints(s.notes)
    greedy, best = solve(s, c), solve(s, c, optimise=True)
    fuel = lambda p: sum(t.fuel_kg for t in p.timing)  # noqa: E731
    assert not hard_failures(best.checks)
    assert fuel(best) <= fuel(greedy)
    assert sorted(ln.flight for ln in best.lines) == sorted(f.flight for f in s.flights)
