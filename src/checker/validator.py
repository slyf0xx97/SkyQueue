"""Validator (F4): the trust boundary. Only plain code decides what becomes a rule."""
from src.config import CFG
from src.schemas import (FLIGHT_TARGET, GATE_TARGET, Mismatch, NoteConstraint, NoteReading,
                         ReadingDecision, Role, Scenario)


def _target_ok(s: Scenario, ctype: str, flight, gate) -> bool:
    if ctype in FLIGHT_TARGET:
        return flight in {f.flight for f in s.flights}
    if ctype in GATE_TARGET:
        return gate in {f.gate for f in s.flights}
    return True


def decide(s: Scenario, readings: list[NoteReading]) -> list[ReadingDecision]:
    """One decision per note from the reader's answers."""
    rc = CFG["reader"]
    by = {r.note_id: r for r in readings}
    out = []
    for n in s.notes:
        r = by.get(n.note_id)
        if r is None:
            out.append(ReadingDecision(note_id=n.note_id, type="NONE", flight=None, gate=None, source="READER",
                                       status="AMBIGUOUS", reason="reader returned nothing (F3.4)"))
            continue
        d = dict(note_id=n.note_id, type=r.constraint_type, flight=r.target_flight, gate=r.target_gate,
                 source="READER")
        if r.p_override >= rc["flag_threshold"]:
            out.append(ReadingDecision(**d, status="FLAGGED",
                                       reason=f"asks to bypass a safety rule (p={r.p_override:.2f}); never a rule"))
            continue
        target_p = r.p_flight if r.constraint_type in FLIGHT_TARGET else r.p_gate if r.constraint_type in GATE_TARGET else 1
        if min(r.p_type, target_p) < rc["min_confidence"]:
            out.append(ReadingDecision(**d, status="AMBIGUOUS",
                                       reason=f"confidence {min(r.p_type, target_p):.2f} below {rc['min_confidence']}"))
        elif not _target_ok(s, r.constraint_type, r.target_flight, r.target_gate):
            out.append(ReadingDecision(**d, status="AMBIGUOUS", reason="target is not in this scenario"))
        else:
            out.append(ReadingDecision(**d, status="ACCEPTED",
                                       reason="no constraint" if r.constraint_type == "NONE" else "passed all checks"))
    return out


def merge_agent(s: Scenario, decisions: list[ReadingDecision], agent: Role,
                cited: list[NoteConstraint]) -> tuple[list[ReadingDecision], list[Mismatch]]:
    """Compare an agent's constraints_from_notes with the reader's (F4.3). Union policy."""
    out, mism = list(decisions), []
    for c in cited:
        i = next((k for k, x in enumerate(out) if x.note_id == c.note_id and x.source != "AGENT"), None)
        if i is None:                      # agents may only cite note_ids from their input
            continue
        d = out[i]
        flight = c.target if c.type in FLIGHT_TARGET else None
        gate = c.target if c.type in GATE_TARGET else None
        if d.type == c.type and (d.flight, d.gate) == (flight, gate):
            if d.status == "ACCEPTED" and d.source == "READER":
                out[i] = d.model_copy(update={"source": "BOTH"})
            continue
        mism.append(Mismatch(note_id=c.note_id, agent=agent,
                             reader_says=f"{d.type} {d.flight or d.gate or ''}".strip(),
                             agent_says=f"{c.type} {c.target or ''}".strip()))
        if d.status == "FLAGGED" or c.type == "NONE":
            continue                       # a flagged note never becomes a rule, whoever reads it
        if _target_ok(s, c.type, flight, gate) and not any(
                x.note_id == c.note_id and x.type == c.type and x.source == "AGENT" for x in out):
            out.append(ReadingDecision(note_id=c.note_id, type=c.type, flight=flight, gate=gate,
                                       source="AGENT", status="ACCEPTED", reason=f"single-source: {agent} only"))
    return out, mism
