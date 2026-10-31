"""Scripted agents for building and tests (no API). Modes match the 3 demo scenarios.

agree:    Tower proposes notes-blind metering, Pilot and Ground counter from the notes, Tower merges,
          everyone accepts in round 2.
deadlock: Pilot and Ground keep rejecting, so the backup plan runs.
unsafe:   Tower's round-1 plan holds an aircraft at a gate without ground power and is blocked.
"""
from src.checker.rules import NO_HOLD_FLIGHT, active
from src.schemas import GATE_TARGET, AgentReply, NoteConstraint, PlanItem, Role, hhmm
from src.solver.backup import solve


class FakeAgents:
    name = "FAKE"

    def __init__(self, mode: str = "agree"):
        self.mode = mode

    def respond(self, role: Role, rnd: int, s, decisions, plan, feedback) -> AgentReply:
        cons = active(decisions)
        mine = [c for c in cons if (c.type in NO_HOLD_FLIGHT or c.type == "TURBULENCE") == (role == "PILOT")]
        cited = [NoteConstraint(type=c.type, target=c.flight or c.gate, note_id=c.note_id) for c in mine]
        if role == "TOWER":
            return self._tower(rnd, s, cons, feedback)

        if self.mode == "deadlock":
            return AgentReply(type="REJECT", constraints_from_notes=cited,
                              rationale="I can't take this: my crews need those planes gone now." if role == "PILOT"
                              else "I can't take this: I need those gates back for arrivals.")
        changes = []
        for ln in plan:
            f = s.flight(ln.flight)
            for c in mine:
                if role == "PILOT" and c.flight == ln.flight and c.type in NO_HOLD_FLIGHT and ln.action != "PUSH":
                    changes.append(PlanItem(flight=ln.flight, action="PUSH", runway_slot=ln.runway_slot))
                if role == "GROUND" and c.type in GATE_TARGET and c.gate == f.gate and ln.action == "GATE_HOLD":
                    changes.append(PlanItem(flight=ln.flight, action="REASSIGN_GATE", gate=s.remote_stands[-1],
                                            until=ln.until, runway_slot=ln.runway_slot))
        if changes:
            return AgentReply(type="COUNTER", plan=changes, constraints_from_notes=cited,
                              constraints_cited=["DUTY-01" if role == "PILOT" else "GATE-02"],
                              rationale=f"{changes[0].flight} can't wait at the gate. Change {len(changes)} line(s).")
        return AgentReply(type="ACCEPT", refs=[ln.line_id for ln in plan], constraints_from_notes=cited,
                          rationale="Crew hours, fuel and connections are covered." if role == "PILOT"
                          else "Every hold has power and the gates clear in time.")

    def _tower(self, rnd, s, cons, feedback) -> AgentReply:
        if rnd == 1:
            lines = solve(s, None).lines
            if self.mode == "unsafe":
                bad = next((f for f in s.flights if not f.gate_power), None)
                if bad:
                    lines = [ln if ln.flight != bad.flight else
                             ln.model_copy(update={"action": "GATE_HOLD", "gate": None,
                                                   "until": hhmm(bad.ready + 15)})
                             for ln in lines]
            return AgentReply(type="PROPOSE", plan=[PlanItem(**ln.model_dump(include=set(PlanItem.model_fields)))
                                                    for ln in lines],
                              constraints_cited=["RATE-01", "WAKE-01"],
                              rationale="Keep engines off: each plane waits at its gate until its runway slot.")
        lines = solve(s, cons).lines
        return AgentReply(type="PROPOSE", plan=[PlanItem(**ln.model_dump(include=set(PlanItem.model_fields)))
                                                for ln in lines],
                          constraints_cited=["RATE-01", "WAKE-01"],
                          rationale="Same slots, but I now respect every ops note.")
