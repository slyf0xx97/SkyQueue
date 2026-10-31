"""Build scenarios from trigger rows in the 2015 DOT sample (F1). No AI."""
import zlib
from functools import lru_cache

import numpy as np
import pandas as pd

from src.config import CFG, ROOT
from src.schemas import Flight, Scenario

# Gate letters only; the DOT data has no gates, so every gate is synthetic.
GATE_POOL = [f"{c}{n}" for c in "BCF" for n in range(1, 31)]


def _mins(hhmm) -> int:
    hhmm = int(hhmm)
    return (hhmm // 100 % 24) * 60 + hhmm % 100


@lru_cache(maxsize=1)
def load_flights() -> pd.DataFrame:
    full = ROOT / "data" / "flights.csv"
    if full.exists():
        df = pd.read_csv(full, low_memory=False)
    else:  # hosted copy: only the 8 demo airports' departures, original row numbers kept (scripts/make_extract.py)
        df = pd.read_csv(ROOT / "data" / "flights_extract.csv.gz", index_col="ROW", low_memory=False)
    df["valid"] = (df.DIVERTED == 0) & (df.CANCELLED == 0) & df.TAXI_OUT.notna() \
        & df.DEPARTURE_TIME.notna() & df.WHEELS_OFF.notna() & df.AIR_TIME.notna()
    return df


def declined(df: pd.DataFrame, airport: str) -> pd.DataFrame:
    """Trigger rows we skip and log (F1.2)."""
    return df[(df.ORIGIN_AIRPORT == airport) & ~df.valid]


def triggers(df: pd.DataFrame, airport: str) -> pd.DataFrame:
    t = df[(df.ORIGIN_AIRPORT == airport) & df.valid
           & ((df.WEATHER_DELAY > 15) | (df.LATE_AIRCRAFT_DELAY > 20))]
    dep = t.DEPARTURE_TIME.astype(int).map(_mins)
    w = CFG["scenario"]["window_min"]
    # shortcut: skip windows that cross midnight; the sample has enough daytime rows
    return t[(dep >= w + 30) & (dep <= 1440 - w - 30)]


def normal_taxi(df: pd.DataFrame, airport: str) -> float:
    return float(df[(df.ORIGIN_AIRPORT == airport) & df.valid].TAXI_OUT.quantile(0.10))


def _flight_from_row(r, rng: np.random.Generator, gate: str) -> Flight:
    ready = _mins(r.DEPARTURE_TIME)
    sched = _mins(r.SCHEDULED_DEPARTURE)
    if sched - ready > 600:          # departed after midnight vs schedule
        ready += 1440
    wo = _mins(r.WHEELS_OFF)
    if wo < ready - 600:
        wo += 1440
    wake = rng.choice(["H", "M", "L"], p=[0.15, 0.75, 0.10])
    burn = rng.uniform(20, 30) if wake == "H" else rng.uniform(9, 14)
    fuel = rng.uniform(6000, 40000)
    slack = burn * rng.uniform(20, 70)  # kg above trip + reserve: 20 to 70 min of taxi
    return Flight(
        flight=f"{r.AIRLINE}{int(r.FLIGHT_NUMBER)}", airline=r.AIRLINE,
        tail=None if pd.isna(r.TAIL_NUMBER) else str(r.TAIL_NUMBER), dest=str(r.DESTINATION_AIRPORT),
        sched_dep=sched, ready=ready, real_wheels_off=wo, real_taxi_out=int(r.TAXI_OUT),
        air_time=int(r.AIR_TIME), taxi_in=int(r.TAXI_IN) if not pd.isna(r.TAXI_IN) else 8,
        # arrival in origin local time, so delay is comparable with our computed arrival
        sched_arr=sched + int(r.SCHEDULED_TIME),
        wake=wake, gate=gate, gate_power=bool(rng.random() < 0.85),
        inbound_at=int(ready + rng.integers(10, 60)) if rng.random() < 0.4 else None,
        fuel_kg=round(fuel), trip_reserve_kg=round(fuel - slack), burn_kg_min=round(burn, 1),
        duty_end=int(ready + rng.integers(30, 240)),
        ramp_shift_end=int(ready + rng.integers(20, 200)),
        connecting_pax=int(rng.integers(1, 40)) if rng.random() < 0.4 else 0,
    )


def build(df: pd.DataFrame, row_index: int, max_queue: int | None = None, with_notes=True) -> Scenario:
    """Scenario for one trigger row. max_queue=None keeps the whole ±60 min window."""
    from src.sim.notes import make_notes

    sc = CFG["scenario"]
    max_queue = sc["max_queue"] if max_queue is None else (max_queue or None)
    trig = df.loc[row_index]
    airport, w = trig.ORIGIN_AIRPORT, sc["window_min"]
    day = df[(df.ORIGIN_AIRPORT == airport) & (df.MONTH == trig.MONTH) & (df.DAY == trig.DAY) & df.valid]
    t0 = _mins(trig.DEPARTURE_TIME)
    dep = day.DEPARTURE_TIME.astype(int).map(_mins)
    window = day[(dep - t0).abs() <= w]
    wo = window.WHEELS_OFF.astype(int).map(_mins)
    rate = max(1.0, ((wo - t0).abs() <= w).sum() / (2 * w / 15))

    queue = window.assign(d=(dep[window.index] - t0).abs()).sort_values("d")
    if max_queue:
        queue = queue.head(max_queue)
    queue = queue.sort_values("DEPARTURE_TIME")

    sid = f"{airport}-2015{int(trig.MONTH):02d}{int(trig.DAY):02d}-{trig.AIRLINE}{int(trig.FLIGHT_NUMBER)}"
    rng = np.random.default_rng(sc["seed"] + zlib.crc32(sid.encode()))
    gates = rng.choice(GATE_POOL, size=len(queue), replace=False)
    flights = [_flight_from_row(r, rng, str(g)) for r, g in zip(queue.itertuples(), gates)]
    # dedupe flight IDs (same flight number twice in one window is rare but possible)
    seen = {}
    for f in flights:
        seen[f.flight] = seen.get(f.flight, 0) + 1
        if seen[f.flight] > 1:
            f.flight += f"-{seen[f.flight]}"

    reason = "WEATHER_DELAY > 15" if trig.WEATHER_DELAY > 15 else "LATE_AIRCRAFT_DELAY > 20"
    s = Scenario(scenario_id=sid, airport=airport, date=f"2015-{int(trig.MONTH):02d}-{int(trig.DAY):02d}",
                 trigger_flight=f"{trig.AIRLINE}{int(trig.FLIGHT_NUMBER)}", trigger_reason=reason,
                 flights=flights, remote_stands=list(sc["remote_stands"]), rate_per_15=round(rate, 2),
                 normal_taxi=normal_taxi(df, airport))
    if with_notes:
        s.notes = make_notes(s, rng)
    return s
