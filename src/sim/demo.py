"""Demo samples (F13.5) at any of the busiest airports: real trigger rows on storm days, fixed note mixes."""
import zlib
from functools import lru_cache

import numpy as np
import pandas as pd

from src.checker.rules import hard_failures, truth_constraints
from src.config import CFG, ROOT
from src.schemas import Note, NoteTruth
from src.sim.notes import make_notes
from src.sim.scenarios import build, load_flights, triggers
from src.solver.backup import solve

AIRPORTS = ["ORD", "ATL", "DFW", "DEN", "LAX", "SFO", "LAS", "LGA"]   # most trigger rows in the 2015 sample

DEMOS = {
    "demo1": {"mode": "agree", "offset": 0, "name": "Storm at {city}", "blurb": "Agents agree in round 2", "icon": "i-storm",
              "notes": ["duty", "broken_gpu", "connection", "turbulence", "ambiguous"]},
    "demo2": {"mode": "deadlock", "offset": 1, "name": "Gate standoff", "blurb": "No deal, so code builds a backup plan", "icon": "i-gate",
              "notes": ["gate_unavailable", "turbulence", "duty", "ambiguous"]},
    "demo3": {"mode": "unsafe", "offset": 2, "name": "Bad advice", "blurb": "A hostile note and an unsafe plan, both stopped", "icon": "i-warn",
              "notes": ["injection", "broken_gpu", "connection", "ambiguous"]},
}


@lru_cache(maxsize=None)
def airport_info(code: str) -> dict:
    a = pd.read_csv(ROOT / "data" / "airports.csv").set_index("IATA_CODE").loc[code]
    return {"code": code, "name": a.AIRPORT, "city": a.CITY, "state": a.STATE, "icao": "K" + code}


@lru_cache(maxsize=None)
def storm_days(airport: str) -> tuple:
    t = triggers(load_flights(), airport)
    return tuple(t.groupby(["MONTH", "DAY"]).size().sort_values(ascending=False).index[:15])


@lru_cache(maxsize=None)
def demo_scenario(name: str, airport: str = "ORD"):
    """First storm day (skipping the other samples' days) where a safe plan exists."""
    d, df = DEMOS[name], load_flights()
    t = triggers(df, airport)
    days = storm_days(airport)
    mine = days[d["offset"]::3]
    for mo, dy in mine + tuple(x for x in days if x not in mine):
        tt = t[(t.MONTH == mo) & (t.DAY == dy)]
        s = build(df, tt.index[len(tt) // 2], with_notes=False)
        rng = np.random.default_rng(CFG["scenario"]["seed"] + zlib.crc32(f"{name}{airport}".encode()))
        s.notes = make_notes(s, rng, d["notes"])
        ok = len(s.flights) >= 12 and not hard_failures(solve(s, truth_constraints(s.notes)).checks)
        if ok and (d["mode"] != "unsafe" or any(not f.gate_power for f in s.flights)):
            return s
    return s


def with_visitor_notes(s, rows: list[dict]):
    """Visitor-written notes have no hidden answer: only a live reader can read them."""
    s = s.model_copy(deep=True)
    for r in rows[:8]:
        text = f"{r['ref']}: {r['text']}" if r.get("ref") else r["text"]
        s.notes.append(Note(note_id=f"N{len(s.notes) + 1}", text=text[:240], source=r.get("source") or "You",
                            received=r.get("received"), truth=NoteTruth(kind="visitor", type="NONE")))
    return s
