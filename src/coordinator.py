"""Negotiation coordinator (F7). Code assigns every ID and writes every trace link.

Run one scenario:  python -m src.coordinator [demo1|demo2|demo3]
"""
import sys
import time

from src.agents.llm import USAGE
from src.checker.rules import hard_failures, rule_summary
from src.checker.validator import decide, merge_agent
from src.config import CFG
from src.log import RunLog, now
from src.schemas import Message, Plan, PlanLine, Scenario
from src.solver.backup import solve

PROVENANCE = {"flight": "real", "ready": "real", "gate": "synthetic", "push": "estimate",
              "wheels_off": "estimate", "arrival": "estimate", "fuel_kg": "estimate"}


def _key(it) -> tuple:
    return (it.flight, it.action, it.until, it.runway_slot, it.gate)


class Coordinator:
    def __init__(self, s: Scenario, reader, agents, log: RunLog, round_limit: int | None = None):
        self.s, self.reader, self.agents, self.log = s, reader, agents, log
        self.round_limit = round_limit or CFG["agents"]["round_limit"]
        self.known: dict[tuple, tuple[str, str]] = {}   # line key -> (line_id, msg_id that first proposed it)
        self.seq = 0
        self.messages: list[Message] = []
        self.mismatches = []
        self.blocked: list[str] = []

    def _lines(self, items, msg_id) -> list[PlanLine]:
        out = []
        for it in items:
            k = _key(it)
            if k not in self.known:
                self.seq += 1
                self.known[k] = (f"L{self.seq:03d}", msg_id)
            line_id, first = self.known[k]
            out.append(PlanLine(**it.model_dump(), line_id=line_id, proposed_in=first, provenance=PROVENANCE))
        return out

    def _message(self, reply, rnd, role, n) -> Message:
        msg_id = f"R{rnd}-{role}-{n:02d}"
        valid_notes = {x.note_id for x in self.s.notes}
        reply.constraints_from_notes = [c for c in reply.constraints_from_notes if c.note_id in valid_notes]
        m = Message(**reply.model_dump(), msg_id=msg_id, round=rnd, sender=role, timestamp=now(),
                    lines=self._lines(reply.plan, msg_id))
        for ln in m.lines:
            self.log.link("message", msg_id, "flight", ln.flight)
        for c in m.constraints_from_notes:
            self.log.link("message", msg_id, "note", c.note_id)
        self.decisions, mism = merge_agent(self.s, self.decisions, role, reply.constraints_from_notes)
        for x in mism:
            self.log.mismatch(rnd, x)
        self.mismatches += mism
        self.messages.append(m)
        return m

    def run(self) -> Plan:
        t0 = time.time()
        USAGE.clear()
        s, log = self.s, self.log
        log.run(s, self.reader.name, self.agents.name)
        readings = self.reader.read(s)
        for r in readings:
            log.reading(r)
        self.decisions = decide(s, readings)
        for n in s.notes:
            for f in n.flights:
                log.link("note", n.note_id, "flight", f)

        plan_lines, agreed, feedback = None, False, []
        for rnd in range(1, self.round_limit + 1):
            reply = self.agents.respond("TOWER", rnd, s, self.decisions, plan_lines or [], feedback)
            prop = self._message(reply, rnd, "TOWER", 1)
            if not prop.lines:                         # Tower sent no plan (reject or failed call): nothing to check
                log.message(prop)
                continue
            timing, checks = _check(s, prop.lines, self.decisions)
            log.checks(prop.msg_id, checks)
            fails = hard_failures(checks)
            if fails:                                  # F7.6: back to the sender, never shown to the others
                prop.blocked_by = fails
                # a blocked proposal never counts as where a line was proposed
                self.known = {k: v for k, v in self.known.items() if v[1] != prop.msg_id}
                self.blocked += fails
                feedback = [f"{prop.msg_id} blocked by {', '.join(fails)}"]
                log.message(prop)
                continue
            log.message(prop)
            plan_lines, feedback, replies = prop.lines, [], []
            for role in ("PILOT", "GROUND"):
                r = self.agents.respond(role, rnd, s, self.decisions, plan_lines, [])
                m = self._message(r, rnd, role, 1)
                log.message(m)
                replies.append(m)
                if m.type == "COUNTER":
                    feedback.append(f"{m.msg_id} counters: " + "; ".join(
                        f"{ln.line_id} {ln.flight} {ln.action} {ln.until or ''} {ln.gate or ''}" for ln in m.lines))
            if all(m.type == "ACCEPT" for m in replies):
                agreed = True
                break

        if agreed:
            for ln in plan_lines:
                ln.agreed_by = ["TOWER", "PILOT", "GROUND"]
            timing, checks = _check(s, plan_lines, self.decisions)
            plan = Plan(source="AGREED", lines=plan_lines, timing=timing, checks=checks)
        else:
            plan = solve(s, self.decisions, blocked_by=sorted(set(self.blocked)) or ["NO-AGREEMENT"], optimise=True)

        self._finish(plan)
        log.usage(USAGE)
        log.outcome(f"{plan.source} in {round(time.time() - t0, 1)} s")
        log.commit()
        return plan

    def _finish(self, plan: Plan):
        """Attach notes_used and checks to every line and write the trace links (F6.4, F12.2)."""
        s, log = self.s, self.log
        check_ids = log.checks("PLAN", plan.checks)
        accepted = [d for d in self.decisions if d.status == "ACCEPTED" and d.type != "NONE"]
        for ln in plan.lines:
            gate = s.flight(ln.flight).gate
            ln.notes_used = sorted({d.note_id for d in accepted if d.flight == ln.flight or d.gate == gate})
            ln.checks = [c for c in plan.checks if c.flight == ln.flight]
            log.link("plan_line", ln.line_id, "flight", ln.flight)
            log.link("plan_line", ln.line_id, "message", ln.proposed_in)
            for a in ln.agreed_by:
                log.link("plan_line", ln.line_id, "agent", a)
            for nid in ln.notes_used:
                log.link("plan_line", ln.line_id, "note", nid)
            for c, cid in zip(plan.checks, check_ids):
                if c.flight == ln.flight:
                    log.link("plan_line", ln.line_id, "rule_check", cid)
        for d in self.decisions:
            log.decision_row(d)
        log.plan(plan)


def _check(s, lines, decisions):
    from src.checker.rules import check
    return check(s, lines, decisions)


def main(argv):
    from src.agents.fake import FakeAgents
    from src.agents.readers import get_reader
    from src.sim.demo import DEMOS, demo_scenario

    name = argv[1] if len(argv) > 1 else "demo1"
    s = demo_scenario(name)
    agents = FakeAgents(DEMOS[name]["mode"])
    if CFG["agents"]["kind"] == "claude":
        from src.agents.claude import ClaudeAgents
        agents = ClaudeAgents()
    log = RunLog(f"{name}-{s.scenario_id}")
    c = Coordinator(s, get_reader(), agents, log)
    plan = c.run()
    for m in c.messages:
        print(f"{m.msg_id:14} {m.type:8} {('BLOCKED ' + ','.join(m.blocked_by)) if m.blocked_by else ''} {m.rationale}")
    print("plan:", plan.source, plan.blocked_by or "", plan.note)
    print("rules:", {k: v for k, v in rule_summary(plan.checks).items() if not v} or "all pass")
    print("decisions:", [(d.note_id, d.type, d.status, d.source) for d in c.decisions])
    print("run:", log.run_id)


if __name__ == "__main__":
    main(sys.argv)
