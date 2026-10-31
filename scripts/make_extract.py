"""Write data/flights_extract.csv.gz: the 8 demo airports' departures from flights.csv, original row numbers kept.

The hosted app has no flights.csv (it is never committed), so load_flights() reads this instead.
Run from the repo root: python -m scripts.make_extract
"""
import pandas as pd

from src.sim.demo import AIRPORTS

COLS = ["MONTH", "DAY", "AIRLINE", "FLIGHT_NUMBER", "TAIL_NUMBER", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "DEPARTURE_TIME", "TAXI_OUT", "WHEELS_OFF", "SCHEDULED_TIME", "AIR_TIME", "TAXI_IN",
        "DIVERTED", "CANCELLED", "WEATHER_DELAY", "LATE_AIRCRAFT_DELAY"]

df = pd.read_csv("data/flights.csv", low_memory=False)
df[df.ORIGIN_AIRPORT.isin(AIRPORTS)][COLS].to_csv("data/flights_extract.csv.gz", index_label="ROW", compression="gzip")
