"""Shared Pydantic models. Times are minutes after local midnight unless named *_hhmm."""
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ConstraintType = Literal["NO_GATE_HOLD", "DUTY_LIMIT", "PRIORITY_CONNECTION",
                         "TURBULENCE", "GATE_UNAVAILABLE", "NONE"]
Role = Literal["TOWER", "PILOT", "GROUND"]
Action = Literal["PUSH", "GATE_HOLD", "REASSIGN_GATE"]
Provenance = Literal["real", "synthetic", "estimate"]

FLIGHT_TARGET = {"DUTY_LIMIT", "PRIORITY_CONNECTION", "TURBULENCE"}
GATE_TARGET = {"NO_GATE_HOLD", "GATE_UNAVAILABLE"}


def hhmm(minutes: int) -> str:
    return f"{int(minutes) // 60 % 24:02d}:{int(minutes) % 60:02d}"


def minutes(hhmm_str: str) -> int:
    h, m = hhmm_str.split(":")
    return int(h) * 60 + int(m)


# ---------- scenario ----------

class Flight(BaseModel):
    flight: str                     # AIRLINE + FLIGHT_NUMBER, e.g. UA1234
    airline: str
    tail: Optional[str] = None
    dest: str
    # real (2015 DOT)
    sched_dep: int
    ready: int                      # real DEPARTURE_TIME (gate departure)
    real_wheels_off: int
    real_taxi_out: int
    air_time: int
    taxi_in: int
    sched_arr: int
    # synthetic (fixed seed)
    wake: Literal["L", "M", "H"]
    gate: str
    gate_power: bool
    inbound_at: Optional[int]       # inbound needs this gate at this time
    fuel_kg: float
    trip_reserve_kg: float
    burn_kg_min: float
    duty_end: int
    ramp_shift_end: int
    connecting_pax: int

    SYNTHETIC: ClassVar[tuple] = ("wake", "gate", "gate_power", "inbound_at", "fuel_kg",
                                  "trip_reserve_kg", "burn_kg_min", "duty_end",
                                  "ramp_shift_end", "connecting_pax")


class NoteTruth(BaseModel):
    """Hidden ground truth. Never shown to agents or readers."""
    kind: str                       # template name
    type: ConstraintType
    flight: Optional[str] = None
    gate: Optional[str] = None
    urgency: int = 0
    injection: bool = False


class Note(BaseModel):
    note_id: str
    text: str
    source: str = ""                # Crew, Ramp, Dispatch, Pilot report, Ops chat, You
    received: Optional[str] = None  # HH:MM local
    flights: list[str] = []
    gates: list[str] = []
    synthetic: bool = True
    truth: NoteTruth


class Scenario(BaseModel):
    scenario_id: str
    airport: str
    date: str
    trigger_flight: str
    trigger_reason: str
    flights: list[Flight]
    remote_stands: list[str]
    rate_per_15: float              # real wheels-off rate in the ±60 min window
    normal_taxi: float              # airport's 10th percentile TAXI_OUT
    notes: list[Note] = []

    def flight(self, fid: str) -> Flight:
        return next(f for f in self.flights if f.flight == fid)

    @property
    def gates(self) -> list[str]:
        return [f.gate for f in self.flights] + self.remote_stands


# ---------- note reading ----------

class NoteReading(BaseModel):
    note_id: str
    reader: Literal["CLAUDE", "FAKE"]
    constraint_type: ConstraintType
    p_type: float
    target_flight: Optional[str]
    p_flight: float
    target_gate: Optional[str]
    p_gate: float
    urgency: int = Field(ge=0, le=3)
    p_override: float


class ReadingDecision(BaseModel):
    note_id: str
    type: ConstraintType
    flight: Optional[str]
    gate: Optional[str]
    source: Literal["READER", "AGENT", "BOTH"]
    status: Literal["ACCEPTED", "AMBIGUOUS", "FLAGGED"]
    reason: str = ""


class Mismatch(BaseModel):
    note_id: str
    agent: Role
    reader_says: str
    agent_says: str


# ---------- plans and messages ----------

class Check(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    rule_id: str
    passed: bool = Field(alias="pass")
    detail: str
    flight: Optional[str] = None    # the plan line this check covers; None = whole plan
    hard: bool = True


class PlanItem(BaseModel):
    """One line as an agent writes it. No IDs: code assigns them."""
    flight: str
    action: Action
    until: Optional[str] = None      # HH:MM, for GATE_HOLD
    runway_slot: Optional[int] = None
    gate: Optional[str] = None       # for REASSIGN_GATE


class PlanLine(PlanItem):
    line_id: str
    proposed_in: str                 # msg_id, or BACKUP
    agreed_by: list[Role] = []
    notes_used: list[str] = []
    checks: list[Check] = []
    provenance: dict[str, Provenance] = {}


class NoteConstraint(BaseModel):
    type: ConstraintType
    target: Optional[str] = None
    note_id: str


class AgentReply(BaseModel):
    """What an agent returns. Validated before it becomes a Message."""
    type: Literal["PROPOSE", "COUNTER", "ACCEPT", "REJECT"]
    plan: list[PlanItem] = []
    refs: list[str] = []             # line_ids it accepts or changes
    constraints_from_notes: list[NoteConstraint] = []
    constraints_cited: list[str] = []
    rationale: str = Field(default="", max_length=300)


class Message(AgentReply):
    model_config = ConfigDict(populate_by_name=True)
    msg_id: str
    round: int
    sender: Role = Field(alias="from")
    lines: list[PlanLine] = []       # plan with code-assigned line_ids
    blocked_by: list[str] = []       # rule IDs if the checker refused it
    timestamp: str


class FlightTiming(BaseModel):
    flight: str
    gate: str                        # gate it pushes from (after any move)
    push: int
    hold_min: int
    wheels_off: float
    taxi_min: float
    fuel_kg: float
    co2_kg: float
    dep_delay: int                   # push minus scheduled departure
    arrival: int
    arr_delay: int
    runway_pos: int


class Plan(BaseModel):
    source: Literal["AGREED", "BACKUP", "B0", "B1", "B2"]
    lines: list[PlanLine]
    timing: list[FlightTiming] = []
    checks: list[Check] = []
    blocked_by: list[str] = []
    note: str = ""
    summary: str = ""
